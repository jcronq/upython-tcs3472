from machine import I2C as _I2C
from micropython import const

try:
    import threading
except ImportError:
    threading = None

I2C_MASTER_PORT = const(0)

class ContextManaged:
    """An object that automatically deinitializes hardware with a context manager."""

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.deinit()

    # pylint: disable=no-self-use
    def deinit(self):
        """Free any hardware used by the object."""
        return

    # pylint: enable=no-self-use


class Lockable(ContextManaged):
    """An object that must be locked to prevent collisions on a microcontroller resource."""

    _locked = False

    def try_lock(self):
        """Attempt to grab the lock. Return True on success, False if the lock is already taken."""
        if self._locked:
            return False
        self._locked = True
        return True

    def unlock(self):
        """Release the lock so others may use the resource."""
        if self._locked:
            self._locked = False
        else:
            raise ValueError("Not locked")

class I2C(Lockable):
    """
    Busio I2C Class for CircuitPython Compatibility. Used
    for both MicroPython and Linux.
    """

    def __init__(self, scl, sda, freq=100000):
        self.deinit()

        self._i2c = _I2C(I2C_MASTER_PORT, sda=sda, scl=scl, freq=freq)

        if threading is not None:
            self._lock = threading.RLock()

    def deinit(self):
        """Deinitialization"""
        try:
            del self._i2c
        except AttributeError:
            pass

    def __enter__(self):
        if threading is not None:
            self._lock.acquire()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if threading is not None:
            self._lock.release()
        self.deinit()

    def scan(self):
        """Scan for attached devices"""
        return self._i2c.scan()

    def readfrom_into(self, address, buffer, *, start=0, end=None):
        """Read from a device at specified address into a buffer"""
        if start != 0 or end is not None:
            if end is None:
                end = len(buffer)
            buffer = memoryview(buffer)[start:end]
        stop = True  # remove for efficiency later
        return self._i2c.readfrom_into(address, buffer, stop)

    def writeto(self, address, buffer, *, start=0, end=None, stop=True):
        """Write to a device at specified address from a buffer"""
        if isinstance(buffer, str):
            buffer = bytes([ord(x) for x in buffer])
        if start != 0 or end is not None:
            if end is None:
                return self._i2c.writeto(address, memoryview(buffer)[start:], stop)
            return self._i2c.writeto(address, memoryview(buffer)[start:end], stop)
        return self._i2c.writeto(address, buffer, stop)

    def writeto_then_readfrom(
        self,
        address,
        buffer_out,
        buffer_in,
        *,
        out_start=0,
        out_end=None,
        in_start=0,
        in_end=None,
        stop=False
    ):
        """ "Write to a device at specified address from a buffer then read
        from a device at specified address into a buffer
        """
        self.writeto(address, buffer_out, start=out_start, end=out_end, stop=stop)
        return self.readfrom_into(address, buffer_in, start=in_start, end=in_end)
