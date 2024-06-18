from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.scenes.chat_settings.base import Action, ChatSettingsCB
from bot.storages.psql import DBChatSettingsModel


def admin_settings_keyboard(chat_settings: DBChatSettingsModel) -> InlineKeyboardMarkup:
    return (
        InlineKeyboardBuilder()
        .row(
            InlineKeyboardButton(
                text="✅" if chat_settings.reports_enabled is True else "❌ ",
                callback_data=ChatSettingsCB(action=Action.REPORTS_SWITCH).pack(),
            ),
            InlineKeyboardButton(
                text="📕 Reports policy",
                callback_data=ChatSettingsCB(action=Action.SET_REPORTS_POLICY).pack(),
            ),
        )
        .row(
            InlineKeyboardButton(
                text="🔙 Back",
                callback_data=ChatSettingsCB(action=Action.BACK).pack(),
            ),
            InlineKeyboardButton(
                text="❌ Exit",
                callback_data=ChatSettingsCB(action=Action.EXIT).pack(),
            ),
        )
    ).as_markup()
