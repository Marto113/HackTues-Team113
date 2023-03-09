import asyncio
import telegram

async def send(token, chat_id):
    bot = telegram.Bot(token)
    message = "ALARM IS GOING OFF"
    await bot.send_message(chat_id, message)

async def main():
    # bot token using BotFather
    token = '6063360147:AAG1O9B9dClWpKNb8IO1HW3672Xc3pMvnU0'

    # group to send the message to
    chat_id = '-977069027'
    await send(token, chat_id)

if __name__ == '__main__':
    asyncio.run(main())
    