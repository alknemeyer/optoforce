"""
    optoforce
"""
import serial
import logging
from serial.tools.list_ports import comports
from typing import Literal, Optional
from .reading import read_16bytes, read_22bytes, read_34bytes

__version__ = '0.2.0'
__all__ = ['OptoForce16', 'OptoForce34', 'OptoForce22']

logger = logging.getLogger(__name__)


# constants from datasheet
OPTO_PARAMS = {
    'baudrate': 1000_000,
    'stopbits': serial.STOPBITS_ONE,
    'parity': serial.PARITY_NONE,
    'bytesize': serial.EIGHTBITS,
}

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


class _OptoForce:
    def __init__(self, port: Optional[str] = None,
                 speed_hz: SPEEDS = 100,
                 filter_hz: FILTERS = 15,
                 zero: bool = False):
        if speed_hz not in SPEED_MAPPING:
            raise KeyError(f'speed_hz must be one of: {list(SPEED_MAPPING.keys())}. Got: {speed_hz}')
        if filter_hz not in FILTER_MAPPING:
            raise KeyError(f'filter_hz must be one of: {list(FILTER_MAPPING.keys())}. Got: {filter_hz}')

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

    def read(self, only_latest_data: bool):
        # opt_ser.in_waiting returns the number of bytes in the buffer
        if only_latest_data and self.opt_ser.in_waiting > 16:

            # flush input to make sure we don't read old data
            self.opt_ser.reset_input_buffer()

        expected_header = bytes((170, 7, 8, 10))
        self.opt_ser.read_until(expected_header)

        logger.debug('received frame header')

    def close(self):
        if hasattr(self, 'opt_ser'):
            self.opt_ser.close()
            logger.info('closed connection')

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *args):
        self.close()

    def __del__(self):
        self.close()


HEADER_SIZE = 4


class OptoForce16(_OptoForce):
    def read(self, only_latest_data: bool):
        super().read(only_latest_data)
        return read_16bytes(self.opt_ser.read(16 - HEADER_SIZE))


class OptoForce34(_OptoForce):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        logging.warning('this force sensor model hasn\'t been tested. '
                        'Please mention on the source repo how it went!')

    def read(self, only_latest_data: bool):
        super().read(only_latest_data)
        return read_34bytes(self.opt_ser.read(34 - HEADER_SIZE))


class OptoForce22(_OptoForce):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        logging.warning('this force sensor model hasn\'t been tested. '
                        'Please mention on the source repo how it went! '
                        'Also, the torques aren\'t scaled, since I don\'t have that datasheet!')

    def read(self, only_latest_data: bool):
        super().read(only_latest_data)
        return read_22bytes(self.opt_ser.read(22 - HEADER_SIZE))
