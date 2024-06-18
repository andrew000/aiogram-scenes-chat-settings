import random
from collections.abc import Awaitable, Callable
from datetime import timedelta
from typing import Any

from aiogram import BaseMiddleware
from aiogram.enums import ChatType
from aiogram.types import Chat, TelegramObject, Update, User
from redis.asyncio.client import Redis
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from bot.storages.psql.chat.chat_model import DBChatModel, RDChatModel
from bot.storages.psql.chat.chat_settings_model import DBChatSettingsModel, RDChatSettingsModel


async def _get_chat_model(
    db_session: async_sessionmaker[AsyncSession],
    redis: Redis,
    chat: Chat,
    user: User,
) -> tuple[RDChatModel, RDChatSettingsModel]:
    chat_model: RDChatModel | None = await RDChatModel.get(redis, chat.id)
    chat_settings: RDChatSettingsModel | None = await RDChatSettingsModel.get(redis, chat.id)

    if chat_model and chat_settings:
        return chat_model, chat_settings

    async with db_session() as session:
        stmt = (
            insert(DBChatModel)
            .values(
                id=chat.id,
                chat_type=chat.type,
                username=chat.username,
            )
            .on_conflict_do_update(
                index_elements=["id"],
                set_={
                    "username": chat.username,
                },
            )
            .returning(DBChatModel)
        )
        chat_model: DBChatModel = await session.scalar(stmt)

        stmt = (
            insert(DBChatSettingsModel)
            .values(
                id=chat.id,
                language_code=user.language_code or "ru",
            )
            .on_conflict_do_update(
                index_elements=["id"],
                set_={
                    "language_code": DBChatSettingsModel.language_code,  # Required for returning
                },
            )
            .returning(DBChatSettingsModel)
        )
        chat_settings: DBChatSettingsModel = await session.scalar(stmt)

        await session.commit()

        chat_model: RDChatModel = RDChatModel.from_orm(chat_model)
        chat_settings: RDChatSettingsModel = RDChatSettingsModel.from_orm(chat_settings)

        ttl = timedelta(minutes=random.randint(45, 75))
        await chat_model.save(redis, ttl)
        await chat_settings.save(redis, ttl)

    return chat_model, chat_settings


class CheckChatMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: dict[str, Any],
    ) -> Any:
        chat: Chat = data.get("event_chat")
        user: User = data.get("event_from_user")

        match event.event_type:
            case "message" | "callback_query" | "my_chat_member" | "chat_member":
                if chat.type in (ChatType.GROUP, ChatType.SUPERGROUP, ChatType.CHANNEL):
                    data["chat_model"], data["chat_settings"] = await _get_chat_model(
                        data["db_session"],
                        data["redis"],
                        chat,
                        user,
                    )
            case _:
                pass

        return await handler(event, data)
