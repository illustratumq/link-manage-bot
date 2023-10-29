import sqlalchemy as sa

from app.database.models.base import TimedBaseModel


class Category(TimedBaseModel):

    __tablename__ = 'categories'

    category_id = sa.Column(sa.BIGINT, primary_key=True, autoincrement=True)
    name = sa.Column(sa.VARCHAR, nullable=False)


