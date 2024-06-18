import random
from datetime import timedelta
from enum import Enum
from typing import Final, Self

import msgspec
from redis.asyncio import Redis
from redis.typing import ExpiryT
from sqlalchemy import BigInteger, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from bot.storages.psql.base import Base
from bot.storages.psql.utils.alchemy_struct import AlchemyStruct

ENCODER: Final[msgspec.msgpack.Encoder] = msgspec.msgpack.Encoder()


class GreetingFarewellType(Enum):
    TEXT = "text"
    PHOTO = "photo"
    VIDEO = "video"
    GIF = "gif"
    STICKER = "sticker"


class ReportPolicy(Enum):
    MAIN_CHAT = "main_chat"
    SPECIAL_CHAT = "special_chat"


class DBChatSettingsModel(Base):
    __tablename__ = "chats_settings"

    id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("chats.id", onupdate="CASCADE", deferrable=True),
        primary_key=True,
        autoincrement=False,
    )
    language_code: Mapped[str] = mapped_column(
        String(2),
        nullable=False,
        default="uk",
    )  # language_code is set from User.language_code, which add bot to group
    timezone: Mapped[str] = mapped_column(String, nullable=True)
    kus_enabled: Mapped[bool] = mapped_column(nullable=False, default=True)
    allow_kus_admin: Mapped[bool] = mapped_column(
        nullable=False, default=True, comment="Is it allowed to kus Admins"
    )
    admin_tools_enabled: Mapped[bool] = mapped_column(nullable=False, default=True)
    reports_enabled: Mapped[bool] = mapped_column(nullable=False, default=True)
    reports_policy: Mapped[str] = mapped_column(
        String, nullable=False, server_default=ReportPolicy.MAIN_CHAT.value
    )
    reports_special_chat_id: Mapped[int] = mapped_column(BigInteger, nullable=True)

    greeting_enabled: Mapped[bool] = mapped_column(nullable=False, default=True)
    greeting_type: Mapped[str] = mapped_column(
        String,
        nullable=False,
        server_default=GreetingFarewellType.PHOTO.value,
    )
    greeting_text: Mapped[str] = mapped_column(String, nullable=True, default=None)
    greeting_photo_id: Mapped[str] = mapped_column(String, nullable=True, default=None)
    greeting_video_id: Mapped[str] = mapped_column(String, nullable=True, default=None)
    greeting_gif_id: Mapped[str] = mapped_column(String, nullable=True, default=None)
    greeting_sticker_id: Mapped[str] = mapped_column(String, nullable=True, default=None)
    greeting_topic_id: Mapped[int] = mapped_column(BigInteger, nullable=True)

    farewell_enabled: Mapped[bool] = mapped_column(nullable=False, default=True)
    farewell_type: Mapped[str] = mapped_column(
        String, nullable=False, server_default=GreetingFarewellType.PHOTO.value
    )
    farewell_text: Mapped[str] = mapped_column(String, nullable=True, default=None)
    farewell_photo_id: Mapped[str] = mapped_column(String, nullable=True, default=None)
    farewell_video_id: Mapped[str] = mapped_column(String, nullable=True, default=None)
    farewell_gif_id: Mapped[str] = mapped_column(String, nullable=True, default=None)
    farewell_sticker_id: Mapped[str] = mapped_column(String, nullable=True, default=None)
    farewell_topic_id: Mapped[int] = mapped_column(BigInteger, nullable=True)


class RDChatSettingsModel(AlchemyStruct, kw_only=True, array_like=True):
    id: int
    language_code: str
    timezone: str | None = msgspec.field(default=None)
    kus_enabled: bool
    allow_kus_admin: bool
    admin_tools_enabled: bool
    reports_enabled: bool
    reports_policy: ReportPolicy = msgspec.field(default=ReportPolicy.MAIN_CHAT)
    reports_special_chat_id: int | None = msgspec.field(default=None)

    greeting_enabled: bool
    greeting_type: GreetingFarewellType
    greeting_text: str | None = msgspec.field(default=None)
    greeting_photo_id: str | None = msgspec.field(default=None)
    greeting_video_id: str | None = msgspec.field(default=None)
    greeting_gif_id: str | None = msgspec.field(default=None)
    greeting_sticker_id: str | None = msgspec.field(default=None)
    greeting_topic_id: int | None = msgspec.field(default=None)

    farewell_enabled: bool
    farewell_type: GreetingFarewellType
    farewell_text: str | None = msgspec.field(default=None)
    farewell_photo_id: str | None = msgspec.field(default=None)
    farewell_video_id: str | None = msgspec.field(default=None)
    farewell_gif_id: str | None = msgspec.field(default=None)
    farewell_sticker_id: str | None = msgspec.field(default=None)
    farewell_topic_id: int | None = msgspec.field(default=None)

    @classmethod
    def key(cls, chat_id: int | str) -> str:
        return f"{cls.__name__}:{chat_id}"

    @classmethod
    async def get(cls, redis: Redis, chat_id: int | str) -> Self | None:
        data = await redis.get(cls.key(chat_id))
        if data:
            return msgspec.msgpack.decode(data, type=cls)
        return None

    async def save(self, redis: Redis, ttl: ExpiryT | None = None) -> bool:
        ttl = ttl or timedelta(minutes=random.randint(45, 90))
        return await redis.setex(self.key(self.id), ttl, ENCODER.encode(self))

    @classmethod
    async def delete(cls, redis: Redis, chat_id: int | str) -> int:
        return await redis.delete(cls.key(chat_id))

    @classmethod
    async def delete_all(cls, redis: Redis) -> int:
        keys = await redis.keys(f"{cls.__name__}:*")
        return await redis.delete(*keys)
