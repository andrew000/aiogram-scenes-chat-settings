from aiogram import F, Router
from aiogram.enums import ChatType
from aiogram.filters import Command, MagicData, StateFilter
from aiogram.fsm.scene import SceneRegistry

from .base import BaseScene, ChatSettingsStates
from .filters import CallbackClickedByFSMDataOwner
from .stages import admin_settings, general_settings, main

router = Router()

router.message.register(
    main.ChatSettingsMainWindow.as_handler(),
    Command("chat_settings"),
    F.chat.type.in_({ChatType.GROUP, ChatType.SUPERGROUP}),
    StateFilter(None, ChatSettingsStates),
    # Consider using ChatAdminFilter instead of MagicData
    # ChatAdminFilter(ChatAdminPermission(status=ChatMemberStatus.ADMINISTRATOR)),
    MagicData(F.event_from_user.id == F.developer_id),
)

BaseScene.as_router().message.filter(
    StateFilter(ChatSettingsStates),
    F.chat.type.in_({ChatType.GROUP, ChatType.SUPERGROUP}),
    # Consider using ChatAdminFilter instead of MagicData
    # ChatAdminFilter(ChatAdminPermission(status=ChatMemberStatus.ADMINISTRATOR)),
    MagicData(F.event_from_user.id == F.developer_id),
)
BaseScene.as_router().callback_query.filter(
    StateFilter(ChatSettingsStates),
    # Consider using ChatAdminFilter instead of MagicData
    # ChatAdminFilter(ChatAdminPermission(status=ChatMemberStatus.ADMINISTRATOR)),
    MagicData(F.event_from_user.id == F.developer_id),
    CallbackClickedByFSMDataOwner(),
)

registry = SceneRegistry(router)
registry.register(
    main.ChatSettingsMainWindow,
    general_settings.GeneralSettingsWindow,
    general_settings.SetLanguageWindow,
    general_settings.SetTimezoneWindow,
    general_settings.SetGreetingWindow,
    general_settings.SetGreetingTypeWindow,
    general_settings.SetGreetingTextWindow,
    general_settings.SetGreetingMediaWindow,
    general_settings.SetGreetingTopicIDWindow,
    general_settings.SetFarewellWindow,
    general_settings.SetFarewellTypeWindow,
    general_settings.SetFarewellTextWindow,
    general_settings.SetFarewellMediaWindow,
    general_settings.SetFarewellTopicIDWindow,
    admin_settings.AdminSettingsWindow,
    admin_settings.ReportsPolicyWindow,
    admin_settings.SetReportsSpecialChatWindow,
)

__all__ = ("router",)
