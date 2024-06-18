import pytz
from aiogram import Bot, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.scene import on
from aiogram.types import CallbackQuery, Message
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from bot.scenes.chat_settings.base import (
    Action,
    BaseScene,
    ChatSettingsCB,
    ChatSettingsStates,
    FSMData,
)
from bot.scenes.chat_settings.stages.general_settings.keyboards import timezone_keyboard
from bot.storages.psql import DBChatSettingsModel, RDChatSettingsModel


class SetTimezoneWindow(BaseScene, state=ChatSettingsStates.TIMEZONE):
    @on.message.enter()
    async def on_enter_msg(self, msg: Message, state: FSMContext) -> None:
        sent = await msg.answer(
            "⏰ Write the name of your time zone (for example, <code>Europe/Kyiv</code>):",
            reply_markup=timezone_keyboard(),
        )

        await state.update_data(FSMData(current_message_id=sent.message_id))

    @on.callback_query.enter()
    async def on_enter_cb(self, cb: CallbackQuery, state: FSMContext) -> None:
        sent = await cb.message.edit_text(
            "⏰ Write the name of your time zone (for example, <code>Europe/Kyiv</code>):",
            reply_markup=timezone_keyboard(),
        )

        await state.update_data(FSMData(current_message_id=sent.message_id))

    @on.message(F.text)
    async def timezone_handler(
        self,
        msg: Message,
        bot: Bot,
        state: FSMContext,
        db_session: async_sessionmaker[AsyncSession],
        redis: Redis,
    ) -> None:
        data = await state.get_data()
        try:
            timezone = pytz.timezone(msg.text)

        except pytz.UnknownTimeZoneError:
            await bot.edit_message_text(
                chat_id=msg.chat.id,
                message_id=data["current_message_id"],
                text="⚠️ Unknown time zone.",
            )
            sent = await msg.answer(
                "⚠️ Unknown time zone. Try again.\n"
                "\n"
                " 💁‍♂️ The time zone is specified in <code>Continent/City</code> format\n"
                "\n"
                " 💡 For example:\n"
                " <blockquote><code>Europe/Kyiv</code></blockquote>\n"
                " <blockquote><code>America/New_York</code></blockquote>",
                reply_markup=timezone_keyboard(),
            )
            await state.update_data(FSMData(current_message_id=sent.message_id))
            return

        else:
            async with db_session() as session:
                stmt = select(DBChatSettingsModel).where(DBChatSettingsModel.id == msg.chat.id)
                chat_settings: DBChatSettingsModel = await session.scalar(stmt)
                chat_settings.timezone = timezone.zone

                await session.commit()

                await RDChatSettingsModel.from_orm(chat_settings).save(redis)

            await state.update_data(FSMData(current_message_id=None))

            await bot.edit_message_text(
                chat_id=msg.chat.id,
                message_id=data["current_message_id"],
                text=(
                    "✅ Time zone saved:\n"
                    f"<blockquote><code>{timezone.zone}</code></blockquote>"
                ),
            )

            await self.wizard.goto(ChatSettingsStates.GENERAL_SETTINGS)

    @on.callback_query(ChatSettingsCB.filter(F.action == Action.BACK))
    async def back_handler(self, _: CallbackQuery) -> None:
        await self.wizard.goto(ChatSettingsStates.GENERAL_SETTINGS)
