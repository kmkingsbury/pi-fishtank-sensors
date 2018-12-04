# pi-fishtank-sensors
Code for collection sensor information from a pi on the outdoor Koi fish tank.


Currently a 1-wire temperature sensor hooked up.

Hardware Setup:
Waterproof DS18B20 Digital temperature 
https://www.adafruit.com/product/381

Wires:
Red - 3v3 pin 1.
Blue - Ground pin 6
Yellow - GPIO17 (pin 11)


Edit the /boot/config.txt
Near/At the bottom add/edit the dtoverlay line.
``` 
dtoverlay=w1-gpio,gpiopin=17
```

Name | Description
-----|------------
`1-wire.py` | Script for recording temperature
`config.yml` | Config file
`fishtank.sql` | Database Schema
`README.md` | This file
`monit-1-wire` | Configuration file for monitoring the script with Monit

