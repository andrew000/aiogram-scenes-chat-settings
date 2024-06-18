import asyncio

from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command, MagicData
from aiogram.types import Message
from redis.asyncio import Redis

from bot.storages.redis.bot.reaction_media import RDBotReactionMedia

router = Router()


@router.message(Command("prepare"), MagicData(F.event_from_user.id == F.developer_id))
async def prepare_bot_reaction_media(
    msg: Message,
    bot: Bot,
    dispatcher: Dispatcher,
    redis: Redis,
) -> None:
    bot_reaction_media, bot_message_ids = await RDBotReactionMedia.prepare_images(msg, redis)

    dispatcher.workflow_data.update(bot_reaction_media=bot_reaction_media)

    await bot.delete_messages(chat_id=msg.chat.id, message_ids=bot_message_ids)
    await asyncio.sleep(0.5)

    await msg.answer(
        "Bot reaction media prepared!\n"
        "\n"
        "<blockquote expandable>"
        f"GREETING: <code>{bot_reaction_media.GREETING}</code>\n\n"
        f"FAREWELL: <code>{bot_reaction_media.FAREWELL}</code>\n\n"
        f"PROMOTE: <code>{bot_reaction_media.PROMOTE}</code>\n\n"
        f"EMPTY_VIDEO: <code>{bot_reaction_media.EMPTY_VIDEO}</code>\n\n"
        f"EMPTY_GIF: <code>{bot_reaction_media.EMPTY_GIF}</code>\n\n"
        f"EMPTY_STICKER: <code>{bot_reaction_media.EMPTY_STICKER}</code>"
        "</blockquote>",
    )


@router.message(Command("prepare"))
async def prepare_if_not_developer(msg: Message) -> None:
    await msg.answer("You are not allowed to use this command. Check `developer_id` in config.")
