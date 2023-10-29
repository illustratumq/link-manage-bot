import asyncio
import logging

import aiogram
import betterlogging as bl
from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.redis import RedisStorage2
from aiogram.types import ParseMode, AllowedUpdates, BotCommand

from app import handlers, middlewares
from app.config import Config
from app.database.services.db_engine import create_db_engine_and_session_pool
from app.misc.default_category import setup_default_category

log = logging.getLogger(__name__)


async def set_bot_commands(bot: Bot) -> None:
    await bot.set_my_commands(
        [
            BotCommand('menu', 'Меню боту'),
        ]
    )
    log.info("Установка комманд пройшла успішно")


async def notify_admin(bot: Bot, admin_ids: tuple[int]) -> None:
    for admin_id in admin_ids:
        try:
            await bot.send_message(admin_id, 'Бот запущено')
        except aiogram.exceptions.ChatNotFound:
            log.warning(f'Адмін з {admin_id} не ініціалізував чат.')


async def main():
    config = Config.from_env()
    bl.basic_colorized_config(level=config.misc.log_level)
    log.info('Запускаюсь...')

    storage = RedisStorage2(host=config.redis.host, port=config.redis.port)
    bot = Bot(config.bot.token, parse_mode=ParseMode.HTML)
    dp = Dispatcher(bot, storage=storage)
    db_engine, sqlalchemy_session = await create_db_engine_and_session_pool(config.db.sqlalchemy_url, config)

    allowed_updates = (
            AllowedUpdates.MESSAGE + AllowedUpdates.CALLBACK_QUERY +
            AllowedUpdates.CHAT_JOIN_REQUEST + AllowedUpdates.CHANNEL_POST + AllowedUpdates.CHAT_MEMBER
    )

    environments = dict(config=config, dp=dp)
    handlers.setup(dp)
    middlewares.setup(dp, environments, sqlalchemy_session)

    await set_bot_commands(bot)
    # await notify_admin(bot, config.bot.admin_ids)
    await setup_default_category(sqlalchemy_session)

    try:
        await dp.skip_updates()
        await dp.start_polling(allowed_updates=allowed_updates, reset_webhook=True)
    finally:
        await storage.close()
        await storage.wait_closed()
        await (await bot.get_session()).close()
        await db_engine.dispose()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        log.warning('Бот зупинено')
