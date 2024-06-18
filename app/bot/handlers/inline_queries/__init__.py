from aiogram import Router

from . import set_reports_special_chat

router = Router()


router.include_routers(
    set_reports_special_chat.router,
)
