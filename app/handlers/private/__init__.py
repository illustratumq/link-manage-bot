from aiogram import Dispatcher

from app.handlers.private import menu


def setup(dp: Dispatcher):
    menu.setup(dp)