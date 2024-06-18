from aiogram import F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.scene import on
from aiogram.types import CallbackQuery, Message
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from bot.scenes.chat_settings.base import (
    Action,
    BaseScene,
    ChatSettingsCB,
    ChatSettingsStates,
    FSMData,
)
from bot.scenes.chat_settings.stages.general_settings.set_greeting.keyboards import (
    greeting_media_keyboard,
)
from bot.storages.psql import DBChatSettingsModel, RDChatSettingsModel
from bot.storages.psql.chat.chat_settings_model import GreetingFarewellType

CHAT_SETTINGS_GREETING_SET_MEDIA_WINDOW_TEXT = (
    "💁‍♂️ In this window, you need to send a media file that the bot will send to new chat "
    "participants.\n"
    "\n"
    "📝 A media file can be an image, video, GIF, or sticker.\n"
    "\n"
    "💡 Pay attention:\n"
    "— Depending on the type of media sent, the bot will change the type of greeting "
    "accordingly.\n"
    "— When you reset a media, the media whose type is currently selected will be reset.\n"
    "— Stickers don't support text."
)


class SetGreetingMediaWindow(BaseScene, state=ChatSettingsStates.GREETING_SET_MEDIA):
    @on.callback_query.enter()
    async def on_enter_cb(self, cb: CallbackQuery, state: FSMContext) -> None:
        sent = await cb.message.edit_text(
            CHAT_SETTINGS_GREETING_SET_MEDIA_WINDOW_TEXT,
            reply_markup=greeting_media_keyboard(),
        )

        await state.update_data(FSMData(current_message_id=sent.message_id))

    @on.message(F.photo)
    async def set_greeting_photo_handler(
        self,
        msg: Message,
        state: FSMContext,
        db_session: async_sessionmaker[AsyncSession],
        redis: Redis,
    ) -> None:
        data: FSMData = await state.get_data()

        async with db_session() as session:
            stmt = select(DBChatSettingsModel).where(DBChatSettingsModel.id == msg.chat.id)
            chat_settings: DBChatSettingsModel = await session.scalar(stmt)

            chat_settings.greeting_photo_id = msg.photo[-1].file_id
            chat_settings.greeting_type = GreetingFarewellType.PHOTO.value

            await session.commit()

            await RDChatSettingsModel.from_orm(chat_settings).save(redis)

        await state.update_data(
            FSMData(
                bot_messages_to_delete=list(
                    {
                        *data["bot_messages_to_delete"],
                        data["current_message_id"],
                        data["greeting_farewell_message_id"],
                    }
                ),
                user_messages_to_delete=list({*data["user_messages_to_delete"], msg.message_id}),
            ),
        )

        await self.wizard.goto(ChatSettingsStates.GREETING, updated=True)

    @on.message(F.video)
    async def set_greeting_video_handler(
        self,
        msg: Message,
        state: FSMContext,
        db_session: async_sessionmaker[AsyncSession],
        redis: Redis,
    ) -> None:
        data: FSMData = await state.get_data()

        async with db_session() as session:
            stmt = select(DBChatSettingsModel).where(DBChatSettingsModel.id == msg.chat.id)
            chat_settings: DBChatSettingsModel = await session.scalar(stmt)

            chat_settings.greeting_video_id = msg.video.file_id
            chat_settings.greeting_type = GreetingFarewellType.VIDEO.value

            await session.commit()

            await RDChatSettingsModel.from_orm(chat_settings).save(redis)

        await state.update_data(
            FSMData(
                bot_messages_to_delete=list(
                    {
                        *data["bot_messages_to_delete"],
                        data["current_message_id"],
                        data["greeting_farewell_message_id"],
                    },
                ),
                user_messages_to_delete=list({msg.message_id}),
            ),
        )

        await self.wizard.goto(ChatSettingsStates.GREETING, updated=True)

    @on.message(F.animation)
    async def set_greeting_gif_handler(
        self,
        msg: Message,
        state: FSMContext,
        db_session: async_sessionmaker[AsyncSession],
        redis: Redis,
    ) -> None:
        data: FSMData = await state.get_data()

        async with db_session() as session:
            stmt = select(DBChatSettingsModel).where(DBChatSettingsModel.id == msg.chat.id)
            chat_settings: DBChatSettingsModel = await session.scalar(stmt)

            chat_settings.greeting_gif_id = msg.animation.file_id
            chat_settings.greeting_type = GreetingFarewellType.GIF.value

            await session.commit()

            await RDChatSettingsModel.from_orm(chat_settings).save(redis)

        await state.update_data(
            FSMData(
                bot_messages_to_delete=list(
                    {
                        *data["bot_messages_to_delete"],
                        data["current_message_id"],
                        data["greeting_farewell_message_id"],
                    },
                ),
                user_messages_to_delete=list({*data["user_messages_to_delete"], msg.message_id}),
            ),
        )

        await self.wizard.goto(ChatSettingsStates.GREETING, updated=True)

    @on.message(F.sticker)
    async def set_greeting_sticker_handler(
        self,
        msg: Message,
        state: FSMContext,
        db_session: async_sessionmaker[AsyncSession],
        redis: Redis,
    ) -> None:
        data: FSMData = await state.get_data()

        async with db_session() as session:
            stmt = select(DBChatSettingsModel).where(DBChatSettingsModel.id == msg.chat.id)
            chat_settings: DBChatSettingsModel = await session.scalar(stmt)

            chat_settings.greeting_sticker_id = msg.sticker.file_id
            chat_settings.greeting_type = GreetingFarewellType.STICKER.value

            await session.commit()

            await RDChatSettingsModel.from_orm(chat_settings).save(redis)

        await state.update_data(
            FSMData(
                bot_messages_to_delete=list(
                    {
                        *data["bot_messages_to_delete"],
                        data["current_message_id"],
                        data["greeting_farewell_message_id"],
                    },
                ),
                user_messages_to_delete=list({*data["user_messages_to_delete"], msg.message_id}),
            ),
        )

        await self.wizard.goto(ChatSettingsStates.GREETING, updated=True)

    @on.callback_query(ChatSettingsCB.filter(F.action == Action.GREETING_RESET_MEDIA))
    async def reset_greeting_media_handler(
        self,
        cb: CallbackQuery,
        state: FSMContext,
        db_session: async_sessionmaker[AsyncSession],
        redis: Redis,
    ) -> None:
        data: FSMData = await state.get_data()

        updated = await reset_greeting_media(cb, db_session, redis)

        if updated is True:
            await state.update_data(
                FSMData(
                    bot_messages_to_delete=list(
                        {
                            *data["bot_messages_to_delete"],
                            cb.message.message_id,
                            data["greeting_farewell_message_id"],
                        }
                    ),
                    user_messages_to_delete=list({*data["user_messages_to_delete"]}),
                ),
            )

        await self.wizard.goto(ChatSettingsStates.GREETING, updated=updated)

    @on.callback_query(ChatSettingsCB.filter(F.action == Action.BACK))
    async def back_handler_cb(self, _: CallbackQuery) -> None:
        await self.wizard.goto(ChatSettingsStates.GREETING, updated=False)


async def reset_greeting_media(
    cb: CallbackQuery, db_session: async_sessionmaker[AsyncSession], redis: Redis
) -> bool:
    updated: bool = False

    async with db_session() as session:
        stmt = select(DBChatSettingsModel).where(DBChatSettingsModel.id == cb.message.chat.id)
        chat_settings: DBChatSettingsModel = await session.scalar(stmt)

        match chat_settings.greeting_type:
            case GreetingFarewellType.PHOTO.value:
                if chat_settings.greeting_photo_id is not None:
                    updated = True

                chat_settings.greeting_photo_id = None
            case GreetingFarewellType.VIDEO.value:
                if chat_settings.greeting_video_id is not None:
                    updated = True

                chat_settings.greeting_video_id = None
            case GreetingFarewellType.GIF.value:
                if chat_settings.greeting_gif_id is not None:
                    updated = True

                chat_settings.greeting_gif_id = None
            case GreetingFarewellType.STICKER.value:
                if chat_settings.greeting_sticker_id is not None:
                    updated = True

                chat_settings.greeting_sticker_id = None

            case _:
                pass

        await session.commit()

        await RDChatSettingsModel.from_orm(chat_settings).save(redis)

    return updated
