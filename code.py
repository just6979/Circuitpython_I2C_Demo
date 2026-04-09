import time

import board
import microcontroller
from adafruit_ble import BLERadio, Advertisement
from adafruit_ble.advertising.standard import ProvideServicesAdvertisement
from adafruit_is31fl3741 import PREFER_BUFFER
from adafruit_is31fl3741.adafruit_rgbmatrixqt import Adafruit_RGBMatrixQT
from adafruit_lsm6ds.lsm6dsox import LSM6DSOX
from adafruit_max1704x import MAX17048
from adafruit_sht4x import SHT4x
from adafruit_spa06_003 import SPA06_003
from wiichuck.nunchuk import Nunchuk

start_time = time.monotonic()

try_max1704 = True
try_sht4x = True
try_spa06_003 = True
try_is31fl3741 = True
try_nunchuck = True
try_lsm6dsox = True

MAX17048_ADDR = 0x36
SHT4X_ADDR = 0x44
SPA06_003_ADDR = 0x77
IS31FL3741_ADDR = 0x30
NUNCHUK_ADDR = 0x52
LSM6DSOX_ADDR = 0x6A

max17048 = None
sht4x = None
spa06_003 = None
is31fl3741 = None
nunchuk = None
lsm6dsox = None

try_ble = True
do_ble_scan = not True
ble = None

print(
    f'{board.board_id}: '
    f'UID 0x{microcontroller.cpu.uid.hex()}, '
    f'{microcontroller.cpu.frequency / 1000 / 1000} MHz, '
    f'{microcontroller.cpu.temperature} °C'
)
print('Starting up...')

i2c = board.I2C()
print(f'Opened I2C bus')
i2c.try_lock()
print(f'Locked I2C bus to scan for devices')
devs = [dev for dev in i2c.scan()]
hex_devs = list(map(lambda dev: hex(dev), devs))
print(f'Found {len(devs)} I2C devices: {hex_devs}')
i2c.unlock()
print('Unlocked I2C bus')

if try_max1704 and MAX17048_ADDR in devs:
    print(f'Trying MAX17048 at {MAX17048_ADDR:#x}')
    try:
        max17048 = MAX17048(i2c, MAX17048_ADDR)
        print(f'Found MAX17048 at {MAX17048_ADDR:#x}, Ver: {hex(max17048.chip_version)}, ID: {hex(max17048.chip_id)}')
    except ValueError:
        print(f'No MAX17048 found at {MAX17048_ADDR:#x}')

if try_sht4x:
    print(f'Trying SHT4x at {SHT4X_ADDR:#x}')
    try:
        sht4x = SHT4x(i2c, SHT4X_ADDR)
        print(f'Found SHT4x at {SHT4X_ADDR:#x}, ID: 0x{hex(sht4x.serial_number)}')
    except ValueError:
        print(f'No SHT4x found at {SHT4X_ADDR:#x}')

if try_spa06_003:
    print(f'Trying SPA06-003 at {SPA06_003_ADDR:#x}')
    try:
        spa06_003 = SPA06_003.over_i2c(i2c, SPA06_003_ADDR)
        print(f'Found SPA06-003 at {SPA06_003_ADDR:#x}, ID: {hex(spa06_003.chip_id)}')
    except ValueError:
        print(f'No SPA06-003 found at {SPA06_003_ADDR:#x}')

if try_is31fl3741:
    print(f'Trying IS31FL3741 at {IS31FL3741_ADDR:#x}')
    try:
        is31fl3741 = Adafruit_RGBMatrixQT(i2c, IS31FL3741_ADDR, allocate=PREFER_BUFFER)
        print(f'Found IS31FL3741 at {IS31FL3741_ADDR:#x}')
        is31fl3741.set_led_scaling(0x01)
        is31fl3741.global_current = 0xFF
        is31fl3741.enable = True
    except ValueError:
        print(f'No IS31FL3741 found at {IS31FL3741_ADDR:#x}')

if try_nunchuck:
    print(f'Trying Nunchuck at {NUNCHUK_ADDR:#x}')
    try:
        nunchuk = Nunchuk(i2c, NUNCHUK_ADDR)
        print(f'Found Wii Nunchuck at {NUNCHUK_ADDR:#x}')
    except ValueError:
        print(f'No Wii Nunchuck found at {NUNCHUK_ADDR:#x}')

if try_lsm6dsox and LSM6DSOX_ADDR in devs:
    print(f'Trying LSM6DS at {LSM6DSOX_ADDR:#x}')
    try:
        lsm6dsox = LSM6DSOX(i2c, LSM6DSOX_ADDR)
        print(f'Found LSM6DS at {LSM6DSOX_ADDR:#x}, ID: {lsm6dsox.CHIP_ID}')
    except ValueError:
        print(f'No LSM6DS found at {LSM6DSOX_ADDR:#x}')

if try_ble:
    try:
        ble = BLERadio()
        print(f'Enabling BLE radio: {ble.name}')
    except:
        print('No BLE radio found')

# check the environment every 5 seconds
ENV_READ_DELAY = 5
last_env_read = 0

# update dispays at 60Hz
DISPLAY_UPDATE_DELAY = 0.016
last_display_update = 0

# read nunchucks at 500Hz
WII_READ_DELAY = 0.002
last_wii_read = 0

ble_scanning = False
found = set()
responses = set()

jx = jy = 127
ax = ay = az = 0
jz = jc = False

pixel_x = 6
pixel_y = 4
old_x = old_y = 0

print(f'Setup complete: {time.monotonic() - start_time}s')

while True:
    now = time.monotonic()

    if now - last_env_read >= ENV_READ_DELAY:
        last_env_read = now

        print(f'{now:.3f}s: MCU Temp: {microcontroller.cpu.temperature} °C', end='')

        if max17048:
            max17048.wake()
            print(f', Battery: {max17048.cell_voltage:.2f} V {max17048.cell_percent:.1f}%')
            max17048.hibernate()
        else:
            print()

        if sht4x and spa06_003:
            if spa06_003.temperature_data_ready and spa06_003.pressure_data_ready:
                sht_temp, sht_humidity = sht4x.measurements
                print(f'{now:.3f}s: SHT4x: {sht_temp:.1f} °C, SPA06: {spa06_003.temperature:.1f} °C')
                avg_temp = (sht_temp + spa06_003.temperature) / 2.0
                print(
                    f'{now:.3f}s: {avg_temp:.1f}°C, {avg_temp * (9 / 5) + 32:.1f}°F, '
                    f'{sht_humidity:.0f} %RH, {spa06_003.pressure} hPa'
                )
            else:
                print(f'{now:.3f}s: SPA06 not ready, showing only SHT41 data')
                sht_temp, sht_humidity = sht4x.measurements
                print(f'{now:.3f}s: {sht_temp:.1f}°C, {sht_temp * (9 / 5) + 32:.1f}°F, {sht_humidity:.0f} %RH')

    if nunchuk:
        if now - last_wii_read >= WII_READ_DELAY:
            last_wii_read = now
            jx, jy = nunchuk.joystick
            ax, ay, az = nunchuk.acceleration
            bc, bz = nunchuk.buttons
            print(
                f'{now:.3f}s: '
                f'[{'Z' if bz else ' '}{'C' if bc else ' '}] '
                f'J {jx:>3},{jy:>3} '
                f'A {ax:>3},{ay:>3},{az:>3}',
            )

    if now - last_display_update >= DISPLAY_UPDATE_DELAY:
        if is31fl3741 and nunchuk:
            last_display_update = now
            old_x = pixel_x
            old_y = pixel_y
            pixel_x = (12 * (jx - 127) // 255) + 6
            pixel_y = -(8 * (jy - 127) // 255) + 4
            print(f'[{pixel_x}, {pixel_y}]')
            is31fl3741.pixel(old_x, old_y, 0x000000)
            is31fl3741.pixel(pixel_x, pixel_y, 0xFFFFFF)
            is31fl3741.show()

        if lsm6dsox:
            print("AX:% 3.2f AY: % 3.2f AZ: % 3.2f m/s^2, " % lsm6dsox.acceleration, end='')
            print("GX:% 3.2f GY: % 3.2f GZ: % 3.2F °/s" % lsm6dsox.gyro)

    if ble and do_ble_scan and not ble_scanning:
        ble_scanning = True
        print(f'{now}s: Scanning BLE')
        scan_start_time = time.monotonic()
        for advert in ble.start_scan(ProvideServicesAdvertisement, Advertisement,
                                     buffer_size=2048, extended=True, timeout=5):
            addr = advert.address
            if advert.scan_response and addr not in responses:
                responses.add(addr)
            elif not advert.scan_response and addr not in found:
                found.add(addr)
            else:
                continue
            # data = advert.data_dict
            # switchbot_macs = ["e5:90:03:06:15:2f", "e8:76:c6:46:43:15"]
            # mac = addr.address_bytes.hex(':')
            # if mac in switchbot_macs:
            #     print(mac, end=' ')
            #     print("SwitchBot")
            #     for (key, val) in data.items():
            #         if key == 1:
            #             continue
            #         string_val = ''
            #         for c in val:
            #             string_val += f'{c} '
            #         print(f'{key}: {string_val}')
        # print(responses)
        # print(found)
        ble_scanning = False
