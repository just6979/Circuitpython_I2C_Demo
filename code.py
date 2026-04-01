import time

import board
import busio
import microcontroller
from adafruit_is31fl3741 import PREFER_BUFFER
from adafruit_is31fl3741.adafruit_rgbmatrixqt import Adafruit_RGBMatrixQT
from adafruit_max1704x import MAX17048
from adafruit_sht4x import SHT4x
from adafruit_spa06_003 import SPA06_003
from wiichuck.nunchuk import Nunchuk

try_max1704 = True
try_sht4x = not True
try_spa06_003 = not True
try_nunchuck = not True
try_is31fl3741 = not True

max17048_addr = 0x36
sht4x_addr = 0x44
spa06_003_addr = 0x77
is31fl3741_addr = 0x30
nunchuk_addr = 0x52

max17048 = None
sht4x = None
spa06_003 = None
is31fl3741 = None
nunchuk = None

# pause to let serial connect
time.sleep(2)

print(
    f'{board.board_id}: '
    f'UID 0x{microcontroller.cpu.uid.hex()}, '
    f'{microcontroller.cpu.frequency / 1000 / 1000} MHz, '
    f'{microcontroller.cpu.temperature} °C'
)
print('Setting up...')

i2c_clock_options = {
    'Standard': 100_000,
    'Fast': 400_000,
    'Fast2': 800_000,
    'Fast Plus': 1_000_000,
    'High Speed': 1_700_000,
    'High Speed Plus': 3_400_000,
    'Ultra Fast': 5_000_000
}
# The ESP32-S3 and all the devices on test here seem to handle Fast Plus just fine
# Scan works on High Speed, but it freezes when trying to access any of the devices
i2c_clock = i2c_clock_options['Fast']
i2c = busio.I2C(board.SCL, board.SDA, frequency=i2c_clock)
print(f'Opened I2C bus at {i2c_clock // 1000}KHz')
i2c.try_lock()
print(f'Locked I2C bus to scan for devices')
devs = [hex(dev) for dev in i2c.scan()]
print(f'Found {len(devs)} I2C devices: {devs}')
i2c.unlock()
print('Unlocked I2C bus')

if try_max1704:
    print(f'Trying MAX17048 at {max17048_addr:#x}')
    max17048 = MAX17048(i2c, max17048_addr)
    print(f'Found MAX17048 at {max17048_addr:#x}, Ver: {hex(max17048.chip_version)}, ID: {hex(max17048.chip_id)}')

if try_sht4x:
    print(f'Trying SHT4x at {sht4x_addr:#x}')
    try:
        sht4x = SHT4x(i2c, sht4x_addr)
        print(f'Found SHT4x at {sht4x_addr:#x}, ID: 0x{hex(sht4x.serial_number)}')
    except ValueError:
        print(f'No SHT4x found at {sht4x_addr:#x}')

if try_spa06_003:
    print(f'Trying SPA06-003 at {spa06_003_addr:#x}')
    try:
        spa06_003 = SPA06_003.over_i2c(i2c, spa06_003_addr)
        print(f'Found SPA06-003 at {spa06_003_addr:#x}, ID: {hex(spa06_003.chip_id)}')
    except ValueError:
        print(f'No SPA06-003 found at {spa06_003_addr:#x}')

if try_is31fl3741:
    print(f'Trying IS31FL3741 at {is31fl3741_addr:#x}')
    try:
        is31fl3741 = Adafruit_RGBMatrixQT(i2c, is31fl3741_addr, allocate=PREFER_BUFFER)
        print(f'Found IS31FL3741 at {is31fl3741_addr:#x}')
        is31fl3741.set_led_scaling(0x01)
        is31fl3741.global_current = 0xFF
    except ValueError:
        print(f'No IS31FL3741 found at {is31fl3741_addr:#x}')
if is31fl3741: is31fl3741.enable = True

if try_nunchuck:
    print(f'Trying Nunchuck at {nunchuk_addr:#x}')
    try:
        nunchuk = Nunchuk(i2c, nunchuk_addr)
        print(f'Found Wii Nunchuck at {nunchuk_addr:#x}')
    except ValueError:
        print(f'No Wii Nunchuck found at {nunchuk_addr:#x}')

print('Warming up devices')
time.sleep(1)

# check the environment every 5 seconds
env_read_delay = 10
last_env_read = 0

# update the led matrix at 60Hz
led_update_delay = 0.016
last_led_update = 0
wheel_offset = 0

# read nunchucks at 500Hz
wii_read_delay = 0.002
last_wii_read = 0

jx = jy = 127
ax = ay = az = 0
jz = jc = False

pixel_x = 6
pixel_y = 4
old_x = old_y = 0

print('Starting')

while True:
    now = time.monotonic()

    if now - last_env_read >= env_read_delay:
        last_env_read = now

        print(f'{now}s: MCU Temp: {microcontroller.cpu.temperature} °C')

        if max17048:
            max17048.wake()
            print(f'{now}s: {max17048.cell_voltage:.2f} V, {max17048.cell_percent:.1f}%')
            max17048.hibernate()

        if sht4x and spa06_003:
            if spa06_003.temperature_data_ready and spa06_003.pressure_data_ready:
                sht_temp, sht_humidity = sht4x.measurements
                # print(f'SHT4x: {sht_temp:.1f} °C, SPA06: {spa.temperature:.1f} °C')
                avg_temp = (sht_temp + spa06_003.temperature) / 2.0
                print(
                    f'{avg_temp:.1f}°C, '
                    f'{avg_temp * (9 / 5) + 32:.1f}°F, '
                    f'{sht_humidity:.0f} %RH, '
                    f'{spa06_003.pressure} hPa'
                )
            else:
                print(f'SPA06 not ready, showing only SHT41 data')
                sht_temp, sht_humidity = sht4x.measurements
                print(
                    f'{sht_temp:.1f}°C, '
                    f'{sht_temp * (9 / 5) + 32:.1f}°F, '
                    f'{sht_humidity:.0f} %RH, '
                )

    if nunchuk:
        if now - last_wii_read >= wii_read_delay:
            last_wii_read = now
            jx, jy = nunchuk.joystick
            ax, ay, az = nunchuk.acceleration
            bc, bz = nunchuk.buttons
            print(f'J[{jx:>3},{jy:>3}] A[{ax:>3},{ay:>3},{az:>3}] [{'Z' if bz else ' '}{'C' if bc else ' '}]')

    if is31fl3741 and nunchuk:
        if now - last_led_update >= led_update_delay:
            last_led_update = now
            old_x = pixel_x
            old_y = pixel_y
            pixel_x = (12 * (jx - 127) // 255) + 6
            pixel_y = -(8 * (jy - 127) // 255) + 4
            print(f'[{pixel_x}, {pixel_y}]')
            is31fl3741.pixel(old_x, old_y, 0x000000)
            is31fl3741.pixel(pixel_x, pixel_y, 0xFFFFFF)
            is31fl3741.show()
