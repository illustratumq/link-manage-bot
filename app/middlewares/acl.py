from aiogram.dispatcher.handler import CancelHandler
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.types import AllowedUpdates, Message, CallbackQuery, ChatType

from app.config import Config
from app.database.services.enums import UserTypeEnum
from app.database.services.repos import UserRepo


class ACLMiddleware(BaseMiddleware):
    allowed_updates = (AllowedUpdates.MESSAGE, AllowedUpdates.CALLBACK_QUERY)

    @staticmethod
    async def user_disallowed(msg: Message):
        text = (
            f'Доступ до цього боту мають тільки адміністратори.'
        )
        await msg.bot.send_message(msg.from_user.id, text)
        raise CancelHandler()

    async def setup_chat(self, msg: Message, user_db: UserRepo,  config: Config) -> None:
        if not msg.from_user.is_bot:
            disallowed = False
            user = await user_db.get_user(msg.from_user.id)
            if not user:
                await user_db.add(
                    full_name=msg.from_user.full_name, user_id=msg.from_user.id,
                )
                if msg.from_user.id in config.bot.admin_ids:
                    await user_db.update_user(msg.from_user.id, type=UserTypeEnum.ADMIN)
                else:
                    disallowed = True
            elif user.type == UserTypeEnum.USER:
                disallowed = True
            else:
                values_to_update = dict()
                if user.full_name != msg.from_user.full_name:
                    values_to_update.update(full_name=msg.from_user.full_name)
                if user.user_id not in config.bot.admin_ids:
                    values_to_update.update(type=UserTypeEnum.USER)
                    disallowed = True
                if values_to_update:
                    await user_db.update_user(msg.from_user.id, **values_to_update)

            if disallowed:
                await self.user_disallowed(msg)

    async def on_pre_process_message(self, msg: Message, data: dict) -> None:
        if not bool(msg.media_group_id):
            if msg.chat.type == ChatType.PRIVATE:
                await self.setup_chat(msg, data['user_db'], Config.from_env())

    async def on_pre_process_callback_query(self, call: CallbackQuery, data: dict) -> None:
        if call.message.chat.type == ChatType.PRIVATE:
            await self.setup_chat(call.message, data['user_db'], Config.from_env())
