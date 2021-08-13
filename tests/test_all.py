from optoforce import Reading16
import serial
import optoforce
from pathlib import Path

DATA = {
    # some longer data
    '/dev/data0': b"\xaa\x00P\x01\x00\x00\xfb\xaa\x07\x08\n-j\x00\x00\xff\xf7\xff\xfb\x00\x07\x05Q\xaa\x07\x08\n-k\x00\x00\xff\xf9\xff\xfe\x00\x0c\x05\\\xaa\x07\x08\n-l\x00\x00\xff\xf3\x00\x01\x00\n\x03Y\xaa\x07\x08\n-m\x00\x00\xff\xf3\x00\x02\x00\r\x03^\xaa\x07\x08\n-n\x00\x00\xff\xf6\x00\x03\x00\x0c\x03b\xaa\x07\x08\n-o\x00\x00\xff\xfb\xff\xff\x00\x0b\x05b\xaa\x07\x08\n-p\x00\x00\xff\xfc\xff\xfb\x00\x0b\x05`\xaa\x07\x08\n-q\x00\x00\xff\xf9\xff\xf9\x00\x0b\x05\\\xaa\x07\x08\n-r\x00\x00\xff\xf9\xff\xfb\x00\t\x05]\xaa\x07\x08\n-s\x00\x00\xff\xfd\xff\xfb\x00\t\x05b\xaa\x07\x08\n-t\x00\x00\xff\xf3\xff\xf9\x00\x0b\x05Y\xaa\x07\x08\n-u\x00\x00\x00\x00\xff\xfa\x00\x0b\x03i\xaa\x07\x08\n-v\x00\x00\xff\xfb\xff\xfc\x00\t\x05d\xaa\x07\x08\n-w\x00\x00\xff\xf9\xff\xf6\x00\n\x05^\xaa\x07\x08\n-x\x00\x00\xff\xf5\x00\x03\x00\x0c\x03k\xaa\x07\x08\n-y\x00\x00\xff\xf7\x00\x01\x00\x0b\x03k\xaa\x07\x08\n-z\x00\x00\xff\xf8\xff\xfb\x00\t\x05d\xaa\x07\x08\n",
    # the same, but shorter
    '/dev/data1': b"\xaa\x00P\x01\x00\x00\xfb\xaa\x07\x08\n-j\x00\x00\xff\xf7\xff\xfb\x00\x07\x05Q\xaa\x07\x08\n-k\x00\x00\xff\xf9\xff\xfe\x00\x0c\x05\\\xaa\x07\x08\n-l\x00\x00\xff\xf3\x00\x01\x00\n\x03Y\xaa\x07\x08\n-m\x00\x00\xff\xf3\x00",
    # a file
    'test-data.bin': (Path(__file__).parent / 'test-data.bin').read_bytes(),
}


# A dummy class, so that we don't have to read from an actual serial port
class SerialTester(serial.Serial):
    def __init__(self, *args, **kwargs):
        self._idx = 0
        self._is_open = True
        self._input_buffer_was_reset = False
        self._bytes_written = bytearray()

        for k, v in DATA.items():
            if k in args or k in kwargs.values():
                self._data = v
                return

        raise RuntimeError()

    def open(self):
        self._is_open = True

    def close(self):
        self._is_open = False

    @property
    def in_waiting(self):
        assert self._is_open
        return len(self._data) - self._idx

    @property
    def is_open(self):
        return self._is_open

    def read_until(self, expected: bytes, size=-1):
        if size > 0:
            size += self._idx
        self._idx += self._data[self._idx:size].index(expected) + len(expected)

    def read(self, size: int = 1):
        assert self._is_open
        i = self._idx
        self._idx += size
        return self._data[i: i + size]

    def write(self, data) -> int:
        self._bytes_written.extend(data)
        return len(data)

    def reset_input_buffer(self):
        self._input_buffer_was_reset = True


# monkey patch serial module
serial.Serial = SerialTester


def test_serialtester():
    s = serial.Serial(port='/dev/data0')
    assert s.is_open
    assert s.read() == b'\xaa'
    s.read_until(b'\x00\x00')
    assert s.read() == b'\xfb'
    s.close()
    assert not s.is_open


##


def test_write_correct_header():
    force_sensor = optoforce.OptoForce16(port="/dev/data0")
    force_sensor.connect()

    expected_header = bytes([170, 0, 50, 3, 10, 4, 0, 0, 237])
    assert force_sensor.opt_ser._bytes_written == expected_header  # type: ignore


EXPECTED = [
    Reading16(count=11626, status=0, Fx=-0.34069400630914826, Fy=-
              0.17359101955792156, Fz=2.3144321375433954, checksum=1361, valid_checksum=True),
    Reading16(count=11627, status=0, Fx=-0.26498422712933756, Fy=-
              0.06943640782316862, Fz=3.967597950074392, checksum=1372, valid_checksum=True),
    Reading16(count=11628, status=0, Fx=-0.4921135646687697,
              Fy=0.03471820391158431, Fz=3.3063316250619934, checksum=857, valid_checksum=True)
]


def test_read_all():
    with optoforce.OptoForce16(port="/dev/data1") as force_sensor:
        assert force_sensor.read_all_packets_in_buffer() == EXPECTED


def test_read_all_no_packets_lost():
    port = '/dev/data0'
    with optoforce.OptoForce16(port=port) as force_sensor:
        packets = force_sensor.read_all_packets_in_buffer()
        buffer = DATA[port]
        assert len(packets) == len(buffer)//16


def test_read_one():
    with optoforce.OptoForce16(port="/dev/data1") as force_sensor:
        assert force_sensor.read(only_latest_data=False) == EXPECTED[0]


def test_read_latest():
    with optoforce.OptoForce16(port="/dev/data1") as force_sensor:
        force_sensor.read(only_latest_data=True)
        assert force_sensor.opt_ser._input_buffer_was_reset  # type: ignore
