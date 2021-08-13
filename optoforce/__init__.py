"""

    optoforce

A package which simplifies connecting to and reading from optoforce sensors
"""
import serial
import logging
from serial.tools.list_ports import comports
from typing import Generic, List, Optional, TypeVar
from . import status

# typing.Literal introduced in Python v3.8
try:
    from typing import Literal  # type: ignore
except ImportError:
    from typing_extensions import Literal  # type: ignore

from .reading import Reading16, Reading22, Reading34, read_16bytes, read_22bytes, read_34bytes

__version__ = '0.3.0'
__all__ = ['OptoForce16', 'OptoForce34', 'OptoForce22', 'status']

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
    10: 100,
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
    1.5: 6,
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


T = TypeVar("T")


class _OptoForce(Generic[T]):
    # attributes which are filled in by the classes that inherit from this one
    _expected_header: bytes
    _packet_size: int
    def _decoder(self, b: bytes) -> T: ...

    def __init__(self,
                 port: Optional[str] = None,
                 speed_hz: SPEEDS = 100,
                 filter_hz: FILTERS = 15,
                 zero: bool = False):
        if speed_hz not in SPEED_MAPPING:
            raise KeyError(
                f'speed_hz must be one of: {list(SPEED_MAPPING.keys())}. Got: {speed_hz}'
            )
        if filter_hz not in FILTER_MAPPING:
            raise KeyError(
                f'filter_hz must be one of: {list(FILTER_MAPPING.keys())}. Got: {filter_hz}'
            )

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

    def read(self, only_latest_data: bool) -> T:
        """
        Read a packet from the serial buffer. If `only_latest_data` is True,
        and there is more than one packet waiting in the buffer, flush the buffer
        until there is only one packet left (the latest packet). Otherwise,
        just read the next packet in the buffer, even if that packet is slightly
        old.
        """
        # opt_ser.in_waiting returns the number of bytes in the buffer
        if only_latest_data and self.opt_ser.in_waiting > self._packet_size:

            # flush input to make sure we don't read old data
            self.opt_ser.reset_input_buffer()

        # Start by reading data from the input buffer until the header `expected_bytes`
        # is found. This flushes data until a packet is found
        self.opt_ser.read_until(self._expected_header)
        logger.debug('received frame header')

        # next, read the body of the packet
        raw_data = self.opt_ser.read(
            self._packet_size - len(self._expected_header)
        )

        # decode (deserialize) the bytes into regular Python data
        return self._decoder(raw_data)

    def read_all_packets_in_buffer(self) -> List[T]:
        """
        Read all packets in the buffer. Note that the `count` attribute of a packet
        can be used to tell when the packet was sent from the optoforce.
        """
        data: List[T] = []
        while self.opt_ser.in_waiting >= self._packet_size:
            data.append(self.read(only_latest_data=False))
        return data

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

##


class OptoForce16(_OptoForce[Reading16]):
    _expected_header = bytes((170, 7, 8, 10))
    _packet_size = 16
    def _decoder(self, b): return read_16bytes(self._expected_header, b)


class OptoForce34(_OptoForce[Reading34]):
    _expected_header = bytes((170, 7, 8, 28))
    _packet_size = 34
    def _decoder(self, b): return read_34bytes(self._expected_header, b)


class OptoForce22(_OptoForce[Reading22]):
    _expected_header = bytes((170, 7, 8, 16))
    _packet_size = 22
    def _decoder(self, b): return read_22bytes(self._expected_header, b)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        logger.warning("This force sensor model hasn't been tested. "
                       "Please mention on the source repo how it went! "
                       "Also, the torques aren't scaled, since I don't have that datasheet!")
