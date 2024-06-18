import asyncio
import contextlib
import logging
from asyncio import CancelledError
from functools import partial

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.telegram import PRODUCTION
from aiogram.exceptions import TelegramAPIError
from aiogram.fsm.storage.memory import SimpleEventIsolation
from aiogram.fsm.storage.redis import DefaultKeyBuilder, RedisStorage
from aiogram.utils.deep_linking import create_start_link
from redis.asyncio import Redis

from bot import handlers, scenes
from bot.middlewares.check_chat_middleware import CheckChatMiddleware
from bot.settings import Settings
from bot.storages.psql import close_db, create_db_session_pool, init_db
from bot.storages.redis.bot.reaction_media import RDBotReactionMedia

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


async def startup(dispatcher: Dispatcher, bot: Bot, settings: Settings, redis: Redis) -> None:
    await bot.delete_webhook(drop_pending_updates=True)

    engine, db_session = await create_db_session_pool(settings)

    await init_db(engine)

    dispatcher.workflow_data.update(
        {
            "db_session": db_session,
            "db_session_closer": partial(close_db, engine),
        }
    )

    # Delete all keys from redis
    # await redis.flushall()

    bot_reaction_media = await RDBotReactionMedia.get(redis)

    if bot_reaction_media is None:
        logger.warning(
            "Media for bot reactions not ready. Consider using the /prepare command to prepare "
            "the media for the bot's response."
        )
        deeplink = await create_start_link(bot=bot, payload="prepare")
        logger.info("Use this deeplink to prepare the media for the bot's response: %s", deeplink)

        with contextlib.suppress(TelegramAPIError):
            await bot.send_message(
                settings.developer_id,
                "Media for bot reactions not ready.\n"
                "\n"
                "Consider using the /prepare command to prepare the media for the bot's response.",
            )

    dispatcher.workflow_data.update(bot_reaction_media=bot_reaction_media)

    dispatcher.update.outer_middleware(CheckChatMiddleware())
    # dispatcher.update.outer_middleware(CheckUserMiddleware())

    logger.info("Bot started")


async def shutdown(dispatcher: Dispatcher, **__) -> None:
    await dispatcher["db_session_closer"]()
    logger.info("Bot stopped")


async def main() -> None:
    settings = Settings()

    bot = Bot(
        token=settings.bot_token.get_secret_value(),
        session=AiohttpSession(api=PRODUCTION),
        default=DefaultBotProperties(parse_mode="HTML"),
    )

    storage = RedisStorage(
        redis=await settings.redis_dsn(),
        key_builder=DefaultKeyBuilder(with_bot_id=True, with_destiny=True),
    )

    dp = Dispatcher(
        storage=storage,
        events_isolation=SimpleEventIsolation(),
        settings=settings,
        redis=storage.redis,
        developer_id=settings.developer_id,
    )
    dp.include_routers(scenes.router, handlers.router)
    dp.startup.register(startup)
    dp.shutdown.register(shutdown)

    await dp.start_polling(
        bot,
        allowed_updates=dp.resolve_used_update_types(),
    )


if __name__ == "__main__":
    try:
        uvloop = __import__("uvloop")
        loop_factory = uvloop.new_event_loop

    except ModuleNotFoundError:
        loop_factory = asyncio.new_event_loop
        logger.info("uvloop not found, using default event loop")

    try:
        with asyncio.Runner(loop_factory=loop_factory) as runner:
            runner.run(main())

    except (CancelledError, KeyboardInterrupt):
        __import__("sys").exit(0)
