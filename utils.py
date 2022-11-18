import logging
import os
from aiogram import types
from aiogram.types.document import Document
from typing import Dict, List

sessions = None
router = None

def text_to_clubs_dict(msg: str) -> Dict:
    res = {}
    lines = msg.split('\n')
    for num, line in enumerate(lines):
        name, percent = line.strip().split(' ')
        res[num] = {'name': name, 'comission': percent, 'participate': False}
    return res


def get_union_by_id(message: types.Message , union_id: int) -> Dict:
    try:
        union = sessions[message.from_user.id]['unions'][union_id]
    except KeyError:
        logging.getLogger().error(f'Указанного союза нет в словаре сессии. Index:{union_id}')
        union = None
    return union



def get_clubs_str(clubs: Dict) -> str:
    """Получить список клубов текущего союза в текстовом формате для сообщения"""
    clubs_txt = ''
    for club in clubs:
        if clubs[club]['participate']:
            mark = '🟢'
        else:
            mark = '🔵'
        clubs_txt += f'{mark}{club + 1}. {clubs[club]["name"]}\n'
    return clubs_txt


async def get_clubs_from_source(message: types.Message) -> Dict:
    if message.document:
        clubs = await parse_doc(message.document)
    else:
        clubs = text_to_clubs_dict(message.text)
    return clubs


def parse_excel(file):
    pass


def parse_csv(file):
    pass


async def parse_doc(document: Document) -> Dict:
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
        os.remove(file_path)
        return res


def get_current_union(user_id) -> Dict:
    union = None
    index = sessions[user_id]['current']
    union = sessions[user_id]['unions'][index]
    return union


def make_new_union(user_id) -> Dict:
    index = sessions[user_id].get('current', -1)
    if index != -1:
        index = max(sessions[user_id]['unions']) + 1
        sessions[user_id]['current'] = index
    else:
        index = 0
        sessions[user_id]['current'] = index
    sessions[user_id]['unions'][index] = {}
    union = sessions[user_id]['unions'][index]
    return union


def set_active_clubs(clubs: Dict, indexes: List[str]) -> None:
    """Установить флаг участия в dp"""
    for index in indexes:
        raw_index = int(index) - 1
        club = clubs[raw_index]
        club['participate'] = True



def get_unions_info(message) -> Dict:
    session = sessions[message.from_user.id]
    unions = session['unions']
    msg = '<b>Список союзов:</b>\n'
    for union_id in sorted(unions):
        union = unions[union_id]
        msg += f"{union_id + 1} {union['name']} Ребейт: {union['rebate']}.\n"
    return msg
