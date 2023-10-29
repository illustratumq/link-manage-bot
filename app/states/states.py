from app.states.base import *


class AddChannelSG(StatesGroup):
    WaitForChannel = State()
    WaitForBotAdmin = State()

class AddLinkSG(StatesGroup):
    WaitForLink = State()


class AddCategorySG(StatesGroup):
    WaitForCategory = State()