import time
from machine import Pin
from micropython import const
from src.utils.locakable_i2c import I2C
from src.rgb_sensor_tcs34725 import Driver, GAINS, TIME_ONE_CYCLE

MAX_GAIN_UPPER_C_THESHOLD = const(2000)
MAX_INTEGRATION_TIME = const(612)
MAX_SENSOR_VALUE = const(65535)

INTEGRATION_TIME_STEP = const(50)
DESIRED_INTEGRATION_FLOOR_COUNT = const(63)
DESIRED_INTEGRATION_FLOOR_TIME = const(152)
DESIRED_INTEGRATION_FLOOR_TIME_COMPARISON = const(153)

class Controller:
    def __init__(self, scl_pin, sda_pin, freq, led_pin, interrupt_pin):
        i2c = I2C(scl=Pin(scl_pin), sda=Pin(sda_pin), freq=freq)
        self._sensor_driver = Driver(i2c, led_pin, interrupt_pin)
        self._sensor_driver.register_interrupt_callback(self.get_interrupt_handler())
        self._last_rgb_val = None

        self.start_sensor()
        self.calibrate()

    def start_sensor(self):
        self._sensor_driver.power_on()

        #trigger interrupt when within 5% of the total range of the saturation limits
        self._sensor_driver.interrupt_saturation_tolerance = 0.05 
        # Roughly 1 second of threshold breach: 5 evaulates to 5 (see page 17 of spec sheet for alternative values)
        self._sensor_driver.interrupt_persistance_filter = 5 

        #initial value; configured in calls to callibrate
        self._sensor_driver.gain = 1 

        # 154 will remove flicker from 60 Hz lines, and allows digital saturation thresholds to become dominant.
        self._sensor_driver.integration_time = DESIRED_INTEGRATION_FLOOR_TIME # 151ms
        # Creates a cycle where devide is on for 154 (above) and idle for 100ms (below)
        # Reduces power usage
        self._sensor_driver.wait_time = 100 #ms
        self._sensor_driver.enable_wait_between_integrations()

        self._sensor_driver.enable_rgbc()
        # sleep for 1 integration cycle
        sleep_time = (self._sensor_driver.integration_time + self._sensor_driver.wait_time) / 1000
        print("sleep for {}".format(sleep_time))
        time.sleep(sleep_time)

    def get_interrupt_handler(self):
        def interrupt_handler():
            print("controller interrupt called")
            self.calibrate()
        
        return interrupt_handler

    
    def calibrate(self):
        print("calibrate")
        if self._sensor_driver.is_interrupt_enabled:
            self._sensor_driver.disable_interrupt()
            self._sensor_driver.clear_interrupt()
        r, g, b, c = self._sensor_driver.color_raw
        current_gain = self._sensor_driver.gain
        current_integration_time = self._sensor_driver.integration_time
        next_integraion_time = current_integration_time
        print("c", c)
        if c < 100:
            # The sensor is undersaturated. Increase Gain
            next_gain_index = GAINS.index(current_gain) + 1
            if next_gain_index > 3:
                # Gain is maxed, increase integration time up to max
                next_gain_index = 3
                next_integraion_time = min(255*2.4, current_integration_time + INTEGRATION_TIME_STEP)
        elif (
            GAINS.index(current_gain) == 3 
            and current_integration_time > DESIRED_INTEGRATION_FLOOR_TIME_COMPARISON 
            and c >= MAX_GAIN_UPPER_C_THESHOLD
        ):
            # Move integation time to desired time before reducing 
            next_gain_index = 3
            next_integraion_time = max(DESIRED_INTEGRATION_FLOOR_TIME_COMPARISON, current_integration_time - INTEGRATION_TIME_STEP)
        else:
            # The sensor is oversaturated. and we're at the desired integration time.
            # Reduce gain
            next_gain_index = GAINS.index(current_gain) - 1
            if next_gain_index < 0:
                next_gain_index = 0

        next_gain = GAINS[next_gain_index]
        next_integraion_time = max(0, min(MAX_INTEGRATION_TIME, next_integraion_time))
        self._sensor_driver.gain = next_gain
        self._sensor_driver.integration_time = next_integraion_time
        self._sensor_driver.interrupt_thresholds = self.get_interrupt_thresholds(next_gain_index, next_integraion_time)

        self._sensor_driver.enable_interrupt()
    
    def get_interrupt_thresholds(self, gain_index, integration_time):
        integration_count = integration_time / TIME_ONE_CYCLE
        # 5% of the total range
        saturation_tolerance = 0.05 * MAX_SENSOR_VALUE
        low_threshold = 100 #Recommended value from DN40 3.14

        # SATURATION LEVELS: DN40 3.5 & 3.7
        if integration_count < 63:
            upper_saturation = (1024 * integration_count * 0.75)
        else:
            upper_saturation = MAX_SENSOR_VALUE
        
        if gain_index == 3 and  integration_count == 255:
            # Disable low threshold as we can't increase signal from here
            low_threshold = 0 

        if gain_index == 3 and integration_count > 64:
            # Favor integration times around 150 ms to prevent ripple variance and keep
            # keep the measurement cycle fast
            high_threshold = MAX_GAIN_UPPER_C_THESHOLD
        else:
            upper_saturation = upper_saturation - saturation_tolerance
            high_threshold = min(MAX_SENSOR_VALUE, max(0, int(upper_saturation)))
        return (low_threshold, high_threshold)

    @property
    def ct(self):
        return self._sensor_driver._temperature_and_lux_dn40()[1] 

    @property
    def lux(self):
        return self._sensor_driver._temperature_and_lux_dn40()[0] 

    @property
    def color_raw(self):
        return self._sensor_driver.color_raw

    @property
    def driver(self):
        return self._sensor_driver

    @property
    def status(self):
        return {
            'gain': self._sensor_driver.gain,
            'integration_time': self._sensor_driver.integration_time,
            'wait_time': self._sensor_driver.wait_time,
            'wait_enabled': self._sensor_driver.is_wait_between_integration_enabled
        }
