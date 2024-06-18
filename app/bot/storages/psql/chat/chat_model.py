from datetime import datetime
from typing import Final, Literal, Self

import msgspec
from redis.asyncio import Redis
from redis.typing import ExpiryT
from sqlalchemy import BigInteger, CheckConstraint, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import expression

from bot.storages.psql.base import Base
from bot.storages.psql.utils.alchemy_struct import AlchemyStruct

ENCODER: Final[msgspec.msgpack.Encoder] = msgspec.msgpack.Encoder()


class DBChatModel(Base):
    __tablename__ = "chats"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    chat_type: Mapped[str] = mapped_column(nullable=False)
    username: Mapped[str] = mapped_column(
        String,
        nullable=True,
        default=None,
        server_default=expression.null(),
    )
    registration_datetime: Mapped[datetime] = mapped_column(
        nullable=False, server_default=expression.text("(now() AT TIME ZONE 'UTC'::text)")
    )

    __table_args__ = (CheckConstraint("chat_type in ('group', 'supergroup', 'channel')"),)


class RDChatModel(AlchemyStruct, kw_only=True, array_like=True):
    id: int
    chat_type: Literal["group", "supergroup", "channel"]
    username: str | None = msgspec.field(default=None)
    registration_datetime: datetime

    @classmethod
    def key(cls, chat_id: int | str) -> str:
        return f"{cls.__name__}:{chat_id}"

    @classmethod
    async def get(cls, redis: Redis, chat_id: int | str) -> Self | None:
        data = await redis.get(cls.key(chat_id))
        if data:
            return msgspec.msgpack.decode(data, type=cls)
        return None

    async def save(self, redis: Redis, ttl: ExpiryT) -> int:
        return await redis.setex(self.key(self.id), ttl, ENCODER.encode(self))

    @classmethod
    async def delete(cls, redis: Redis, chat_id: int | str) -> int:
        return await redis.delete(cls.key(chat_id))

    @classmethod
    async def delete_all(cls, redis: Redis) -> int:
        keys = await redis.keys(f"{cls.__name__}:*")
        return await redis.delete(*keys)
