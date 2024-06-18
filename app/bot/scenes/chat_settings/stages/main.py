from aiogram import F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.scene import on
from aiogram.types import CallbackQuery, Message

from bot.scenes.chat_settings.base import (
    Action,
    BaseScene,
    ChatSettingsCB,
    ChatSettingsStates,
    FSMData,
)
from bot.scenes.chat_settings.stages.keyboards import main_window_keyboard


class ChatSettingsMainWindow(BaseScene, state=ChatSettingsStates.MAIN_WINDOW):
    @on.message.enter()
    async def on_enter_msg(self, msg: Message, state: FSMContext) -> None:
        sent = await msg.answer(
            "💁‍♂️ Select the settings item:",
            reply_markup=main_window_keyboard(),
        )

        await state.update_data(
            FSMData(
                owner_id=msg.from_user.id,
                current_message_id=sent.message_id,
                current_topic_id=msg.message_thread_id,
                bot_messages_to_delete=[],
                user_messages_to_delete=[],
            ),
        )

    @on.callback_query.enter()
    async def on_enter_cb(self, cb: CallbackQuery, state: FSMContext) -> None:
        sent = await cb.message.edit_text(
            "💁‍♂️ Select the settings item:",
            reply_markup=main_window_keyboard(),
        )

        await state.update_data(
            FSMData(
                owner_id=cb.from_user.id,
                current_message_id=sent.message_id,
                current_topic_id=cb.message.message_thread_id,
                bot_messages_to_delete=[],
                user_messages_to_delete=[],
            ),
        )

    @on.callback_query(ChatSettingsCB.filter(F.action == Action.GENERAL_SETTINGS))
    async def goto_general_settings(self, _: CallbackQuery) -> None:
        await self.wizard.goto(ChatSettingsStates.GENERAL_SETTINGS)

    @on.callback_query(ChatSettingsCB.filter(F.action == Action.ADMIN_SETTINGS))
    async def goto_admin_settings(self, _: CallbackQuery) -> None:
        await self.wizard.goto(ChatSettingsStates.ADMIN_SETTINGS)
