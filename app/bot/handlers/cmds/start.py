import logging

from aiogram import Dispatcher, F, Router
from aiogram.filters import CommandObject, CommandStart, MagicData
from aiogram.types import Message
from redis.asyncio import Redis

from bot.handlers.cmds.prepare import prepare_bot_reaction_media

router = Router(name="start_router")
logger = logging.getLogger(__name__)


@router.message(
    CommandStart(deep_link=True, magic=F.args == "prepare"),
    MagicData(F.event_from_user.id == F.developer_id),
)
async def start_prepare(
    msg: Message,
    command: CommandObject,
    dispatcher: Dispatcher,
    redis: Redis,
) -> None:
    logger.info("User %s started bot with deep link: %s", msg.from_user.id, command.args)

    await prepare_bot_reaction_media(msg=msg, dispatcher=dispatcher, redis=redis)


@router.message(CommandStart(deep_link=False))
async def start_cmd(msg: Message) -> None:
    await msg.answer(
        "Hello! I'm a bot with chat settings example panel.\n"
        "\n"
        "Use /chat_settings to open the panel.\n"
        "\n"
        "Please verify you are Administrator and Bot has all necessary permissions.",
    )
