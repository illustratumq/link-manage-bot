from aiogram.dispatcher.filters import BoundFilter
from aiogram.dispatcher.handler import ctx_data
from aiogram.types import Message, CallbackQuery, InlineQuery

from app.database.services.enums import UserTypeEnum
from app.database.services.repos import UserRepo


class IsAdminFilter(BoundFilter):
    async def check(self, upd: Message | CallbackQuery, *args: ...) -> bool:
        data: dict = ctx_data.get()
        user_db: UserRepo = data['user_db']
        user = await user_db.get_user(upd.from_user.id)
        return False if not user else user.type == UserTypeEnum.ADMIN
