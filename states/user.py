from aiogram.dispatcher.filters.state import StatesGroup, State


class TopUpStates(StatesGroup):
    wait_for_account_number = State()
    wait_for_transfer_amount = State()
    wait_for_check = State()


class TopUpPercentStates(StatesGroup):
    wait_for_account_number = State()
    wait_for_transfer_amount = State()
    wait_for_check = State()

class WithdrawStates(StatesGroup):
    wait_for_account_number = State()
    wait_for_transfer_amount = State()
    wait_for_secure_code = State()
    wait_for_user_payments_info = State()
    wait_confirm_code = State()
