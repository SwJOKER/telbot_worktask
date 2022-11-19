import keyboards
import utils
from states import RouterStates
from utils import get_unions_info, get_clubs_str, \
    get_clubs_from_source, msg_union_info, get_all_unions, get_selected_union, get_selected_club
from strings import *
import db

from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardRemove
from aiogram.types import FSInputFile

router = Router()
utils.router = router
db.check_db_exists()


@router.message(Command(commands=['start']))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    if not db.get_user(user_id):
        db.insert('users', {'id': user_id})
    await message.answer(
        STR_WELCOME, reply_markup=keyboards.union_options_kb()
    )
    await state.set_state(RouterStates.new_union)


@router.message(Command(commands=['list']))
async def cmd_list(message: types.Message, state: FSMContext):
    await state.clear()
    unions = utils.get_all_unions(message.from_user.id)
    msg = get_unions_info(unions) + '\n'
    msg += STR_INSERT_UNION_NUM
    await state.update_data(unions=unions)
    await message.answer(msg, reply_markup=ReplyKeyboardRemove())
    await state.set_state(RouterStates.show_union)


@router.message(RouterStates.new_union)
async def new_union(message: types.Message, state: FSMContext):
    data = await state.get_data()
    if message.text == STR_MAKE_UNION:
        await message.answer(STR_INSERT_TITLE, reply_markup=ReplyKeyboardRemove())
        return
    if not data.get('name'):
        await state.update_data(name=message.text)
        await message.answer(STR_INSERT_REBATE)
        return
    if not data.get('rebate'):
        await state.update_data(rebate=message.text)
        await message.answer(STR_LIST_OR_EXCEL)
        return
    if not data.get('clubs'):
        clubs = await get_clubs_from_source(message)
        clubs_txt = get_clubs_str(clubs)
        await state.update_data(clubs=clubs)
        await message.answer(STR_CHOICE_DP_CLUBS % clubs_txt)
        return
    clubs = data.get('clubs')
    if not any(clubs[x]['participate'] for x in clubs):
        info = STR_CHECK_DATA % (data["name"], data["rebate"])
        active_indexes = message.text.split(' ')
        utils.set_active_clubs(clubs, active_indexes)
        info += get_clubs_str(clubs)
        db.save_union(data, message.from_user.id)
        await message.answer(info, reply_markup=keyboards.accept_union_data_kb())
        await state.set_state(RouterStates.accept_data)


@router.message(RouterStates.accept_data, lambda message: message.text == STR_TRUE)
async def accept_data(message: types.Message, state: FSMContext):
    await state.clear()
    unions = utils.get_all_unions(message.from_user.id)
    msg = get_unions_info(unions) + '\n'
    msg += STR_INSERT_UNION_NUM
    await state.update_data(unions=unions)
    await message.answer(msg, reply_markup=ReplyKeyboardRemove())
    await state.set_state(RouterStates.show_union)


@router.message(RouterStates.show_union, lambda message: message.text.isdigit())
async def show_union_data(message: types.Message, state: FSMContext):
    index = int(message.text) - 1
    data = await state.get_data()
    unions = data['unions']
    if index in unions:
        await state.update_data(selected_union=index)
    else:
        await message.answer(STR_WRONG_NUM)
        return
    msg = msg_union_info(unions[index])
    await message.answer(msg, reply_markup=keyboards.work_data_kb())
    await state.set_state(RouterStates.editing)


@router.message(RouterStates.accept_data, lambda message: message.text == STR_EDIT)
async def edit_data(message: types.Message, state: FSMContext):
    union = await get_selected_union(state)
    msg = msg_union_info(union)
    await message.answer(msg, reply_markup=keyboards.edit_data_kb())
    await state.set_state(RouterStates.editing)


@router.message(RouterStates.editing, lambda message: message.text == STR_EDIT_UNION)
async def edit_data(message: types.Message, state: FSMContext):
    await message.answer(STR_CHOICE_OPTION, reply_markup=keyboards.edit_union_data_kb())
    await state.set_state(RouterStates.editing_union)


@router.message(RouterStates.editing, lambda message: message.text == STR_EDIT_CLUB)
async def edit_data(message: types.Message, state: FSMContext):
    await message.answer(STR_INSERT_CLUB_NUM, reply_markup=ReplyKeyboardRemove())
    await state.set_state(RouterStates.show_editing_club)


@router.message(RouterStates.editing, lambda message: message.text == STR_ADD_CLUB)
async def change_club_name(message: types.Message, state: FSMContext):
    await message.answer(STR_INSERT_NAME_COMISSION, reply_markup=ReplyKeyboardRemove())
    await state.set_state(RouterStates.add_club)


@router.message(RouterStates.editing, lambda message: message.text == STR_COUNT)
async def send_file(message: types.Message, state: FSMContext):
    agenda = FSInputFile("1.xlsx", filename="result.xlsx")
    await message.answer_document(agenda)
    data = await state.get_data()
    msg = get_unions_info(data['unions']) + '\n'
    msg += STR_INSERT_UNION_NUM
    await message.answer(msg, reply_markup=ReplyKeyboardRemove())
    await state.set_state(RouterStates.show_union)


@router.message(RouterStates.show_editing_club, lambda message: message.text.strip().isdigit())
async def show_club(message: types.Message, state: FSMContext):
    club_index = int(message.text) - 1
    union = await get_selected_union(state)
    clubs = union['clubs']
    if club_index not in clubs:
        await message.answer(STR_WRONG_NUM)
        return
    await state.update_data(selected_club=club_index)
    club = clubs[club_index]
    answer = STR_SHOW_CLUB % (club['name'], club['comission'])
    await message.answer(answer, reply_markup=keyboards.edit_club_kb())
    await state.set_state(RouterStates.editing_club)


@router.message(RouterStates.editing_club, lambda message: message.text == STR_DELETE_CLUB)
async def delete_club(message: types.Message, state: FSMContext):
    club = await get_selected_club(state)
    db.delete('clubs', club['id'])
    await state.update_data(unions=get_all_unions(message.from_user.id))
    updated_union = await get_selected_union(state)
    await message.answer(msg_union_info(updated_union), reply_markup=keyboards.accept_union_data_kb())
    await state.set_state(RouterStates.accept_data)


@router.message(RouterStates.editing_club, lambda message: message.text == STR_CHANGE_NAME)
async def change_club_name(message: types.Message, state: FSMContext):
    await message.answer(STR_INSERT_NEW_NAME, reply_markup=ReplyKeyboardRemove())
    await state.set_state(RouterStates.editing_club_name)


@router.message(RouterStates.add_club)
async def add_club(message: types.Message, state: FSMContext):
    union = await get_selected_union(state)
    splitted = message.text.split()
    if len(splitted) != 2:
        await message.answer('Данные не корректны, попробуйте еще раз')
        return
    club = {
        'name': splitted[0],
        'comission': splitted[1],
        'participate': True,
        'union_id': union['id']
    }
    db.insert('clubs', club)
    await state.update_data(unions=get_all_unions(message.from_user.id))
    updated_union = await get_selected_union(state)
    await message.answer(msg_union_info(updated_union), reply_markup=keyboards.accept_union_data_kb())
    await state.set_state(RouterStates.accept_data)


@router.message(RouterStates.editing_club_name)
async def edit_club_name(message: types.Message, state: FSMContext):
    club = await get_selected_club(state)
    db.update(table='clubs', id=club['id'], column='name', value=message.text)
    await state.update_data(unions=get_all_unions(message.from_user.id))
    updated_union = await get_selected_union(state)
    await message.answer(msg_union_info(updated_union), reply_markup=keyboards.accept_union_data_kb())
    await state.set_state(RouterStates.accept_data)


@router.message(RouterStates.editing_union, lambda message: message.text == STR_NEW_NAME)
async def edit_union_name(message: types.Message, state: FSMContext):
    await message.answer(STR_INSERT_NEW_NAME, reply_markup=ReplyKeyboardRemove())
    await state.set_state(RouterStates.editing_union_name)


@router.message(RouterStates.editing_union, lambda message: message.text == STR_NEW_REBATE)
async def edit_union_rebate(message: types.Message, state: FSMContext):
    await message.answer(STR_INSERT_NEW_REBATE, reply_markup=ReplyKeyboardRemove())
    await state.set_state(RouterStates.editing_union_rebate)


@router.message(RouterStates.editing_union_rebate)
async def edit_union_rebate_set(message: types.Message, state: FSMContext):
    union = await get_selected_union(state)
    db.update(table='unions', id=union['id'], column='rebate', value=message.text)
    await state.update_data(unions=get_all_unions(message.from_user.id))
    updated_union = await get_selected_union(state)
    await message.answer(msg_union_info(updated_union), reply_markup=keyboards.accept_union_data_kb())
    await state.set_state(RouterStates.accept_data)


@router.message(RouterStates.editing_union_name)
async def edit_union_name(message: types.Message, state: FSMContext):
    union = await get_selected_union(state)
    db.update(table='unions', id=union['id'], column='name', value=message.text)
    await state.update_data(unions=get_all_unions(message.from_user.id))
    updated_union = await get_selected_union(state)
    await message.answer(msg_union_info(updated_union), reply_markup=keyboards.accept_union_data_kb())
    await state.set_state(RouterStates.accept_data)


@router.message(RouterStates.editing)
async def edit_data(message: types.Message):
    await message.answer(STR_CHOOSE_PROPER_ANSWER, reply_markup=keyboards.edit_union_data_kb())


@router.message(RouterStates.editing_union)
async def edit_data(message: types.Message):
    await message.answer(STR_CHOOSE_PROPER_ANSWER, reply_markup=keyboards.edit_union_data_kb())
