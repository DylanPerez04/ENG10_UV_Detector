import time
import board
import digitalio
import neopixel

button = digitalio.DigitalInOut(board.A2)
button.direction = digitalio.Direction.INPUT
button.pull = digitalio.Pull.UP

button_led = neopixel.NeoPixel(board.A0, 1, brightness=1, auto_write=True)

GREEN = (0, 255, 0)
OFF = (0, 0, 0)

led_on = False
button_led[0] = OFF
last_state = button.value

while True:
    current_state = button.value

    # Trigger only on the falling edge (moment of press)
    if not current_state and last_state:
        led_on = not led_on
        button_led[0] = GREEN if led_on else OFF
        print(f"Toggled LED: {'ON' if led_on else 'OFF'}")
        time.sleep(0.05)  # Debounce

    last_state = current_state
    time.sleep(0.01)
