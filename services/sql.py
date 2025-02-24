import sqlite3


class DataBase:

    def __init__(self, db_file):
        self.connect = sqlite3.connect(db_file)
        self.cursor = self.connect.cursor()
        self.cards = []
        self.index = 0

    async def add_user(self, user_id, username, full_name):
        with self.connect:
            return self.cursor.execute(
                """INSERT INTO users (user_id, username, full_name) VALUES (?, ?, ?)""",
                [user_id, username, full_name])

    async def get_user(self, user_id):
        with self.connect:
            return self.cursor.execute("""SELECT user_id FROM users WHERE user_id=(?)""", [user_id]).fetchone()

    async def get_all_user(self):
        with self.connect:
            return self.cursor.execute("""SELECT user_id FROM users""",).fetchall()

    async def is_admin(self, user_id):
        with self.connect:
            return self.cursor.execute("""SELECT user_id FROM admins WHERE user_id=(?)""", [user_id]).fetchone()

    async def is_banned(self, user_id):
        with self.connect:
            result = self.cursor.execute("SELECT is_banned FROM bans WHERE user_id = ?", (user_id,)).fetchone()

        if result and result[0] == 1:  # Если поле banned установлено в 1
            return True
        return False

    async def ban(self, user_id):
        with self.connect:
            return self.cursor.execute("""INSERT INTO bans (user_id, is_banned) VALUES (?, '1')""",
                                       [user_id])

    async def unban(self, user_id):
        with self.connect:
            return self.cursor.execute("""UPDATE bans SET is_banned = 0 WHERE user_id=(?)""",
                                       [user_id])

    async def get_account_id_for_user_id(self, user_id):
        with self.connect:
            return self.cursor.execute("""SELECT default_account_id FROM users WHERE user_id=(?)""",
                                       [user_id]).fetchall()

    async def get_amount_for_transfer_id(self, id):
        with self.connect:
            return self.cursor.execute("""SELECT amount FROM transfers WHERE id=(?)""", [id]).fetchall()

    async def update_users_default_account_id(self, default_account_id, user_id):
        with self.connect:
            return self.cursor.execute("""UPDATE users SET default_account_id = (?) WHERE user_id=(?)""",
                                       [default_account_id, user_id])

    async def get_media(self, media_type):
        with self.connect:
            return self.cursor.execute("""SELECT file_id FROM medias WHERE media_type=(?)""", [media_type]).fetchall()

    async def get_requisites(self):
        with self.connect:
            return self.cursor.execute("""SELECT * FROM requisites""").fetchall()


    async def get_requisites_ready(self):
        with self.connect:
            return self.cursor.execute("""SELECT * FROM requisites WHERE status='ready'""").fetchall()


    async def update_status_card(self, status, id):
        with self.connect:
            return self.cursor.execute("""UPDATE requisites SET status = (?) WHERE id=(?)""",
                                       [status, id])

    async def add_card(self, bank_name, number_card, channel_id):
        with self.connect:
            return self.cursor.execute(
                """INSERT INTO requisites (bank_name, number_card, status, channel_id) VALUES (?, ?, ?, ?)""",
                [bank_name, number_card, "ready", channel_id])

    async def delete_card(self, id):
        with self.connect:
            return self.cursor.execute(
                """DELETE FROM requisites WHERE id=(?);""",
                [id])

    async def load_cards(self):
        """Загружает карточки из базы."""
        self.cursor.execute("SELECT * FROM requisites WHERE status=(?)", ["ready"])
        # Подстрой под свою таблицу
        self.cards = self.cursor.fetchall()

    async def get_next_card(self):
        """Возвращает следующую карточку по порядку."""

        await self.load_cards()

        if not self.cards:
            return None  # Если карточек нет в базе

        card = self.cards[self.index]
        self.index = (self.index + 1) % len(self.cards)  # Зацикливание

        return card

    async def get_card_where_id(self, id):
        with self.connect:
            return self.cursor.execute("SELECT channel_id FROM requisites WHERE id=(?)", [id]).fetchone()

    async def create_transfer(self, amount, account_id, status, type, user_id):
        with self.connect:
            self.cursor.execute(
                """INSERT INTO transfers (amount, account_id, status, type, user_id) VALUES (?, ?, ?, ?, ?)""",
                [amount, account_id, status, type, user_id]
            )
            # Получаем ID последней вставленной записи
            transfer_id = self.cursor.lastrowid
            return transfer_id



    async def update_transfer(self, status, id):
        with self.connect:
            return self.cursor.execute("""UPDATE transfers SET status = (?) WHERE id=(?)""",
                                       [status, id])

    async def get_all_users(self):
        with self.connect:
            return self.cursor.execute("""SELECT COUNT(*) FROM users""").fetchall()

    async def get_all_transfers(self):
        with self.connect:
            return self.cursor.execute("""SELECT COUNT(*) FROM transfers""").fetchall()

    async def get_complete_transfers(self):
        with self.connect:
            return self.cursor.execute("""SELECT COUNT(*) FROM transfers WHERE status = 'COMPLETE'""").fetchall()

    async def get_count_complete_payout(self):
        with self.connect:
            return self.cursor.execute("""SELECT COUNT(*) FROM transfers WHERE status = 'COMPLETE' AND type = 'PAYOUT'""").fetchall()

    async def get_count_complete_top_up(self):
        with self.connect:
            return self.cursor.execute("""SELECT COUNT(*) FROM transfers WHERE status = 'COMPLETE'AND type = 'TOP_UP'""").fetchall()

    async def get_sum_top_up(self):
        with self.connect:
            return self.cursor.execute("""SELECT SUM(amount) FROM transfers WHERE status = 'COMPLETE' AND type = 'TOP_UP'""").fetchall()

    async def get_sum_payout(self):
        with self.connect:
            return self.cursor.execute("""SELECT SUM(amount) FROM transfers WHERE status = 'COMPLETE' AND type = 'PAYOUT'""").fetchall()
