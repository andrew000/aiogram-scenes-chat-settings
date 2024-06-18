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
from bot.scenes.chat_settings.stages.general_settings.keyboards import general_settings_keyboard
from bot.storages.psql import DBChatSettingsModel, RDChatSettingsModel

CHAT_SETTINGS_GENERAL_SETTINGS_WINDOW_TEXT = (
    "<b>⚙️ General chat settings</b>\n"
    "\n"
    "💁‍♂️ In this window, you can configure general chat settings, such as language, time zone, "
    "greetings, farewells, and reports."
)


class GeneralSettingsWindow(BaseScene, state=ChatSettingsStates.GENERAL_SETTINGS):
    @on.message.enter()
    async def on_enter_msg(
        self,
        msg: Message,
        bot: Bot,
        state: FSMContext,
        chat_settings: RDChatSettingsModel,
        db_session: async_sessionmaker[AsyncSession],
    ) -> None:
        data: FSMData = await state.get_data()

        async with db_session() as session:
            stmt = select(DBChatSettingsModel).where(DBChatSettingsModel.id == msg.chat.id)
            chat_settings: DBChatSettingsModel = await session.scalar(stmt)

        sent = await bot.send_message(
            chat_id=msg.chat.id,
            text=CHAT_SETTINGS_GENERAL_SETTINGS_WINDOW_TEXT,
            reply_markup=general_settings_keyboard(chat_settings),
            message_thread_id=data["current_topic_id"],
        )

        await state.update_data(FSMData(current_message_id=sent.message_id))

    @on.callback_query.enter()
    async def on_enter_cb(
        self,
        cb: CallbackQuery,
        bot: Bot,
        state: FSMContext,
        chat_settings: RDChatSettingsModel,
        db_session: async_sessionmaker[AsyncSession],
        redis: Redis,
    ) -> None:
        await process_message_delete(bot=bot, chat_id=cb.message.chat.id, state=state, redis=redis)

        async with db_session() as session:
            stmt = select(DBChatSettingsModel).where(DBChatSettingsModel.id == cb.message.chat.id)
            chat_settings: DBChatSettingsModel = await session.scalar(stmt)

        sent = await cb.message.edit_text(
            text=CHAT_SETTINGS_GENERAL_SETTINGS_WINDOW_TEXT,
            reply_markup=general_settings_keyboard(chat_settings),
        )

        await state.update_data(FSMData(current_message_id=sent.message_id))

    @on.callback_query(ChatSettingsCB.filter(F.action == Action.GOTO_SET_LANGUAGE))
    async def goto_select_language(self, _: CallbackQuery) -> None:
        await self.wizard.goto(ChatSettingsStates.LANGUAGE)

    @on.callback_query(ChatSettingsCB.filter(F.action == Action.GOTO_SET_TIMEZONE))
    async def goto_select_timezone(self, _: CallbackQuery) -> None:
        await self.wizard.goto(ChatSettingsStates.TIMEZONE)

    @on.callback_query(ChatSettingsCB.filter(F.action == Action.GREETING_SWITCH))
    async def greeting_switch(
        self,
        cb: CallbackQuery,
        db_session: async_sessionmaker[AsyncSession],
        redis: Redis,
    ) -> None:
        async with db_session() as session:
            stmt = select(DBChatSettingsModel).where(DBChatSettingsModel.id == cb.message.chat.id)
            chat_settings: DBChatSettingsModel = await session.scalar(stmt)
            chat_settings.greeting_enabled = not chat_settings.greeting_enabled

            await session.commit()

            await RDChatSettingsModel.from_orm(chat_settings).save(redis)

        await self.wizard.retake()

    @on.callback_query(ChatSettingsCB.filter(F.action == Action.GREETING_SETUP))
    async def greeting_setup(
        self,
        cb: CallbackQuery,
        state: FSMContext,
    ) -> None:
        data = await state.get_data()
        await state.update_data(
            FSMData(
                bot_messages_to_delete=list(
                    {*data["bot_messages_to_delete"], cb.message.message_id}
                ),
                user_messages_to_delete=list({*data["user_messages_to_delete"]}),
            )
        )
        await self.wizard.goto(ChatSettingsStates.GREETING)

    @on.callback_query(ChatSettingsCB.filter(F.action == Action.FAREWELL_SWITCH))
    async def farewell_switch(
        self,
        cb: CallbackQuery,
        db_session: async_sessionmaker[AsyncSession],
        redis: Redis,
    ) -> None:
        async with db_session() as session:
            stmt = select(DBChatSettingsModel).where(DBChatSettingsModel.id == cb.message.chat.id)
            chat_settings: DBChatSettingsModel = await session.scalar(stmt)
            chat_settings.farewell_enabled = not chat_settings.farewell_enabled

            await session.commit()

            await RDChatSettingsModel.from_orm(chat_settings).save(redis)

        await self.wizard.retake()

    @on.callback_query(ChatSettingsCB.filter(F.action == Action.FAREWELL_SETUP))
    async def farewell_setup(self, cb: CallbackQuery, state: FSMContext) -> None:
        data = await state.get_data()
        await state.update_data(
            FSMData(
                bot_messages_to_delete=list(
                    {*data["bot_messages_to_delete"], cb.message.message_id}
                ),
                user_messages_to_delete=list({*data["user_messages_to_delete"]}),
            )
        )
        await self.wizard.goto(ChatSettingsStates.FAREWELL)

    @on.callback_query(ChatSettingsCB.filter(F.action == Action.BACK))
    async def goto_main_window(self, _: CallbackQuery) -> None:
        await self.wizard.goto(ChatSettingsStates.MAIN_WINDOW)
