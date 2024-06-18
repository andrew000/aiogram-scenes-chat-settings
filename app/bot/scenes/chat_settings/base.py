import asyncio
import contextlib
from enum import Enum
from typing import Final, TypedDict

from aiogram import Bot, F
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import Command
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.context import FSMContext
from aiogram.fsm.scene import After, Scene, on
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from redis.asyncio import Redis

from bot.storages.psql.chat.chat_settings_model import GreetingFarewellType
from bot.storages.redis.chat import RDChatBotModel
from bot.storages.redis.reports_special_chat.set_reports_special_chat_pending_model import (
    RDSetReportsSpecialChatPending,
)

MAX_GREETING_FAREWELL_LENGTH: Final[int] = 1000


class PossibleLanguageCodes(Enum):
    en = "en"  # English
    uk = "uk"  # Ukrainian
    pl = "pl"  # Polish
    de = "de"  # German
    ja = "ja"  # Japanese
    ru = "ru"  # Russian


class PossibleLanguages(Enum):
    en = "🇺🇸 English"
    uk = "🇺🇦 Українська"
    pl = "🇵🇱 Polski"
    de = "🇩🇪 Deutsch"
    ja = "🇯🇵 日本語"
    ru = "🇷🇺 Российский"


class FSMData(TypedDict, total=False):
    owner_id: int
    current_message_id: int | None
    current_topic_id: int | None
    greeting_farewell_message_id: int | None
    bot_messages_to_delete: list[int] | None
    user_messages_to_delete: list[int] | None


class Action(Enum):
    EXIT = "exit"
    BACK = "back"
    GENERAL_SETTINGS = "general_settings"
    ADMIN_SETTINGS = "admin_settings"
    KUS_SWITCH = "kus_switch"
    GOTO_SET_LANGUAGE = "goto_set_language"
    SET_LANGUAGE = "set_language"
    GOTO_SET_TIMEZONE = "goto_set_timezone"
    SET_TIMEZONE = "set_timezone"

    GREETING_SWITCH = "greeting_switch"
    GREETING_SETUP = "greeting_setup"
    GREETING_SET_TYPE = "greeting_set_type"
    GREETING_SET_TEXT = "greeting_set_text"
    GREETING_RESET_TEXT = "greeting_reset_text"
    GREETING_SET_MEDIA = "greeting_set_media"
    GREETING_RESET_MEDIA = "greeting_reset_media"
    GREETING_SET_TOPIC = "greeting_set_topic"
    GREETING_RESET_TOPIC = "greeting_reset_topic"
    GREETING_RESET_ALL = "greeting_reset_all"

    FAREWELL_SWITCH = "farewell_switch"
    FAREWELL_SETUP = "farewell_setup"
    FAREWELL_SET_TYPE = "farewell_set_type"
    FAREWELL_SET_TEXT = "farewell_set_text"
    FAREWELL_RESET_TEXT = "farewell_reset_text"
    FAREWELL_SET_MEDIA = "farewell_set_media"
    FAREWELL_RESET_MEDIA = "farewell_reset_media"
    FAREWELL_SET_TOPIC = "farewell_set_topic"
    FAREWELL_RESET_TOPIC = "farewell_reset_topic"
    FAREWELL_RESET_ALL = "farewell_reset_all"

    REPORTS_SWITCH = "reports_switch"
    SET_REPORTS_POLICY = "set_reports_policy"
    SET_REPORTS_SPECIAL_CHAT = "set_reports_special_chat"


class ChatSettingsCB(CallbackData, prefix="chat_settings"):
    action: Action


class SelectLanguageCB(CallbackData, prefix="cs_sl"):
    language_code: PossibleLanguageCodes


class ChatSettingsGreetingCB(CallbackData, prefix="cs_gs"):
    greeting_type: GreetingFarewellType


class ChatSettingsFarewellCB(CallbackData, prefix="cs_fs"):
    farewell_type: GreetingFarewellType


class ChatSettingsStates(StatesGroup):
    MAIN_WINDOW = State()
    GENERAL_SETTINGS = State()
    ADMIN_SETTINGS = State()
    LANGUAGE = State()
    TIMEZONE = State()

    GREETING = State()
    GREETING_SET_TYPE = State()
    GREETING_SET_TEXT = State()
    GREETING_SET_MEDIA = State()
    GREETING_SET_TOPIC_ID = State()

    FAREWELL = State()
    FAREWELL_SET_TYPE = State()
    FAREWELL_SET_TEXT = State()
    FAREWELL_SET_MEDIA = State()
    FAREWELL_SET_TOPIC_ID = State()

    REPORTS_POLICY = State()
    REPORTS_SPECIAL_CHAT = State()


class BaseScene(Scene):
    async def on_enter_msg(self, msg: Message, state: FSMContext) -> None: ...

    async def on_enter_cb(self, cb: CallbackQuery, state: FSMContext) -> None: ...

    @on.callback_query(ChatSettingsCB.filter(F.action == Action.EXIT), after=After.exit())
    async def exit_handler(self, _: CallbackQuery) -> None:
        pass

    @on.message(Command("exit", "cancel"))
    async def exit_handler_msg(self, _: Message) -> None:
        await self.wizard.exit()

    @on.message.exit()
    async def on_exit_msg(
        self,
        msg: Message,
        bot: Bot,
        state: FSMContext,
        redis: Redis,
        do_nothing: bool = False,
    ) -> None:
        # Reset SetRepostsSpecialChat pending state in Redis
        await RDSetReportsSpecialChatPending.delete(redis, msg.from_user.id)

        if do_nothing is True:
            await self.wizard.clear_data()
            return

        data: FSMData = await state.get_data()

        with contextlib.suppress(TelegramAPIError):
            if data.get("current_message_id") is not None:
                await bot.edit_message_text(
                    text="✅ Chat settings saved!",
                    chat_id=msg.chat.id,
                    message_id=data["current_message_id"],
                )

        await self.wizard.clear_data()

    @on.callback_query.exit()
    async def on_exit_cb(
        self,
        cb: CallbackQuery,
        redis: Redis,
        do_nothing: bool = False,
    ) -> None:
        # Reset SetRepostsSpecialChat pending state in Redis
        await RDSetReportsSpecialChatPending.delete(redis, cb.from_user.id)

        if do_nothing is True:
            await self.wizard.clear_data()
            return

        with contextlib.suppress(TelegramAPIError):
            await cb.message.edit_text("✅ Chat settings saved!")

        await self.wizard.clear_data()


async def process_message_delete(
    bot: Bot,
    chat_id: int,
    state: FSMContext,
    redis: Redis,
    extend_message_ids: list[int] | None = None,
    updated: bool = True,
) -> None:
    if extend_message_ids is None:
        extend_message_ids = []

    data: FSMData = await state.get_data()
    bot_messages_to_delete = set(data["bot_messages_to_delete"])
    user_messages_to_delete = set(data["user_messages_to_delete"])

    if updated is True:
        # Extend messages to delete
        user_messages_to_delete.update({*extend_message_ids})

    if bot_messages_to_delete:
        with contextlib.suppress(TelegramAPIError):
            await bot.delete_messages(chat_id=chat_id, message_ids=list(bot_messages_to_delete))

    if user_messages_to_delete:
        bot_member = await RDChatBotModel.get_or_create(redis=redis, chat_id=chat_id, bot=bot)

        if bot_member.can_delete_messages:
            with contextlib.suppress(TelegramAPIError):
                await bot.delete_messages(
                    chat_id=chat_id, message_ids=list(user_messages_to_delete)
                )

    await state.update_data(FSMData(bot_messages_to_delete=[], user_messages_to_delete=[]))

    if bot_messages_to_delete or user_messages_to_delete:
        await asyncio.sleep(1)
