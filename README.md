# TCS34725 - Color Temperature Sensor
The TCS34725 is an RGB sensor.  I've connected it to an ESP32 and perform some mild processing to extract color temperature data as well.

The interface file in rgb_sensor/src/rgb_sensor_tcs34725 is a complete implementation of the chips capabilities.

The controller has implemented an auto-focus for the chips exposure and gain settings.

These are likely the most useful parts of the project for anyone that has stumbled their way here.

## SETUP

Add yourself to the dialout group.
```bash
sudo usermod -a -G dialout <username>
```

Install the required dependencies.
```
sudo apt install picocom
pip install -r dev-requirements.txt
```

## Flash the ESP32
Flashing the ESP32 with microPython only needs to be done once.
```bash
make flash
```

## Connecting to Serial Port
Connect using rbash:
```bash
make connect
```

Or connect directly to the REPL:
```bash
make connect-repl
```

To end the picocom session: hold [ctrl] and press [a] then [q] without releasing [ctrl].

## Adding the code to the ESP32

```bash
make install
```
