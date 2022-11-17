from aiogram import types
from aiogram.types.document import Document

sessions = None
router = None

def text_to_clubs(msg: str):
    res = {}
    lines = msg.split('\n')
    for num, line in enumerate(lines):
        name, percent = line.strip().split(' ')
        res[num] = {'name': name, 'percent': percent, 'participate': False}
    return res


def get_clubs_str(message: types.Message):
    """Получить список клубов текущего союза в текстовом формате для сообщения"""
    session = get_current_union(message.from_user.id)
    clubs_txt = ''
    for club in session['clubs']:
        clubs_txt += f'{club + 1}. {session["clubs"][club]["name"]}\n'
    return clubs_txt


async def get_clubs_from_source(message: types.Message):
    session = get_current_union(message.from_user.id)
    if message.document:
        clubs = await parse_doc(message.document)
    else:
        clubs = text_to_clubs(message.text)
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
    index = sessions[user_id]['current']
    try:
        union = sessions[user_id]['unions'][index]
    except KeyError:
        sessions[user_id]['unions'][0] = {}
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
    user = sessions[message.from_user.id]
    msg = 'Список союзов:\n'
    for union in user['unions']:
        msg += f"Name: {union['name']}. Rebate: {union['rebate']}.\n"
    return msg
