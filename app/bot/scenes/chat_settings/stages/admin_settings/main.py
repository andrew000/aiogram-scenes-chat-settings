from aiogram import F
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
)
from bot.scenes.chat_settings.stages.admin_settings.keyboards import admin_settings_keyboard
from bot.storages.psql import DBChatSettingsModel, RDChatSettingsModel

ADMIN_SETTINGS_WINDOW_TEXT = (
    "👮 Admin settings\n"
    "\n"
    "💁‍♂️ In this window, you can configure the administrative settings of the chat."
)


class AdminSettingsWindow(BaseScene, state=ChatSettingsStates.ADMIN_SETTINGS):
    @on.message.enter()
    async def on_enter_msg(
        self,
        msg: Message,
        state: FSMContext,
        db_session: async_sessionmaker[AsyncSession],
    ) -> None:
        async with db_session() as session:
            stmt = select(DBChatSettingsModel).where(DBChatSettingsModel.id == msg.chat.id)
            chat_settings: DBChatSettingsModel = await session.scalar(stmt)

        sent = await msg.answer(
            ADMIN_SETTINGS_WINDOW_TEXT,
            reply_markup=admin_settings_keyboard(chat_settings),
            message_thread_id=msg.message_thread_id,
        )

        await state.update_data(FSMData(current_message_id=sent.message_id))

    @on.callback_query.enter()
    async def on_enter_cb(
        self,
        cb: CallbackQuery,
        state: FSMContext,
        db_session: async_sessionmaker[AsyncSession],
    ) -> None:
        async with db_session() as session:
            stmt = select(DBChatSettingsModel).where(DBChatSettingsModel.id == cb.message.chat.id)
            chat_settings: DBChatSettingsModel = await session.scalar(stmt)

        sent = await cb.message.edit_text(
            ADMIN_SETTINGS_WINDOW_TEXT,
            reply_markup=admin_settings_keyboard(chat_settings),
        )

        await state.update_data(FSMData(current_message_id=sent.message_id))

    @on.callback_query(ChatSettingsCB.filter(F.action == Action.REPORTS_SWITCH))
    async def reports_switch(
        self,
        cb: CallbackQuery,
        db_session: async_sessionmaker[AsyncSession],
        redis: Redis,
    ) -> None:
        async with db_session() as session:
            stmt = select(DBChatSettingsModel).where(DBChatSettingsModel.id == cb.message.chat.id)
            chat_settings: DBChatSettingsModel = await session.scalar(stmt)
            chat_settings.reports_enabled = not chat_settings.reports_enabled

            await session.commit()

            await RDChatSettingsModel.from_orm(chat_settings).save(redis)

        await self.wizard.retake()

    @on.callback_query(ChatSettingsCB.filter(F.action == Action.SET_REPORTS_POLICY))
    async def set_reports_policy(self, _: CallbackQuery) -> None:
        await self.wizard.goto(ChatSettingsStates.REPORTS_POLICY)

    @on.callback_query(ChatSettingsCB.filter(F.action == Action.BACK))
    async def goto_main_window(self, _: CallbackQuery) -> None:
        await self.wizard.goto(ChatSettingsStates.MAIN_WINDOW)
