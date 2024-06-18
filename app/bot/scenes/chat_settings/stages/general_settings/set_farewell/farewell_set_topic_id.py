from aiogram import Bot, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.fsm.scene import on
from aiogram.types import CallbackQuery, Message, ReactionTypeEmoji
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from bot.errors.errors import TopicClosedError, resolve_exception
from bot.scenes.chat_settings.base import (
    Action,
    BaseScene,
    ChatSettingsCB,
    ChatSettingsStates,
    FSMData,
)
from bot.scenes.chat_settings.stages.general_settings.set_farewell.keyboards import (
    farewell_topic_id_keyboard,
)
from bot.storages.psql import DBChatSettingsModel, RDChatSettingsModel

CHAT_SETTINGS_SET_TOPIC_ID_WINDOW_TEXT = (
    "💁‍♂️ Now send any text message in the Topic where the bot should send greetings/farewells "
    "to chat members.\n"
    "\n"
    "💾 Current Topic ID: <blockquote>{stored_topic_id}</blockquote>"
)


class SetFarewellTopicIDWindow(BaseScene, state=ChatSettingsStates.FAREWELL_SET_TOPIC_ID):
    @on.callback_query.enter()
    async def on_enter_cb(
        self,
        cb: CallbackQuery,
        state: FSMContext,
        db_session: async_sessionmaker[AsyncSession],
    ) -> None:
        if not cb.message.is_topic_message:
            await cb.answer("⚠️ This chat doesn't contain Topics", show_alert=True)
            await self.wizard.goto(ChatSettingsStates.FAREWELL, updated=False)
            return

        async with db_session() as session:
            stmt = select(DBChatSettingsModel).where(DBChatSettingsModel.id == cb.message.chat.id)
            chat_settings: DBChatSettingsModel = await session.scalar(stmt)

        sent = await cb.message.edit_text(
            CHAT_SETTINGS_SET_TOPIC_ID_WINDOW_TEXT.format(
                stored_topic_id=(chat_settings.farewell_topic_id or "General"),
            ),
            reply_markup=farewell_topic_id_keyboard(),
        )

        await state.update_data(FSMData(current_message_id=sent.message_id))

    @on.message(F.text)
    async def set_farewell_topic_id_handler(
        self,
        msg: Message,
        bot: Bot,
        state: FSMContext,
        db_session: async_sessionmaker[AsyncSession],
        redis: Redis,
    ) -> None:
        topic_id = msg.message_thread_id
        data: FSMData = await state.get_data()

        async with db_session() as session:
            stmt = select(DBChatSettingsModel).where(DBChatSettingsModel.id == msg.chat.id)
            chat_settings: DBChatSettingsModel = await session.scalar(stmt)
            chat_settings.farewell_topic_id = topic_id

            await session.commit()

            await RDChatSettingsModel.from_orm(chat_settings).save(redis)

        await state.update_data(
            FSMData(
                bot_messages_to_delete=list(
                    {
                        *data["bot_messages_to_delete"],
                        data["current_message_id"],
                        data["greeting_farewell_message_id"],
                    },
                ),
                user_messages_to_delete=list({*data["user_messages_to_delete"]}),
            ),
        )
        try:
            await msg.answer(
                text="✅ Topic ID saved:\n"
                "\n"
                f"TOPIC_ID: <blockquote><code>{topic_id or 'General'}</code></blockquote>"
            )
        except TelegramBadRequest as e:
            e = resolve_exception(e)

            match e:
                case TopicClosedError():
                    await msg.react([ReactionTypeEmoji(emoji="👎")])
                    await bot.send_message(
                        chat_id=msg.chat.id,
                        message_thread_id=data["current_topic_id"],
                        text=f"⚠️ {msg.from_user.mention_html(msg.from_user.username)}, the "
                        f"selected Topic is closed, which means that the bot will not be "
                        f"able to send messages to it.\n"
                        f"\n"
                        f"💁‍♂️ Give me the rights to <b>Manage Threads</b> in the chat "
                        f"administrator settings or select another Topic.\n"
                        f"\n"
                        f"💡 To cancel, click the button in the message with the settings: "
                        f"<blockquote><code>🔙 Back</code></blockquote> or send /cancel",
                    )
                    return

                case _:
                    raise

        await self.wizard.goto(ChatSettingsStates.FAREWELL)

    @on.callback_query(ChatSettingsCB.filter(F.action == Action.FAREWELL_RESET_TOPIC))
    async def reset_farewell_topic_id_handler(
        self,
        cb: CallbackQuery,
        db_session: async_sessionmaker[AsyncSession],
        redis: Redis,
    ) -> None:
        async with db_session() as session:
            stmt = select(DBChatSettingsModel).where(DBChatSettingsModel.id == cb.message.chat.id)
            chat_settings: DBChatSettingsModel = await session.scalar(stmt)
            chat_settings.farewell_topic_id = None

            await session.commit()

            await RDChatSettingsModel.from_orm(chat_settings).save(redis)

        await cb.answer("✅ Topic ID reset.", show_alert=True)

        await self.wizard.goto(ChatSettingsStates.FAREWELL, updated=False)

    @on.callback_query(ChatSettingsCB.filter(F.action == Action.BACK))
    async def back_handler(self, _: CallbackQuery) -> None:
        await self.wizard.goto(ChatSettingsStates.FAREWELL, updated=False)
