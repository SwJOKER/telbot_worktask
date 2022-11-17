from aiogram.utils.keyboard import ReplyKeyboardBuilder, ReplyKeyboardMarkup
from strings import *


def union_options_kb():
    kb = ReplyKeyboardBuilder()
    kb.button(text=STR_MAKE_UNION)
    return kb.as_markup(resize_keyboard=True)

def accept_union_data_kb():
    kb = ReplyKeyboardBuilder()
    kb.button(text=STR_TRUE)
    kb.button(text=STR_EDIT)
    return kb.as_markup(resize_keyboard=True)

def edit_data_kb():
    kb = ReplyKeyboardBuilder()
    kb.button(text=STR_EDIT_UNION)
    kb.button(text=STR_EDIT_CLUB)
    kb.button(text=STR_ADD_CLUB)
    return kb.as_markup(resize_keyboard=True)

def work_data_kb():
    kb = ReplyKeyboardBuilder()
    kb.button(text=STR_COUNT)
    kb.button(text=STR_EDIT_UNION)
    kb.button(text=STR_EDIT_CLUB)
    kb.button(text=STR_ADD_CLUB)
    return kb.as_markup(resize_keyboard=True)

def edit_club_kb():
    kb = ReplyKeyboardBuilder()
    kb.button(text=STR_DELETE_CLUB)
    kb.button(text=STR_CHANGE_NAME)
    kb.button(text=STR_EDIT_JACKPOT)
    kb.button(text=STR_EDIT_CONTRIBUTION)
    return kb.as_markup(resize_keyboard=True)



def edit_union_data_kb():
    kb = ReplyKeyboardBuilder()
    kb.button(text=STR_NEW_NAME)
    kb.button(text=STR_NEW_REBATE)
    return kb.as_markup(resize_keyboard=True)

def yes_no_kb():
    kb = ReplyKeyboardBuilder()
    kb.button(text=STR_YES)
    kb.button(text=STR_NO)
    return kb.as_markup(resize_keyboard=True)


def get_number_kb(key_count: int) -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardBuilder()
    for i in range(key_count):
        kb.button(text=str(i + 1))
    return kb.as_markup(resize_keyboard=True)