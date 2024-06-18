from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, SwitchInlineQueryChosenChat
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.handlers.inline_queries.set_reports_special_chat import (
    build_set_reports_special_chat_pattern,
)
from bot.scenes.chat_settings.base import Action, ChatSettingsCB


def reports_policy_keyboard() -> InlineKeyboardMarkup:
    return (
        InlineKeyboardBuilder()
        .row(
            InlineKeyboardButton(
                text="🔧 Set up a chat for reports",
                callback_data=ChatSettingsCB(action=Action.SET_REPORTS_SPECIAL_CHAT).pack(),
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


def set_reports_special_chat_keyboard(public_hash: str) -> InlineKeyboardMarkup:
    return (
        InlineKeyboardBuilder()
        .row(
            InlineKeyboardButton(
                text="🔧 Choose chat",
                switch_inline_query_chosen_chat=SwitchInlineQueryChosenChat(
                    query=build_set_reports_special_chat_pattern(public_hash),
                    allow_group_chats=True,
                ),
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


def back_keyboard() -> InlineKeyboardMarkup:
    return (
        InlineKeyboardBuilder()
        .row(
            InlineKeyboardButton(
                text="🔙 Back",
                callback_data=ChatSettingsCB(action=Action.BACK).pack(),
            ),
        )
        .as_markup()
    )
