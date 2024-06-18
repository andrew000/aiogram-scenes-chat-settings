from typing import TYPE_CHECKING

from aiogram.filters import Filter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

if TYPE_CHECKING:
    from bot.scenes.chat_settings.base import FSMData


class CallbackClickedByFSMDataOwner(Filter):
    async def __call__(self, cb: CallbackQuery, state: FSMContext) -> bool:
        data: FSMData = await state.get_data()

        if not data or not (owner_id := data.get("owner_id")):
            await cb.answer("❌", show_alert=True)
            return False

        if cb.from_user.id == owner_id and cb.message.message_id == data["current_message_id"]:
            return True

        await cb.answer("❌", show_alert=True)
        return False
