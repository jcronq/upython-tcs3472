from src.rgb_sensor_tcs34725 import Interface

class Controller:
    def __init__(self):
        self._sensor_interface = Interface()

        self._sensor_interface.register_interrupt_callback(self.get_interrupt_handler())
        self._last_rgb_val = None

        self.start_sensor()
        self.calibrate()

    def start_sensor(self):
        self._sensor_interface.power_on()
        self._sensor_interface.set_wait_time(100)
        self._sensor_interface.enable_rgbc()

    def get_interrupt_handler(self):
        def interrupt_handler():
            self.calibrate()
        
        return interrupt_handler
    
    def calibrate(self):
        print("Callibration not implenmented yet")

    