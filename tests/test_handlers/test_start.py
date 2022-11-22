import pytest
from aiogram import Dispatcher, Bot

from aiogram.fsm.storage.base import StorageKey
from aiogram.methods import SendMessage
import db
import keyboards
import utils
from states import RouterStates
from tests.test_utils import TEST_USER, TEST_CHAT, get_message, get_update, wrong_answer_test
from strings import *
import routers
from utils import get_clubs_from_source, get_clubs_str, set_active_clubs
from random import choice


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


@pytest.mark.asyncio
async def test_delete_club(dispatcher: Dispatcher, bot: Bot):
    key = StorageKey(bot.id, TEST_CHAT.id, user_id=TEST_USER.id)
    bot_key = {'bot': bot, 'key': key}
    clubs = {0: {'name': 'TestClub1', 'comission': '1', 'participate': False},
             1: {'name': 'DeletingClub2', 'comission': '2', 'participate': False}}
    union = {'name': 'test_delete',
             'rebate': 1,
             'clubs': clubs
             }
    db.save_union(union, user_id=TEST_USER.id)
    unions = utils.get_all_unions(TEST_USER.id)
    index = max(unions)
    test_data = {'unions': unions, 'selected_union': index, 'selected_club': 1}
    message = get_message(STR_DELETE_CLUB)
    await dispatcher.storage.set_state(**bot_key, state=RouterStates.editing_club)
    await dispatcher.storage.set_data(**bot_key, data=test_data)
    result: SendMessage = await dispatcher.feed_update(bot=bot, update=get_update(message))
    assert isinstance(result, SendMessage)
    unions = utils.get_all_unions(TEST_USER.id)
    union = unions[index]
    assert not union['clubs'].get(1)
    assert result.text == utils.msg_union_info(union)


@pytest.mark.asyncio
async def test_change_club_name(dispatcher: Dispatcher, bot: Bot):
    key = StorageKey(bot.id, TEST_CHAT.id, user_id=TEST_USER.id)
    await dispatcher.storage.set_state(bot=bot, key=key, state=RouterStates.editing_club)
    message = get_message(STR_CHANGE_NAME)
    result: SendMessage = await dispatcher.feed_update(bot=bot, update=get_update(message))
    assert isinstance(result, SendMessage)
    assert result.text == STR_INSERT_NEW_NAME
    assert result.reply_markup.remove_keyboard


@pytest.mark.asyncio
async def test_add_club(dispatcher: Dispatcher, bot: Bot):
    key = StorageKey(bot.id, TEST_CHAT.id, user_id=TEST_USER.id)
    bot_key = {'bot': bot, 'key': key}
    unions = utils.get_all_unions(TEST_USER.id)
    test_union_index = 0
    test_data = {'unions': unions, 'selected_union': test_union_index}
    await dispatcher.storage.set_state(**bot_key, state=RouterStates.add_club)
    await dispatcher.storage.set_data(**bot_key, data=test_data)
    # send wrong data
    message = get_message('Test_club 12 3')
    result = await dispatcher.feed_update(bot=bot, update=get_update(message))
    assert isinstance(result, SendMessage)
    assert result.text == STR_WRONG_DATA
    # send proper data
    new_club_name = 'Test_club'
    new_club_comission = 12
    message = get_message(' '.join([new_club_name, str(new_club_comission)]))
    result = await dispatcher.feed_update(bot=bot, update=get_update(message))
    state_data = await dispatcher.storage.get_data(**bot_key)
    unions = state_data['unions']
    clubs = unions[test_union_index]['clubs']
    added_club = unions[test_union_index]['clubs'][max(clubs)]
    assert isinstance(result, SendMessage)
    assert result.reply_markup == keyboards.accept_union_data_kb()
    assert added_club['name'] == new_club_name
    assert added_club['comission'] == new_club_comission


@pytest.mark.asyncio
async def test_edit_club_name(dispatcher: Dispatcher, bot: Bot):
    key = StorageKey(bot.id, TEST_CHAT.id, user_id=TEST_USER.id)
    bot_key = {'bot': bot, 'key': key}
    await dispatcher.storage.set_state(**bot_key, state=RouterStates.editing_club_name)
    test_union_index = 0
    test_club_index = 0
    unions = utils.get_all_unions(TEST_USER.id)
    test_data = {'unions': unions, 'selected_union': test_union_index, 'selected_club': test_club_index}
    await dispatcher.storage.set_data(**bot_key, data=test_data)
    new_name = 'newname'
    message = get_message(new_name)
    result = await dispatcher.feed_update(bot=bot, update=get_update(message))
    state_data = await dispatcher.storage.get_data(**bot_key)
    state = await dispatcher.storage.get_state(**bot_key)
    club_in_state = state_data['unions'][test_union_index]['clubs'][test_club_index]
    club_in_db = utils.get_all_unions(TEST_USER.id)[test_union_index]['clubs'][test_club_index]
    assert isinstance(result, SendMessage)
    assert club_in_state['name'] == club_in_db['name'] == new_name
    assert state == RouterStates.accept_data
    assert result.text == utils.msg_union_info(state_data['unions'][test_union_index])
    assert result.reply_markup == keyboards.accept_union_data_kb()


@pytest.mark.asyncio
async def test_edit_union_name(dispatcher: Dispatcher, bot: Bot):
    key = StorageKey(bot.id, TEST_CHAT.id, user_id=TEST_USER.id)
    bot_key = {'bot': bot, 'key': key}
    await dispatcher.storage.set_state(**bot_key, state=RouterStates.editing_union)
    message = get_message(STR_NEW_NAME)
    result: SendMessage = await dispatcher.feed_update(bot=bot, update=get_update(message))
    state = await dispatcher.storage.get_state(**bot_key)
    assert isinstance(result, SendMessage)
    assert state == RouterStates.editing_union_name
    assert result.text == STR_INSERT_NEW_NAME
    assert result.reply_markup.remove_keyboard


@pytest.mark.asyncio
async def test_edit_union_rebate(dispatcher: Dispatcher, bot: Bot):
    key = StorageKey(bot.id, TEST_CHAT.id, user_id=TEST_USER.id)
    bot_key = {'bot': bot, 'key': key}
    await dispatcher.storage.set_state(**bot_key, state=RouterStates.editing_union)
    message = get_message(STR_NEW_REBATE)
    result: SendMessage = await dispatcher.feed_update(bot=bot, update=get_update(message))
    state = await dispatcher.storage.get_state(**bot_key)
    assert isinstance(result, SendMessage)
    assert state == RouterStates.editing_union_rebate
    assert result.text == STR_INSERT_NEW_REBATE
    assert result.reply_markup.remove_keyboard


@pytest.mark.asyncio
async def test_edit_union_rebate_set(dispatcher: Dispatcher, bot: Bot):
    key = StorageKey(bot.id, TEST_CHAT.id, user_id=TEST_USER.id)
    bot_key = {'bot': bot, 'key': key}
    await dispatcher.storage.set_state(**bot_key, state=RouterStates.editing_union_rebate)
    unions = utils.get_all_unions(TEST_USER.id)
    test_union_index = 1
    test_data = {'unions': unions, 'selected_union': test_union_index}
    await dispatcher.storage.set_data(**bot_key, data=test_data)
    new_rebate = 666
    message = get_message(str(new_rebate))
    result: SendMessage = await dispatcher.feed_update(bot=bot, update=get_update(message))
    state_union_rebate = (await dispatcher.storage.get_data(**bot_key))['unions'][test_union_index]['rebate']
    db_union_rebate = utils.get_all_unions(TEST_USER.id)[test_union_index]['rebate']
    state = await dispatcher.storage.get_state(**bot_key)
    assert isinstance(result, SendMessage)
    assert result.reply_markup == keyboards.accept_union_data_kb()
    assert new_rebate == db_union_rebate == state_union_rebate
    assert state == RouterStates.accept_data


@pytest.mark.asyncio
async def test_edit_union_name_set(dispatcher: Dispatcher, bot: Bot):
    key = StorageKey(bot.id, TEST_CHAT.id, user_id=TEST_USER.id)
    bot_key = {'bot': bot, 'key': key}
    await dispatcher.storage.set_state(**bot_key, state=RouterStates.editing_union_name)
    unions = utils.get_all_unions(TEST_USER.id)
    test_union_index = 1
    test_data = {'unions': unions, 'selected_union': test_union_index}
    await dispatcher.storage.set_data(**bot_key, data=test_data)
    new_name = 'new_name'
    message = get_message(new_name)
    result: SendMessage = await dispatcher.feed_update(bot=bot, update=get_update(message))
    state_union_name = (await dispatcher.storage.get_data(**bot_key))['unions'][test_union_index]['name']
    db_union_name = utils.get_all_unions(TEST_USER.id)[test_union_index]['name']
    state = await dispatcher.storage.get_state(**bot_key)
    assert isinstance(result, SendMessage)
    assert result.reply_markup == keyboards.accept_union_data_kb()
    assert new_name == db_union_name == state_union_name
    assert state == RouterStates.accept_data


@pytest.mark.asyncio
async def test_edit_wrong_answer(dispatcher: Dispatcher, bot: Bot):
    await wrong_answer_test(RouterStates.editing, dispatcher=dispatcher, bot=bot)


@pytest.mark.asyncio
async def test_edit_union_wrong_answer(dispatcher: Dispatcher, bot: Bot):
    await wrong_answer_test(RouterStates.editing_union, dispatcher=dispatcher, bot=bot)
