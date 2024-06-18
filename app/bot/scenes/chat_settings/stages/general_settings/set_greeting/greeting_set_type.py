from aiogram import F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.scene import on
from aiogram.types import CallbackQuery
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from bot.scenes.chat_settings.base import (
    Action,
    BaseScene,
    ChatSettingsCB,
    ChatSettingsGreetingCB,
    ChatSettingsStates,
    FSMData,
)
from bot.scenes.chat_settings.stages.general_settings.set_greeting.keyboards import (
    greeting_type_keyboard,
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


class SetGreetingTypeWindow(BaseScene, state=ChatSettingsStates.GREETING_SET_TYPE):
    @on.callback_query.enter()
    async def on_enter_cb(self, cb: CallbackQuery, state: FSMContext) -> None:
        sent = await cb.message.edit_text(
            text=CHAT_SETTINGS_GREETING_SET_TEXT_WINDOW_TEXT,
            reply_markup=greeting_type_keyboard(),
        )

        await state.update_data(FSMData(current_message_id=sent.message_id))

    @on.callback_query(ChatSettingsGreetingCB.filter())
    async def set_greeting_type_handler(
        self,
        cb: CallbackQuery,
        callback_data: ChatSettingsGreetingCB,
        state: FSMContext,
        chat_settings: RDChatSettingsModel,
        db_session: async_sessionmaker[AsyncSession],
        redis: Redis,
    ) -> None:
        data: FSMData = await state.get_data()

        if callback_data.greeting_type == chat_settings.greeting_type:
            await self.wizard.goto(ChatSettingsStates.GREETING, updated=False)
            return

        async with db_session() as session:
            stmt = select(DBChatSettingsModel).where(DBChatSettingsModel.id == cb.message.chat.id)
            chat_settings: DBChatSettingsModel = await session.scalar(stmt)
            chat_settings.greeting_type = callback_data.greeting_type.value

            await session.commit()

            await RDChatSettingsModel.from_orm(chat_settings).save(redis)

        await state.update_data(
            FSMData(
                bot_messages_to_delete=list(
                    {
                        *data["bot_messages_to_delete"],
                        cb.message.message_id,
                        data["greeting_farewell_message_id"],
                    }
                ),
                user_messages_to_delete=list({*data["user_messages_to_delete"]}),
            ),
        )

        await self.wizard.goto(ChatSettingsStates.GREETING)

    @on.callback_query(ChatSettingsCB.filter(F.action == Action.BACK))
    async def back_handler(self, _: CallbackQuery) -> None:
        await self.wizard.goto(ChatSettingsStates.GREETING, updated=False)
