import re
import uuid
from typing import Final

from aiogram import F, Router
from aiogram.types import InlineQuery, InlineQueryResultArticle, InputTextMessageContent
from redis.asyncio import Redis

from bot.storages.redis.reports_special_chat.set_reports_special_chat_pending_model import (
    RDSetReportsSpecialChatPending,
)

router = Router()

REPORTS_SPECIAL_CHAT_CONSTANT: Final[str] = "set_reports_special_chat"
RE_REPORTS_SPECIAL_CHAT_PATTERN: Final[re.Pattern] = re.compile(
    rf"{REPORTS_SPECIAL_CHAT_CONSTANT}:(?P<public_hash>.+)"
)


def build_set_reports_special_chat_pattern(public_hash: str) -> str:
    return f"{REPORTS_SPECIAL_CHAT_CONSTANT}:{public_hash}"


@router.inline_query(F.query.regexp(RE_REPORTS_SPECIAL_CHAT_PATTERN).as_("public_hash"))
async def inline_query(query: InlineQuery, public_hash: re.Match, redis: Redis) -> None:
    public_hash: str = public_hash.group("public_hash")

    pending = await RDSetReportsSpecialChatPending.get(
        redis=redis,
        user_id=query.from_user.id,
        public_hash=public_hash,
    )

    if pending is None:
        await query.answer(
            [
                InlineQueryResultArticle(
                    id=uuid.uuid4().hex,
                    title="No pending reports special chat",
                    input_message_content=InputTextMessageContent(
                        message_text="No pending reports special chat",
                    ),
                ),
            ],
            cache_time=1,
            is_personal=True,
        )
        return

    secret_hash, additional_entropy = RDSetReportsSpecialChatPending.calc_secret_hash(
        pending.origin_chat_id,
        query.from_user.id,
        pending.additional_entropy,
    )

    if secret_hash != pending.secret_hash:
        await query.answer(
            [
                InlineQueryResultArticle(
                    id=uuid.uuid4().hex,
                    title="No pending reports special chat",
                    input_message_content=InputTextMessageContent(
                        message_text="No pending reports special chat",
                    ),
                ),
            ],
            cache_time=1,
            is_personal=True,
        )
        return

    await query.answer(
        [
            InlineQueryResultArticle(
                id=uuid.uuid4().hex,
                title="Set reports special chat",
                input_message_content=InputTextMessageContent(
                    message_text=f"/set_reports_special_chat {public_hash}:"
                    f"{pending.secret_hash}",
                ),
            ),
        ],
        cache_time=1,
        is_personal=True,
    )
