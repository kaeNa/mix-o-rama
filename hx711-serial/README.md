# Rationale
Since RaspberryPi has a lot of jitter when setting the GPIO, and GPCLK0 / PWM is not useful for HX711 protocol, I am going to have to use a realtime chip to convert those values to serial text protocol, and read that from python

# Dependencies
https://github.com/olkal/HX711_ADC/archive/v1.0.2.zip

# Usage
Flash hx711-serial.ino onto an Arduino Leonardo-like board, and connect:
* Arduino's D10 to HX711 DT
* Arduino's D11 to HX711 SCK

