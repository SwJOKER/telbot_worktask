import os

import pytest
from aiogram import Dispatcher, Bot

from aiogram.fsm.storage.base import StorageKey
from aiogram.methods import SendMessage
import db
import keyboards
import utils
from states import RouterStates
from tests.test_utils import TEST_USER, TEST_CHAT, get_message, get_update
from strings import *
import routers
from utils import get_clubs_from_source, get_clubs_str, set_active_clubs
from random import choice


db.check_db_exists()


@pytest.mark.asyncio
async def test_start_command(dispatcher: Dispatcher, bot: Bot):
    key = StorageKey(bot.id, TEST_CHAT.id, user_id=TEST_USER.id)
    await dispatcher.storage.set_data(bot=bot,
                                      key=key,
                                      data={'test': 12})
    message = get_message('/start')
    result: SendMessage = await dispatcher.feed_update(bot=bot, update=get_update(message=message))
    data = await dispatcher.storage.get_data(bot=bot, key=key)
    state = await dispatcher.storage.get_state(bot=bot, key=key)
    assert state == RouterStates.new_union
    assert isinstance(result, SendMessage)
    assert not data


@pytest.mark.asyncio
async def test_list_command(dispatcher: Dispatcher, bot: Bot):
    key = StorageKey(bot.id, TEST_CHAT.id, user_id=TEST_USER.id)
    test_data = {'test': 'test'}
    await dispatcher.storage.set_data(bot=bot,
                                      key=key,
                                      data=test_data)
    message = get_message('/list')
    result: SendMessage = await dispatcher.feed_update(bot=bot, update=get_update(message=message))
    data = await dispatcher.storage.get_data(bot=bot, key=key)
    state = await dispatcher.storage.get_state(bot=bot, key=key)
    assert state == RouterStates.show_union
    assert isinstance(result, SendMessage)
    assert data != test_data
    assert data


@pytest.mark.asyncio
async def test_new_union(dispatcher: Dispatcher, bot: Bot):
    unions_count = len(db.get_users_unions(TEST_USER.id))
    key = StorageKey(bot.id, TEST_CHAT.id, user_id=TEST_USER.id)
    await dispatcher.storage.set_state(bot=bot, key=key, state=RouterStates.new_union)
    state = dispatcher.fsm.get_context(bot=bot, user_id=TEST_USER.id, chat_id=TEST_CHAT.id)
    # Создать союз
    message = get_message(STR_MAKE_UNION)
    result: SendMessage = await dispatcher.feed_update(bot=bot, update=get_update(message=message))
    assert result.reply_markup.remove_keyboard
    assert isinstance(result, SendMessage)
    assert result.text == STR_INSERT_TITLE
    # Введите название
    message = get_message('Имя')
    result: SendMessage = await routers.new_union(message, state)
    data = await dispatcher.storage.get_data(bot=bot, key=key)
    assert isinstance(result, SendMessage)
    assert data['name'] == message.text.strip()
    assert result.text == STR_INSERT_REBATE
    # Введите ребейт
    message = get_message('1')
    result: SendMessage = await routers.new_union(message, state)
    data = await dispatcher.storage.get_data(bot=bot, key=key)
    assert isinstance(result, SendMessage)
    assert data['rebate'] == message.text.strip()
    assert result.text == STR_LIST_OR_EXCEL
    # Список клубов или файл
    message = get_message('Клуб 1\nКлуб 2')
    clubs = await get_clubs_from_source(message)
    clubs_txt = get_clubs_str(clubs)
    result: SendMessage = await routers.new_union(message, state)
    data = await dispatcher.storage.get_data(bot=bot, key=key)
    assert isinstance(result, SendMessage)
    assert data['clubs'] == clubs
    # клубы в "дп"
    message = get_message('1')
    info = STR_CHECK_DATA % (data["name"], data["rebate"])
    active_indexes = message.text.split(' ')
    set_active_clubs(clubs, active_indexes)
    info += get_clubs_str(clubs)
    result: SendMessage = await routers.new_union(message, state)
    data = await dispatcher.storage.get_data(bot=bot, key=key)
    assert isinstance(result, SendMessage)
    assert data['clubs'] == clubs
    assert result.text == info
    assert unions_count < len(db.get_users_unions(TEST_USER.id))


@pytest.mark.asyncio
async def test_accept_data(dispatcher: Dispatcher, bot: Bot):
    message = get_message(STR_TRUE)
    key = StorageKey(bot.id, TEST_CHAT.id, user_id=TEST_USER.id)
    test_data = {'test': 'test'}
    bot_key = {'bot': bot, 'key': key}
    await dispatcher.storage.set_state(**bot_key, state=RouterStates.accept_data)
    await dispatcher.storage.set_data(**bot_key, data=test_data)
    result: SendMessage = await dispatcher.feed_update(bot=bot, update=get_update(message))
    data = await dispatcher.storage.get_data(**bot_key)
    state = await dispatcher.storage.get_state(**bot_key)
    assert isinstance(result, SendMessage)
    assert state == RouterStates.show_union
    assert not data.get('test'), 'not cleaned data'
    assert data['unions'] == utils.get_all_unions(message.from_user.id)


@pytest.mark.asyncio
async def test_show_union_data(dispatcher: Dispatcher, bot: Bot):
    key = StorageKey(bot.id, TEST_CHAT.id, user_id=TEST_USER.id)
    bot_key = {'bot': bot, 'key': key}
    unions = utils.get_all_unions(TEST_USER.id)
    await dispatcher.storage.set_state(**bot_key, state=RouterStates.show_union)
    await dispatcher.storage.set_data(**bot_key, data={'unions': unions})
    # Пользовательский вид индекса = index + 1, заведомо неверный индекс = max + 2
    index = choice(list(unions.keys())) + 1
    wrong_index = max(unions.keys()) + 2
    message = get_message(str(wrong_index))
    result: SendMessage = await dispatcher.feed_update(bot=bot, update=get_update(message))
    assert isinstance(result, SendMessage)
    assert result.text == STR_WRONG_NUM
    message = get_message(str(index))
    result: SendMessage = await dispatcher.feed_update(bot=bot, update=get_update(message))
    data = await dispatcher.storage.get_data(**bot_key)
    state = await dispatcher.storage.get_state(**bot_key)
    assert isinstance(result, SendMessage)
    # в хранилище должен быть фактический индекс
    assert data.get('selected_union') == index - 1
    assert state == RouterStates.editing
    assert result.reply_markup == keyboards.work_data_kb()


@pytest.mark.asyncio
async def test_edit_data(dispatcher: Dispatcher, bot: Bot):
    key = StorageKey(bot.id, TEST_CHAT.id, user_id=TEST_USER.id)
    bot_key = {'bot': bot, 'key': key}
    unions = utils.get_all_unions(TEST_USER.id)
    test_data = {'unions': unions, 'selected_union': 1}
    test_union = test_data['unions'][test_data['selected_union']]
    message = get_message(STR_EDIT)
    out_message = utils.msg_union_info(test_union)
    await dispatcher.storage.set_state(**bot_key, state=RouterStates.accept_data)
    await dispatcher.storage.set_data(**bot_key, data=test_data)
    result: SendMessage = await dispatcher.feed_update(bot=bot, update=get_update(message))
    state = await dispatcher.storage.get_state(**bot_key)
    assert isinstance(result, SendMessage)
    assert state == RouterStates.editing
    assert result.text == out_message
    assert result.reply_markup == keyboards.edit_data_kb()


@pytest.mark.asyncio
async def test_edit_union_menu(dispatcher: Dispatcher, bot: Bot):
    key = StorageKey(bot.id, TEST_CHAT.id, user_id=TEST_USER.id)
    bot_key = {'bot': bot, 'key': key}
    await dispatcher.storage.set_state(**bot_key, state=RouterStates.editing)
    message = get_message(STR_EDIT_UNION)
    result: SendMessage = await dispatcher.feed_update(bot=bot, update=get_update(message))
    state = await dispatcher.storage.get_state(**bot_key)
    assert isinstance(result, SendMessage)
    assert state == RouterStates.editing_union
    assert result.text == STR_CHOICE_OPTION
    assert result.reply_markup == keyboards.edit_union_data_kb()


@pytest.mark.asyncio
async def test_edit_club_menu(dispatcher: Dispatcher, bot: Bot):
    key = StorageKey(bot.id, TEST_CHAT.id, user_id=TEST_USER.id)
    bot_key = {'bot': bot, 'key': key}
    await dispatcher.storage.set_state(**bot_key, state=RouterStates.editing)
    message = get_message(STR_EDIT_CLUB)
    result: SendMessage = await dispatcher.feed_update(bot=bot, update=get_update(message))
    state = await dispatcher.storage.get_state(**bot_key)
    assert isinstance(result, SendMessage)
    assert state == RouterStates.show_editing_club
    assert result.text == STR_INSERT_CLUB_NUM
    assert result.reply_markup.remove_keyboard


@pytest.mark.asyncio
async def test_change_club_name(dispatcher: Dispatcher, bot: Bot):
    key = StorageKey(bot.id, TEST_CHAT.id, user_id=TEST_USER.id)
    bot_key = {'bot': bot, 'key': key}
    await dispatcher.storage.set_state(**bot_key, state=RouterStates.editing)
    message = get_message(STR_ADD_CLUB)
    result: SendMessage = await dispatcher.feed_update(bot=bot, update=get_update(message))
    state = await dispatcher.storage.get_state(**bot_key)
    assert isinstance(result, SendMessage)
    assert state == RouterStates.add_club
    assert result.text == STR_INSERT_NAME_COMISSION
    assert result.reply_markup.remove_keyboard


@pytest.mark.asyncio
async def test_show_club(dispatcher: Dispatcher, bot: Bot):
    key = StorageKey(bot.id, TEST_CHAT.id, user_id=TEST_USER.id)
    bot_key = {'bot': bot, 'key': key}
    unions = utils.get_all_unions(TEST_USER.id)
    test_data = {'unions': unions, 'selected_union': 1}
    test_union = test_data['unions'][test_data['selected_union']]
    test_clubs = test_union['clubs']
    test_club = test_clubs[0]
    await dispatcher.storage.set_state(**bot_key, state=RouterStates.show_editing_club)
    index = 0
    wrong_index = max(test_clubs) + 1
    await dispatcher.storage.set_data(**bot_key, data=test_data)
    message = get_message(str(wrong_index + 1))
    result: SendMessage = await dispatcher.feed_update(bot=bot, update=get_update(message))
    assert isinstance(result, SendMessage)
    assert result.text == STR_WRONG_NUM
    message = get_message(str(index + 1))
    result: SendMessage = await dispatcher.feed_update(bot=bot, update=get_update(message))
    data = await dispatcher.storage.get_data(**bot_key)
    state = await dispatcher.storage.get_state(**bot_key)
    out_message = STR_SHOW_CLUB % (test_club['name'], test_club['comission'])
    assert isinstance(result, SendMessage)
    assert result.text == out_message
    assert data['selected_club'] == index
    assert state == RouterStates.editing_club
    assert result.reply_markup == keyboards.edit_club_kb()























