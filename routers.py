import logging
import keyboards
import utils
from states import RouterStates
from utils import get_unions_info, get_current_union, get_clubs_str, get_clubs_from_source
from strings import *
import db


from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardRemove
from aiogram.types import FSInputFile


router = Router()
sessions = {}
utils.router = router
utils.sessions = sessions


@router.message(Command(commands=['start']))
async def cmd_start(message: types.Message, state: FSMContext):
    if not sessions.get(message.from_user.id):
        sessions[message.from_user.id] = {'unions': {}}
    await message.answer(
        STR_WELCOME, reply_markup=keyboards.union_options_kb()
    )
    await state.set_state(RouterStates.new_union)


@router.message(Command(commands=['list']))
async def cmd_list(message: types.Message, state: FSMContext):
    if not sessions.get(message.from_user.id) or len(sessions[message.from_user.id]['unions']) < 1:
        await message.answer(STR_NULL_DATA)
        return
    msg = get_unions_info(message) + '\n'
    msg += STR_INSERT_UNION_NUM
    await message.answer(msg, reply_markup=ReplyKeyboardRemove)
    await state.set_state(RouterStates.show_union)


@router.message(RouterStates.new_union)
async def new_union(message: types.Message, state: FSMContext):
    try:
        union = get_current_union(message.from_user.id)
    except KeyError:
        union = utils.make_new_union(message.from_user.id)
    if union.get('finished'):
        union = utils.make_new_union(message.from_user.id)
    if message.text == STR_MAKE_UNION:
        await message.answer(STR_INSERT_TITLE, reply_markup=ReplyKeyboardRemove)
        return
    if not union.get('name'):
        union['name'] = message.text
        await message.answer(STR_INSERT_REBATE)
        return
    if not union.get('rebate'):
        union['rebate'] = message.text
        await message.answer(STR_LIST_OR_EXCEL)
        return
    if not union.get('clubs'):
        await get_clubs_from_source(message)
        clubs_txt = get_clubs_str(message)
        await message.answer(STR_CHOICE_DP_CLUBS % clubs_txt)
        return
    clubs = union.get('clubs')
    if not any(clubs[x]['participate'] for x in clubs):
        data = STR_CHECK_DATA % (union["name"], union["rebate"])
        utils.set_active_clubs(message)
        data += get_clubs_str(message)
        union['finished'] = True
        await message.answer(data, reply_markup=keyboards.accept_union_data_kb())
        await state.set_state(RouterStates.accept_data)


@router.message(RouterStates.accept_data, lambda message: message.text == STR_TRUE)
async def accept_data(message: types.Message, state: FSMContext):
    msg = get_unions_info(message) + '\n'
    msg += STR_INSERT_UNION_NUM
    await message.answer(msg, reply_markup=ReplyKeyboardRemove)
    await state.set_state(RouterStates.show_union)


@router.message(RouterStates.show_union, lambda message: message.text.isdigit())
async def accept_data(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    index = int(message.text) - 1
    if index in sessions[user_id]['unions']:
        sessions[user_id]['current'] = index
    else:
        await message.answer(STR_WRONG_NUM)
        return
    get_current_union(user_id)
    msg = msg_union_info(message)
    await message.answer(msg, reply_markup=keyboards.work_data_kb())
    await state.set_state(RouterStates.editing)


def msg_union_info(message):
    union = get_current_union(message.from_user.id)
    clubs_str = get_clubs_str(message)
    msg = f'Союз:\n' \
          f'{union["name"]}\n' \
          f'Ребейт: {union["rebate"]}\n' \
          f'Клубы:\n' \
          f'{clubs_str}'
    return msg


@router.message(RouterStates.accept_data, lambda message: message.text == STR_EDIT)
async def accept_data(message: types.Message, state: FSMContext):
    msg = msg_union_info(message)
    await message.answer(msg, reply_markup=keyboards.edit_data_kb())
    await state.set_state(RouterStates.editing)


@router.message(RouterStates.editing, lambda message: message.text == STR_EDIT_UNION)
async def edit_data(message: types.Message, state: FSMContext):
    await message.answer(STR_CHOICE_OPTION, reply_markup=keyboards.edit_union_data_kb())
    await state.set_state(RouterStates.editing_union)


@router.message(RouterStates.editing, lambda message: message.text == STR_EDIT_CLUB)
async def edit_data(message: types.Message, state: FSMContext):
    await message.answer(STR_INSERT_CLUB_NUM, reply_markup=ReplyKeyboardRemove)
    await state.set_state(RouterStates.show_editing_club)


@router.message(RouterStates.editing, lambda message: message.text == STR_ADD_CLUB)
async def change_club_name(message: types.Message, state: FSMContext):
    await message.answer(STR_INSERT_NAME_COMISSION, reply_markup=ReplyKeyboardRemove)
    await state.set_state(RouterStates.add_club)


@router.message(RouterStates.editing, lambda message: message.text == STR_COUNT)
async def count(message: types.Message, state: FSMContext):
    agenda = FSInputFile("1.xlsx", filename="result.xlsx")
    await message.answer_document(agenda)
    msg = get_unions_info(message) + '\n'
    msg += STR_INSERT_UNION_NUM
    await message.answer(msg, reply_markup=ReplyKeyboardRemove)
    await state.set_state(RouterStates.show_union)


@router.message(RouterStates.show_editing_club, lambda message: message.text.strip().isdigit())
async def show_club(message: types.Message, state: FSMContext):
    club_num = int(message.text) - 1
    if club_num not in sessions[message.from_user.id]['unions']:
        await message.answer(STR_WRONG_NUM)
        return
    current_union_id = sessions[message.from_user.id]['current']
    union = sessions[message.from_user.id]['unions'][current_union_id]
    union['edit_club'] = club_num
    club = union['clubs'][club_num]
    answer = f'{club["name"]} {club["percent"]}'
    await message.answer(answer, reply_markup=keyboards.edit_club_kb())
    await state.set_state(RouterStates.editing_club)


@router.message(RouterStates.editing_club, lambda message: message.text == STR_DELETE_CLUB)
async def delete_club(message: types.Message, state: FSMContext):
    current_union_id = sessions[message.from_user.id]['current']
    union = sessions[message.from_user.id]['unions'][current_union_id]
    club_id = union.get('edit_club', -1)
    if club_id != -1:
        del(union['clubs'][club_id])
        del(union['edit_club'])
    await message.answer(msg_union_info(message), reply_markup=keyboards.accept_union_data_kb())
    await state.set_state(RouterStates.accept_data)


@router.message(RouterStates.editing_club, lambda message: message.text == STR_CHANGE_NAME)
async def change_club_name(message: types.Message, state: FSMContext):
    await message.answer(STR_INSERT_NEW_NAME, reply_markup=ReplyKeyboardRemove)
    await state.set_state(RouterStates.editing_club_name)


@router.message(RouterStates.add_club)
async def change_club_name(message: types.Message, state: FSMContext):
    splitted = message.text.split()
    if len(splitted) != 2:
        await message.answer('Данные не корректны, попробуйте еще раз')
        return
    session = sessions[message.from_user.id]
    current_union_id = session['current']
    union = session['unions'][current_union_id]
    new_index = max(union['clubs']) + 1
    union['clubs'][new_index] = {}
    union['clubs'][new_index]['name'], union['clubs'][new_index]['percent'] = splitted[0], splitted[1]
    union['clubs'][new_index]['participate'] = True
    await message.answer(msg_union_info(message), reply_markup=keyboards.accept_union_data_kb())
    await state.set_state(RouterStates.accept_data)


@router.message(RouterStates.editing_club_name)
async def delete_club(message: types.Message, state: FSMContext):
    current_union_id = sessions[message.from_user.id]['current']
    union = sessions[message.from_user.id]['unions'][current_union_id]
    print(union.get('edit_club'))
    club_id = union.get('edit_club', -1)
    if club_id != -1:
        union['clubs'][club_id]['name'] = message.text
        del(union['edit_club'])
    else:
        logging.getLogger().error('Ошибка измненеия имени клуба. Нет метки union["edit_club"]')
    await message.answer(msg_union_info(message), reply_markup=keyboards.accept_union_data_kb())
    await state.set_state(RouterStates.accept_data)

@router.message(RouterStates.editing_union, lambda message: message.text == STR_NEW_NAME)
async def edit_union_name(message: types.Message, state: FSMContext):
    await message.answer(STR_INSERT_NEW_NAME, reply_markup=keyboards.edit_union_data_kb())
    await state.set_state(RouterStates.editing_union_name)


@router.message(RouterStates.editing_union, lambda message: message.text == STR_NEW_REBATE)
async def edit_union_rebate(message: types.Message, state: FSMContext):
    await message.answer(STR_INSERT_NEW_REBATE, reply_markup=keyboards.edit_union_data_kb())
    await state.set_state(RouterStates.editing_union_rebate)


@router.message(RouterStates.editing_union_rebate)
async def edit_union_rebate_set(message: types.Message, state: FSMContext):
    new_rebate = message.text
    union = get_current_union(message.from_user.id)
    union['rebate'] = new_rebate
    await message.answer(msg_union_info(message), reply_markup=keyboards.accept_union_data_kb())
    await state.set_state(RouterStates.accept_data)


@router.message(RouterStates.editing_union_name)
async def edit_union(message: types.Message, state: FSMContext):
    new_name = message.text
    union = get_current_union(message.from_user.id)
    union['name'] = new_name
    await message.answer(msg_union_info(message), reply_markup=keyboards.accept_union_data_kb())
    await state.set_state(RouterStates.accept_data)
