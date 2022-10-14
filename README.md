# ForceESP

A dynamic force measurement solution, build to evaluate climbing performance and inform training.

## Operating Principle
Force is transduced to voltage by a wheatstone bridge load cell, values are digitalized with a HX711 analog-digital-converter. A ESP32 Microcontroller reads the HX711 values, converts to weights and recieves commands/transmits data via Bluetooth Low Energy (BLE)

A PC client controls measuring and stores, organizes and visualizes the resulting data.

## Hardware

* Elseif ESP32 Microcontroller Dev board
* status LEDs
* HX711 amplifier/adc
* S-load cell (YZC-516C 500kg, but any other with the right range should work)

TODO: Circuit diagramm, pretty self-expanitory though

## Software

### ESP Firmare

Written in C++ for PlatformIO. Use PlatformIO ([documentation](https://docs.platformio.org/en/latest/)) to install dependencies and set up the serial bus connection to an ESP32 board.

### Client

Written in python. Use

```$ pip install -r requirements.txt``` to install Python dependencies

Also requires a bash shell and gnuplot ([documentation](http://www.gnuplot.info/documentation.html)) for data visualization. (Hopefully to be replaced by GUI)

## TODO

* Calibration, functions to set do exist but is currently hard-coded
* GUI (current plan: a simple web-stack based gui using eel)
