import logging
from typing import Any

from aiogram import Dispatcher
from app.middlewares.database import DatabaseMiddleware
from app.middlewares.environment import EnvironmentMiddleware
from app.middlewares.throttling import ThrottlingMiddleware
from sqlalchemy.orm import sessionmaker

from app.middlewares.acl import ACLMiddleware

log = logging.getLogger(__name__)


def setup(dp: Dispatcher, environments: dict[str, Any], session_pool: sessionmaker):
    dp.setup_middleware(EnvironmentMiddleware(environments))
    dp.setup_middleware(DatabaseMiddleware(session_pool))
    # dp.setup_middleware(ThrottlingMiddleware(limit=0.1))
    dp.setup_middleware(ACLMiddleware())
    log.info('Мідлварі успішно встановлені...')
