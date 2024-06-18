from aiogram import Router

from . import chat_settings

router = Router()

router.include_routers(chat_settings.router)
