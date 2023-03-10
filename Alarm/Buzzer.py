import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

BUZZER_PIN = 17
GPIO.setup(BUZZER_PIN, GPIO.OUT)
FREQUENCY = 500

DURATION_1 = 0.2
DURATION_2 = 0.2
try:
    while True:
        for duty_cycle in range(0, 101, 5):
            GPIO.output(BUZZER_PIN, True)
            time.sleep(DURATION_1 / 100.0)
            GPIO.output(BUZZER_PIN, False)
            time.sleep((DURATION_1 * 4 / 5) / 100.0)
        
        
        GPIO.output(BUZZER_PIN, True)
        time.sleep(DURATION_2)
        GPIO.output(BUZZER_PIN, False)
        time.sleep(DURATION_2)
            
except KeyboardInterrupt:
    GPIO.cleanup()
