from aiogram.dispatcher.filters.state import StatesGroup, State


class AddCard(StatesGroup):
    name_bank = State()
    number_card = State()
    channel_id = State()

class Mailing(StatesGroup):
    text = State()

class Users(StatesGroup):
    user_id_ban = State()
    user_id_unban = State()
