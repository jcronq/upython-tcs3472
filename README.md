# TCS34725 - Color Temperature Sensor

## SETUP

Add yourself to the dialout group.
```bash
sudo usermod -a -G dialout <username>
```

Install the required dependencies.
```
sudo apt install picocom
pip install -r requirements.txt
```

## Flash the ESP32
Flashing the ESP32 with microPython only needs to be done once.
```bash
make flash
```

## Connecting to Serial Port
Install picocom to communicate over UART channel.
```bash
sudo apt install picocom
```

Then you can connect with the following
```bash
picocom /dev/ttyUSB0 -b115200
```
or
```bash
make connect
```

To end the picocom session: hold [ctrl] and press [a] then [q] without releasing [ctrl].

## Adding the code to the ESP32

```bash
make install
```


TODO: 
* Callibrate CT sensor to CT values produced by HUE White-Ambiance/Color bulbs
