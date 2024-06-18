from aiogram import Router

from . import prepare, set_reports_special_chat, start

router = Router(name="cmds_router")

router.include_routers(start.router, prepare.router, set_reports_special_chat.router)
