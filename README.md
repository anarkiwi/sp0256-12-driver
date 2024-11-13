Standalone driver for [SP0256](http://www.bitsavers.org/components/gi/speech/General_Instrument_-_SP0256A-AL2_datasheet_(Radio_Shack_276-1784)_-_Apr1984.pdf) speech chip.

This driver consumes allophones as bytes from the serial port and echos them back once the chip has spoken them.

Typical usage:

```
#!/usr/bin/env python

import serial
import time

PORT = "/dev/ttyACM0"
SPEED = 115200
s = serial.Serial(PORT, SPEED, timeout=0.001)
s.reset_input_buffer()

def readwait():
  while len(s.read(1)):
    continue

readwait()

for i in range(10):
  s.write([0x10, 0x07, 0x07, 0x2d, 0x1a, 0x0b, 0x13, 0x02])
  readwait()
  time.sleep(1)
```

Regular text can be converted to allophones [algorithmically](https://github.com/greg-kennedy/p5-NRL-TextToPhoneme)
