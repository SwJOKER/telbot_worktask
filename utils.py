import logging

from aiogram import types
from aiogram.types.document import Document

sessions = None
router = None

def text_to_clubs_dict(msg: str):
    res = {}
    lines = msg.split('\n')
    for num, line in enumerate(lines):
        name, percent = line.strip().split(' ')
        res[num] = {'name': name, 'percent': percent, 'participate': False}
    return res


def get_union_by_id(message: types.Message , union_id: int):
    try:
        union = sessions[message.from_user.id]['unions'][union_id]
    except KeyError:
        logging.getLogger().error(f'Указанного союза нет в словаре сессии. Index:{union_id}')
        union = None
    return union



def get_clubs_str(message: types.Message, union_id = None):
    """Получить список клубов текущего союза в текстовом формате для сообщения"""
    if not union_id:
        union = get_current_union(message.from_user.id)
    clubs_txt = ''
    for club in union['clubs']:
        if union["clubs"][club]['participate']:
            mark = '🟢'
        else:
            mark = '🔵'
        clubs_txt += f'{mark}{club + 1}. {union["clubs"][club]["name"]}\n'
    return clubs_txt


async def get_clubs_from_source(message: types.Message):
    session = get_current_union(message.from_user.id)
    if message.document:
        print(message.document)
        clubs = await parse_doc(message.document)
    else:
        clubs = text_to_clubs_dict(message.text)
    session['clubs'] = clubs


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


def get_current_union(user_id):
    union = None
    index = sessions[user_id]['current']
    union = sessions[user_id]['unions'][index]
    return union


def make_new_union(user_id):
    index = sessions[user_id].get('current', -1)
    if index != -1:
        index += 1
        sessions[user_id]['current'] = index
    else:
        index = 0
        sessions[user_id]['current'] = index
    sessions[user_id]['unions'][index] = {}
    union = sessions[user_id]['unions'][index]
    return union


def get_active_clubs(message):
    """Получить клубы участвующие в 'дп'"""
    indexes = message.text.split(' ')
    union = get_current_union(message.from_user.id)
    clubs = union.get('clubs')
    selected_clubs = {}
    for index in indexes:
        raw_index = int(index) - 1
        club = clubs[raw_index]
        club['participate'] = True
        selected_clubs[raw_index] = club
    return selected_clubs


def get_unions_list(message):
    session = sessions[message.from_user.id]
    unions = session['unions']
    msg = '<b>Список союзов:</b>\n'
    for union_id in sorted(unions):
        union = unions[union_id]
        msg += f"{union_id + 1}. <b>{union['name']}</b> Ребейт: {union['rebate']}.\n"
    return msg
