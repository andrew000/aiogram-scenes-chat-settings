from aiogram import F
from aiogram.fsm.scene import on
from aiogram.types import CallbackQuery
from redis.asyncio import Redis

from bot.scenes.chat_settings.base import Action, BaseScene, ChatSettingsCB, ChatSettingsStates
from bot.scenes.chat_settings.stages.admin_settings.reports_policy.keyboards import (
    reports_policy_keyboard,
)
from bot.storages.redis.reports_special_chat.set_reports_special_chat_pending_model import (
    RDSetReportsSpecialChatPending,
)

REPORTS_POLICY_TEXT = (
    "<b>📕 Reports policy</b>\n"
    "\n"
    "💁‍♂️ In this window, you can set up reports policy.\n"
    "\n"
    "🆔 To set up a chat for reports, click the button: <blockquote><code>🔧 "
    "Set up a chat for reports</code></blockquote>\n"
)


class ReportsPolicyWindow(BaseScene, state=ChatSettingsStates.REPORTS_POLICY):
    @on.callback_query.enter()
    async def on_enter_cb(self, cb: CallbackQuery, redis: Redis) -> None:
        # Reset SetRepostsSpecialChat pending state in Redis
        await RDSetReportsSpecialChatPending.delete(redis, cb.from_user.id)

        await cb.message.edit_text(REPORTS_POLICY_TEXT, reply_markup=reports_policy_keyboard())

    @on.callback_query(ChatSettingsCB.filter(F.action == Action.SET_REPORTS_SPECIAL_CHAT))
    async def on_set_reports_special_chat_cb(self, _: CallbackQuery) -> None:
        await self.wizard.goto(ChatSettingsStates.REPORTS_SPECIAL_CHAT)

    @on.callback_query(ChatSettingsCB.filter(F.action == Action.BACK))
    async def back_handler(self, _: CallbackQuery) -> None:
        await self.wizard.goto(ChatSettingsStates.ADMIN_SETTINGS, updated=False)

    @on.callback_query.leave()
    async def on_leave_cb(self, cb: CallbackQuery, redis: Redis) -> None:
        # Reset SetRepostsSpecialChat pending state in Redis
        await RDSetReportsSpecialChatPending.delete(redis, cb.from_user.id)
