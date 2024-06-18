from aiogram import F
from aiogram.fsm.scene import on
from aiogram.types import CallbackQuery
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from bot.scenes.chat_settings.base import Action, BaseScene, ChatSettingsCB, ChatSettingsStates
from bot.scenes.chat_settings.stages.admin_settings.reports_policy.keyboards import (
    set_reports_special_chat_keyboard,
)
from bot.storages.psql import DBChatSettingsModel
from bot.storages.redis.reports_special_chat.set_reports_special_chat_pending_model import (
    RDSetReportsSpecialChatPending,
)

CHAT_SETTINGS_REPORTS_SPECIAL_CHAT_TEXT = (
    "📕 Chat for storing reports: {is_set}\n"
    "🆔 CHAT_ID: {chat_id}\n"
    "\n"
    "💁‍♂️ To set up a chat for storing reports - click the button and select the desired chat "
    "where you are the owner: <blockquote><code>🔧 Choose chat</code></blockquote>\n"
    "\n"
    "💡 Pay attention:\n"
    "— If a chat for reports is set, the bot will send messages about reports to this chat.\n"
    "— If the chat for reports is not set, the bot will send messages about reports to the chat "
    "where the report was sent."
)


class SetReportsSpecialChatWindow(BaseScene, state=ChatSettingsStates.REPORTS_SPECIAL_CHAT):
    @on.callback_query.enter()
    async def on_enter_cb(
        self,
        cb: CallbackQuery,
        db_session: async_sessionmaker[AsyncSession],
        redis: Redis,
    ) -> None:
        # Reset SetRepostsSpecialChat pending state in Redis
        await RDSetReportsSpecialChatPending.delete(redis, cb.from_user.id)

        async with db_session() as session:
            stmt = select(DBChatSettingsModel).where(DBChatSettingsModel.id == cb.message.chat.id)
            chat_settings: DBChatSettingsModel = await session.scalar(stmt)

        public_hash = await RDSetReportsSpecialChatPending.set(
            redis,
            cb.message.chat.id,
            cb.message.message_id,
            cb.from_user.id,
        )

        await cb.message.edit_text(
            CHAT_SETTINGS_REPORTS_SPECIAL_CHAT_TEXT.format(
                is_set=bool(chat_settings.reports_special_chat_id),
                chat_id=chat_settings.reports_special_chat_id or "❌",
            ),
            reply_markup=set_reports_special_chat_keyboard(public_hash),
        )

    @on.callback_query(ChatSettingsCB.filter(F.action == Action.BACK))
    async def back_handler(self, _: CallbackQuery) -> None:
        await self.wizard.goto(ChatSettingsStates.REPORTS_POLICY)

    @on.callback_query.leave()
    async def on_leave_cb(self, cb: CallbackQuery, redis: Redis) -> None:
        # Reset SetRepostsSpecialChat pending state in Redis
        await RDSetReportsSpecialChatPending.delete(redis, cb.from_user.id)
