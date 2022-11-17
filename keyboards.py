from aiogram.utils.keyboard import ReplyKeyboardBuilder, ReplyKeyboardMarkup

def union_options_kb():
    kb = ReplyKeyboardBuilder()
    kb.button(text='Создать союз')
    #kb.button(text='Добавить союз')
    return kb.as_markup(resize_keyboard=True)

def accept_union_data_kb():
    kb = ReplyKeyboardBuilder()
    kb.button(text='Верно')
    kb.button(text='Редактировать')
    return kb.as_markup(resize_keyboard=True)

def edit_data_kb():
    kb = ReplyKeyboardBuilder()
    kb.button(text='Редактировать союз')
    kb.button(text='Редактировать клуб')
    kb.button(text='Добавить клуб')
    return kb.as_markup(resize_keyboard=True)

def edit_club_kb():
    kb = ReplyKeyboardBuilder()
    kb.button(text='Удалить клуб')
    kb.button(text='Изменить имя')
    kb.button(text='Редактировать джекпот + эквити')
    kb.button(text='Редактировать взнос')
    return kb.as_markup(resize_keyboard=True)

def edit_union_data_kb():
    kb = ReplyKeyboardBuilder()
    kb.button(text='Новое имя')
    kb.button(text='Новый ребейт')
    return kb.as_markup(resize_keyboard=True)

def yes_no_kb():
    kb = ReplyKeyboardBuilder()
    kb.button(text='Да')
    kb.button(text='Нет')
    return kb.as_markup(resize_keyboard=True)


def get_number_kb(key_count: int) -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardBuilder()
    for i in range(key_count):
        kb.button(text=str(i + 1))
    return kb.as_markup(resize_keyboard=True)