# SPDX-FileCopyrightText: Copyright (c) 2020 ladyada for Adafruit Industries
#
# SPDX-License-Identifier: MIT

import time

import adafruit_is31fl3741
import adafruit_max1704x
import adafruit_sht4x
import board
import busio
import microcontroller
from adafruit_is31fl3741.adafruit_rgbmatrixqt import Adafruit_RGBMatrixQT
from adafruit_spa06_003 import SPA06_003
from rainbowio import colorwheel

# pause to let serial connect
time.sleep(2)
print(
    f'MCU: '
    f'UID 0x{microcontroller.cpu.uid.hex()}, '
    f'{microcontroller.cpu.frequency / 1000 / 1000} MHz, '
    f'{microcontroller.cpu.temperature} °C'
)

i2c_clock_options = {
    'Standard': 100_000,
    'Fast': 400_000,
    'Fast2': 800_000,
    'Fast Plus': 1_000_000,
    'High Speed': 1_700_000,
    'High Speed Plus': 3_400_000,
    'Ultra Fast': 5_000_000
}
i2c_clock = i2c_clock_options['Fast']
i2c = busio.I2C(board.SCL, board.SDA, frequency=i2c_clock)
print(f'Opened I2C bus at {i2c_clock // 1000}KHz')
i2c.try_lock()
devs = [hex(dev) for dev in i2c.scan()]
print(f'Found {len(devs)} I2C devices: {devs}')
i2c.unlock()

max17_addr = 0x36
max17 = adafruit_max1704x.MAX17048(i2c, max17_addr)
print(f'Found MAX1704x at {max17_addr:#x}, Ver: {hex(max17.chip_version)}, ID: {hex(max17.chip_id)}')

sht41_addr = 0x44
sht41 = adafruit_sht4x.SHT4x(i2c, sht41_addr)
print(f'Found SHT41 at {sht41_addr:#x}, ID: 0x{hex(sht41.serial_number)}')

spa06_addr = 0x77
spa06 = SPA06_003.over_i2c(i2c, spa06_addr)
print(f'Found SPA06-003 at {spa06_addr:#x}, ID: {hex(spa06.chip_id)}')

is31_addr = 0x30
is31 = Adafruit_RGBMatrixQT(i2c, is31_addr, allocate=adafruit_is31fl3741.PREFER_BUFFER)
print(f'Found IS31FL3741 at {is31_addr:#x}')
is31.set_led_scaling(0x01)
is31.global_current = 0xFF

print('Warming up devices')
time.sleep(1)

is31.enable = True

env_read_delay = 2
last_env_read = 0
wheeloffset = 0

while True:
    now = time.monotonic()

    if now - last_env_read >= env_read_delay:
        max17.wake()
        print(f'{max17.cell_voltage:.2f} Volts, {max17.cell_percent:.1f} %')
        max17.hibernate()

        if spa06.temperature_data_ready and spa06.pressure_data_ready:
            sht_temp, sht_humidity = sht41.measurements
            # print(f'SHT4x: {sht_temp:.1f} °C, SPA06: {spa.temperature:.1f} °C')
            avg_temp = (sht_temp + spa06.temperature) / 2.0
            print(
                f'{avg_temp:.1f}°C, '
                f'{avg_temp * (9 / 5) + 32:.1f}°F, '
                f'{sht_humidity:.0f} %RH, '
                f'{spa06.pressure} hPa'
            )
        else:
            print(f'SPA06 not ready, showing only SHT41 data')
            sht_temp, sht_humidity = sht41.measurements
            print(
                f'{sht_temp:.1f}°C, '
                f'{sht_temp * (9 / 5) + 32:.1f}°F, '
                f'{sht_humidity:.0f} %RH, '
            )

        last_env_read = now

    for y in range(9):
        for x in range(13):
            is31.pixel(x, y, colorwheel((y * 13 + x) * 2 + wheeloffset))
    wheeloffset += 1
    is31.show()

    # time.sleep(0.00001)
