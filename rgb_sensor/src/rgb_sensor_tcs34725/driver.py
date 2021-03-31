# -*- coding: utf-8 -*-
"""
Light Sensor TCS34725
Adafruit RGB Color Sensor
DataSheet: https://cdn-shop.adafruit.com/datasheets/TCS34725.pdf
C Example: https://github.com/adafruit/Adafruit_TCS34725/

@author: jcron
"""
from machine import Pin, SoftI2C
from micropython import const
import time
import _thread
from src.utils.i2c_device import I2CDevice

ADDR_ENABLE_REG = const(0x00)
ENABLE_POWER_BIT = const(0x01)
ENABLE_RGBC_BIT  = const(0x02)
ENABLE_WAIT_BETWEEN_INTEGRATIONS = const(0x08)
ENABLE_CLEAR_INTERRUPT_BIT = const(0x010)

ADDR_RGBC_INTEGRATION_TIME = const(0x01)
INTEGRATIONTIME_2_4MS = const(0xFF) # <  2.4ms - 1 cycle    - Max Count: 1024 
INTEGRATIONTIME_24MS  = const(0xF6) # <  24ms  - 10 cycles  - Max Count: 10240
INTEGRATIONTIME_50MS  = const(0xEB) # <  50ms  - 20 cycles  - Max Count: 20480
INTEGRATIONTIME_101MS = const(0xD5) # <  101ms - 42 cycles  - Max Count: 43008
INTEGRATIONTIME_154MS = const(0xC0) # <  154ms - 64 cycles  - Max Count: 65535
INTEGRATIONTIME_700MS = const(0x00) # <  700ms - 256 cycles - Max Count: 65535

ADDR_WAIT_TIME_REG = const(0x03)

ADDR_INTERRUPT_THRESHOLD_LOW      = const(0x04)
ADDR_INTERRUPT_THRESHOLD_HIGH     = const(0x06)
ADDR_INTERRUPT_PERSISTANCE_FILTER = const(0x0C)

ADDR_WAIT_CONFIGURATION_REGISTER = const(0x0D)
CYCLES = (0, 1, 2, 3, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60)
LONG_WAIT_BIT = const(0x02)

ADDR_CONTROL_REG = const(0x0F)
GAINS = (1, 4, 16, 60)

ADDR_DEVICE_ID  = const(0x12)
ADDR_STATUS_REG = const(0x13)
STATUS_INTEGRATION_VALID_BIT   = const(0x01)
STATUS_CLEAR_CHANNEL_INTERRUPT = const(0x10)

ADDR_DATA_READ_BYTE_CLEAR = const(0x14)
ADDR_DATA_READ_BYTE_RED   = const(0x16)
ADDR_DATA_READ_BYTE_GREEN = const(0x18)
ADDR_DATA_READ_BYTE_BLUE  = const(0x1A)

TIME_ONE_CYCLE = 2.4 # milliseconds
LONG_WAIT_MULTIPLIER = const(12)

COMMAND_BIT    = const(0x80)
COMMAND_SPECIAL_FUNCTION = const(0x60)
COMMAND_AUTO_INCREMENT = const(0x20)
COMMAND_CLEAR_INTERRUPT = const(0x06)

class Driver:
    i2c_freq = 9600


    def __init__(self, i2c, led_pin, interrupt_pin):
        self.interrupt_saturation_tolerance = 0.0
        self._BUFFER = bytearray(3)

        # Initialize pins
        self._led_pin = Pin(led_pin, Pin.OUT)
        self._interrupt_pin = Pin(interrupt_pin, Pin.IN, Pin.PULL_UP)
        self._interrupt_pin.irq(trigger=Pin.IRQ_FALLING, handler=self.get_clear_interrupt_handler())
        self._interrupt_callbacks = []

        device_addr = i2c.scan()[0]
        self.device = I2CDevice(i2c, device_addr)

    def register_interrupt_callback(self, callback):
        print("adding callback")
        self._interrupt_callbacks.append(callback)

    def get_clear_interrupt_handler(self):
        def clear_interrupt_handler(p):
            print("Interrupt Triggered", p)
            for callback in self._interrupt_callbacks:
                callback()

        return clear_interrupt_handler

    # Lowest Level Communications
    def read8(self, addr):
        with self.device as i2c:
            self._BUFFER[0] = (COMMAND_BIT | addr) & 0xFF
            i2c.write_then_readinto(self._BUFFER, self._BUFFER, out_end=1, in_end=1)
            return self._BUFFER[0]

    def read16(self, addr):
        with self.device as i2c:
            self._BUFFER[0] = (COMMAND_BIT | COMMAND_AUTO_INCREMENT | addr) & 0xFF
            i2c.write_then_readinto(self._BUFFER, self._BUFFER, out_end=1, in_end=2)
            return (self._BUFFER[1] << 8) | self._BUFFER[0]

    def write8(self, addr, data):
        with self.device as i2c:
            self._BUFFER[0] = (COMMAND_BIT | addr) & 0xFF
            self._BUFFER[1] = data & 0xFF
            i2c.write(self._BUFFER, end=2)

    def write16(self, addr, data):
        with self.device as i2c:
            self._BUFFER[0] = (COMMAND_BIT | COMMAND_AUTO_INCREMENT | addr) & 0xFF
            self._BUFFER[1] = data & 0xFF
            self._BUFFER[2] = (data >> 8 ) & 0xFF
            i2c.write(self._BUFFER)

    def clear_interrupt(self):
        with self.device as i2c:
            self._BUFFER[0] = (COMMAND_BIT | COMMAND_SPECIAL_FUNCTION | COMMAND_CLEAR_INTERRUPT) & 0xFF
            i2c.write(self._BUFFER, end=1)

    # State
    @property
    def color_raw(self):
        clear  = self.read16(ADDR_DATA_READ_BYTE_CLEAR)
        red    = self.read16(ADDR_DATA_READ_BYTE_RED)
        green  = self.read16(ADDR_DATA_READ_BYTE_GREEN)
        blue   = self.read16(ADDR_DATA_READ_BYTE_BLUE)

        return (red, green, blue, clear)
    
    @property
    def led_state(self):
        return self._led_pin.value()

    @property
    def is_enabled(self):
        return bool(self.read8(ADDR_ENABLE_REG) & ENABLE_POWER_BIT & ENABLE_RGBC_BIT)
    
    @property
    def is_power_on(self):
        return bool(self.read8(ADDR_ENABLE_REG) & ENABLE_POWER_BIT)

    @property
    def is_adc_enabled(self):
        return bool(self.read8(ADDR_ENABLE_REG) & ENABLE_RGBC_BIT)

    @property
    def is_integration_complete(self):
        return bool(self.read8(ADDR_STATUS_REG) & STATUS_INTEGRATION_VALID_BIT)

    @property
    def is_wait_between_integration_enabled(self):
        return bool(self.read8(ADDR_ENABLE_REG) & ENABLE_WAIT_BETWEEN_INTEGRATIONS)

    @property
    def is_interrupt_enabled(self):
        return bool(self.read8(ADDR_ENABLE_REG) & ENABLE_CLEAR_INTERRUPT_BIT)

    @property
    def interrupt_thresholds(self):
        low_threshold  = self.read16(ADDR_INTERRUPT_THRESHOLD_LOW)
        high_threshold = self.read16(ADDR_INTERRUPT_THRESHOLD_HIGH)

        return (low_threshold, high_threshold)

    @interrupt_thresholds.setter
    def interrupt_thresholds(self, interrupt_thresholds):
        print("Interrupt Thresholds set", interrupt_thresholds)
        self.write16(ADDR_INTERRUPT_THRESHOLD_LOW, interrupt_thresholds[0])
        self.write16(ADDR_INTERRUPT_THRESHOLD_HIGH, interrupt_thresholds[1])

    @property
    def interrupt_persistance_filter(self):
        return self.read8(ADDR_INTERRUPT_PERSISTANCE_FILTER)

    @interrupt_persistance_filter.setter
    def interrupt_persistance_filter(self, interrupt_persistance_filter):
        """full chart found on page 17 of spec sheet.
        """
        print("Persistance filter set", interrupt_persistance_filter)
        self.write8(ADDR_INTERRUPT_PERSISTANCE_FILTER, interrupt_persistance_filter)
    
    @property
    def long_wait_set(self):
        return bool(self.read8(ADDR_WAIT_CONFIGURATION_REGISTER) & LONG_WAIT_BIT)

    @property
    def wait_time(self):
        wait_reg = self.read8(ADDR_WAIT_TIME_REG)
        wait_count = 256 - wait_reg
        if self.long_wait_set:
            return (wait_count * TIME_ONE_CYCLE * LONG_WAIT_MULTIPLIER)
        else:
            return (wait_count * TIME_ONE_CYCLE)

    @wait_time.setter
    def wait_time(self, wait_time_ms):
        wait_time_count = int(wait_time_ms / TIME_ONE_CYCLE)

        if wait_time_count > 256:
            self.set_long_wait()
            wait_time_count = wait_time_ms / (LONG_WAIT_MULTIPLIER * TIME_ONE_CYCLE)
        else:
            self.clear_long_wait()

        wait_time_2s_complement = 256 - max(0, min(256, wait_time_count))
        print("wait time set", wait_time_ms, wait_time_2s_complement)
        self.write8(ADDR_WAIT_TIME_REG, wait_time_2s_complement)

    @property
    def gain(self):
        return GAINS[self.read8(ADDR_CONTROL_REG)]

    @gain.setter
    def gain(self, gain):
        """Sensor gain: 1, 4, 16, 60 """
        print("gain set", GAINS.index(gain), "(x{})".format(gain))
        self.write8(ADDR_CONTROL_REG, GAINS.index(gain))

    @property
    def ATIME(self):
        return self.read8(ADDR_RGBC_INTEGRATION_TIME)

    @ATIME.setter
    def ATIME(self, atime):
        # Set the correct interrupt thresholds according to saturation levels
        print("ATIME set", atime, "({}ms)".format((256-atime)*TIME_ONE_CYCLE))
        self.write8(ADDR_RGBC_INTEGRATION_TIME, atime)


    @property
    def integration_count(self):
        return 256 - self.ATIME
    
    @integration_count.setter
    def integration_count(self, integration_count):
        self.ATIME = 255 - integration_count

    @property
    def integration_time(self):
        print("integration time")
        atime = self.read8(ADDR_RGBC_INTEGRATION_TIME)
        print("integration time", atime)
        return (255 - atime) * TIME_ONE_CYCLE

    @integration_time.setter
    def integration_time(self, integration_time_ms):
        integration_time_count = int(integration_time_ms / TIME_ONE_CYCLE)
        self.integration_count = max(0, min(256, integration_time_count))

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
        print("power on")
        enable_reg_value = self.read8(ADDR_ENABLE_REG)
        self.write8(ADDR_ENABLE_REG, enable_reg_value | ENABLE_POWER_BIT)
        time.sleep(0.003)

    def enable_rgbc(self):
        print("enable_rgbc")
        enable_reg_value = self.read8(ADDR_ENABLE_REG)
        print('enable_reg_value', enable_reg_value)
        self.write8(ADDR_ENABLE_REG, enable_reg_value | ENABLE_RGBC_BIT)
        print('complete')

    def enable_wait_between_integrations(self):
        print("enable wait")
        enable_reg_value = self.read8(ADDR_ENABLE_REG)
        self.write8(ADDR_ENABLE_REG, enable_reg_value | ENABLE_WAIT_BETWEEN_INTEGRATIONS)

    def enable_interrupt(self):
        print("enable interrupt")
        enable_reg_value = self.read8(ADDR_ENABLE_REG)
        self.write8(ADDR_ENABLE_REG, (enable_reg_value | ENABLE_CLEAR_INTERRUPT_BIT))

    def set_long_wait(self):
        print("enable long wait")
        self.write8(ADDR_WAIT_CONFIGURATION_REGISTER, LONG_WAIT_BIT)

    def power_off(self):
        print("power off")
        enable_reg_value = self.read8(ADDR_ENABLE_REG)
        self.write8(ADDR_ENABLE_REG, enable_reg_value & ~ENABLE_POWER_BIT)

    def disable_rgbc(self):
        print("disable rgbc")
        enable_reg_value = self.read8(ADDR_ENABLE_REG)
        self.write8(ADDR_ENABLE_REG, enable_reg_value & ~ENABLE_RGBC_BIT)

    def disable_wait_between_integrations(self):
        print("disable wait")
        enable_reg_value = self.read8(ADDR_ENABLE_REG)
        self.write8(ADDR_ENABLE_REG, (enable_reg_value & ~ENABLE_WAIT_BETWEEN_INTEGRATIONS))

    def disable_interrupt(self):
        print("disable interrupt")
        enable_reg_value = self.read8(ADDR_ENABLE_REG)
        self.write8(ADDR_ENABLE_REG, (enable_reg_value & ~ENABLE_CLEAR_INTERRUPT_BIT))

    def clear_long_wait(self):
        print("clear long wait")
        self.write8(ADDR_WAIT_CONFIGURATION_REGISTER, 0x00)

    # Compute
    def _temperature_and_lux_dn40(self):
        """ Converts the raw RGBC values to color temperature in degrees
        Kelvin using the algorithm described in DN40 from Taos (now AMS).
        Also computes lux. Returns tuple with both values or tuple of Nones
        if computation can not be done.
        """
        ATIME = self.ATIME
        ATIME_ms = (256 - ATIME) * TIME_ONE_CYCLE
        AGAINx = self.gain
        R, G, B, C = self.color_raw

        # Device specific values (DN40 Table 1 in Appendix I)
        GA = 1 # Glass Attenuation (1 for no glass) see DNS40 3.3
        DF = 310.0 # Device Factor
        R_Coef = 0.136
        G_Coef = 1.0 # used in lux computation
        B_Coef = -0.444
        CT_Coef = 3810
        CT_Offset = 1391

        #ANALOG/Digital Saturation (DN40 3.5)
        # if ATIME_ms >  154ms; then we're dealing with digital saturation
        # if ATIME_ms <= 154ms; then we MIGHT have analog saturation.
        #                       in other words, the total amount accumulated
        #                       is going to be equal to 1024 * num_cycles
        #                       rather than the max digital value of 65535. 
        SATURATION_LEVEL = 65535 if 256 - ATIME > 63 else 1024 * (256 - ATIME)

        # Ripple Saturation (DN40 3.7)
        # Ripple Rejection: Man-made light sources (in N.A.) will oscilate at 60 Hz
        #                   Integration times in multiples of 50ms will remove ripple  
        # Ripple Saturation: Occurs when the peak of a ripple is saturated, giving incorrect
        #                    values.  integration_times > 150ms will experience digital_saturation
        #                    before analog saturation, so we can ignore ripple saturation effects
        if ATIME_ms < 150:
            SATURATION_LEVEL -= SATURATION_LEVEL / 4
        
        # Check for saturation and mark sample as invalid
        # Extended range sensing is possible (see DN40 3.13)
        if C >= SATURATION_LEVEL:
            return None, None

        # IR Rejection (DN40 3.1)
        IR = (R + G + B - C) / 2 if R + G + B > C else 0.0
        R2 = R - IR
        G2 = G - IR
        B2 = B - IR

        # Lux Calculation (DN40 3.2)
        G1 = R_Coef * R2 + G_Coef * G2 + B_Coef * B2
        CPL = (ATIME_ms * AGAINx) / (GA * DF)
        CPL = 0.001 if CPL == 0 else CPL
        lux = G1 / CPL

        #CT Calculations (DN40 3.4)
        # Color Saturation will make this number much less acurate. See DN40 3.12
        R2 = 0.001 if R2 == 0 else R2
        CT = CT_Coef * B2 / R2 + CT_Offset

        return lux, CT
