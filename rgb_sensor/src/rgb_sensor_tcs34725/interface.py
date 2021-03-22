# -*- coding: utf-8 -*-
"""
Light Sensor TCS34725
Adafruit RGB Color Sensor
DataSheet: https://cdn-shop.adafruit.com/datasheets/TCS34725.pdf
C Example: https://github.com/adafruit/Adafruit_TCS34725/

@author: jcron
"""
from machine import Pin, I2C
import time
import _thread

HARDWARE_I2C = 1

class Interface:
    i2c_freq = 9600

    LED_PIN = 13
    SCL_PIN = 22
    SDA_PIN = 21
    INTERUPT_PIN = 23

    ADDR_ENABLE_REG = 0x00
    ENABLE_POWER_BIT = 0x01
    ENABLE_RGBC_BIT  = 0x02
    ENABLE_WAIT_BETWEEN_INTEGRATIONS = 0x08
    ENABLE_CLEAR_INTERRUPT_BIT = 0x010

    ADDR_RGBC_INTEGRATION_TIME = 0x01
    INTEGRATIONTIME_2_4MS = 0xFF # <  2.4ms - 1 cycle    - Max Count: 1024 
    INTEGRATIONTIME_24MS  = 0xF6 # <  24ms  - 10 cycles  - Max Count: 10240
    INTEGRATIONTIME_50MS  = 0xEB # <  50ms  - 20 cycles  - Max Count: 20480
    INTEGRATIONTIME_101MS = 0xD5 # <  101ms - 42 cycles  - Max Count: 43008
    INTEGRATIONTIME_154MS = 0xC0 # <  154ms - 64 cycles  - Max Count: 65535
    INTEGRATIONTIME_700MS = 0x00 # <  700ms - 256 cycles - Max Count: 65535

    ADDR_WAIT_TIME_REG = 0x03

    GAIN_1X  = 0x00 #  No gain
    GAIN_4X  = 0x01 #  4x gain  
    GAIN_16X = 0x02 # 16x gain 
    GAIN_60X = 0x03 # 60x gain 

    ADDR_INTERRUPT_THRESHOLD_LOW      = 0x04
    ADDR_INTERRUPT_THRESHOLD_HIGH     = 0x06
    ADDR_INTERRUPT_PERSISTANCE_FILTER = 0x0C

    ADDR_WAIT_CONFIGURATION_REGISTER = 0x0D
    LONG_WAIT_BIT = 0x02

    ADDR_CONTROL_REG = 0x0F
    GAIN_VALUES = {
        "x1":  0x00,
        "x4":  0x01,
        "x16": 0x02,
        "x60": 0x03,
    }

    ADDR_DEVICE_ID  = 0x12
    ADDR_STATUS_REG = 0x13
    STATUS_INTEGRATION_VALID_BIT   = 0x01
    STATUS_CLEAR_CHANNEL_INTERRUPT = 0x10

    ADDR_DATA_READ_BYTE_CLEAR = 0x14
    ADDR_DATA_READ_BYTE_RED   = 0x16
    ADDR_DATA_READ_BYTE_GREEN = 0x18
    ADDR_DATA_READ_BYTE_BLUE  = 0x1A
    
    TIME_ONE_CYCLE = 2.4 # milliseconds
    LONG_WAIT_MULTIPLIER = 12

    DELAY_MAP = {
            0xFF: 0.003,
            0xF6: 0.024,
            0xEB: 0.050,
            0xD5: 0.101,
            0xC0: 0.154,
            0x00: 0.700
        }

    COMMAND_BIT    = 0x80
    COMMAND_SPECIAL_FUNCTION = 0x60
    COMMAND_AUTO_INCREMENT = 0x20
    COMMAND_CLEAR_INTERRUPT = 0x06

    #Derived weighting from documentation's sensitivity graph
    redWeight   = {'r': 0.7532235049919056,  'g': 0.14084511600247626, 'b': 0.1059313790056181}
    greenWeight = {'r': 0.06758290205201241, 'g': 0.6661713652167925,  'b': 0.26624573273119495}
    blueWeight  = {'r': 0.05098020440153231, 'g': 0.18708423930505969, 'b': 0.761935556293408}
    irWeight    = {'r': 0.3741264427999289,  'g': 0.3126542645036191,  'b': 0.31321929269645193}

    def __init__(self):
        self._last_read = None

        # Initialize pins
        self._led_pin = Pin(self.LED_PIN, Pin.OUT)
        self._interrupt_pin = Pin(self.INTERRUPT_PIN, Pin.IN, Pin.PULL_UP)
        self._interrupt_pin.irq(trigger=Pin.IRQ_FALLING, handler=self.get_clear_interrupt_handler)
        self._interrupt_callbacks = []
        self.i2c = I2C(HARDWARE_I2C, scl = Pin(self.SCL_PIN), sda=Pin(self.SDA_PIN), freq=9600)
        self.i2c_addr = self.i2c.scan()[0]

    def register_interrupt_callback(self, callback):
        self._interrupt_callbacks.append(callback)

    def get_clear_interrupt_handler(self):
        def clear_interrupt_handler():
            print("Intterrupt Triggered")
            for callback in self._interrupt_callbacks:
                callback()

        return clear_interrupt_handler


    def wait_for_integration_complete(self):
        now = time.time()
        time_since_last_read = now - self._last_read
        integration_delay = self.DELAY_MAP[self._integration_time]
        if time_since_last_read < integration_delay
            time.sleep(integration_delay - time_since_last_read + self.CLOCK_TIME)

        integration_complete = False
        while not integration_complete
            status = self.read8(self.ADDR_STATUS_REG)
            clear_interrupt_set = bool(status & self.STATUS_CLEAR_CHANNEL_INTERRUPT)
            integration_complete = bool(status & self.STATUS_INTEGRATION_VALID_BIT)
            if not integration_complete:
                time.sleep(self.CLOCK_TIME)

    # Lowest Level Communications
    def read8(self, addr=None):
        if addr is not None:
            self.i2c.writeto(self.i2c_addr, (self.COMMAND_BIT | self.COMMAND_AUTO_INCREMENT | addr).to_bytes(1, 'big'))

        return int.from_bytes(self.i2c.readfrom(self.i2c_addr, 1), 'big')

    def read16(self, low_addr=None):
        if low_addr is not None:
            self.i2c.writeto(self.i2c_addr, (self.COMMAND_BIT | self.COMMAND_AUTO_INCREMENT | low_addr).to_bytes(1, 'big'))

        low_byte  = int.from_bytes(self.i2c.readfrom(self.i2c_addr, 1), 'big')
        high_byte = int.from_bytes(self.i2c.readfrom(self.i2c_addr, 1), 'big')
        full_res = (high_byte << 8) | low_byte
        return full_res

    def write8(self, addr, data):
        self.i2c.writeto(self.i2c_addr, (self.COMMAND_BIT | addr).to_bytes(1, 'big'))
        self.i2c.writeto(self.i2c_addr, (data & 0xFF).to_bytes(1, 'big'))

    def write16(self, low_addr, data):
        data_low_filter  = 0x00FF
        self.i2c.writeto(self.i2c_addr, (self.COMMAND_BIT | self.COMMAND_AUTO_INCREMENT | low_addr).to_bytes(1, 'big'))
        self.i2c.writeto(self.i2c_addr, (data_low_filter & data).to_bytes(1, 'big'))
        self.i2c.writeto(self.i2c_addr, (data >> 8).to_bytes(1, 'big'))

    def clear_interrupt(self):
        self.i2c.writeto(self.i2c_addr, (self.COMMAND_BIT | self.COMMAND_SPECIAL_FUNCTION | self.COMMAND_CLEAR_INTERRUPT).to_bytes(1, 'big'))

    # State
    @property
    def rgbc(self):
        # dev_id & status, c, r, g, b are in sequential registers. 
        # can read them all at once becase we are using sequential read option in read16
        status = self.read8(self.ADDR_STATUS_REG)
        clear  = self.read16()
        red    = self.read16()
        green  = self.read16()
        blue   = self.read16()

        adc_valid       = deviceid_and_status & STATUS_INTEGRATION_VALID_BIT
        clear_interrupt = deviceid_and_status & STATUS_CLEAR_CHANNEL_INTERRUPT
        self._last_read = time.time()
        return {
            "clear_interrupt": clear_interrupt,
            "adc_valid": adc_valid,
            "r": red, "g": green, "b": blue, "c": clear
        }

    @property
    def led_state(self):
        return self._led_pin.value()

    @property
    def is_enabled(self):
        return bool(self.read8(self.ADDR_ENABLE_REG) & self.ENABLE_POWER_BIT & self.ENABLE_RGBC_BIT)
    
    @property
    def is_power_on(self):
        return bool(self.read8(self.ADDR_ENABLE_REG) & self.ENABLE_POWER_BIT)

    @property
    def is_adc_enabled(self):
        return bool(self.read8(self.ADDR_ENABLE_REG) & self.ENABLE_RGBC_BIT)

    @property
    def is_wait_between_integration_enabled(self):
        return bool(self.read8(self.ADDR_ENABLE_REG) & self.ENABLE_WAIT_BETWEEN_INTEGRATIONS)

    @property
    def is_interrupt_enabled(self):
        return bool(self.read8(self.ADDR_ENABLE_REG) & self.ENABLE_CLEAR_INTERRUPT_BIT)

    @property
    def is_interrupt_enabled(self):
        return bool(self.read8(self.ADDR_ENABLE_REG) & self.ENABLE_CLEAR_INTERRUPT_BIT)

    @property
    def interrupt_thresholds(self):
        low_threshold  = self.read16(self.ADDR_INTERRUPT_THRESHOLD_LOW)
        high_threshold = self.read16()

        return {
            "low": low_threshold,
            "high": high_threshold,
        }

    @property
    def interrupt_persistance_filter(self)
        return self.read8(self.ADDR_INTERRUPT_PERSISTANCE_FILTER)

    @property
    def integration_time(self):
        integration_reg = self.read8(self.ADDR_RGBC_INTEGRATION_TIME)
        return (256 - integration_reg) * self.TIME_ONE_CYCLE
    
    @property
    def long_wait_set(self):
        return bool(self.read8(self.ADDR_WAIT_CONFIGURATION_REGISTER) & self.LONG_WAIT_BIT)

    @property
    def wait_time(self):
        wait_reg = self.read8(self.ADDR_WAIT_TIME_REG)
        wait_count = 256 - wait_reg
        if self.long_wait_set:
            return (wait_count * self.TIME_ONE_CYCLE * self.LONG_WAIT_MULTIPLIER)
        else:
            return (wait_count * self.TIME_ONE_CYCLE)

    @property
    def gain(self):
        return self.read8(self.ADDR_CONTROL_REG)

    # LED Control
    def turn_on_led(self):
        self._led_pin.value(1)
    
    def turn_off_led(self):
        self._led_pin.value(0)

    def toggle_led(self):
        if self._led_pin.value():
            self.turn_off_led()
        else:
            self.turn_on_led()

    # ENABLE/DISABLE
    def power_on(self):
        enable_reg_value = self.read8(self.ADDR_ENABLE_REG)
        self.write8(self.ADDR_ENABLE_REG, enable_reg_value | self.ENABLE_POWER_BIT)
        time.sleep(0.003)

    def enable_rgbc(self):
        enable_reg_value = self.read8(self.ADDR_ENABLE_REG)
        self.write8(self.ADDR_ENABLE_REG, enable_reg_value | self.ENABLE_RGBC_BIT)

    def enable_wait_between_integrations(self):
        enable_reg_value = self.read8(self.ADDR_ENABLE_REG)
        self.write8(self.ADDR_ENABLE_REG, enable_reg_value | self.ENABLE_WAIT_BETWEEN_INTEGRATIONS)

    def enable_intterrupt(self):
        enable_reg_value = self.read8(self.ADDR_ENABLE_REG)
        self.write8(self.ADDR_ENABLE_REG, enable_reg_value | self.ENABLE_CLEAR_INTERRUPT_BIT)

    def set_long_wait(self):
        self.write8(self.ADDR_WAIT_CONFIGURATION_REGISTER, self.LONG_WAIT_BIT)

    def power_off(self):
        enable_reg_value = self.read8(self.ADDR_ENABLE_REG)
        self.write8(self.ADDR_ENABLE_REG, enable_reg_value & ~self.ENABLE_POWER_BIT)

    def disable_rgbc(self):
        enable_reg_value = self.read8(self.ADDR_ENABLE_REG)
        self.write8(self.ADDR_ENABLE_REG, enable_reg_value & ~self.ENABLE_RGBC_BIT)

    def disable_wait_between_integrations(self):
        enable_reg_value = self.read8(self.ADDR_ENABLE_REG)
        self.write8(self.ADDR_ENABLE_REG, enable_reg_value & ~self.ENABLE_WAIT_BETWEEN_INTEGRATIONS)

    def disable_interrupt(self):
        enable_reg_value = self.read8(self.ADDR_ENABLE_REG)
        self.write8(self.ADDR_ENABLE_REG, enable_reg_value & ~self.ENABLE_CLEAR_INTERRUPT_BIT)

    def clear_long_wait(self):
        self.write8(self.ADDR_WAIT_CONFIGURATION_REGISTER, 0x00)

    # CONFIGURATION SETTINGS
    def set_interrupt_thresholds(self, low_threshold, high_threshold, interrupt_filter=None):
        # if high_threshold < low_threshold, then high_threshold is never checked
        self.write16(self.ADDR_INTERRUPT_THRESHOLD_LOW, low_threshold)
        self.write16(self.ADDR_INTERRUPT_THRESHOLD_HIGH, high_threshold)

    def set_interrupt_persistance_filter(self, interrupt_persistance_filter)
        self.write8(self.ADDR_INTERRUPT_PERSISTANCE_FILTER, interrupt_persistance_filter)

    def set_integration_time(self, integration_time_ms):
        integration_time_count = int(integration_time_ms / self.TIME_ONE_CYCLE)
        integration_time_2s_complement = 256 - max(0, min(256, wait_time))
        self.write8(self.ADDR_RGBC_INTEGRATION_TIME, integration_time_2s_complement)

    def set_wait_time(self, wait_time_ms):
        wait_time_count = int(wait_time_ms / self.TIME_ONE_CYCLE)

        if wait_time_count > 256:
            self.set_long_wait()
            wait_time_count = wait_time_ms / (self.LONG_WAIT_MULTIPLIER * self.TIME_ONE_CYCLE)
        else:
            self.clear_long_wait()

        wait_time_2s_complement = 256 - max(0, min(256, wait_time_count))
        self.write8(self.ADDR_WAIT_TIME_REG, wait_time_2s_complement)

    def set_gain(self, gain):
        self.write8(self.ADDR_CONTROL_REG, gain)

