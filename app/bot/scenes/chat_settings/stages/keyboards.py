from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.scenes.chat_settings.base import Action, ChatSettingsCB


def main_window_keyboard() -> InlineKeyboardMarkup:
    return (
        InlineKeyboardBuilder()
        .row(
            InlineKeyboardButton(
                text="⚙️ General settings",
                callback_data=ChatSettingsCB(action=Action.GENERAL_SETTINGS).pack(),
            ),
        )
        .row(
            InlineKeyboardButton(
                text="👮 Admin settings",
                callback_data=ChatSettingsCB(action=Action.ADMIN_SETTINGS).pack(),
            ),
        )
        .row(
            InlineKeyboardButton(
                text="❌ Exit",
                callback_data=ChatSettingsCB(action=Action.EXIT).pack(),
            ),
        )
        .as_markup()
    )
