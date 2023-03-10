import asyncio
import telegram
from dotenv import dotenv_values

async def send_alarm(message):
    config = dotenv_values("../.env")
    token = config['telegram_token']
    chat_id = config['telegram_chat_id']

    async with telegram.Bot(token) as bot:
        await bot.send_message(chat_id, message)

if __name__ == '__main__':
    asyncio.run(send_alarm("The Alarm has been triggered!"))
