from aiogram.fsm.state import StatesGroup, State

class RouterStates(StatesGroup):
    new_union = State()
    accept_data = State()
    editing = State()
    editing_union = State()
    editing_union_name = State()
    editing_union_rebate = State()
    editing_club = State()
    show_editing_club = State()
    editing_club_name = State()
    editing_club_delete = State()
    show_union = State()
    add_club = State()
