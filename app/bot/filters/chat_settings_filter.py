from types import NoneType

import msgspec
from aiogram.enums import ChatType
from aiogram.filters import Filter
from aiogram.types import Chat, TelegramObject

from bot.storages.psql.chat import RDChatSettingsModel


class ChatSettings(msgspec.Struct, frozen=True, kw_only=True):
    kus_enabled: bool | None = None
    admin_tools_enabled: bool | None = None
    reports_enabled: bool | None = None
    greetings_enabled: bool | None = None
    farewell_enabled: bool | None = None


class ChatSettingsFilter(Filter):
    def __init__(self, settings: ChatSettings | None = None) -> None:
        if not isinstance(settings, (ChatSettings, NoneType)):
            msg = "Permission must be ChatPermissions or None"
            raise TypeError(msg)

        self.settings = settings

    async def __call__(
        self,
        event: TelegramObject,  # noqa: ARG002
        event_chat: Chat,
        chat_settings: RDChatSettingsModel,
    ) -> bool:
        match event_chat.type:
            case ChatType.PRIVATE:
                return True
            case ChatType.CHANNEL:
                return False

        if self.settings is None:
            return True

        fields = {
            field: value
            for field, value in msgspec.structs.asdict(self.settings).items()
            if value is not None
        }
        return all(getattr(chat_settings, field, None) == value for field, value in fields.items())
