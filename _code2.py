"""
from adafruit_circuitplayground import cp
import board
import digitalio
from time import sleep

led = digitalio.DigitalInOut(board.A1);
led.direction = digitalio.Direction.OUTPUT;

while True:
    led.value = True
    sleep(0.5)
    led.value = False
    sleep(0.5)
"""

"""
import board
import pwmio
from adafruit_circuitplayground import cp
import adafruit_motor.servo
from time import sleep

# Setup Section
pwm = pwmio.PWMOut(board.A1, frequency=50)
servo = adafruit_motor.servo.Servo(pwm, min_pulse=750, max_pulse=2600)

# Function Section
def light_to_servo_pos(light):
    light_max = 320
    return 180 - ((light/light_max) * 180)

def light_detected(light):
    light_max = 320
    if light > (light_max / 2):
        return True

    return False

# Loop Section
angle = 0
while True:
    if light_detected(cp.light):
        angle = (angle + 10) % 360

    #if angle > 180:
    #    servo.angle = -1 * (angle % 180);
    #else:
        servo.angle = angle

    #servo.angle = light_to_servo_pos(cp.light)
    print(servo.angle)
    sleep(0.05)
"""

import board
import pwmio
from adafruit_circuitplayground import cp
from adafruit_hcsr04 import HCSR04
import adafruit_motor.servo
from time import sleep

# Setup Section
led_brightness = 0.25
t = 0
dt = 0.25
sonar = HCSR04(trigger_pin=board.TX, echo_pin=board.A6)
cp.pixels.fill((255,0,0))
cp.pixels.brightness = 0
"""
sonar = HCSR04(trigger_pin=board.TX, echo_pin=board.A6)
pwm = pwmio.PWMOut(board.A1, frequency=50)
servo = adafruit_motor.servo.Servo(pwm, min_pulse=750, max_pulse=2600)
"""
# Function Section
def pixel_flip():
    if cp.pixels.brightness > 0:
        cp.pixels.brightness = 0
    else:
        cp.pixels.brightness = led_brightness

""""
def servo_pos(dist):
    dist_min = 5
    dist_max = 50
    dist = min((max((dist, dist_min)), dist_max))
    return (((dist-dist_min)/(dist_max-dist_min)) * 180)
"""

# Loop Section
while True:
    try:
        d = sonar.distance
        # Closer than 15 cm is Dangerously Close
        if d <=5:
            pixel_flip()
            if t >= 1.0:
                cp.play_tone(440, 0.25)
                t = 0

        # Closer than 15 cm is Very Close
        elif d <= 15:
            pixel_flip()

        # Closer than 30 cm is Close
        elif d <= 30:
            if t >= 1.0:
                pixel_flip()
                t = 0

        # Farther than 25 cm is Safe
        else:
            cp.pixels.brightness = 0

        print((d,))
        t+=dt
    except RuntimeError:
        print("Retrying!")
    sleep(dt)
