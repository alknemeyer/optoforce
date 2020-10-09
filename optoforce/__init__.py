"""
    optoforce
"""
import serial
import struct
import logging
from serial.tools.list_ports import comports
from typing import Literal, Tuple, Optional

__version__ = '0.0.1'
__all__ = ['OptoForce']

logger = logging.getLogger(__name__)


# constants from datasheet
OPTO_PARAMS = {
    'baudrate': 1000_000,
    'stopbits': serial.STOPBITS_ONE,
    'parity': serial.PARITY_NONE,
    'bytesize': serial.EIGHTBITS,
}

FX_SCALE = 1/7925 * 300   # ~= 1/26.42
FY_SCALE = 1/8641 * 300   # ~= 1/28.8
FZ_SCALE = 1/6049 * 2000  # ~= 1/3.02

SPEED_MAPPING = {
    'stop': 0,
    1000: 1,
    333: 3,
    100: 10,
    30: 33,
    10: 100
}
# must be one of these specific values:
SPEEDS = Literal['stop', 1000, 333, 100, 30, 10]

FILTER_MAPPING = {
    'none': 0,
    500: 1,
    150: 2,
    50: 3,
    15: 4,
    5: 5,
    1.5: 6
}
FILTERS = Literal['none', 500, 150, 50, 15, 5, 1.5]


def find_optoforce_port() -> str:
    devices = [dev for dev in comports() if dev.description == 'OptoForce DAQ']

    if len(devices) == 0:
        raise RuntimeError(f"Couldn't find an OptoForce")

    elif len(devices) == 1:
        port = devices[0].device
        assert port is not None
        return port

    else:
        raise RuntimeError(f'Found more than one OptoForce: {devices}')


class OptoForce:
    def __init__(self, port: Optional[str] = None,
                 speed_hz: SPEEDS = 100,
                 filter_hz: FILTERS = 15,
                 zero: bool = False):
        self.speed = SPEED_MAPPING[speed_hz]
        self.filter = FILTER_MAPPING[filter_hz]
        self.zero = 255 if zero else 0

        if port is None:
            self.port = find_optoforce_port()
        else:
            self.port = port

    def connect(self):
        logger.info(f'connecting at port: {self.port}')
        self.opt_ser = serial.Serial(self.port, **OPTO_PARAMS)

        # write optoforce setup code
        header = (170, 0, 50, 3)
        checksum = sum(header) + self.speed + self.filter + self.zero
        payload = (*header,
                   self.speed, self.filter, self.zero,
                   *divmod(checksum, 256))

        logger.info(f'sending configuration bytes: {payload}')
        self.opt_ser.write(payload)

    def read(self, only_latest_data: bool) -> Tuple[float, float, float]:
        # opt_ser.in_waiting returns the number of bytes in the buffer
        if only_latest_data and self.opt_ser.in_waiting > 16:

            # flush input to make sure we don't read old data
            self.opt_ser.reset_input_buffer()

        expected_header = bytes((170, 7, 8, 10))  # => b'\xaa\x07\x08\n'
        self.opt_ser.read_until(expected_header)

        # https://docs.python.org/3/library/struct.html#format-characters
        count, status, fx, fy, fz, checksum = (
            struct.unpack('>HHhhhH', self.opt_ser.read(12))
        )

        logger.debug(
            f'received data: {count}, {status}, {fx}, {fy}, {fz}, {checksum}'
        )

        return (fx * FX_SCALE, fy*FY_SCALE, fz*FZ_SCALE)

    def close(self):
        self.opt_ser.close()
        logger.info('closed connection')

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *args):
        self.close()

    def __del__(self):
        self.close()
