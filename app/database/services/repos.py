from aiogram.types import ChatJoinRequest

from app.database.models import *
from app.database.services.db_ctx import BaseRepo


class UserRepo(BaseRepo[User]):
    model = User

    async def get_user(self, user_id: int) -> User:
        return await self.get_one(self.model.user_id == user_id)

    async def update_user(self, user_id: int, **kwargs) -> None:
        return await self.update(self.model.user_id == user_id, **kwargs)

    async def delete_user(self, user_id: int):
        return await self.delete(self.model.user_id == user_id)


class ChannelRepo(BaseRepo[Channel]):
    model = Channel

    async def get_channel(self, channel_id: int) -> Channel:
        return await self.get_one(self.model.channel_id == channel_id)

    async def get_channels_by_category(self, category_id: int) -> list[Channel]:
        return await self.get_all(self.model.category_id == category_id)

    async def update_channel(self, channel_id: int, **kwargs) -> None:
        return await self.update(self.model.channel_id == channel_id, **kwargs)

    async def delete_channel(self, channel_id: int):
        return await self.delete(self.model.channel_id == channel_id)


class LinkRepo(BaseRepo[Link]):
    model = Link

    async def get_link(self, link_id: int) -> Link:
        return await self.get_one(self.model.link_id == link_id)

    async def get_channel_link(self, channel_id: int, category_id: int) -> list[Link]:
        return await self.get_all(self.model.channel_id == channel_id, self.model.category_id == category_id)

    async def count_channel_links(self, channel_id: int):
        return await self.count(self.model.channel_id == channel_id)

    async def get_link_by_url(self, cjr: ChatJoinRequest) -> Link:
        links = await self.get_all(self.model.channel_id == cjr.chat.id)
        for link in links:
            if cjr.invite_link.invite_link.replace('...', '') in link.url:
                return link

    async def get_links_by_name(self, name: str) -> list[Link]:
        return await self.get_all(self.model.name == name)

    async def update_link(self, link_id: int, **kwargs) -> None:
        return await self.update(self.model.link_id == link_id, **kwargs)

    async def delete_link(self, link_id: int):
        return await self.delete(self.model.link_id == link_id)


class CategoryRepo(BaseRepo[Category]):
    model = Category

    async def get_category(self, category_id: int) -> Category:
        return await self.get_one(self.model.category_id == category_id)

    async def update_category(self, category_id: int, **kwargs) -> None:
        return await self.update(self.model.category_id == category_id, **kwargs)

    async def delete_category(self, category_id: int):
        return await self.delete(self.model.category_id == category_id)

