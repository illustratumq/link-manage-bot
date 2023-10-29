import sqlalchemy as sa

from app.database.models.base import TimedBaseModel


class Channel(TimedBaseModel):
    channel_id = sa.Column(sa.BIGINT, primary_key=True, autoincrement=False, index=True)
    name = sa.Column(sa.VARCHAR, nullable=False)
    category_id = sa.Column(sa.BIGINT, sa.ForeignKey('categories.category_id', ondelete='SET NULL'), nullable=True)


