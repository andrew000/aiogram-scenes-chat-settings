from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.scenes.chat_settings.base import Action, ChatSettingsCB, ChatSettingsGreetingCB
from bot.storages.psql.chat.chat_settings_model import GreetingFarewellType, RDChatSettingsModel


def greeting_keyboard(chat_settings: RDChatSettingsModel) -> InlineKeyboardMarkup:
    match chat_settings.greeting_type:
        case GreetingFarewellType.TEXT:
            greeting_set_type_text = "⚙️ Greeting type: 📝 Text"
        case GreetingFarewellType.PHOTO:
            greeting_set_type_text = "⚙️ Greeting type: 🖼 Photo"
        case GreetingFarewellType.VIDEO:
            greeting_set_type_text = "⚙️ Greeting type: 📹 Video"
        case GreetingFarewellType.GIF:
            greeting_set_type_text = "⚙️ Greeting type: 🎞 GIF"
        case GreetingFarewellType.STICKER:
            greeting_set_type_text = "⚙️ Greeting type: 🤪 Sticker"
        case _:
            greeting_set_type_text = "⚙️ Greeting type: Unknown type"

    return (
        InlineKeyboardBuilder()
        .row(
            InlineKeyboardButton(
                text=greeting_set_type_text,
                callback_data=ChatSettingsCB(action=Action.GREETING_SET_TYPE).pack(),
            ),
        )
        .row(
            InlineKeyboardButton(
                text="📝 Text",
                callback_data=ChatSettingsCB(action=Action.GREETING_SET_TEXT).pack(),
            ),
            InlineKeyboardButton(
                text="♻️ Reset",
                callback_data=ChatSettingsCB(action=Action.GREETING_RESET_TEXT).pack(),
            ),
        )
        .row(
            InlineKeyboardButton(
                text="🖼 Media",
                callback_data=ChatSettingsCB(action=Action.GREETING_SET_MEDIA).pack(),
            ),
            InlineKeyboardButton(
                text="♻️ Reset",
                callback_data=ChatSettingsCB(action=Action.GREETING_RESET_MEDIA).pack(),
            ),
        )
        .row(
            InlineKeyboardButton(
                text="🆔 Topic ID",
                callback_data=ChatSettingsCB(action=Action.GREETING_SET_TOPIC).pack(),
            ),
            InlineKeyboardButton(
                text="♻️ Reset",
                callback_data=ChatSettingsCB(action=Action.GREETING_RESET_TOPIC).pack(),
            ),
        )
        .row(
            InlineKeyboardButton(
                text="🔙 Back",
                callback_data=ChatSettingsCB(action=Action.BACK).pack(),
            ),
            InlineKeyboardButton(
                text="♻️ Reset all",
                callback_data=ChatSettingsCB(action=Action.GREETING_RESET_ALL).pack(),
            ),
        )
        .as_markup()
    )


def greeting_type_keyboard() -> InlineKeyboardMarkup:
    return (
        InlineKeyboardBuilder()
        .row(
            InlineKeyboardButton(
                text="📝 Text",
                callback_data=ChatSettingsGreetingCB(
                    greeting_type=GreetingFarewellType.TEXT.value
                ).pack(),
            ),
            InlineKeyboardButton(
                text="🖼 Photo",
                callback_data=ChatSettingsGreetingCB(
                    greeting_type=GreetingFarewellType.PHOTO.value
                ).pack(),
            ),
        )
        .row(
            InlineKeyboardButton(
                text="📹 Video",
                callback_data=ChatSettingsGreetingCB(
                    greeting_type=GreetingFarewellType.VIDEO.value
                ).pack(),
            ),
            InlineKeyboardButton(
                text="🎞 GIF",
                callback_data=ChatSettingsGreetingCB(
                    greeting_type=GreetingFarewellType.GIF.value
                ).pack(),
            ),
        )
        .row(
            InlineKeyboardButton(
                text="🤪 Sticker",
                callback_data=ChatSettingsGreetingCB(
                    greeting_type=GreetingFarewellType.STICKER.value
                ).pack(),
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


def greeting_text_keyboard() -> InlineKeyboardMarkup:
    return (
        InlineKeyboardBuilder()
        .row(
            InlineKeyboardButton(
                text="🔙 Back",
                callback_data=ChatSettingsCB(action=Action.BACK).pack(),
            ),
            InlineKeyboardButton(
                text="♻️ Reset",
                callback_data=ChatSettingsCB(action=Action.GREETING_RESET_TEXT).pack(),
            ),
        )
        .as_markup()
    )


def greeting_media_keyboard() -> InlineKeyboardMarkup:
    return (
        InlineKeyboardBuilder()
        .row(
            InlineKeyboardButton(
                text="🔙 Back",
                callback_data=ChatSettingsCB(action=Action.BACK).pack(),
            ),
            InlineKeyboardButton(
                text="♻️ Reset",
                callback_data=ChatSettingsCB(action=Action.GREETING_RESET_MEDIA).pack(),
            ),
        )
        .as_markup()
    )


def greeting_topic_id_keyboard() -> InlineKeyboardMarkup:
    return (
        InlineKeyboardBuilder()
        .row(
            InlineKeyboardButton(
                text="🔙 Back",
                callback_data=ChatSettingsCB(action=Action.BACK).pack(),
            ),
            InlineKeyboardButton(
                text="♻️ Reset",
                callback_data=ChatSettingsCB(action=Action.GREETING_RESET_TOPIC).pack(),
            ),
        )
        .as_markup()
    )
