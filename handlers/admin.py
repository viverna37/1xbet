
from http.client import responses
from logging import exception

from aiogram.dispatcher.filters import Command, state
from aiogram.dispatcher import FSMContext
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.callback_data import CallbackData
from pyexpat.errors import messages

from handlers.content import Text
from services.sql import DataBase
from bot import bot, dp
from states.admin import AddCard, Mailing, Users
from services.xbet import CashdeskAPI
import os
# dp_path = os.getenv("DB_PATH")
# db = DataBase(db_file=dp_path)
db = DataBase('base.db')
flag_top_up = False

cb = CallbackData('btn', 'type', 'user_id', 'transfer_id', "card_id")
api = CashdeskAPI(
    api_url="https://partners.servcul.com/CashdeskBotAPI/",
    hash_key="b2d73cf41c1d6ccb5d2b3bff3814d714ad7e6a045502e783fdf515c2d52b716a",
    cashier_pass="8G9xuW5yg2^7",
    cashdesk_id="1265128"
)

async def keyboard_card():
    data = await db.get_requisites()
    keyboard = InlineKeyboardMarkup()
    for i in data:
        keyboard.add(InlineKeyboardButton(text=i[2], callback_data="none"),
                     InlineKeyboardButton(text="✅" if i[3] == "ready" else "❌",
                                          callback_data=f"btn:card:{i[0]}:{'close' if i[3] == 'ready' else 'ready'}:-"))
    return keyboard

async def keyboard_card_for_del():
    data = await db.get_requisites()
    keyboard = InlineKeyboardMarkup()
    for i in data:
        keyboard.add(InlineKeyboardButton(text=i[2], callback_data="none"),
                     InlineKeyboardButton(text= "❌",
                                          callback_data=f"btn:remove_card:{i[0]}:-:-"))
    return keyboard

@dp.message_handler(Command('top_up'), state="*")
async def start(message: Message, state: FSMContext):
    global flag_top_up
    flag_top_up = not flag_top_up
    await message.answer(f"Доступность пополнения: {flag_top_up}")


@dp.callback_query_handler(cb.filter(type='confirm_top_up'))
async def select_city(call: CallbackQuery, callback_data: dict):
    await bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("ОДОБРЕНО✅", callback_data="none")))
    await bot.send_message(callback_data['user_id'], "<b>Ваша транзакция одобрена✅</b>")
    await db.update_transfer("COMPLETE", callback_data['transfer_id'])
    account_id = await db.get_account_id_for_user_id(callback_data['user_id'])
    amount = await db.get_amount_for_transfer_id(callback_data['transfer_id'])
    await api.deposit(account_id[0][0], amount[0][0])

    card_id = callback_data['card_id']
    channel_id = await db.get_card_where_id(card_id)
    await bot.send_photo(chat_id=channel_id[0], photo=call.message.photo[1].file_id)


@dp.callback_query_handler(cb.filter(type='confirm_payout'))
async def select_city(call: CallbackQuery, callback_data: dict):
    await bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("ОДОБРЕНО✅", callback_data="none")))
    await bot.send_message(callback_data['user_id'], "<b>Ваша транзакция одобрена✅</b>")
    await db.update_transfer("COMPLETE", callback_data['transfer_id'])


@dp.callback_query_handler(cb.filter(type='card'))
async def select_city(call: CallbackQuery, callback_data: dict):
    await db.update_status_card(callback_data['transfer_id'], callback_data['user_id'])
    await bot.edit_message_reply_markup(chat_id=call.from_user.id, message_id=call.message.message_id, reply_markup= await keyboard_card())

@dp.callback_query_handler(cb.filter(type='add_card'))
async def select_city(call: CallbackQuery, state: FSMContext):
    await bot.edit_message_text(chat_id=call.from_user.id, message_id=call.message.message_id, text="Введите название банка ")
    try:
        await bot.delete_message(chat_id=call.from_user.id, message_id=call.message.message_id + 1)
    except:
        pass
    await state.set_state(AddCard.name_bank)


@dp.message_handler(content_types=['text'], state=AddCard.name_bank)
async def wait_name_bank(message: Message, state: FSMContext):
    await state.update_data(name_bank=message.text)
    await message.answer("Введите номер карты")
    await state.set_state(AddCard.number_card)



@dp.message_handler(content_types=['text'], state=AddCard.number_card)
async def wait_name_bank(message: Message, state: FSMContext):
    await state.update_data(number=message.text)
    await message.answer("Теперь айди канала")
    await state.set_state(AddCard.channel_id)


@dp.message_handler(content_types=['text'], state=AddCard.channel_id)
async def wait_name_bank(message: Message, state: FSMContext):
    data = await state.get_data()
    await db.add_card(data['name_bank'], data['number'], message.text)
    await message.answer("Карта успешно добавлена", reply_markup=InlineKeyboardMarkup(row_width=1).add(InlineKeyboardButton("Добавить", callback_data="btn:add_card:-:-:-"), InlineKeyboardButton("Удалить", callback_data="btn:removee_card:-:-:-")))
    await state.finish()


@dp.callback_query_handler(cb.filter(type='removee_card'))
async def select_city(call: CallbackQuery, callback_data: dict):
    await bot.delete_message(chat_id=call.from_user.id, message_id=call.message.message_id + 1)
    try:
        await call.message.answer("Какую карту вы хотите удалить?", reply_markup=await keyboard_card_for_del())
    except:
        pass

@dp.callback_query_handler(cb.filter(type='remove_card'))
async def select_city(call: CallbackQuery, callback_data: dict):
    await db.delete_card(callback_data['user_id'])
    await bot.edit_message_reply_markup(chat_id=call.from_user.id, message_id=call.message.message_id,
                                        reply_markup=await keyboard_card_for_del())


@dp.callback_query_handler(cb.filter(type='ban'))
async def select_city(call: CallbackQuery, callback_data: dict, state: FSMContext):
    await call.message.answer(f"Отправь мне user_id")
    await state.set_state(Users.user_id_ban)


@dp.callback_query_handler(cb.filter(type='unban'))
async def select_city(call: CallbackQuery, callback_data: dict, state: FSMContext):
    await call.message.answer(f"Отправь мне user_id")
    await state.set_state(Users.user_id_unban)

@dp.message_handler(content_types=['text'], state=Users.user_id_ban)
async def find_limits(message: Message, state: FSMContext):
    user_id = int(message.text)
    await db.ban(user_id)
    await message.answer(f"Забанил {user_id}")
    await state.finish()


@dp.message_handler(content_types=['text'], state=Users.user_id_unban)
async def find_limits(message: Message, state: FSMContext):
    user_id = int(message.text)
    await db.unban(user_id)
    await message.answer(f"Забанил {user_id}")
    await state.finish()


@dp.message_handler(text=('Банки'))
async def find_limits(message: Message):
    await message.answer("Меню добавления реквизитов", reply_markup=InlineKeyboardMarkup(row_width=1).add(InlineKeyboardButton("Добавить", callback_data="btn:add_card:-:-:-"), InlineKeyboardButton("Удалить", callback_data="btn:removee_card:-:-:-")))
    await message.answer("Меню отключения реквизитов", reply_markup=await keyboard_card())

@dp.message_handler(text=('Банки'))
async def find_limits(message: Message):
    await message.answer("Ваши реквизиты", reply_markup=await keyboard_card())

@dp.message_handler(text=('Рассылка'))
async def find_limits(message: Message, state: FSMContext):
    await message.answer("Какой текст вы хотите разослать?")
    await state.set_state(Mailing.text)

@dp.message_handler(content_types=['text'], state=Mailing.text)
async def find_limits(message: Message, state: FSMContext):
    await message.answer("Начинаю рассылку")
    data = await db.get_all_user()

    valid_users = 0
    not_valid_users = 0
    for i in data:
        try:
            await bot.send_message(i[0], message.text)
            valid_users += 1
        except:
            not_valid_users += 1
    await message.answer(f"Проспамил {valid_users}\nЗаблокирован у {not_valid_users}")
    await state.finish()

@dp.message_handler(text=('Игроки'))
async def find_limits(message: Message, state: FSMContext):
    await message.answer("Выберите действие", reply_markup=InlineKeyboardMarkup(row_width=1).add(InlineKeyboardButton("Бан", callback_data="btn:ban:-:-:-"), InlineKeyboardButton("Разбан", callback_data="btn:unban:-:-:-")))

@dp.message_handler(text=('Статистика'))
async def find_limits(message: Message):
    all_users: int = await db.get_all_users()
    all_transfers: int = await db.get_all_transfers()
    complete_transfers: int = await db.get_complete_transfers()
    sum_top_up: int = await db.get_sum_top_up()
    sum_payout: int = await db.get_sum_payout()
    count_complete_top_up: int = await db.get_count_complete_top_up()
    count_complete_payout: int = await db.get_count_complete_payout()
    await message.answer(f'<b>Всего:\n</b>'
                         f'Человек: <code>{all_users[0][0]}</code>\n'
                         f'Операций: <code>{all_transfers[0][0]}</code>\n'
                         f'Успешных операций: <code>{complete_transfers[0][0]}</code>\n'
                         f'Пополнеий в RUB: <code>{sum_top_up[0][0]}</code>\n'
                         f'Выводов в RUB: <code>{sum_payout[0][0]}</code>\n\n'
                         f'<b>Среднее:\n</b>'
                         f'Пополнение одним пользователем: <code>{sum_top_up[0][0]/count_complete_top_up[0][0]}</code>\n'
                         f'Снятие одним пользователем: <code>{sum_payout[0][0]/count_complete_payout[0][0]}</code>')