from aiogram import Bot, F, Router
from aiogram.filters import Command, CommandObject, MagicData
from aiogram.types import Message
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from bot.scenes.chat_settings.stages.admin_settings.reports_policy.keyboards import back_keyboard
from bot.storages.psql import DBChatSettingsModel
from bot.storages.psql.chat.chat_settings_model import RDChatSettingsModel, ReportPolicy
from bot.storages.redis.reports_special_chat.set_reports_special_chat_pending_model import (
    RDSetReportsSpecialChatPending,
)

router = Router()
router.message.filter(Command("set_reports_special_chat"))


@router.message(
    # Consider using ChatAdminFilter instead of MagicData
    # ChatAdminFilter(ChatAdminPermission(status=ChatMemberStatus.CREATOR)),
    MagicData(F.event_from_user.id == F.developer_id),
)
async def set_reports_special_chat(
    msg: Message,
    bot: Bot,
    command: CommandObject,
    db_session: async_sessionmaker[AsyncSession],
    redis: Redis,
) -> None:
    if command.args and ":" in command.args:
        public_hash_arg, secret_hash_arg = command.args.split(":")

    else:
        await msg.answer("⚠️ Chat for reports is not set.")
        return

    pending = await RDSetReportsSpecialChatPending.get(
        redis=redis,
        user_id=msg.from_user.id,
        public_hash=public_hash_arg,
    )

    if pending is None:
        await msg.answer("⚠️ Chat for reports is not set.")
        return

    secret_hash, additional_entropy = RDSetReportsSpecialChatPending.calc_secret_hash(
        pending.origin_chat_id,
        msg.from_user.id,
        pending.additional_entropy,
    )

    if any(
        (
            secret_hash != pending.secret_hash,
            secret_hash != secret_hash_arg,
            pending.secret_hash != secret_hash_arg,
        ),
    ):
        await msg.answer("⚠️ Chat for reports is not set.")
        return

    # Reset SetReportsSpecialChatPending
    await RDSetReportsSpecialChatPending.delete(
        redis=redis,
        user_id=msg.from_user.id,
    )

    async with db_session() as session:
        stmt = select(DBChatSettingsModel).where(DBChatSettingsModel.id == pending.origin_chat_id)
        chat_settings = await session.scalar(stmt)
        chat_settings.reports_special_chat_id = msg.chat.id
        chat_settings.reports_policy = ReportPolicy.SPECIAL_CHAT.value
        await session.commit()

        await RDChatSettingsModel.from_orm(chat_settings).save(redis)

    await msg.answer(
        "✅ Chat for reports has been saved:\n"
        "\n"
        f"CHAT_ID: {pending.origin_chat_id}\n"
        f"\n"
        f"💁‍♂️ You can now return to the settings window."
    )

    await bot.edit_message_text(
        chat_id=pending.origin_chat_id,
        message_id=pending.origin_message_id,
        text="✅ Chat for reports has been saved:\n"
        "\n"
        f"CHAT_ID: {pending.origin_chat_id}\n"
        f"\n"
        f"💁‍♂️ You can now return to the settings window.",
        reply_markup=back_keyboard(),
    )


@router.message()
async def set_reports_special_chat_default(msg: Message) -> None:
    await msg.answer(
        "💁‍♂️ This command allows you to set up a chat for storing reports.\n"
        "\n"
        "🆔 To set up a chat to store reports:\n"
        "1. Open the chat settings [ /chat_settings ]\n"
        "2. Go to the [ ⚙️ General settings ] section\n"
        "\n"
        "\n"
        "💡 Pay attention:\n"
        "- If the chat for reports is set up, the bot will send messages about reports to this "
        "chat.\n"
        "- If the chat for reports is not set, the bot will send notifications about reports to "
        "the chat where the reports was sent."
    )
