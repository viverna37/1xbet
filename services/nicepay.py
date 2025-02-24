import asyncio

import aiohttp

from config import Config
from bot import dp


async def create_payment_link(amount, transfer_id, user_id, requests=None):
    url = f"https://nicepay.io/public/api/payment"
    headers = {
        "Content-Type": "application/json"
    }

    data = {
        "merchant_id": Config.nice_pay_id,
        "secret": Config.nice_pay_secret_key,
        "order_id": transfer_id,
        "customer": user_id,
        "amount": amount,
        "currency": "RUB",
        "description": "Top up balance on website"
    }

    async with aiohttp.ClientSession() as session:
        response = await session.post(
            f"{url}",
            json=data,
            headers=headers,
        )
        print(await response.json())
        return await response.json()



asyncio.run(create_payment_link(120000, 423141, 3214))