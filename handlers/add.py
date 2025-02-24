import datetime
import os

from aiogram.dispatcher import FSMContext
from aiogram.types import Message, InputFile, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton, \
    ContentTypes
import random
from bot import bot, dp
from states.user import TopUpStates, WithdrawStates
from config import Config
from services.xbet import CashdeskAPI
from services.sql import DataBase
from enum import Enum





# Инициализация
api = CashdeskAPI(
    api_url="https://partners.servcul.com/CashdeskBotAPI/",
    hash_key="b2d73cf41c1d6ccb5d2b3bff3814d714ad7e6a045502e783fdf515c2d52b716a",
    cashier_pass="8G9xuW5yg2^7",
    cashdesk_id="1265128"
)
# dp_path = os.getenv("DB_PATH")
# db = DataBase(db_file=dp_path)
db = DataBase('base.db')


#################################################### Пополнение ###################################################
@dp.message_handler(text=('➕ ПОПОЛНЕНИЕ'))
async def cabinet(message: Message, state: FSMContext):
    photo = InputFile("image/where_to_find_id.jpg")
    await bot.send_photo(message.from_user.id, photo=photo, caption='Введите ID (Номер Счёта) 1XBET!')
    await state.set_state(TopUpStates.wait_for_account_number)


@dp.message_handler(content_types=['text'], state=TopUpStates.wait_for_account_number)
async def find_limits(message: Message, state: FSMContext):
    if message.text == "ВЫВОД 📤":
        photo = InputFile("image/where_to_find_id_.jpg")
        await bot.send_photo(message.from_user.id, photo=photo, caption='Введите ID (Номер Счёта) 1XBET!')
        await state.set_state(WithdrawStates.wait_for_account_number)
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
            await message.answer("Неизвестная ошибка. Попробуйте позже...")
            return
        elif account.get('CurrencyId') != 1:
            await message.answer("Бот работает только с аккаунтами, у которых валюта счёта - Рубль.")
            return

    except Exception as e:
        print("Ошибка при поиске игрока", e)
        await message.answer("Неизвестная ошибка. Попробуйте позже...")
        return
    print(account)
    await state.update_data(account_id=account_id)
    await message.answer(f"🆔ID игрока: {account['UserId']}\n✉️ФИО: {account['Name']}\n\n💵Укажите сумму пополнения RUB.\n<b>Минимальная: 1.000 РУБ\nМаксимальная: 3.500 РУБ</b>")
    await db.update_users_default_account_id(account_id, message.from_user.id)
    await state.set_state(TopUpStates.wait_for_transfer_amount)


@dp.message_handler(content_types=['text'], state=TopUpStates.wait_for_transfer_amount)
async def set_transfer_amount(message: Message, state: FSMContext):
    user_id = message.from_user.id
    if not message.text:
        await message.answer("Проверьте введенное значение.")
        return
    try:
        transfer_amount = int(message.text)
        if transfer_amount < 1000:
            await message.answer("Минимальная сумма 1000.\n")
            return
        elif transfer_amount > 3500:
            await message.answer(" Максимальна сумма 3500.")
            return
    except ValueError:
        await message.answer("Проверьте введенное значение.")
        return

    data = await state.get_data()

    card = await db.get_requisites_ready()
    card = random.choice(card)

    kasa_data = await api.get_balance(datetime.datetime.now())
    kasa_balance = kasa_data.get('Limit')
    from .admin import flag_top_up
    if flag_top_up:
        if kasa_balance > transfer_amount:
            if card:
                transfer_id = await db.create_transfer(transfer_amount, data['account_id'], "CREATE", 'TOP_UP', user_id)
                await message.answer(f"<b>Реквизиты для пополнения</b>\n\n🏦Банк: {card[1]}\n💳Номер карты: <code>{card[2]}</code>")
                await message.answer('<b>Для подтверждения оплаты требуется предоставить боту скриншот чека-квитанции, на котором чётко видны время и данные отправителя. Другие скриншоты оплаты не будут приняты.\n\nВнимательно сверьте реквизиты и название банка, при ошибке администрации не несет никакой ответственности и денежные средства будут утеряны</b>')
            else:
                await message.answer("В данный момент нету свободных реквизитов, попробуйте позже🕟")
                await state.finish()
                return
            await state.update_data(transfer_id=transfer_id, transfer_amount=transfer_amount, card=card, bank={card[1]})
            await state.set_state(TopUpStates.wait_for_check)
        else:
            await message.answer(
                f"<b>На данный момент пополнение не доступно, попробуйте позднее\nПриносим свои извинения</b>")
            await state.finish()
    else:
        await message.answer(
            f"<b>На данный момент пополнение не доступно, попробуйте позднее\nПриносим свои извинения</b>")
        await state.finish()

@dp.message_handler(content_types=['photo'], state=TopUpStates.wait_for_check)
async def confirm_transfer(message: Message, state: FSMContext):
    user_id = message.from_user.id
    username = message.from_user.username

    data = await state.get_data()
    photo = message.photo[0].file_id
    await db.update_transfer("SEND_MONEY", data.get('transfer_id'))
    await message.reply(
        f"✅ Заявка #{data.get('transfer_id')} принята на проверку!\n"
        f"🆔: {data.get('account_id')}\n"
        f"💵 Сумма: {data.get('transfer_amount')}\n"
        "⚠️ Пополнение занимает от 1 секунды до 10 минут. В редких случаях до 3 часов. Пожалуйста, подождите!"
    )
    await db.update_transfer("WAIT_COMPLETE", data.get('transfer_id'))
    await bot.send_photo(Config.channel_id_top_up, photo=photo,
                         caption=f"Запрос на проверку поступления денежных средств\nСумма {data.get('transfer_amount')}\nБанк: {data.get('bank')}\nКарта {data.get('card')[2]}\nЗаявка #{data.get('transfer_id')}"
                                 f"\n\nОтправлена\nID: <code>{user_id}</code>\nUsername: @{username}\n1XBet_ID: <code>{data.get('account_id')}</code>",
                         reply_markup=InlineKeyboardMarkup(row_width=1).add(InlineKeyboardButton("Одобрить", callback_data=f"btn:confirm_top_up:{user_id}:{data.get('transfer_id')}:{data.get('card')[0]}")))
    await state.finish()

@dp.message_handler(content_types=ContentTypes.VIDEO)
async def confirm_transfer(message: Message, state: FSMContext):
    print(message.video.file_id)