import asyncio
from typing import Self

import msgspec
from aiogram.types import FSInputFile, Message
from redis.asyncio import Redis

from bot.images.images import (
    EMPTY_GIF_IMAGE_PATH,
    EMPTY_STICKER_IMAGE_PATH,
    EMPTY_VIDEO_IMAGE_PATH,
    FAREWELL_IMAGE_PATH,
    GREETING_IMAGE_PATH,
    PROMOTE_IMAGE_PATH,
)


class RDBotReactionMedia(msgspec.Struct, kw_only=True):
    """
    Class for preparing and storing bot reaction media.

    This class is only used for this example and should not be used in production.

    Use better ways to upload media and store their file_ids.
    """

    GREETING: str
    FAREWELL: str
    PROMOTE: str
    EMPTY_VIDEO: str
    EMPTY_GIF: str
    EMPTY_STICKER: str

    @classmethod
    def key(cls) -> str:
        return f"{cls.__name__}"

    @classmethod
    async def prepare_images(cls, msg: Message, redis: Redis) -> tuple[Self, list[int]]:
        bot_message_ids: list[int] = []

        greeting = await msg.answer_photo(photo=FSInputFile(GREETING_IMAGE_PATH))
        bot_message_ids.append(greeting.message_id)
        await asyncio.sleep(0.5)

        farewell = await msg.answer_photo(photo=FSInputFile(FAREWELL_IMAGE_PATH))
        bot_message_ids.append(farewell.message_id)
        await asyncio.sleep(0.5)

        promote = await msg.answer_photo(photo=FSInputFile(PROMOTE_IMAGE_PATH))
        bot_message_ids.append(promote.message_id)
        await asyncio.sleep(0.5)

        video = await msg.answer_video(video=FSInputFile(EMPTY_VIDEO_IMAGE_PATH))
        bot_message_ids.append(video.message_id)
        await asyncio.sleep(0.5)

        animation = await msg.answer_animation(animation=FSInputFile(EMPTY_GIF_IMAGE_PATH))
        bot_message_ids.append(animation.message_id)
        await asyncio.sleep(0.5)

        sticker = await msg.answer_sticker(sticker=FSInputFile(EMPTY_STICKER_IMAGE_PATH))
        bot_message_ids.append(sticker.message_id)
        await asyncio.sleep(0.5)

        bot_reaction_media = cls(
            GREETING=greeting.photo[-1].file_id,
            FAREWELL=farewell.photo[-1].file_id,
            PROMOTE=promote.photo[-1].file_id,
            EMPTY_VIDEO=video.video.file_id,
            EMPTY_GIF=animation.animation.file_id,
            EMPTY_STICKER=sticker.sticker.file_id,
        )

        await bot_reaction_media.save(redis)

        return bot_reaction_media, bot_message_ids

    @classmethod
    async def get(cls, redis: Redis) -> Self | None:
        data = await redis.get(cls.key())
        if data:
            return msgspec.msgpack.decode(data, type=cls)
        return None

    async def save(self, redis: Redis) -> Self:
        await redis.set(self.key(), msgspec.msgpack.encode(self))
        return self
