from app.database.models import Category
from app.keyboards.inline.back import back_bt
from app.keyboards.inline.base import *

menu_cb = CallbackData('mn', 'action')
approve_cb = CallbackData('apr', 'action', 'chat_id')
category_cb = CallbackData('atc', 'action', 'channel_id', 'category_id')
channel_cb = CallbackData('chl', 'action', 'channel_id')
link_pag_cb = CallbackData('lnkp', 'action', 'page', 'name')

names_on_page = 10

def paired_list(input_list: list):
    return [input_list[i:i + 2] for i in range(0, len(input_list), 2)]

def button_menu_cb(action: str):
    return dict(callback_data=menu_cb.new(action=action))


def button_approve_cb(action: str, chat_id: int):
    return dict(callback_data=approve_cb.new(action=action, chat_id=chat_id))


def button_channel_cb(action: str, chat_id: int):
    return dict(callback_data=channel_cb.new(action=action, chat_id=chat_id))

def button_category_cb(action: str, chat_id: int, category_id: int):
    return dict(callback_data=category_cb.new(action=action, channel_id=chat_id, category_id=category_id))


def buttons_link_pag_cb(action: str, name: str, page: int = 0):
    return dict(callback_data=link_pag_cb.new(action=action, name=name, page=page))

def menu_kb():

    inline_keyboard = [
        [InlineKeyboardButton(Buttons.menu.new_link, **button_menu_cb('new_link')),
         InlineKeyboardButton(Buttons.menu.add_channel, **button_menu_cb('add_channel'))],
        [InlineKeyboardButton(Buttons.menu.links, **button_menu_cb('links')),
         InlineKeyboardButton(Buttons.menu.channels, **button_menu_cb('channels'))]
    ]

    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard, row_width=2)

def approve_chat_add_kb(chat_id: int):

    inline_keyboard = [
        [
            InlineKeyboardButton('Так', **button_approve_cb('approve', chat_id)),
            back_bt(text='Ні')
        ]
    ]

    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard, row_width=2)


def check_bot_in_channel_kb(chat_id: int):

    inline_keyboard = [
        [InlineKeyboardButton(Buttons.menu.check, **button_approve_cb('check', chat_id))],
        [back_bt(text='Відмінити')]
    ]

    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard, row_width=1)

def category_list_to_add(chat_id: int, categories: list[Category]):
    category_buttons = []
    for category in categories:
        category_buttons.append(
            InlineKeyboardButton(category.name,
                                 **button_category_cb('add', chat_id, category.category_id))
        )
    inline_keyboard = paired_list(category_buttons)
    inline_keyboard.insert(
        0,
        [InlineKeyboardButton(Buttons.menu.add_category,
                              **button_category_cb('new', chat_id, 'None'))]
    )
    inline_keyboard += [[back_bt('Відмінити')]]
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard, row_width=2)


def category_menu_kb(categories: list[Category], new_link: bool = False):
    category_buttons = []
    for category in categories:
        category_buttons.append(
            InlineKeyboardButton(category.name,
                                 **button_category_cb('select' if not new_link else 'new_link', 'none',
                                                      category.category_id))
        )
    inline_keyboard = paired_list(category_buttons)
    inline_keyboard += [[back_bt()]]
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard, row_width=2)


def channels_category_kb(category_id: int):
    inline_keyboard = [
        [InlineKeyboardButton(Buttons.menu.new_link, **button_category_cb('new_link', 'none', category_id))],
        # [InlineKeyboardButton(Buttons.menu.delete_channel, **button_category_cb('delete_channel', 'none', category_id))],
        [back_bt(to='category')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard, row_width=2)


def count_pages(names: list, names_on_page: int = 10) -> int:
    pages = len(names) / names_on_page
    if float(pages) > float(len(names) // names_on_page):
        return int(pages + 1)
    elif pages < 1:
        return 1
    else:
        return int(pages)


def linkname_pagination_kb(names: list, cur_name: str, page: int = 0):

    buttons_names = []
    for name in names:
        marker = '✔️ ' if name == cur_name else ''
        buttons_names.append(
            InlineKeyboardButton(f'{marker}{name}', **buttons_link_pag_cb('pag', name, page))
        )
    buttons_names = paired_list(buttons_names[names_on_page*page:names_on_page*(1+page)])
    buttons_names.insert(0, [
        InlineKeyboardButton(Buttons.menu.update_info, **buttons_link_pag_cb('upd', cur_name, page)),
        InlineKeyboardButton(Buttons.menu.delete, **buttons_link_pag_cb('delete', cur_name, page))]
    )
    page_numbers = count_pages(names, names_on_page)
    next_page = (page + 1) % page_numbers
    prev_page = (page - 1) % page_numbers
    buttons_names += [
        [InlineKeyboardButton('◀️', **buttons_link_pag_cb('pag', 'none', prev_page)),
         InlineKeyboardButton(f'{page + 1}/{page_numbers}', callback_data='none'),
         InlineKeyboardButton('▶️', **buttons_link_pag_cb('pag', 'none', next_page))],
        [back_bt('Закрити')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons_names)

def delete_link_kb(name: str, page: int):

    inline_keyboard = [
        [InlineKeyboardButton('Так', **buttons_link_pag_cb('conf_del', name,))],
        [back_bt(text='Відмінити', to='link_pag')]
    ]

    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)
