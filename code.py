# SPDX-FileCopyrightText: 2017 Scott Shawcroft, written for Adafruit Industries
# SPDX-FileCopyrightText: Copyright (c) 2022 ladyada for Adafruit Industries
#
# SPDX-License-Identifier: Unlicense

import busio
import digitalio
import board
from lcd.lcd import LCD
from lcd.i2c_pcf8574_interface import I2CPCF8574Interface

from lcd.lcd import CursorMode

print("I2C LCD test - v5")

i2c = busio.I2C(board.GP5, board.GP4)
lcd = LCD(I2CPCF8574Interface(i2c, 0x27), num_rows=4, num_cols=20)
lcd.set_backlight(True)

# Initialize 8 switch inputs with pull-ups
switches = [
    digitalio.DigitalInOut(board.GP0),
    digitalio.DigitalInOut(board.GP1),
    digitalio.DigitalInOut(board.GP2),
    digitalio.DigitalInOut(board.GP3),
    digitalio.DigitalInOut(board.GP6),
    digitalio.DigitalInOut(board.GP7),
    digitalio.DigitalInOut(board.GP8),
    digitalio.DigitalInOut(board.GP9),
]

for switch in switches:
    switch.direction = digitalio.Direction.INPUT
    switch.pull = digitalio.Pull.UP

# Scan and print the address of all I2C devices
# while not i2c.try_lock():
#    pass
# try:
#    for address in i2c.scan():
#        print(f"I2C device found at address {address:02X}")
# finally:
#    i2c.unlock()

smiley = bytearray(
    [
        0b00000,
        0b01010,
        0b01010,
        0b00000,
        0b10001,
        0b10001,
        0b01110,
        0b00000,
    ]
)

barn_left = bytearray(
    [
        0b0001,
        0b0010,
        0b0100,
        0b1010,
        0b0101,
        0b0100,
        0b0100,
        0b0011,
    ]
)

barn_right = bytearray(
    [
        0b1000,
        0b0100,
        0b0010,
        0b0101,
        0b1010,
        0b0010,
        0b0010,
        0b1100,
    ]
)
lcd.create_char(5, smiley)
lcd.create_char(6, barn_left)
lcd.create_char(7, barn_right)


def clear():
    lcd.clear()
    lcd.set_cursor_pos(0, 9)
    lcd.print(chr(6))
    lcd.set_cursor_pos(0, 10)
    lcd.print(chr(7))
    lcd.set_cursor_pos(1, 0)


old = [False] * 8
clear()
row = 0
while True:
    switch_states = [not switch.value for switch in switches]
    if switch_states != old:
        print([str(state) for state in switch_states])
        old = switch_states
        lcd.set_cursor_pos(0, 0)
        lcd.print(["+" if state else "-" for state in switch_states])
        lcd.set_cursor_pos(row, 12)
        lcd.print(["+" if state else "-" for state in old])
        row += 1
        if row > 3:
            row = 0
