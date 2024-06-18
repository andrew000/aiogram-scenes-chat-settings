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
    ChatSettingsFarewellCB,
    ChatSettingsStates,
    FSMData,
)
from bot.scenes.chat_settings.stages.general_settings.set_farewell.keyboards import (
    farewell_type_keyboard,
)
from bot.storages.psql import DBChatSettingsModel, RDChatSettingsModel

CHAT_SETTINGS_FAREWELL_SET_TYPE_WINDOW_TEXT = (
    "💁‍♂️ In this window, you need to select the type of message that the bot will send to "
    "members who have left the chat.\n"
    "\n"
    "📝 The message type can be plain text, image, video, GIF, or sticker.\n"
    "\n"
    "💡 Pay attention:\n"
    "— The message supports formatting. This means that if you make a text in italic, "
    "the bot will also send it in italic.\n"
    "— Stickers do not support text display."
)


class SetFarewellTypeWindow(BaseScene, state=ChatSettingsStates.FAREWELL_SET_TYPE):
    @on.callback_query.enter()
    async def on_enter_cb(self, cb: CallbackQuery, state: FSMContext) -> None:
        sent = await cb.message.edit_text(
            CHAT_SETTINGS_FAREWELL_SET_TYPE_WINDOW_TEXT,
            reply_markup=farewell_type_keyboard(),
        )

        await state.update_data(FSMData(current_message_id=sent.message_id))

    @on.callback_query(ChatSettingsFarewellCB.filter())
    async def set_farewell_type_handler(
        self,
        cb: CallbackQuery,
        callback_data: ChatSettingsFarewellCB,
        state: FSMContext,
        chat_settings: RDChatSettingsModel,
        db_session: async_sessionmaker[AsyncSession],
        redis: Redis,
    ) -> None:
        data: FSMData = await state.get_data()

        if callback_data.farewell_type == chat_settings.farewell_type:
            await self.wizard.goto(ChatSettingsStates.FAREWELL, updated=False)
            return

        async with db_session() as session:
            stmt = select(DBChatSettingsModel).where(DBChatSettingsModel.id == cb.message.chat.id)
            chat_settings: DBChatSettingsModel = await session.scalar(stmt)
            chat_settings.farewell_type = callback_data.farewell_type.value

            await session.commit()

            await RDChatSettingsModel.from_orm(chat_settings).save(redis)

        await state.update_data(
            FSMData(
                bot_messages_to_delete=list(
                    {
                        *data["bot_messages_to_delete"],
                        cb.message.message_id,
                        data["current_message_id"],
                    },
                ),
                user_messages_to_delete=list({*data["user_messages_to_delete"]}),
            ),
        )

        await self.wizard.goto(ChatSettingsStates.FAREWELL)

    @on.callback_query(ChatSettingsCB.filter(F.action == Action.BACK))
    async def back_handler(self, _: CallbackQuery) -> None:
        await self.wizard.goto(ChatSettingsStates.FAREWELL, updated=False)
