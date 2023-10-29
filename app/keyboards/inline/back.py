from app.keyboards.inline.base import *

back_cb = CallbackData('bk', 'to', 'category_id', 'channel_id')


def back_bt(text: str = Buttons.menu.back, to: str = 'menu',
            category_id='none', channel_id='none'):
    return InlineKeyboardButton(text,
                                callback_data=back_cb.new(
                                    to=to, category_id=category_id, channel_id=channel_id))


def back_kb(text: str = Buttons.menu.back, to: str = 'menu',
            category_id='none', channel_id='none'):
    return InlineKeyboardMarkup(row_width=1, inline_keyboard=[[back_bt(text, to, category_id, channel_id)]])
