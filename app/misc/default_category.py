import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

from app.database.services.repos import CategoryRepo

log = logging.getLogger(__name__)


async def setup_default_category(session: sessionmaker):
    session: AsyncSession = session()
    category_db = CategoryRepo(session)
    if await category_db.count() == 0:
        await category_db.add(
            name='Усі канали'
        )
        log.info('Створено категорію "Усі канали" за замовчуванням...')
