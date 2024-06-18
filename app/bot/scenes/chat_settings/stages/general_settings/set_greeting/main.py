from aiogram import Bot, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.scene import on
from aiogram.types import CallbackQuery, Message
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from bot.scenes.chat_settings.base import (
    Action,
    BaseScene,
    ChatSettingsCB,
    ChatSettingsStates,
    FSMData,
    process_message_delete,
)
from bot.scenes.chat_settings.stages.general_settings.set_greeting.greeting_set_media import (
    reset_greeting_media,
)
from bot.scenes.chat_settings.stages.general_settings.set_greeting.greeting_set_text import (
    reset_greeting_text,
)
from bot.scenes.chat_settings.stages.general_settings.set_greeting.keyboards import (
    greeting_keyboard,
)
from bot.storages.psql import DBChatSettingsModel, RDChatSettingsModel
from bot.storages.psql.chat.chat_settings_model import GreetingFarewellType
from bot.storages.redis.bot.reaction_media import RDBotReactionMedia
from bot.utils.greeting_farewell_builder import GF_Message, build_greeting_message

CHAT_SETTINGS_SET_GREETING_WINDOW_TEXT = (
    "💁‍♂️ In this window, you can customize the greeting for new chat members.\n"
    "<blockquote expandable>\n"
    "📝 To set the greeting text, click the button: <code>📝 Text</code>\n"
    "\n"
    "🖼 To set the media, click the button: <code>🖼 Media</code>\n"
    "\n"
    "🆔 To set the Topic ID where the bot will send greetings, click the button: <code>🆔 Topic "
    "ID</code>\n"
    "\n"
    "♻️ To reset a specific setting, click the button: <code>♻️ Reset</code>\n"
    "\n"
    "🗑 To reset all greeting settings, press the button: <code>🗑 Reset all</code></blockquote>"
)


class SetGreetingWindow(BaseScene, state=ChatSettingsStates.GREETING):
    @on.callback_query.enter()
    async def on_enter_cb(
        self,
        cb: CallbackQuery,
        bot: Bot,
        state: FSMContext,
        bot_reaction_media: RDBotReactionMedia,
        db_session: async_sessionmaker[AsyncSession],
        redis: Redis,
        updated: bool = True,
    ) -> None:
        await process_message_delete(
            bot=bot, chat_id=cb.message.chat.id, state=state, redis=redis, updated=updated
        )

        async with db_session() as session:
            stmt = select(DBChatSettingsModel).where(DBChatSettingsModel.id == cb.message.chat.id)
            chat_settings: DBChatSettingsModel = await session.scalar(stmt)
            chat_settings: RDChatSettingsModel = RDChatSettingsModel.from_orm(chat_settings)

        if updated is True:
            sent_greeting_message: GF_Message = await bot(
                build_greeting_message(
                    chat_id=cb.message.chat.id,
                    topic_id=cb.message.message_thread_id if cb.message.chat.is_forum else None,
                    user=cb.from_user,
                    chat_settings=chat_settings,
                    bot_reaction_media=bot_reaction_media,
                ),
            )
            sent = await bot.send_message(
                chat_id=cb.message.chat.id,
                text=CHAT_SETTINGS_SET_GREETING_WINDOW_TEXT,
                reply_to_message_id=sent_greeting_message.message_id,
                reply_markup=greeting_keyboard(chat_settings),
            )

            await state.update_data(
                FSMData(
                    current_message_id=sent.message_id,
                    greeting_farewell_message_id=sent_greeting_message.message_id,
                ),
            )

        elif cb.message.html_text != CHAT_SETTINGS_SET_GREETING_WINDOW_TEXT:
            sent = await cb.message.edit_text(
                text=CHAT_SETTINGS_SET_GREETING_WINDOW_TEXT,
                reply_markup=greeting_keyboard(chat_settings),
            )

        else:
            sent = cb.message

        if updated is False:
            await state.update_data(FSMData(current_message_id=sent.message_id))

    @on.message.enter()
    async def on_enter_msg(
        self,
        msg: Message,
        bot: Bot,
        state: FSMContext,
        bot_reaction_media: RDBotReactionMedia,
        db_session: async_sessionmaker[AsyncSession],
        redis: Redis,
        updated: bool = True,
    ) -> None:
        data: FSMData = await state.get_data()
        await process_message_delete(
            bot=bot, chat_id=msg.chat.id, state=state, redis=redis, updated=updated
        )

        async with db_session() as session:
            stmt = select(DBChatSettingsModel).where(DBChatSettingsModel.id == msg.chat.id)
            chat_settings: DBChatSettingsModel = await session.scalar(stmt)
            chat_settings: RDChatSettingsModel = RDChatSettingsModel.from_orm(chat_settings)

        if updated is True:
            sent_greeting_message: GF_Message = await bot(
                build_greeting_message(
                    chat_id=msg.chat.id,
                    topic_id=data["current_topic_id"],
                    user=msg.from_user,
                    chat_settings=chat_settings,
                    bot_reaction_media=bot_reaction_media,
                ),
            )
            sent = await bot.send_message(
                chat_id=msg.chat.id,
                text=CHAT_SETTINGS_SET_GREETING_WINDOW_TEXT,
                message_thread_id=data["current_topic_id"],
                reply_to_message_id=sent_greeting_message.message_id,
                reply_markup=greeting_keyboard(chat_settings),
            )

            await state.update_data(
                FSMData(
                    current_message_id=sent.message_id,
                    greeting_farewell_message_id=sent_greeting_message.message_id,
                ),
            )

    @on.callback_query(ChatSettingsCB.filter(F.action == Action.GREETING_SET_TYPE))
    async def set_greeting_type_handler(self, _: CallbackQuery) -> None:
        await self.wizard.goto(ChatSettingsStates.GREETING_SET_TYPE)

    @on.callback_query(ChatSettingsCB.filter(F.action == Action.GREETING_SET_TEXT))
    async def set_greeting_text_handler(self, _: CallbackQuery) -> None:
        await self.wizard.goto(ChatSettingsStates.GREETING_SET_TEXT)

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
                        },
                    ),
                    user_messages_to_delete=list({*data["user_messages_to_delete"]}),
                ),
            )

        else:
            await cb.answer(text="✅", show_alert=True)

        await self.wizard.retake(updated=updated)

    @on.callback_query(ChatSettingsCB.filter(F.action == Action.GREETING_SET_MEDIA))
    async def set_greeting_media_id_handler(self, _: CallbackQuery) -> None:
        await self.wizard.goto(ChatSettingsStates.GREETING_SET_MEDIA)

    @on.callback_query(ChatSettingsCB.filter(F.action == Action.GREETING_RESET_MEDIA))
    async def reset_greeting_media_handler(
        self,
        cb: CallbackQuery,
        state: FSMContext,
        db_session: async_sessionmaker[AsyncSession],
        redis: Redis,
    ) -> None:
        data = await state.get_data()

        updated = await reset_greeting_media(cb, db_session, redis)

        if updated is True:
            await state.update_data(
                FSMData(
                    bot_messages_to_delete=list(
                        {
                            *data["bot_messages_to_delete"],
                            cb.message.message_id,
                            data["greeting_farewell_message_id"],
                        },
                    ),
                    user_messages_to_delete=list({*data["user_messages_to_delete"]}),
                ),
            )

        else:
            await cb.answer(text="✅", show_alert=True)

        await self.wizard.goto(ChatSettingsStates.GREETING, updated=updated)

    @on.callback_query(ChatSettingsCB.filter(F.action == Action.GREETING_SET_TOPIC))
    async def set_greeting_topic_id_handler(self, _: CallbackQuery) -> None:
        await self.wizard.goto(ChatSettingsStates.GREETING_SET_TOPIC_ID)

    @on.callback_query(ChatSettingsCB.filter(F.action == Action.GREETING_RESET_TOPIC))
    async def reset_greeting_topic_id_handler(
        self,
        cb: CallbackQuery,
        db_session: async_sessionmaker[AsyncSession],
        redis: Redis,
    ) -> None:
        async with db_session() as session:
            stmt = select(DBChatSettingsModel).where(DBChatSettingsModel.id == cb.message.chat.id)
            chat_settings: DBChatSettingsModel = await session.scalar(stmt)
            chat_settings.greeting_topic_id = None

            await session.commit()

            await RDChatSettingsModel.from_orm(chat_settings).save(redis)

        await cb.answer(text="Chat topic ID has been reset successfully! ✅", show_alert=True)

    @on.callback_query(ChatSettingsCB.filter(F.action == Action.GREETING_RESET_ALL))
    async def reset_greeting_all_handler(
        self,
        cb: CallbackQuery,
        state: FSMContext,
        db_session: async_sessionmaker[AsyncSession],
        redis: Redis,
    ) -> None:
        data = await state.get_data()

        async with db_session() as session:
            stmt = select(DBChatSettingsModel).where(DBChatSettingsModel.id == cb.message.chat.id)
            chat_settings: DBChatSettingsModel = await session.scalar(stmt)
            chat_settings.greeting_type = GreetingFarewellType.PHOTO.value
            chat_settings.greeting_text = None
            chat_settings.greeting_photo_id = None
            chat_settings.greeting_video_id = None
            chat_settings.greeting_gif_id = None
            chat_settings.greeting_sticker_id = None
            chat_settings.greeting_topic_id = None

            await session.commit()

            await RDChatSettingsModel.from_orm(chat_settings).save(redis)

        await cb.answer(text="✅", show_alert=True)

        await state.update_data(
            FSMData(
                bot_messages_to_delete=list(
                    {
                        *data["bot_messages_to_delete"],
                        cb.message.message_id,
                        data["greeting_farewell_message_id"],
                    },
                ),
                user_messages_to_delete=list({*data["user_messages_to_delete"]}),
            ),
        )

        await self.wizard.goto(ChatSettingsStates.GREETING, updated=True)

    @on.callback_query(ChatSettingsCB.filter(F.action == Action.BACK))
    async def back_handler(self, _: CallbackQuery, state: FSMContext) -> None:
        data = await state.get_data()

        await state.update_data(
            FSMData(
                bot_messages_to_delete=list(
                    {
                        *data["bot_messages_to_delete"],
                        data["greeting_farewell_message_id"],
                    },
                ),
                user_messages_to_delete=list({*data["user_messages_to_delete"]}),
            ),
        )

        await self.wizard.goto(ChatSettingsStates.GENERAL_SETTINGS, updated=False)
