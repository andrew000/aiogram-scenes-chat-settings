from typing import Any

from aiogram.filters import Filter
from aiogram.types import CallbackQuery

from bot.utils.callback_datas import OwnerCallbackData


class CallbackClickedByTargetUser(Filter):
    async def __call__(
        self,
        query: CallbackQuery,
        callback_data: OwnerCallbackData | None = None,
    ) -> bool | dict[str, Any]:
        if not callback_data or not hasattr(callback_data, "owner_id"):
            return False

        if query.from_user.id != callback_data.owner_id:
            await query.answer("❌", show_alert=True)
            return False

        return query.from_user.id == callback_data.owner_id
