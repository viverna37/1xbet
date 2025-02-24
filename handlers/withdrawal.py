import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from config import Config
from states.user import WithdrawStates, TopUpStates
from aiogram.dispatcher import FSMContext
from aiogram.types import Message, InputFile
from services.xbet import CashdeskAPI
from services.sql import DataBase
from bot import bot, dp
from enum import Enum

# Инициализация API
api = CashdeskAPI(
    api_url="***",
    hash_key="***",
    cashier_pass="***",
    cashdesk_id="***"
)

import os
# dp_path = os.getenv("DB_PATH")
# db = DataBase(db_file=dp_path)
db = DataBase('base.db')

logger = logging.getLogger(__name__)

@dp.message_handler(text=('ВЫВОД 📤'))
async def cabinet(message: Message, state: FSMContext):
    photo = InputFile("image/where_to_find_id_.jpg")
    await bot.send_photo(message.from_user.id, photo=photo, caption='Введите ID (Номер Счёта) 1XBET!')
    await state.set_state(WithdrawStates.wait_for_account_number)


@dp.message_handler(state=WithdrawStates.wait_for_account_number)
async def set_account_number(message: Message, state: FSMContext):
    if message.text == "➕ ПОПОЛНЕНИЕ":
        photo = InputFile("image/where_to_find_id.jpg")
        await bot.send_photo(message.from_user.id, photo=photo, caption='Введите ID (Номер Счёта) 1XBET!')
        await state.set_state(TopUpStates.wait_for_account_number)
        return 

    if not message.text:
        await message.answer("Проверьте введенное значение.")
        return

    try:
        account_id = int(message.text)
    except ValueError:
        await message.answer("Проверьте введенное значение.")
        return

    try:
        account = await api.find_user(account_id)
        if not account:
            await message.answer("Бот работает только с аккаунтами, у которых валюта счёта - Рубль.")
            return
    except Exception as e:
        logger.exception("Ошибка при поиске аккаунта", exc_info=e)
        await message.answer("Неизвестная ошибка. Попробуйте позже.")
        return

    await state.update_data(account_id=account_id)
    await message.answer(f"🆔ID игрока: {account['UserId']}\n✉️ФИО: {account['Name']}")
    await WithdrawStates.wait_for_secure_code.set()
    await state.update_data(account_id=account['UserId'])
    await message.answer_photo(
        photo=InputFile("image/img.png"),
        caption=(
            "📍Заходим👇\n"
            "📍1. Настройки!\n"
            "📍2. Вывести со счета!\n"
            "📍3. Наличные\n"
            "📍4.Сумму для Вывода!\n"
            "Город: Ртищево\n"
            "Улица: Market Assistant (24/7)\n"
            "📍5. Подтвердить\n"
            "📍6. Получить Код!\n"
            "📍7. Отправить его нам\n\n"
            "Если возникли проблемы 👇\n"
            "👨‍💻Оператор: @Market_Assistant_robot_Support"
        ),
    )
    await message.answer('<b>Ожидаем код...</b>')


@dp.message_handler(state=WithdrawStates.wait_for_secure_code)
async def set_secure_code_handler(message: Message, state: FSMContext):
    await WithdrawStates.wait_for_user_payments_info.set()
    await message.answer("Отправьте реквизиты для получения перевода.")
    await state.update_data(secure_code=message.text)


@dp.message_handler(state=WithdrawStates.wait_for_user_payments_info)
async def send_user_payments_info(message: Message, state: FSMContext):
    await state.update_data(req=message.text)

    data = await state.get_data()
    user_id = message.from_user.id
    username = message.from_user.username
    try:
        payout = await api.payout(
            account_id=data['account_id'],
            secure_code=data['secure_code']
        )
        transfer_id = await db.create_transfer(payout["Summa"], data['account_id'], "CREATE", 'PAYOUT', user_id)
        await state.update_data(transfer_id=transfer_id)
        if payout['Success'] == False:
            await message.answer("Не найдено ни одного запроса на выплату для этого пользователя")
        else:
            await message.answer(
                f"✅ Заявка #{transfer_id} принята на проверку!\n"
                f"🆔: {payout['Summa']}\n"
                f"💵 Сумма: {data.get('transfer_amount')}\n"
                f"💳 Карта: {data.get('req')}\n"
                "⚠️ Вывод занимает от 1 минуты до 3 часов. Пожалуйста, подождите!"
            )
            await bot.send_message(Config.channel_id_payout,
                                   text=f"Запрос на вывод денежных средств\nСумма: {payout['Summa']}\nКарта: <code>{data.get('req')}</code>\nЗаявка #{transfer_id}\n\nОтправлена\nID: <code>{user_id}</code>\nUsername: @{username}\n1XBet_ID: <code>{data.get('account_id')}</code>",
                                   reply_markup=InlineKeyboardMarkup(row_width=1).add(InlineKeyboardButton("Одобрить",
                                                                                                           callback_data=f"btn:confirm_payout:{user_id}:{transfer_id}:card_id")))
            await db.update_transfer("WAIT_COMPLETE", transfer_id)

    except Exception as e:
        logger.exception("Ошибка при подтверждении вывода", exc_info=e)
        await message.answer("Ошибка при обработке вывода. Попробуйте позже.")
        return

    await state.finish()
    # {'Summa': -2000.0, 'OperationId': 4242578115, 'Success': True, 'Message': 'Операция выполнена успешно'}

