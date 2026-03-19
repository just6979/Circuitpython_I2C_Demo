# CircuitPython I2C Demo

Demoing various I2C devices with CircuitPython.

I used an [Adafruit ESP32-S3 Reverse TFT Feather](https://www.adafruit.com/product/5691),
with a bunch of devices connected via STEMMA QT,
but it should run fine on anything that can run CircuitPython and has an I2C bus.

All the device specific sections are guarded so as to not error if they're not detected,
but I2C doesn't really handle hot-plugging, so we only do the detection at boot.
Devices can be [un]plugged at any time, but won't be read and may cause errors until a reboot.

_Note: We don't check what kind of Wii Accessory is connected, just treats it like a Nunchuck._
