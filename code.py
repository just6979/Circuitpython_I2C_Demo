# SPDX-FileCopyrightText: Copyright (c) 2020 ladyada for Adafruit Industries
#
# SPDX-License-Identifier: MIT

import time

import board
from rainbowio import colorwheel

import adafruit_sht4x
from adafruit_spa06_003 import SPA06_003
import adafruit_is31fl3741
from adafruit_is31fl3741.adafruit_rgbmatrixqt import Adafruit_RGBMatrixQT


i2c = board.I2C()  # uses board.SCL and board.SDA
# i2c = board.STEMMA_I2C()  # For using the built-in STEMMA QT connector on a microcontroller
sht = adafruit_sht4x.SHT4x(i2c)
print("Found SHT4x with serial number", hex(sht.serial_number))

sht.mode = adafruit_sht4x.Mode.NOHEAT_HIGHPRECISION
# Can also set the mode to enable heater
# sht.mode = adafruit_sht4x.Mode.LOWHEAT_100MS
print("Current mode is: ", adafruit_sht4x.Mode.string[sht.mode])

# Initialize with default I2C Address
spa = SPA06_003.over_i2c(i2c)

# Initialize with alternate I2C Address
# from adafruit_spa06_003 import SPA06_003_ALTERNATE_ADDR
# spa = SPA06_003.over_i2c(i2c, address=SPA06_003_ALTERNATE_ADDR)


i2c = board.I2C()  # uses board.SCL and board.SDA
# i2c = board.STEMMA_I2C()  # For using the built-in STEMMA QT connector on a microcontroller
is31 = Adafruit_RGBMatrixQT(i2c, allocate=adafruit_is31fl3741.PREFER_BUFFER)
is31.set_led_scaling(0x11)
is31.global_current = 0x11
# print("Global current is: ", is31.global_current)
is31.enable = True
# print("Enabled? ", is31.enable)

wheeloffset = 0
while True:
    temperature, relative_humidity = sht.measurements
    print("Temperature: %0.1f C" % temperature)
    print("Humidity: %0.1f %%" % relative_humidity)
    print("")

    if spa.temperature_data_ready and spa.pressure_data_ready:
        print(f"Temperature: {spa.temperature} °C", end="   ")
        print(f"Pressure: {spa.pressure}  hPa")

    for pixel in range(351):
        is31[pixel] = 255
        time.sleep(0.01)
        is31[pixel] = 0

    time.sleep(1.0)

    for y in range(9):
        for x in range(13):
            is31.pixel(x, y, colorwheel((y * 13 + x) * 2 + wheeloffset))
    wheeloffset += 1
    is31.show()
