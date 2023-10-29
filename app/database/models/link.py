import sqlalchemy as sa

from app.database.models.base import TimedBaseModel


class Link(TimedBaseModel):
    link_id = sa.Column(sa.BIGINT, primary_key=True, autoincrement=True, index=True)
    url = sa.Column(sa.VARCHAR, nullable=False)
    channel_id = sa.Column(sa.BIGINT, sa.ForeignKey('channels.channel_id', ondelete='SET NULL'), nullable=True)
    category_id = sa.Column(sa.BIGINT, sa.ForeignKey('categories.category_id', ondelete='SET NULL'), nullable=True)
    name = sa.Column(sa.VARCHAR, nullable=False)
    count = sa.Column(sa.BIGINT, nullable=False, default=0)



