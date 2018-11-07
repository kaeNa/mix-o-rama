Mix-o-Rama
---
 
A cocktail bartender robot project.

[![Mix-o-Rama User Experience video](https://i.vimeocdn.com/video/737658893.jpg)](https://vimeo.com/299511946 "Mix-o-Rama User Experience video - Click to Watch!") 

Implementation notes
---
A compressor is used to push the liquid out of bottles by pressurizing them, individually opening corresponding solenoid valves.

Liquid in the glass is then measured by setting up digital scales under the glass table.

The system is managed by a Raspberry PI Zero W running a Python Kivy GUI, which is controlling the valves via GPIO-connected relay modules, and reading the scales from a serial port, which is driven by a small Arduino. 
HX711 scales have a very time sensitive protocol, that is impossible to bit-bang with RPi's user-space software as GPIO on/off has jitter to the tune of 500us)


Materials
---
See [BOM](https://github.com/synchrone/mix-o-rama/raw/master/docs/bom.ods)
