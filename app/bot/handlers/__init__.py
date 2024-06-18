from aiogram import Router

from . import cmds, inline_queries

router = Router(name="handlers_router")

router.include_routers(
    cmds.router,
    inline_queries.router,
)
