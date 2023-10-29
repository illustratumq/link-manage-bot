from datetime import timedelta

from aiogram import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery, ContentType, ChatJoinRequest

from app.database.services.repos import CategoryRepo, ChannelRepo, LinkRepo
from app.keyboards import Buttons
from app.keyboards.inline.back import back_kb, back_cb
from app.keyboards.inline.menu import menu_kb, menu_cb, approve_chat_add_kb, approve_cb, check_bot_in_channel_kb, \
    category_list_to_add, category_cb, category_menu_kb, channels_category_kb, linkname_pagination_kb, link_pag_cb, \
    names_on_page, count_pages, delete_link_kb
from app.misc.times import now, localize
from app.states.states import AddChannelSG, AddLinkSG, AddCategorySG


async def start_cmd(msg: Message, state: FSMContext):
    me = (await msg.bot.me).full_name
    text = (
        f'🗓 Сьогодні {now().strftime("%d.%m.%y")}\n'
        f'🕐 Час {now().strftime("%H:%M")}\n\n'
        f'Вітаю в головному меню {me}.'
    )
    await msg.answer(text, reply_markup=menu_kb())
    await state.finish()


async def back_cmd(call: CallbackQuery, callback_data: dict, state: FSMContext, category_db: CategoryRepo,
                   channel_db: ChannelRepo, link_db: LinkRepo):
    to = callback_data.get('to')
    if to == 'menu':
        await call.message.delete()
        await start_cmd(call.message, state)
    elif to == 'category':
        await category_cmd(call, category_db, callback_data)
    elif to == 'channel_list':
        await channel_list_cmd(call, callback_data, category_db, channel_db)
    elif to == 'back_select_category':
        await select_channel_category(call, int(callback_data['channel_id']), category_db)
    elif to == 'link_pag':
        callback_data.update({'action': 'pag'})
        await links_pagination(call, callback_data, link_db, channel_db)


async def add_channel_cmd(call: CallbackQuery, state: FSMContext):
    text = (
        'Введіть chat_id каналу, який потрбіно додати, '
        'або перешліть будь яке повідомлення з нього.'
    )
    msg = await call.message.edit_text(text, reply_markup=back_kb())
    await state.update_data(last_msg_id=msg.message_id)
    await AddChannelSG.WaitForChannel.set()


async def get_channel_id_from_post(msg: Message, state: FSMContext, channel_db: ChannelRepo, category_db: CategoryRepo):
    chat_id = msg.forward_from_chat.id if msg.forward_from_chat else msg.text
    if not isinstance(chat_id, int) and not chat_id.replace('-', '').isnumeric():
        await msg.answer('chat_id має бути числом, спробуйте ще раз.')
        return
    else:
        chat_id = int(chat_id)
    data = await state.get_data()
    try:
        chat = await msg.bot.get_chat(chat_id)
        if channel := await channel_db.get_channel(chat_id):
            category = await category_db.get_category(channel.category_id)
            await msg.answer(f'Цей канал вже додано в категорію "{category.name}"', reply_markup=back_kb('Закрити'))
            return
        last_msg_id = data['last_msg_id']
        await msg.bot.delete_message(msg.from_user.id, last_msg_id)
        text = (
            f'Ви бажаєте додати <a href="{await chat.get_url()}">{chat.title}</a> з {await chat.get_member_count()}'
            f' підписниками?'
        )
        await msg.answer(text, reply_markup=approve_chat_add_kb(chat_id))
    except:
        text = (
            f'Не знайшов канал з {chat_id=}, спробуйте ще раз.\n\n'
            f'<i>Важливо: щоб додати приватний канал, для початку додайте у нього бота '
            f'{(await msg.bot.me).full_name}.</i>'
        )
        await msg.answer(text, reply_markup=back_kb(text='Відмінити'))

async def check_bot_is_admin(call: CallbackQuery, callback_data: dict, state: FSMContext,
                             category_db: CategoryRepo):
    chat_id = int(callback_data['chat_id'])
    bot = (await call.bot.me)
    try:
        admins = await (await call.bot.get_chat(chat_id)).get_administrators()
        for admin in admins:
            if bot.id == admin.user.id:
                await select_channel_category(call, chat_id, category_db)
                await state.finish()
                return
            else:
                raise f'Bot not is admin of chanel {chat_id=}'
    except:
        action = callback_data['action']
        chat = await call.bot.get_chat(chat_id)
        text = (
            f'Для того, щоб продовжити, додайте бота {bot.full_name} в канал {chat.title}, '
            f'після чого натисніть кнопку <i>"{Buttons.menu.check}"</i>.'
        )
        if action == 'check':
            time = now().strftime('%H:%M:%S')
            text += f'\n\nUPD ({time}): Бот не є адміністратором каналу, спробуйте ще раз.'
        await call.message.edit_text(text, reply_markup=check_bot_in_channel_kb(chat_id))
        await AddChannelSG.WaitForChannel.set()


async def select_channel_category(upd: CallbackQuery | Message, chat_id: int, category_db: CategoryRepo):
    categories = await category_db.get_all()
    msg = upd if isinstance(upd, Message) else upd.message
    kwargs = dict(text='Оберіть категорію, в яку буде доданий канал', reply_markup=category_list_to_add(chat_id, categories))
    if isinstance(upd, CallbackQuery):
        await msg.edit_text(**kwargs)
    else:
        await msg.answer(**kwargs)


async def add_channel_to_db(upd: CallbackQuery | Message, callback_data: dict, channel_db: ChannelRepo,
                            category_db: CategoryRepo):
    bot = upd.bot
    channel_id = int(callback_data['channel_id'])
    category_id = int(callback_data['category_id'])
    chat = await bot.get_chat(channel_id)
    await channel_db.add(channel_id=channel_id, name=chat.title, category_id=category_id)
    if isinstance(upd, CallbackQuery):
        await upd.answer(f'Канал {chat.title} успішно додано', show_alert=True)
    await channel_list_cmd(upd, callback_data, category_db, channel_db)


async def category_cmd(call: CallbackQuery, category_db: CategoryRepo, callback_data: dict):
    categories = await category_db.get_all()
    new_link = False
    if 'action' in callback_data.keys() and callback_data['action'] == 'new_link':
        new_link = True
    await call.message.edit_text(
        'Оберіть категорію каналів', reply_markup=category_menu_kb(categories, new_link)
    )

async def channel_list_cmd(upd: CallbackQuery | Message, callback_data: dict, category_db: CategoryRepo,
                           channel_db: ChannelRepo):
    msg = upd if isinstance(upd, Message) else upd.message
    category_id = int(callback_data['category_id'])
    category = await category_db.get_category(category_id)
    channels = await channel_db.get_channels_by_category(category_id)
    channels_list_str = []
    for channel in channels:
        chat = await upd.bot.get_chat(channel.channel_id)
        url = await chat.get_url()
        subs = await chat.get_member_count()
        channel_str = f'<a href="{url}">{chat.title}</a> - {subs}'
        channels_list_str.append(channel_str)
    text = (
        f'{Buttons.menu.add_category[0]} Категорія: {category.name}\n\n' + '\n'.join(channels_list_str)
    )
    kwargs = dict(text=text, reply_markup=channels_category_kb(category_id))
    if isinstance(upd, CallbackQuery):
        await msg.edit_text(**kwargs)
    else:
        await msg.delete()
        await msg.answer(**kwargs)


async def add_new_link_category(call: CallbackQuery, callback_data: dict, state: FSMContext):
    text = (
        f'{Buttons.menu.new_link[0]} Введіть назву для посилань 👇'
    )
    msg = await call.message.edit_text(text,
                                       reply_markup=back_kb(to='channel_list', category_id=callback_data['category_id']))
    await state.update_data(category_id=callback_data['category_id'], last_msg_id=msg.message_id)
    await AddLinkSG.WaitForLink.set()


async def save_new_category_link(msg: Message, state: FSMContext, link_db: LinkRepo, channel_db: ChannelRepo):
    link_name_orig = msg.text.replace('\n', ' ').replace(' ', '_')
    link_name = link_name_orig
    c = 1
    while len(await link_db.get_links_by_name(link_name)) > 0:
        link_name = link_name_orig + f'({c})'
        c += 1
    data = await state.get_data()
    category_id = int(data['category_id'])
    await msg.bot.delete_message(msg.from_user.id, message_id=data['last_msg_id'])
    channels = await channel_db.get_channels_by_category(category_id)
    for channel in channels:
        chat = await msg.bot.get_chat(channel.channel_id)
        link = await msg.bot.create_chat_invite_link(
            chat.id, name=link_name, creates_join_request=True,
            expire_date=now() + timedelta(days=365)
        )
        await link_db.add(url=link.invite_link, channel_id=channel.channel_id,
                          category_id=category_id, name=link_name)
    callback_data = {'action': 'pag', 'name': link_name}
    links = await link_db.get_all()
    if links:
        names = list(set([link.name for link in links]))
        page_numbers = count_pages(names)
        callback_data.update({'page': page_numbers - 1})
    await links_pagination(msg, callback_data, link_db, channel_db)
    await state.finish()


async def links_pagination(upd: CallbackQuery | Message, callback_data: dict, link_db: LinkRepo,
                           channel_db: ChannelRepo):
    msg = upd.message if isinstance(upd, CallbackQuery) else upd
    page = int(callback_data['page']) if 'page' in callback_data.keys() else 0
    names = {}
    if callback_data['action'] == 'upd':
        await upd.answer('Оновлено...')
    for link in await link_db.get_all():
        if link.name not in names.keys():
            names.update({link.name: []})
        names[link.name].append(link)
    if not names:
        if isinstance(upd, CallbackQuery):
            await upd.answer('У вас ще немає лінків')
            return
    if 'name' not in callback_data.keys() or callback_data['name'] == 'none':
        name = list(names.keys())[names_on_page*page:names_on_page*(1+page)][0]
        links = await link_db.get_links_by_name(name)
    else:
        name = callback_data['name']
        links = await link_db.get_links_by_name(callback_data['name'])
    text = (
        f'🔗 Лінк: {name}\n'
        f'🗓 Створення: {localize(links[0].created_at).strftime("%d.%m.%y %H:%M")}\n\n'
    )
    count_all = 0
    channels_dict = {}
    channels = []
    for link in links:
        channel = await channel_db.get_channel(link.channel_id)
        channels.append(channel)
        channels_dict.update(
            {
                channel.channel_id: {
                    'subs': await (await upd.bot.get_chat(channel.channel_id)).get_member_count(),
                    'link_id': link.link_id
                }
            }
        )

    channels = sorted(channels, key=lambda c: channels_dict[c.channel_id]['subs'], reverse=True)
    channel_message_str = f''

    for channel in channels:
        chat = await upd.bot.get_chat(channel.channel_id)
        url = await chat.get_url()
        subs = await chat.get_member_count()
        prefix_to_delete = ['Рідне', 'Рідні', 'Рідний', 'Рідна']
        title = chat.title
        for prefix in prefix_to_delete:
            title = title.replace(prefix, '').strip()
        link = await link_db.get_link(channels_dict[channel.channel_id]['link_id'])
        channel_str = f'<a href="{link.url}">{title}</a> - <code>{link.url}</code> - {subs} - 👤 - {link.count}\n'
        count_all += link.count
        text += channel_str
        channel_message_str += f'<a href="{link.url}">{title}</a>\n'
    if count_all > 0:
        text += f'Всього заявок: {count_all}'
    text += '\n\n' + channel_message_str
    kwargs = {'text': text, 'reply_markup': linkname_pagination_kb(names, name, page)}
    if isinstance(upd, Message):
        await msg.delete()
        await msg.answer(**kwargs)
    else:
        await msg.edit_text(**kwargs)

async def new_category_cmd(call: CallbackQuery, callback_data: dict, state: FSMContext):
    channel_id = int(callback_data['channel_id'])
    msg = await call.message.edit_text('Введіть назву нової категорії',
                                       reply_markup=back_kb(to='back_select_category'))
    await AddCategorySG.WaitForCategory.set()
    await state.update_data(channel_id=channel_id, last_msg_id=msg.message_id)


async def new_category_save(msg: Message, category_db: CategoryRepo, state: FSMContext, channel_db: ChannelRepo):
    data = await state.get_data()
    await msg.bot.delete_message(msg.from_user.id, data['last_msg_id'])
    new_category = await category_db.add(name=msg.text)
    callback_data = dict(channel_id=data['channel_id'], category_id=new_category.category_id)
    await add_channel_to_db(msg, callback_data, channel_db, category_db)
    await state.finish()


# async def select_to_delete(call: CallbackQuery, callback_data: dict, category_db: CategoryRepo):

async def delete_link_name(call: CallbackQuery, callback_data: dict):
    await call.message.edit_text(
        f'Ви дійсно бажаєте видалити посилання <i>"{callback_data["name"]}"</i>?\n\n',
        reply_markup=delete_link_kb(callback_data['name'], callback_data['page'])
    )

async def delete_link_conf(call: CallbackQuery, callback_data: dict, link_db: LinkRepo, channel_db: ChannelRepo):
    links = await link_db.get_links_by_name(callback_data['name'])
    for link in links:
        # chat = await call.bot.get_chat(link.channel_id)
        # await chat.revoke_invite_link(invite_link=link.url)
        await link_db.delete_link(link.link_id)
    await call.answer('Усі посилання були успішно видалені')
    callback_data = dict({'action': 'pag'})
    await links_pagination(call, callback_data, link_db, channel_db)

async def count_chat_join_requests(cjr: ChatJoinRequest, link_db: LinkRepo):
    link = await link_db.get_link_by_url(cjr)
    if link:
        await link_db.update_link(link.link_id, count=cjr.invite_link.pending_join_request_count)


def setup(dp: Dispatcher):
    dp.register_chat_join_request_handler(count_chat_join_requests, state='*')
    dp.register_message_handler(start_cmd, CommandStart(), state='*')
    dp.register_message_handler(start_cmd, Command('menu'), state='*')
    dp.register_callback_query_handler(
        add_channel_cmd, menu_cb.filter(action='add_channel'), state='*')
    dp.register_callback_query_handler(
        back_cmd, back_cb.filter(), state='*')
    dp.register_message_handler(
        get_channel_id_from_post, state=AddChannelSG.WaitForChannel, content_types=ContentType.ANY)
    dp.register_callback_query_handler(
        check_bot_is_admin, approve_cb.filter(action=['approve', 'check']), state='*')
    dp.register_callback_query_handler(
        add_channel_to_db, category_cb.filter(action='add'), state='*')
    dp.register_callback_query_handler(
        category_cmd, menu_cb.filter(action=['channels', 'new_link']), state='*')
    dp.register_callback_query_handler(
        channel_list_cmd, category_cb.filter(action='select'), state='*')
    dp.register_callback_query_handler(
        add_new_link_category, category_cb.filter(action='new_link'), state='*')
    dp.register_message_handler(save_new_category_link, state=AddLinkSG.WaitForLink)
    dp.register_callback_query_handler(
        links_pagination, menu_cb.filter(action='links'), state='*')
    dp.register_callback_query_handler(delete_link_name, link_pag_cb.filter(action='delete'), state='*')
    dp.register_callback_query_handler(delete_link_conf, link_pag_cb.filter(action='conf_del'), state='*')
    dp.register_callback_query_handler(links_pagination, link_pag_cb.filter(), state='*')
    dp.register_callback_query_handler(new_category_cmd, category_cb.filter(action='new'), state='*')
    dp.register_message_handler(new_category_save, state=AddCategorySG.WaitForCategory)
