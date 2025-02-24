
from dataclasses import dataclass
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

import keyboards


@dataclass()
class keyboards:
    menu = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True).row(
        KeyboardButton('➕ ПОПОЛНЕНИЕ'),
        KeyboardButton('ВЫВОД 📤'))
    menu.add(KeyboardButton('🏠 Главное Меню'))
    menu.row(KeyboardButton('Ссылки 🔗'), KeyboardButton('Инструкции ℹ️'))

    menu_for_admin = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True).row(
        KeyboardButton('➕ ПОПОЛНЕНИЕ'),
        KeyboardButton('ВЫВОД 📤'))
    menu_for_admin.add(KeyboardButton('🏠 Главное Меню'))
    menu_for_admin.row(KeyboardButton('Ссылки 🔗'), KeyboardButton('Инструкции ℹ️'))
    menu_for_admin.add(KeyboardButton("Банки"), KeyboardButton("Рассылка"))
    menu_for_admin.add(KeyboardButton("Игроки"), KeyboardButton('Статистика'))


    instruction = InlineKeyboardMarkup(row_width=2).add(
        InlineKeyboardButton('➕ ПОПОЛНЕНИЕ', callback_data='instruction_add'),
        InlineKeyboardButton('ВЫВОД 📤', callback_data='instruction_withdrawal'),
    )


