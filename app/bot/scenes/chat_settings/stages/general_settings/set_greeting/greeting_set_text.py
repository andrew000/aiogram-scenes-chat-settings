from aiogram import F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.scene import on
from aiogram.types import CallbackQuery, Message
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from bot.scenes.chat_settings.base import (
    MAX_GREETING_FAREWELL_LENGTH,
    Action,
    BaseScene,
    ChatSettingsCB,
    ChatSettingsStates,
    FSMData,
)
from bot.scenes.chat_settings.stages.general_settings.set_greeting.keyboards import (
    greeting_text_keyboard,
)
from bot.storages.psql import DBChatSettingsModel, RDChatSettingsModel

CHAT_SETTINGS_GREETING_SET_TEXT_WINDOW_TEXT = (
    "💁‍♂️ In this window, you need to send a message of greeting to the chat members.\n"
    "\n"
    "📝 The message may contain formatting, such as <b>bold</b>, <i>italic</i>, "
    "<code>monospace</code>, etc.\n"
    "\n"
    "💁‍♂️ To mention a user in the text - insert in place of the mention: <blockquote><code>{"
    "mention}</code></blockquote>\n"
    "\n"
    "♻️ To reset the text, press the button <blockquote><code>♻️ Reset</code></blockquote>"
)


class SetGreetingTextWindow(BaseScene, state=ChatSettingsStates.GREETING_SET_TEXT):
    @on.callback_query.enter()
    async def on_enter_cb(self, cb: CallbackQuery, state: FSMContext) -> None:
        sent = await cb.message.edit_text(
            text=CHAT_SETTINGS_GREETING_SET_TEXT_WINDOW_TEXT,
            reply_markup=greeting_text_keyboard(),
        )

        await state.update_data(FSMData(current_message_id=sent.message_id))

    @on.message(F.text & F.text.len() <= MAX_GREETING_FAREWELL_LENGTH)
    async def set_greeting_text_handler(
        self,
        msg: Message,
        state: FSMContext,
        db_session: async_sessionmaker[AsyncSession],
        redis: Redis,
    ) -> None:
        data: FSMData = await state.get_data()

        async with db_session() as session:
            stmt = select(DBChatSettingsModel).where(DBChatSettingsModel.id == msg.chat.id)
            chat_settings: DBChatSettingsModel = await session.scalar(stmt)

            chat_settings.greeting_text = msg.html_text

            await session.commit()

            await RDChatSettingsModel.from_orm(chat_settings).save(redis)

        await state.update_data(
            FSMData(
                bot_messages_to_delete=list(
                    {
                        *data["bot_messages_to_delete"],
                        data["current_message_id"],
                        data["greeting_farewell_message_id"],
                    }
                ),
                user_messages_to_delete=list(
                    {
                        *data["user_messages_to_delete"],
                        msg.message_id,
                    },
                ),
            ),
        )

        await self.wizard.goto(ChatSettingsStates.GREETING, updated=True)

    @on.message(F.text & F.text.len() > MAX_GREETING_FAREWELL_LENGTH)
    async def too_long_greeting_text_handler(self, msg: Message) -> None:
        await msg.answer(
            "⚠️ Text is too long.\n"
            "\n"
            f"💁‍♂️ Maximum text length: <code>{MAX_GREETING_FAREWELL_LENGTH}</code> symbols.\n"
            f"\n"
            f"💡 Enter another text or use /cancel to cancel."
        )

    @on.callback_query(ChatSettingsCB.filter(F.action == Action.GREETING_RESET_TEXT))
    async def reset_greeting_text_handler(
        self,
        cb: CallbackQuery,
        state: FSMContext,
        db_session: async_sessionmaker[AsyncSession],
        redis: Redis,
    ) -> None:
        data = await state.get_data()

        updated = await reset_greeting_text(cb, db_session, redis)

        if updated is True:
            await state.update_data(
                FSMData(
                    bot_messages_to_delete=list(
                        {
                            *data["bot_messages_to_delete"],
                            cb.message.message_id,
                            data["greeting_farewell_message_id"],
                        }
                    ),
                    user_messages_to_delete=list(
                        {*data["user_messages_to_delete"]},
                    ),
                ),
            )

        await self.wizard.goto(ChatSettingsStates.GREETING, updated=updated)

    @on.callback_query(ChatSettingsCB.filter(F.action == Action.BACK))
    async def back_handler_cb(self, _: CallbackQuery) -> None:
        await self.wizard.goto(ChatSettingsStates.GREETING, updated=False)


async def reset_greeting_text(
    cb: CallbackQuery, db_session: async_sessionmaker[AsyncSession], redis: Redis
) -> bool:
    updated: bool = False

    async with db_session() as session:
        stmt = select(DBChatSettingsModel).where(DBChatSettingsModel.id == cb.message.chat.id)
        chat_settings: DBChatSettingsModel = await session.scalar(stmt)

        if chat_settings.greeting_text is not None:
            updated = True

        chat_settings.greeting_text = None

        await session.commit()

        await RDChatSettingsModel.from_orm(chat_settings).save(redis)

    return updated
