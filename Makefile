flash:
	esptool.py --port /dev/ttyUSB0 erase_flash
	esptool.py --chip esp32 --port /dev/ttyUSB0 write_flash -z 0x1000 ./esp32_binaries/esp32-idf4-20210202-v1.14.bin

connect-repl:
	picocom /dev/ttyUSB0 -b115200

connect:
	rshell -p /dev/ttyUSB0

install: flash
	rshell -p /dev/ttyUSB0 -f scripts/install.rsh
