import uuid
from binascii import crc32
from datetime import timedelta
from typing import Self

import msgspec
from redis.asyncio import Redis


class RDSetReportsSpecialChatPending(msgspec.Struct, kw_only=True):
    origin_chat_id: int
    origin_message_id: int
    additional_entropy: str
    secret_hash: str

    @classmethod
    def key(cls, user_id: int, public_hash: str) -> str:
        return f"{cls.__name__}:{user_id}:{public_hash}"

    @classmethod
    def calc_public_hash(cls, chat_id: int, user_id: int, secret_hash: str) -> str:
        return crc32(f"{chat_id}:{user_id}:{secret_hash}".encode()).to_bytes(4, "big").hex()

    @classmethod
    def calc_secret_hash(
        cls,
        chat_id: int,
        user_id: int,
        additional_entropy: str | None = None,
    ) -> tuple[str, str]:
        additional_entropy = uuid.uuid4().hex if additional_entropy is None else additional_entropy
        return (
            crc32(f"{chat_id}:{user_id}:{additional_entropy}".encode()).to_bytes(4, "big").hex(),
            additional_entropy,
        )

    @classmethod
    async def set(
        cls,
        redis: Redis,
        origin_chat_id: int,
        origin_message_id: int,
        user_id: int,
    ) -> str:
        secret_hash, additional_entropy = cls.calc_secret_hash(origin_chat_id, user_id)
        public_hash = cls.calc_public_hash(origin_chat_id, user_id, secret_hash)

        await redis.setex(
            cls.key(user_id, public_hash),
            timedelta(hours=1),
            msgspec.msgpack.encode(
                cls(
                    origin_chat_id=origin_chat_id,
                    origin_message_id=origin_message_id,
                    additional_entropy=additional_entropy,
                    secret_hash=secret_hash,
                ),
            ),
        )

        return public_hash

    @classmethod
    async def get(cls, redis: Redis, user_id: int, public_hash: str) -> Self | None:
        data = await redis.get(cls.key(user_id, public_hash))
        if data is None:
            return None

        return msgspec.msgpack.decode(data, type=cls)

    @classmethod
    async def delete(cls, redis: Redis, user_id: int) -> None:
        keys = await redis.keys(f"{cls.__name__}:{user_id}:*")
        if keys:
            await redis.delete(*keys)

    @classmethod
    async def delete_all(cls, redis: Redis) -> None:
        keys = await redis.keys(f"{cls.__name__}:*")
        if keys:
            await redis.delete(*keys)
