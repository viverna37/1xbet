from aiogram.dispatcher.filters import Command
from aiogram.dispatcher import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.utils.callback_data import CallbackData
from handlers.content import Text
from services.sql import DataBase
from bot import bot, dp
from keyboards.menu import keyboards as kb

import os
# dp_path = os.getenv("DB_PATH")
# db = DataBase(db_file=dp_path)
db = DataBase('base.db')

cb = CallbackData('btn', 'type', 'id')


@dp.message_handler(Command('start'), state="*")
async def start(message: Message, state: FSMContext):
    await state.finish()
    # await state.reset_state()
    if await db.get_user(message.from_user.id) == None:
        await db.add_user(message.from_user.id, message.from_user.username, message.from_user.full_name)
    if await db.is_admin(message.from_user.id):
        await message.answer(Text.start_text, reply_markup=kb.menu_for_admin)
        return
    await message.answer(Text.start_text, reply_markup=kb.menu)


############################################Главное меню###########################################################
@dp.message_handler(text=('🏠 Главное Меню'), state="*")
async def find_limits(message: Message, state: FSMContext):
    await message.answer(Text.start_text, reply_markup=kb.menu)
    await state.finish()


####################################################Инструкции###################################################
@dp.message_handler(text=('Инструкции ℹ️'))
async def cabinet(message: Message):
    await message.answer("Какая инструкиця вам нужна?", reply_markup=kb.instruction)


@dp.callback_query_handler(lambda call: call.data == 'instruction_add')
async def a(callback: CallbackQuery):
    file_id = await db.get_media("TOP_UP_GUIDE")
    try:
        await bot.send_video(callback.from_user.id, video=file_id[0][0], reply_markup=kb.menu)
    except Exception as e:
        await bot.send_message(callback.from_user.id, "Видео не найдено, попробуйте позже", reply_markup=kb.menu)


@dp.callback_query_handler(lambda call: call.data == 'instruction_withdrawal')
async def a(callback: CallbackQuery):
    file_id = await db.get_media("WITHDRAW_GUIDE")
    try:
        await bot.send_video(callback.from_user.id, video=file_id[0][0], reply_markup=kb.menu)
    except Exception as e:
        await bot.send_message(callback.from_user.id, "Видео не найдено, попробуйте позже", reply_markup=kb.menu)


####################################################Ссылки###################################################
@dp.message_handler(text=('Ссылки 🔗'))
async def cabinet(message: Message):
    await message.answer("https://t.me/+98eG0xVMAiYxZTNi", reply_markup=kb.menu)


