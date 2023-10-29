import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ENUM

from app.database.models.base import TimedBaseModel
from app.database.services.enums import UserTypeEnum


class User(TimedBaseModel):
    user_id = sa.Column(sa.BIGINT, primary_key=True, autoincrement=False, index=True)
    full_name = sa.Column(sa.VARCHAR(255), nullable=False)
    type = sa.Column(ENUM(UserTypeEnum), default=UserTypeEnum.USER, nullable=False)
