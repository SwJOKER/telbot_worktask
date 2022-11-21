import os
from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.types.document import Document
from typing import Dict, List
from db import get_unions_clubs, get_users_unions


router = None


def text_to_clubs_dict(msg: str) -> Dict:
    res = {}
    lines = msg.split('\n')
    for num, line in enumerate(lines):
        name, percent = line.strip().split(' ')
        res[num] = {'name': name, 'comission': percent, 'participate': False}
    return res


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


def msg_union_info(union: Dict):
    clubs = union['clubs']
    clubs_str = get_clubs_str(clubs)
    msg = f'Союз:\n' \
          f'{union["name"]}\n' \
          f'Ребейт: {union["rebate"]}\n' \
          f'Клубы:\n' \
          f'{clubs_str}'
    return msg


def set_active_clubs(clubs: Dict, indexes: List[str]) -> None:
    """Установить флаг участия в dp"""
    for index in indexes:
        raw_index = int(index) - 1
        club = clubs[raw_index]
        club['participate'] = True


def get_unions_info(unions: Dict) -> str:
    msg = '<b>Список союзов:</b>\n'
    for union_id in sorted(unions.keys()):
        union = unions[union_id]
        msg += f"{union_id + 1} {union['name']} Ребейт: {union['rebate']}.\n\n"
    return msg


def get_all_unions(user_id):
    unions_list = get_users_unions(user_id)
    unions_dict = {}
    for union_index, union in enumerate(unions_list):
        unions_dict[union_index] = union
        clubs_list = get_unions_clubs(union['id'])
        clubs_dict = {}
        for club_index, club in enumerate(clubs_list):
            clubs_dict[club_index] = club
        unions_dict[union_index]['clubs'] = clubs_dict
    return unions_dict


async def get_selected_union(state: FSMContext) -> Dict:
    data = await state.get_data()
    union_index = data['selected_union']
    union = data['unions'][union_index]
    return union


async def get_selected_club(state: FSMContext) -> Dict:
    data = await state.get_data()
    union = await get_selected_union(state)
    club_index = data['selected_club']
    return union['clubs'][club_index]
