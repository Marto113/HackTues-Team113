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
    def buzzer_alert():
        BUZZER_PIN = 17
        DURATION_1 = 0.2
        DURATION_2 = 0.2

        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(BUZZER_PIN, GPIO.OUT)

        start_time = time.time()
        while (time.time() - start_time) <= 300:  # run for 5 minutes
            for duty_cycle in range(0, 101, 5):
                GPIO.output(BUZZER_PIN, True)
                time.sleep(DURATION_1 / 100.0)
                GPIO.output(BUZZER_PIN, False)
                time.sleep((DURATION_1 * 4 / 5) / 100.0)

            GPIO.output(BUZZER_PIN, True)
            time.sleep(DURATION_2)
            GPIO.output(BUZZER_PIN, False)
            time.sleep(DURATION_2)

        GPIO.cleanup()

    def alert(message, image):
        asyncio.run(telegram_alert(message, image))
        buzzer_alert()
except:
    pass
