from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.scenes.chat_settings.base import (
    Action,
    ChatSettingsCB,
    PossibleLanguages,
    SelectLanguageCB,
)
from bot.storages.psql import DBChatSettingsModel


def language_keyboard() -> InlineKeyboardMarkup:
    return (
        InlineKeyboardBuilder()
        .row(
            *[
                InlineKeyboardButton(
                    text=language.value,
                    callback_data=SelectLanguageCB(language_code=language.name).pack(),
                )
                for language in PossibleLanguages
            ],
            width=2,
        )
        .as_markup()
    )


def timezone_keyboard() -> InlineKeyboardMarkup:
    return (
        InlineKeyboardBuilder()
        .row(
            InlineKeyboardButton(
                text="ℹ️ Help",
                url="https://en.wikipedia.org/wiki/List_of_tz_database_time_zones",
            ),
        )
        .row(
            InlineKeyboardButton(
                text="🔙 Back",
                callback_data=ChatSettingsCB(action=Action.BACK).pack(),
            ),
        )
        .as_markup()
    )


def general_settings_keyboard(chat_settings: DBChatSettingsModel) -> InlineKeyboardMarkup:
    return (
        InlineKeyboardBuilder()
        .row(
            InlineKeyboardButton(
                text=f"🌐 Language: "
                f"{PossibleLanguages.__getitem__(chat_settings.language_code).value}",
                callback_data=ChatSettingsCB(action=Action.GOTO_SET_LANGUAGE).pack(),
            ),
        )
        .row(
            InlineKeyboardButton(
                text=f"⏰ Timezone: {chat_settings.timezone or 'UTC'}",
                callback_data=ChatSettingsCB(action=Action.GOTO_SET_TIMEZONE).pack(),
            ),
        )
        .row(
            InlineKeyboardButton(
                text=f"✋ Greeting: {'✅' if chat_settings.greeting_enabled else '❌'}",
                callback_data=ChatSettingsCB(action=Action.GREETING_SWITCH).pack(),
            ),
            InlineKeyboardButton(
                text="⚙️ Setup",
                callback_data=ChatSettingsCB(action=Action.GREETING_SETUP).pack(),
            ),
        )
        .row(
            InlineKeyboardButton(
                text=f"👋 Farewell: {'✅' if chat_settings.farewell_enabled else '❌'}",
                callback_data=ChatSettingsCB(action=Action.FAREWELL_SWITCH).pack(),
            ),
            InlineKeyboardButton(
                text="⚙️ Setup",
                callback_data=ChatSettingsCB(action=Action.FAREWELL_SETUP).pack(),
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
