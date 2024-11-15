#!/usr/bin/env python

import serial
import sys
import time

PORT = "/dev/ttyACM0"
SPEED = 115200


class Speaker:
    def __init__(self):
        self.port = serial.Serial(PORT, SPEED, timeout=0.001)
        self.port.reset_input_buffer()
        self.wakeup()

    def wakeup(self):
        while len(self.port.read(1)):
            pass

        while True:
            self.port.write(bytes([0]))
            if self.port.read(1) == b"\x00":
                break

        while len(self.port.read(1)):
            pass

    def readwait(self, a):
        while True:
            c = self.port.read(1)
            if len(c) and c == a:
                return

    def speak(self, data):
        for b in data:
            b = bytes([b])
            self.port.write(b)
            self.port.flush()
            self.readwait(b)


speaker = Speaker()

while True:
    data = sys.stdin.buffer.read()
    if not data:
        break
    speaker.speak(data)
