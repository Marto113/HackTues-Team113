import asyncio
import telegram
from dotenv import dotenv_values

async def telegram_alert(message, image):
    config = dotenv_values("../.env")
    token = config['telegram_token']
    chat_id = config['telegram_chat_id']

    async with telegram.Bot(token) as bot:
        await bot.send_message(chat_id, message)
        with open(image, 'rb') as f:
            await bot.send_photo(chat_id, f)

if __name__ == '__main__':
    asyncio.run(telegram_alert("The Alarm has been triggered!", "D:\Programing\HackTues-Team113\App\src\static\images\icon.png"))
