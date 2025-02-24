from aiogram import types
from aiogram.dispatcher.middlewares import BaseMiddleware
from services.sql import DataBase
from aiogram.dispatcher.handler import CancelHandler

class BanCheckMiddleware(BaseMiddleware):
    def __init__(self):
        """Инициализация middleware с подключением к базе данных."""
        import os
        # dp_path = os.getenv("DB_PATH")
        # db = DataBase(db_file=dp_path)
        self.db_connection = DataBase('base.db')

        super().__init__()

    async def on_pre_process_message(self, message: types.Message, data: dict):
        """Выполняется перед обработкой любого сообщения."""
        user_id = message.from_user.id
        # Проверяем, забанен ли пользователь
        if await self.db_connection.is_banned(user_id):
            # Отправляем сообщение о блокировке
            await message.answer("Вы забанены. Обратитесь к администратору.")

            # Прерываем обработку сообщения
            raise CancelHandler()
