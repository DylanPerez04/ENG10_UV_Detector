# Import Section
import board
import analogio
import digitalio  # NEW: needed to read the button's switch contact on A2
import neopixel  # NEW: needed to drive the button's built-in RGB LED on A1
from adafruit_circuitplayground import cp
from time import sleep

debug = False

skin_type_index = 0  # Fitzpatrick skin type, 1 to 6

# Setup Section
uv_sensor = analogio.AnalogIn(board.A6)

cp.pixels.brightness = 1
cp.pixels.fill((0, 0, 0))

# ---------------------------------------------------------------------------
# NEW: ChromaTek button setup
# ---------------------------------------------------------------------------

# NEW: The button's RGB LED data input (DIN) is on A1. It is a single
# NeoPixel-style LED, so we make a 1-pixel strip on that pin.
button_led = neopixel.NeoPixel(board.A1, 1, brightness=1, auto_write=True)

# NEW: The button's switch contact (DOUT) is on A2, read as a digital input.
button_switch = digitalio.DigitalInOut(board.A2)
button_switch.direction = digitalio.Direction.INPUT

# Pressing connects A2 to GND (uses the internal pull-UP resistor)
button_switch.pull = digitalio.Pull.UP

# NEW: Button LED color for each skin type (1 to 6), light to dark.
# These are tuned to look like skin tones on an LED. Edit freely.
skin_colors = [
    (255, 200, 160),  # type 1: very fair
    (255, 160, 90),  # type 2: fair
    (230, 120, 40),  # type 3: medium
    (180, 80, 20),  # type 4: olive / light brown
    (110, 45, 10),  # type 5: brown
    (50, 25, 0),  # type 6: dark brown (kept bright enough to see)
]

# NEW: Bookkeeping variables for the single-press logic
button_event = False  # set to True when a fresh press is detected, cleared once handled
button_down_last = (
    False  # was the button down the last time we checked? (for edge detection)
)

# Function Section

# NEW: Returns True while the button is physically held down.
def button_is_down():
    return not button_switch.value  # pressed = pin pulled LOW


# NEW: Checks the button and records a press ONLY on the moment it goes from
# up to down. Holding the button down counts as just one press.
# The main loop has slow parts (sleeps, tone), so this gets called inside them
# too, so quick taps aren't missed.
def poll_button():
    global button_event, button_down_last
    down = button_is_down()
    if down and not button_down_last:
        button_event = True
    button_down_last = down


# NEW: Replacement for sleep() that keeps watching the button while waiting.
def wait_and_watch(seconds):
    steps = int(seconds / 0.02)
    for i in range(steps):
        poll_button()
        sleep(0.02)


# NEW: Sets the button's LED to the color for the current skin type.
def update_button_color():
    button_led[0] = skin_colors[skin_type_index]


def read_uv_index():
    # Average 10 readings to reduce noise
    total = 0
    for i in range(10):
        total = total + uv_sensor.value
        sleep(0.01)
        poll_button()  # NEW: keep watching the button during the readings
    average = total / 10  # Average of 10 near-instant readings from our uv sensor
    if debug:
        print(f"avg uv_sensor.value = {average}")
    """
        `uv_sensor.value` returns a 16-bit converted ADC value (ranging from 0-65534),
        due to `analogio.AnalogIn`'s internal implementation.

        Connecting our UV sensor to a 3.3v pad (NOT VOUT), we multiply the ADC value by
        the voltage (3.3) and divide it by the 16-bit ADC max value (2^16 = 65535) to get the
        UV sensor value back into analog volts. We multiply by 1000 to get the
        voltage as millivolts.

        @see https://docs.circuitpython.org/en/latest/shared-bindings/analogio/#analogio.AnalogIn.reference_voltage
    """
    voltage = (average * 3.3 / 65535) * 1000  # voltage from 16-bit converted ADC (mV)
    if debug:
        print(f"voltage = {voltage}mV")
    # Adjust for altitude
    return get_uv_index(voltage) * altitude_multiplier


def get_uv_index(mv):
    # Thresholds mapped directly from the Vout(mV) table in sensor specs
    if mv < 50:
        return 0
    elif mv < 227:
        return 1
    elif mv < 318:
        return 2
    elif mv < 408:
        return 3
    elif mv < 503:
        return 4
    elif mv < 606:
        return 5
    elif mv < 696:
        return 6
    elif mv < 795:
        return 7
    elif mv < 881:
        return 8
    elif mv < 976:
        return 9
    elif mv < 1079:
        return 10
    else:
        return 11  # 11+


def show_skin_type():
    # Light up one blue LED per skin type number
    cp.pixels.fill((0, 0, 0))
    cp.pixels[7] = skin_colors[skin_type_index]
    for i in range(skin_type_index + 1):
        cp.pixels[i] = (0, 0, 255)
    update_button_color()  # NEW: the button LED changes to match the new skin type
    wait_and_watch(
        1
    )  # CHANGED: was sleep(1). Same 1 second pause, but the button is still watched


def show_progress(fraction):
    # Light up LEDs as the dose gets closer to sunburn
    lit = int(fraction * 10)
    status = 0  # Status of progress of sunburn. Alarm becomes active by the time we return status = 10
    for i in range(10):
        if i < lit:
            cp.pixels[i] = (255, 150, 0)
            status = i + 1
        else:
            cp.pixels[i] = (0, 0, 0)
    return status


# NEW: Show the starting skin type color on the button right at power-up.

cp.play_file("sega-hd.wav")

for i in range(0, 10):
    cp.pixels[i] = (0, 0, 255)
    sleep(0.05)
sleep(1)

button_down_last = (
    button_is_down()
)  # NEW: start from the real state so we don't get a false press
show_skin_type()
wait_and_watch(1)

uvi = 0

dt = 0.5  # seconds per loop

acc_exp = 0
# Accumulated exposure. Once this >= 1, the user has reached time to sunburn
# MED (minimal erythemal dose) in J/m^2 for skin types 1 to 6
med_values = [200, 250, 300, 450, 600, 1000]

alarm_paused = False  # Whether alarm is paused (muted by program)
muted = False  # Whether alarm is muted BY USER

# Altitude: hardcoded for La Jolla until the altimeter arrives
altitude_m = 100  # meters above sea level (check whatismyelevation.com)
altitude_multiplier = 1 + 0.12 * (altitude_m / 1000)  # about +12% UV per 1000 m

alarm_active = False  # True while the alarm is actually sounding (on and not muted)
in_shade = None  # Whether user is in shade (UVI < 1)

time_elapsed = 0  # The amount of time (in seconds) the has passed since the start of the UV readings
time_alarm_activated = None

# Loop Section
while True:
    # NEW: Grab any press the button detected since the last loop, then clear it.
    # One press gets one job: mute if the alarm is sounding, otherwise change skin.
    ext_pressed = button_event
    button_event = False

    # CHANGED: These two lines are new. They combine the original on-board
    # buttons (A and B) with the external button, so both work.
    skin_change_requested = cp.button_a or (ext_pressed and not alarm_active)
    mute_toggled = cp.button_b or (ext_pressed and alarm_active)

    # Change skin type and restart the count
    # CHANGED: was "if cp.button_a:". Now also triggers from the external button.
    if skin_change_requested:
        skin_type_index = (skin_type_index + 1) % 6
        cp.stop_tone()
        alarm_active = False
        time_alarm_activated = None
        acc_exp = 0
        muted = False
        alarm_paused = False
        in_shade = None
        show_skin_type()
    # Mute the alarm
    # CHANGED: was "if cp.button_b:". Now also triggers from the external button
    # (only when the alarm is actively sounding).
    if mute_toggled:
        muted = not muted
        if muted:
            cp.pixels[9] = (0, 0, 255)
    # Read UV (slide switch = demo mode with simulated sun)
    if cp.switch:
        uvi = 8
    else:
        uvi = read_uv_index()  # accumulate the average of the uvi read
    # Reset the count after a long time in the shade

    # Using manufacturer error margin, check if uvi is negative
    # (more than definitiely likely in shade)
    if uvi < 1:
        in_shade = True
    else:
        if alarm_active:
            # If the user found shade then leaves the shade
            if not muted and not in_shade:
                cp.start_tone(880)
        in_shade = False
    dose = 0
    if uvi > 0:
        dose = 1 / (((0.667 * med_values[skin_type_index]) / uvi) * 60 * (1 / dt))
    if cp.switch:
        acc_exp += dose * 100  # For testing and debugging purposes only
    else:
        acc_exp += dose
    if debug:
        print(f"accumulated_exposure = {acc_exp}")
    if acc_exp < 1:
        show_progress(acc_exp)
    elif acc_exp >= 1:
        # When the dose reaches the sunburn threshold

        cp.pixels.fill((255, 0, 0))
        if muted:
            cp.pixels[9] = (0, 0, 255)
        if alarm_active:
            if muted or in_shade:
                cp.stop_tone()
            elif not muted:
                cp.start_tone(880)
        else:
            alarm_active = True
            time_alarm_activated = time_elapsed
            cp.start_tone(880)
    if debug:
        print((uvi, acc_exp, skin_type_index))
    wait_and_watch(
        dt
    )  # CHANGED: was sleep(dt). Same delay, but the button is still watched

    time_elapsed += dt
    if debug:
        print(f"time_elapsed = {time_elapsed}")
    # Reset program after certain amount of time has passed since alarm was activated
    # In seconds. The time for the program to reset (ideally, after 24 hours = 86400 seconds)
    if (time_alarm_activated is not None) and (
        (time_elapsed - time_alarm_activated) >= 86400
    ):
        cp.stop_tone()
        alarm_active = False
        time_alarm_activated = None
        acc_exp = 0
        muted = False
        alarm_paused = False
        in_shade = None
