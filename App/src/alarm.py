from dotenv import dotenv_values
import asyncio
import telegram
import time

async def telegram_alert(message, image):
    config = dotenv_values("../.env")
    token = config['telegram_token']
    chat_id = config['telegram_chat_id']

    async with telegram.Bot(token) as bot:
        await bot.send_message(chat_id, message)
        with open(image, 'rb') as f:
            await bot.send_photo(chat_id, f)

def telegram_alert_sync(*args, **kwargs):
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(telegram_alert(*args, **kwargs))

try:
    import RPi.GPIO as GPIO
    BUZZER_PIN = 17
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(BUZZER_PIN, GPIO.OUT)

    def set_buzzer(state):
        GPIO.output(BUZZER_PIN, state)
except:
    def set_buzzer(state):
        print('Buzzer', state)
