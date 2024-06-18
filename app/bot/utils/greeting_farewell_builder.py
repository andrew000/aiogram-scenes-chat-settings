from typing import Final, Literal

from aiogram.methods import SendAnimation, SendMessage, SendPhoto, SendSticker, SendVideo
from aiogram.types import User

from bot.storages.psql.chat.chat_settings_model import GreetingFarewellType, RDChatSettingsModel
from bot.storages.redis.bot.reaction_media import RDBotReactionMedia

GF_Message = SendMessage | SendPhoto | SendVideo | SendAnimation | SendSticker
GF_Type = Final[Literal["greeting", "farewell"]]

MENTION_TOKEN: Final[str] = "{mention}"


def _build_message(
    chat_id: int,
    topic_id: int | None,
    chat_settings: RDChatSettingsModel,
    bot_reaction_media: RDBotReactionMedia,
    user: User,
    text: str,
    greeting_or_farewell: GF_Type,
) -> GF_Message:
    match greeting_or_farewell:
        case "greeting":
            gf_type = chat_settings.greeting_type
            text = chat_settings.greeting_text or text
            photo = chat_settings.greeting_photo_id or bot_reaction_media.GREETING
            video = chat_settings.greeting_video_id or bot_reaction_media.EMPTY_VIDEO
            animation = chat_settings.greeting_gif_id or bot_reaction_media.EMPTY_GIF
            sticker = chat_settings.greeting_sticker_id or bot_reaction_media.EMPTY_STICKER
        case "farewell":
            gf_type = chat_settings.farewell_type
            text = chat_settings.farewell_text or text
            photo = chat_settings.farewell_photo_id or bot_reaction_media.FAREWELL
            video = chat_settings.farewell_video_id or bot_reaction_media.EMPTY_VIDEO
            animation = chat_settings.farewell_gif_id or bot_reaction_media.EMPTY_GIF
            sticker = chat_settings.farewell_sticker_id or bot_reaction_media.EMPTY_STICKER
        case _:
            msg = f"Unknown greeting_or_farewell: {greeting_or_farewell}"
            raise ValueError(msg)

    text = text.replace(MENTION_TOKEN, user.mention_html(user.username), -1)

    match gf_type:
        case GreetingFarewellType.TEXT:
            return SendMessage(
                chat_id=chat_id,
                text=text,
                message_thread_id=topic_id,
            )
        case GreetingFarewellType.PHOTO:
            return SendPhoto(
                chat_id=chat_id,
                photo=photo,
                caption=text,
                message_thread_id=topic_id,
            )
        case GreetingFarewellType.VIDEO:
            return SendVideo(
                chat_id=chat_id,
                video=video,
                caption=text,
                message_thread_id=topic_id,
            )
        case GreetingFarewellType.GIF:
            return SendAnimation(
                chat_id=chat_id,
                animation=animation,
                caption=text,
                message_thread_id=topic_id,
            )
        case GreetingFarewellType.STICKER:
            return SendSticker(
                chat_id=chat_id,
                sticker=sticker,
                message_thread_id=topic_id,
            )
        case _:
            msg = f"Unknown msg_type: {chat_settings.greeting_type}"
            raise ValueError(msg)


def build_greeting_message(
    chat_id: int,
    topic_id: int | None,
    user: User,
    chat_settings: RDChatSettingsModel,
    bot_reaction_media: RDBotReactionMedia,
) -> GF_Message:
    return _build_message(
        chat_id=chat_id,
        topic_id=topic_id,
        chat_settings=chat_settings,
        bot_reaction_media=bot_reaction_media,
        user=user,
        text=f"Hello, {user.mention_html(user.username)}",
        greeting_or_farewell="greeting",
    )


def build_farewell_message(
    chat_id: int,
    topic_id: int | None,
    user: User,
    chat_settings: RDChatSettingsModel,
    bot_reaction_media: RDBotReactionMedia,
) -> GF_Message:
    return _build_message(
        chat_id=chat_id,
        topic_id=topic_id,
        chat_settings=chat_settings,
        bot_reaction_media=bot_reaction_media,
        user=user,
        text=f"Goodbye, {user.mention_html(user.username)}",
        greeting_or_farewell="farewell",
    )
