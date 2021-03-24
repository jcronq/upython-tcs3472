import time
from machine import Pin
from src.utils.locakable_i2c import I2C
from src.rgb_sensor_tcs34725 import Driver, GAINS



class Controller:
    IDEAL_C_LEVEL = 200

    def __init__(self):
        SCL_PIN = 22
        SDA_PIN = 21
        i2c = I2C(scl=Pin(SCL_PIN), sda=Pin(SDA_PIN), freq=9600)
        self._sensor_driver = Driver(i2c)
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
        self._sensor_driver.integration_time = 154 #ms
        # Creates a cycle where devide is on for 154 (above) and idle for 100ms (below)
        # Reduces power usage
        self._sensor_driver.wait_time = 100 #ms
        self._sensor_driver.enable_wait_between_integrations()

        self._sensor_driver.enable_rgbc()
        # sleep for 1 integration cycle
        time.sleep((self._sensor_driver.integration_time + self._sensor_driver.wait_time) / 1000)

    def get_interrupt_handler(self):
        def interrupt_handler():
            self.calibrate()
        
        return interrupt_handler

    
    def calibrate(self):
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
                next_integraion_time = min(255*2.4, current_integration_time + 50)
        else:
            # The sensor is oversaturated. Decrease the Gain
            if current_gain == 3 and current_integration_time > 154:
                next_gain_index = 3
                next_integration_time = max(153, current_integration_time - 50)
            else:
                next_gain_index = GAINS.index(current_gain) - 1
                if next_gain_index < 0:
                    next_gain_index = 0

        next_gain = GAINS[next_gain_index]
        self._sensor_driver.gain = next_gain
        self._sensor_driver.integration_time = next_integraion_time

        self._sensor_driver.enable_interrupt()

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
