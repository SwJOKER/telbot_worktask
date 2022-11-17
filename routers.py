import utils
from states import RouterStates
from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardRemove
from aiogram.types.document import Document
import keyboards
from utils import get_unions_list, get_current_union, get_clubs_str, get_clubs_from_source, \
    get_active_clubs, parse_excel, parse_csv



router = Router()
sessions = {}
utils.router = router
utils.sessions = sessions

async def parse_doc(document: Document):
    formats = ['csv', 'xls', 'xlsx']
    format = document.file_name.split('.')[-1]
    if format in formats:
        file = await router.bot.get_file(document.file_id)
        srv_file_path = file.file_path
        file_path = '1.xls'
        await router.bot.download_file(srv_file_path, file_path)
        if format in ['xls', 'xlsx']:
            res = parse_excel(file_path)
        else:
            res = parse_csv
        return res



@router.message(Command(commands=['start']))
async def cmd_start(message: types.Message, state: FSMContext):
    if not sessions.get(message.from_user.id):
        sessions[message.from_user.id] = {'current': 0, 'unions': {}}
    sessions[message.from_user.id]['current'] = len(sessions[message.from_user.id]['unions'])
    await message.answer(
        'Регистрация, выберите опцию', reply_markup=keyboards.union_options_kb()
    )
    await state.set_state(RouterStates.new_union)


@router.message(RouterStates.new_union)
async def new_union(message: types.Message, state: FSMContext):
    union = get_current_union(message.from_user.id)
    if message.text == 'Создать союз':
        await message.answer('Введите название', reply_markup=ReplyKeyboardRemove)
        return
    if not union.get('name'):
        union['name'] = message.text
        await message.answer('Введите ребейт')
        return
    if not union.get('rebate'):
        union['rebate'] = message.text
        await message.answer('Напишите список клубов или отправьте файл excel')
        return
    if not union.get('clubs'):
        await get_clubs_from_source(message)
        clubs_txt = get_clubs_str(message)
        await message.answer(f'Выберете список клубов, которые участвуют в дп.\n'
                             f'Введите номера через пробел\n'
                             f'{clubs_txt}')
        return
    clubs = union.get('clubs')
    if not any(clubs[x]['participate'] for x in clubs):
        selected_clubs = get_active_clubs(message)
        clubs_str = "\n".join([f"{int(x) + 1}. {selected_clubs[x]['name']}" for x in selected_clubs])
        data = f'Проверьте данные\n' \
               f'Имя союза: {union["name"]}\n' \
               f'Ребейт: {union["rebate"]}\n' \
               f'Клубы участвующие в дп:\n'
        data += clubs_str
        await message.answer(data, reply_markup=keyboards.accept_union_data_kb())
        await state.set_state(RouterStates.accept_data)


@router.message(RouterStates.accept_data, lambda message: message.text == 'Верно')
async def accept_data(message: types.Message, state: FSMContext):
    await message.answer(get_unions_list(message))
    await state.clear()


def current_union_msg(message):
    union = get_current_union(message.from_user.id)
    clubs_str = get_clubs_str(message)
    msg = f'Союз:\n' \
          f'{union["name"]}\n' \
          f'Ребейт: {union["rebate"]}\n' \
          f'Клубы:\n' \
          f'{clubs_str}'
    return msg


@router.message(RouterStates.accept_data, lambda message: message.text == 'Редактировать')
async def accept_data(message: types.Message, state: FSMContext):
    msg = current_union_msg(message)
    await message.answer(msg, reply_markup=keyboards.edit_data_kb())
    await state.set_state(RouterStates.editing)


@router.message(RouterStates.editing, lambda message: message.text == 'Редактировать союз')
async def edit_data(message: types.Message, state: FSMContext):
    await message.answer('Выберите опцию', reply_markup=keyboards.edit_union_data_kb())
    await state.set_state(RouterStates.editing_union)


@router.message(RouterStates.editing, lambda message: message.text == 'Редактировать клуб')
async def edit_data(message: types.Message, state: FSMContext):
    await message.answer('Введите номер клуба для редактирования', reply_markup=ReplyKeyboardRemove)
    await state.set_state(RouterStates.show_editing_club)


@router.message(RouterStates.show_editing_club, lambda message: message.text.strip().isdigit())
async def show_club(message: types.Message, state: FSMContext):
    club_num = int(message.text)
    union = sessions[message.from_user.id]['unions'][sessions[message.from_user.id]['current']]
    club = union['clubs'][club_num - 1]
    answer = f'{club["name"]} {club["percent"]}'
    await message.answer(answer, reply_markup=keyboards.edit_club_kb())
    await state.set_state(RouterStates.editing_club)


@router.message(RouterStates.editing_union, lambda message: message.text == 'Новое имя')
async def edit_union_name(message: types.Message, state: FSMContext):
    await message.answer('Напишите новое имя', reply_markup=keyboards.edit_union_data_kb())
    await state.set_state(RouterStates.editing_union_name)


@router.message(RouterStates.editing_union, lambda message: message.text == 'Новый ребейт')
async def edit_union_rebate(message: types.Message, state: FSMContext):
    await message.answer('Напишите новый ребейт', reply_markup=keyboards.edit_union_data_kb())
    await state.set_state(RouterStates.editing_union_rebate)


@router.message(RouterStates.editing_union_rebate)
async def edit_union_set_rebate(message: types.Message, state: FSMContext):
    new_rebate = message.text
    union = get_current_union(message.from_user.id)
    union['rebate'] = new_rebate
    await message.answer(current_union_msg(message), reply_markup=keyboards.accept_union_data_kb())
    await state.set_state(RouterStates.accept_data)


@router.message(RouterStates.editing_union_name)
async def edit_union(message: types.Message, state: FSMContext):
    new_name = message.text
    union = get_current_union(message.from_user.id)
    union['name'] = new_name
    await message.answer(current_union_msg(message), reply_markup=keyboards.accept_union_data_kb())
    await state.set_state(RouterStates.accept_data)
