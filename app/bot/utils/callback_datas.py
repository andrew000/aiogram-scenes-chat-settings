from typing import ClassVar, Literal, TypeVar

from aiogram.filters.callback_data import CallbackData

# Type that is a subclass of CallbackData and has an owner_id attribute of type int
OwnerCallbackData = TypeVar("OwnerCallbackData", bound=CallbackData)
OwnerCallbackData.owner_id = ClassVar[int]


class SelectStartCallbackData(CallbackData, prefix="start"):
    owner_id: int
    action: Literal["profile"]


class CommandsCallbackData(CallbackData, prefix="commands"):
    owner_id: int
    command: Literal["main_commands", "admin_commands", "vip_commands", "other_commands"]


class SelectProfileCallbackData(CallbackData, prefix="profile"):
    owner_id: int
    action: Literal["inventory"]
