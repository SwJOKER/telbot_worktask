from aiogram.fsm.state import StatesGroup, State
from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardRemove
import keyboards
from aiogram.types.document import Document

router = Router()
sessions = {}


class RouterStates(StatesGroup):
    new_union = State()
    accept_data = State()
    editing = State()
    editing_union = State()
    editing_union_name = State()
    editing_union_rebate = State()
    editing_union_add_club = State()
    editing_club = State()


@router.message(Command(commands=['start']))
async def cmd_start(message: types.Message, state: FSMContext):
    if not sessions.get(message.from_user.id):
        sessions[message.from_user.id] = {'current': 0, 'unions': []}
    sessions[message.from_user.id]['current'] = len(sessions[message.from_user.id]['unions'])
    await message.answer(
        'Регистрация, выберите опцию', reply_markup=keyboards.union_options_kb()
    )
    await state.set_state(RouterStates.new_union)


def text_to_clubs(msg: str):
    res = {}
    lines = msg.split('\n')
    for num, line in enumerate(lines):
        name, percent = line.strip().split(' ')
        res[num] = {'name': name, 'percent': percent, 'participate': False, 'id': num}
    return res


async def get_clubs_from_msg(message: types.Message):
    session = get_session_union(message.from_user.id)
    if message.document:
        clubs = await parse_doc(message.document)
    else:
        clubs = text_to_clubs(message.text)
    session['clubs'] = clubs


def get_clubs_str(message: types.Message):
    """Получить список клубов в текстовом формате для сообщения"""
    session = get_session_union(message.from_user.id)
    clubs_txt = ''
    for club in session['clubs']:
        clubs_txt += f'{club + 1}. {session["clubs"][club]["name"]}\n'
    return clubs_txt


def parse_excel(file):
    pass


def parse_csv(file):
    pass


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


def get_union_by_id(user_id, union_id):
    try:
        session = sessions[user_id]['unions'][union_id]
    except IndexError:
        pass


def get_session_union(user_id):
    index = sessions[user_id]['current']
    try:
        union = sessions[user_id]['unions'][index]
    except IndexError:
        sessions[user_id]['unions'].append({})
        union = sessions[user_id]['unions'][index]
    return union


def get_selected_clubs(message):
    indexes = message.text.split(' ')
    union = get_session_union(message.from_user.id)
    clubs = union.get('clubs')
    selected_clubs = []
    for index in indexes:
        raw_index = int(index) - 1
        club = clubs[raw_index]
        # club['id'] = raw_index
        club['participate'] = True
        selected_clubs.append(club)
    return selected_clubs


@router.message(RouterStates.new_union)
async def new_union(message: types.Message, state: FSMContext):
    union = get_session_union(message.from_user.id)
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
        await get_clubs_from_msg(message)
        clubs_txt = get_clubs_str(message)
        await message.answer(f'Выберете список клубов, которые участвуют в дп.\n'
                             f'Введите номера через пробел\n'
                             f'{clubs_txt}')
        return
    clubs = union.get('clubs')
    if not any(clubs[x]['participate'] for x in clubs):
        selected_clubs = get_selected_clubs(message)
        clubs_str = "\n".join([f"{int(x['id']) + 1}. {x['name']}" for x in selected_clubs])
        data = f'Проверьте данные\n' \
               f'Имя союза: {union["name"]}\n' \
               f'Ребейт: {union["rebate"]}\n' \
               f'Клубы участвующие в дп:\n'
        data += clubs_str
        await message.answer(data, reply_markup=keyboards.accept_union_data_kb())
        await state.set_state(RouterStates.accept_data)



def get_unions_list(message):
    user = sessions[message.from_user.id]
    msg = 'Список союзов:\n'
    for union in user['unions']:
        msg += f"Name: {union['name']}. Rebate: {union['rebate']}.\n"
    return msg


@router.message(RouterStates.accept_data, lambda message: message.text == 'Верно')
async def accept_data(message: types.Message, state: FSMContext):
    await message.answer(get_unions_list(message))
    await state.clear()

def current_union_msg(message):
    union = get_session_union(message.from_user.id)
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



@router.message(RouterStates.editing_union, lambda message: message.text == 'Новое имя')
async def edit_union_name(message: types.Message, state: FSMContext):
    await message.answer('Напишите новое имя', reply_markup=keyboards.edit_union_data_kb())

@router.message(RouterStates.editing_union)
async def edit_union(message: types.Message, state: FSMContext):
    new_name = message.text
    union = get_session_union(message.from_user.id)
    union['name'] = new_name
    await message.answer(current_union_msg(message), reply_markup=keyboards.accept_union_data_kb())
    await state.set_state(RouterStates.accept_data)









# @router.message(RouterStates.editing_data, lambda message: message.text == 'Редактировать клуб')
# async def edit_club(message: types.Message, state: FSMContext):
#     await state.set_state(RouterStates.editing_club)
#
# @router.message(RouterStates.editing_data, lambda message: message.text == 'Добавить клуб')
# async def add_club(message: types.Message, state: FSMContext):
#     await state.set_state(RouterStates.add_club)
#
#
#
# @router.message(RouterStates.editing_union)
# async def edit_union(message: types.Message, state: FSMContext):
#     await message.answer('Выберите опцию', reply_markup=keyboards.edit_union_data_kb())
#
#
#
# @router.message(RouterStates.editing_club)
# async def edit_union(message: types.Message, state: FSMContext):
#     pass
#
# @router.message(RouterStates.add_club)
# async def edit_union(message: types.Message, state: FSMContext):
#    pass