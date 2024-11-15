Standalone driver for [SP0256A-AL2](http://www.bitsavers.org/components/gi/speech/General_Instrument_-_SP0256A-AL2_datasheet_(Radio_Shack_276-1784)_-_Apr1984.pdf) speech chip.

This driver consumes allophones as bytes from the serial port and echos them back once the chip has spoken them.

Typical usage:

```
echo hello world | ./text2sp0256.py | ./speaksp0256.py
```
