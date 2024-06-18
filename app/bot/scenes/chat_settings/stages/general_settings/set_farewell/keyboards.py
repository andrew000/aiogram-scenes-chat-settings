from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.scenes.chat_settings.base import Action, ChatSettingsCB, ChatSettingsFarewellCB
from bot.storages.psql.chat.chat_settings_model import GreetingFarewellType, RDChatSettingsModel


def farewell_keyboard(chat_settings: RDChatSettingsModel) -> InlineKeyboardMarkup:
    match chat_settings.farewell_type:
        case GreetingFarewellType.TEXT:
            farewell_set_type_text = "⚙️ Farewell type: 📝 Text"
        case GreetingFarewellType.PHOTO:
            farewell_set_type_text = "⚙️ Farewell type: 🖼 Photo"
        case GreetingFarewellType.VIDEO:
            farewell_set_type_text = "⚙️ Farewell type: 📹 Video"
        case GreetingFarewellType.GIF:
            farewell_set_type_text = "⚙️ Farewell type: 🎞 GIF"
        case GreetingFarewellType.STICKER:
            farewell_set_type_text = "⚙️ Farewell type: 🤪 Sticker"
        case _:
            farewell_set_type_text = "⚙️ Farewell type: Unknown type"

    return (
        InlineKeyboardBuilder()
        .row(
            InlineKeyboardButton(
                text=farewell_set_type_text,
                callback_data=ChatSettingsCB(action=Action.FAREWELL_SET_TYPE).pack(),
            ),
        )
        .row(
            InlineKeyboardButton(
                text="📝 Text",
                callback_data=ChatSettingsCB(action=Action.FAREWELL_SET_TEXT).pack(),
            ),
            InlineKeyboardButton(
                text="♻️ Reset",
                callback_data=ChatSettingsCB(action=Action.FAREWELL_RESET_TEXT).pack(),
            ),
        )
        .row(
            InlineKeyboardButton(
                text="🖼 Media",
                callback_data=ChatSettingsCB(action=Action.FAREWELL_SET_MEDIA).pack(),
            ),
            InlineKeyboardButton(
                text="♻️ Reset",
                callback_data=ChatSettingsCB(action=Action.FAREWELL_RESET_MEDIA).pack(),
            ),
        )
        .row(
            InlineKeyboardButton(
                text="🆔 Topic ID",
                callback_data=ChatSettingsCB(action=Action.FAREWELL_SET_TOPIC).pack(),
            ),
            InlineKeyboardButton(
                text="♻️ Reset",
                callback_data=ChatSettingsCB(action=Action.FAREWELL_RESET_TOPIC).pack(),
            ),
        )
        .row(
            InlineKeyboardButton(
                text="🔙 Back",
                callback_data=ChatSettingsCB(action=Action.BACK).pack(),
            ),
            InlineKeyboardButton(
                text="♻️ Reset all",
                callback_data=ChatSettingsCB(action=Action.FAREWELL_RESET_ALL).pack(),
            ),
        )
        .as_markup()
    )


def farewell_type_keyboard() -> InlineKeyboardMarkup:
    return (
        InlineKeyboardBuilder()
        .row(
            InlineKeyboardButton(
                text="📝 Text",
                callback_data=ChatSettingsFarewellCB(
                    farewell_type=GreetingFarewellType.TEXT.value
                ).pack(),
            ),
            InlineKeyboardButton(
                text="🖼 Photo",
                callback_data=ChatSettingsFarewellCB(
                    farewell_type=GreetingFarewellType.PHOTO.value
                ).pack(),
            ),
        )
        .row(
            InlineKeyboardButton(
                text="📹 Video",
                callback_data=ChatSettingsFarewellCB(
                    farewell_type=GreetingFarewellType.VIDEO.value
                ).pack(),
            ),
            InlineKeyboardButton(
                text="🎞 GIF",
                callback_data=ChatSettingsFarewellCB(
                    farewell_type=GreetingFarewellType.GIF.value
                ).pack(),
            ),
        )
        .row(
            InlineKeyboardButton(
                text="🤪 Sticker",
                callback_data=ChatSettingsFarewellCB(
                    farewell_type=GreetingFarewellType.STICKER.value
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


def farewell_text_keyboard() -> InlineKeyboardMarkup:
    return (
        InlineKeyboardBuilder()
        .row(
            InlineKeyboardButton(
                text="🔙 Back",
                callback_data=ChatSettingsCB(action=Action.BACK).pack(),
            ),
            InlineKeyboardButton(
                text="♻️ Reset",
                callback_data=ChatSettingsCB(action=Action.FAREWELL_RESET_TEXT).pack(),
            ),
        )
        .as_markup()
    )


def farewell_media_keyboard() -> InlineKeyboardMarkup:
    return (
        InlineKeyboardBuilder()
        .row(
            InlineKeyboardButton(
                text="🔙 Назад",
                callback_data=ChatSettingsCB(action=Action.BACK).pack(),
            ),
            InlineKeyboardButton(
                text="♻️ Reset",
                callback_data=ChatSettingsCB(action=Action.FAREWELL_RESET_MEDIA).pack(),
            ),
        )
        .as_markup()
    )


def farewell_topic_id_keyboard() -> InlineKeyboardMarkup:
    return (
        InlineKeyboardBuilder()
        .row(
            InlineKeyboardButton(
                text="🔙 Back",
                callback_data=ChatSettingsCB(action=Action.BACK).pack(),
            ),
            InlineKeyboardButton(
                text="♻️ Reset",
                callback_data=ChatSettingsCB(action=Action.FAREWELL_RESET_TOPIC).pack(),
            ),
        )
        .as_markup()
    )
