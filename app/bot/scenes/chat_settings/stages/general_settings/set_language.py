from aiogram.fsm.context import FSMContext
from aiogram.fsm.scene import After, on
from aiogram.types import CallbackQuery, Message
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from bot.scenes.chat_settings.base import BaseScene, ChatSettingsStates, FSMData, SelectLanguageCB
from bot.scenes.chat_settings.stages.general_settings.keyboards import language_keyboard
from bot.storages.psql import DBChatSettingsModel, RDChatSettingsModel


class SetLanguageWindow(BaseScene, state=ChatSettingsStates.LANGUAGE):
    @on.message.enter()
    async def on_enter_msg(self, msg: Message, state: FSMContext) -> None:
        sent = await msg.answer("🌐 Choose chat language:", reply_markup=language_keyboard())
        await state.update_data(FSMData(current_message_id=sent.message_id))

    @on.callback_query.enter()
    async def on_enter_cb(self, cb: CallbackQuery, state: FSMContext) -> None:
        sent = await cb.message.edit_text(
            "🌐 Choose chat language:",
            reply_markup=language_keyboard(),
        )

        await state.update_data(FSMData(current_message_id=sent.message_id))

    @on.callback_query(
        SelectLanguageCB.filter(),
        after=After.goto(ChatSettingsStates.GENERAL_SETTINGS),
    )
    async def set_language(
        self,
        cb: CallbackQuery,
        callback_data: SelectLanguageCB,
        db_session: async_sessionmaker[AsyncSession],
        redis: Redis,
    ) -> None:
        async with db_session() as session:
            stmt = select(DBChatSettingsModel).where(DBChatSettingsModel.id == cb.message.chat.id)
            chat_settings: DBChatSettingsModel = await session.scalar(stmt)
            chat_settings.language_code = callback_data.language_code.value

            await session.commit()

            await RDChatSettingsModel.from_orm(chat_settings).save(redis)
