import asyncio
import hashlib
import json

import aiohttp


class CashdeskAPI:
    def __init__(self, api_url, hash_key, cashier_pass, cashdesk_id):
        self.api_url = api_url
        self.hash_key = hash_key
        self.cashier_pass = cashier_pass
        self.cashdesk_id = cashdesk_id

    def calculate_sha256(self, data):
        return hashlib.sha256(data.encode()).hexdigest()

    def calculate_md5(self, data):
        return hashlib.md5(data.encode()).hexdigest()

    async def get_balance(self, dt):
        # Формирование confirm
        confirm = self.calculate_md5(f"{self.cashdesk_id}:{self.hash_key}")
        # Формирование URL
        url = f"{self.api_url}Cashdesk/{self.cashdesk_id}/Balance?confirm={confirm}&dt={dt}"

        sha256_hash = self.calculate_sha256(f"hash={self.hash_key}&cashierpass={self.cashier_pass}&dt={dt}")
        md5_hash = self.calculate_md5(f"dt={dt}&cashierpass={self.cashier_pass}&cashdeskid={self.cashdesk_id}")
        final_sign = self.calculate_sha256(sha256_hash + md5_hash)

        headers = {"Authorization": f"{final_sign}"}
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url) as response:
                return await response.json()

    async def find_user(self, user_id):
        # Формирование confirm
        confirm = self.calculate_md5(f"{user_id}:{self.hash_key}")
        # Формирование URL
        url = f"{self.api_url}Users/{user_id}?confirm={confirm}&cashdeskId={self.cashdesk_id}"

        sha256_hash = self.calculate_sha256(f"hash={self.hash_key}&userid={user_id}&cashdeskid={self.cashdesk_id}")
        md5_hash = self.calculate_md5(f"userid={user_id}&cashierpass={self.cashier_pass}&hash={self.hash_key}")
        final_sign = self.calculate_sha256(sha256_hash + md5_hash)

        headers = {"Authorization": f"{final_sign}"}
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url) as response:
                return await response.json()

    async def deposit(self, account_id, summa):
        sha256_part = self.calculate_sha256(f"hash={self.hash_key}&lng=ru&userid={account_id}")
        md5_part = self.calculate_md5(
            f"summa={float(summa)}&cashierpass={self.cashier_pass}&cashdeskid={self.cashdesk_id}")
        signa = self.calculate_sha256(sha256_part + md5_part)

        confirm_code = self.calculate_md5(f"{account_id}:{self.hash_key}")

        payload = json.dumps(
            {
                "cashdeskId": self.cashdesk_id,
                "lng": "ru",
                "summa": float(summa),
                "confirm": confirm_code,
            }
        )
        async with aiohttp.ClientSession() as session:
            response = await session.post(
                f"{self.api_url}Deposit/{account_id}/Add",
                data=payload,
                headers={"sign": signa, "content-type": "application/json"},
            )
            return await response.json()

    async def payout(self, account_id, secure_code):
        sha256_part = self.calculate_sha256(f"hash={self.hash_key}&lng=ru&userid={account_id}")
        md5_part = self.calculate_md5(
            f"code={secure_code}&cashierpass={self.cashier_pass}&cashdeskid={self.cashdesk_id}")
        signa = self.calculate_sha256(sha256_part + md5_part)

        confirm_code = self.calculate_md5(f"{account_id}:{self.hash_key}")
        payload = json.dumps(
            {
                "cashdeskid": self.cashdesk_id,
                "lng": "ru",
                "code": secure_code,
                "confirm": confirm_code,
            },
        )

        async with aiohttp.ClientSession() as session:
            response = await session.post(
                f"{self.api_url}/Deposit/{account_id}/Payout",
                data=payload,
                headers={"sign": signa, "content-type": "application/json"},
            )
            return await response.json()

        # # Формирование подписи
        # sha256_part = self.calculate_sha256(
        #     f"hash={self.hash_key}&lng={lng}&userId={user_id}"
        # )
        #
        # md5_part = self.calculate_md5(
        #     f"code={code}&cashierpass={self.cashier_pass}&cashdeskid={self.cashdesk_id}"
        # )
        #
        # final_hash = self.calculate_sha256(sha256_part + md5_part)
        #
        # # Формирование confirm
        # confirm = self.calculate_md5(f"{user_id}:{self.hash_key}")
        #
        # # Формирование тела запроса
        # url = f"{self.api_url}Deposit/{user_id}/Payout"
        # json_data = {
        #     "cashdeskId": int(self.cashdesk_id),
        #     "lng": lng,
        #     "code": code,
        #     "confirm": confirm,
        # }
        #
        # async with aiohttp.ClientSession() as session:
        #     async with session.post(url, json=json_data) as response:
        #         return await response.json()
