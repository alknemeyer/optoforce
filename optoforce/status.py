from collections import defaultdict
from typing import List, Tuple

__all__ = ['check_status']

###

DAQ_TYPE = defaultdict(lambda: 'reserved', {
    0b000: 'no error',
    0b001: 'daq error',
    0b010: 'communication error'
})
SENSOR_TYPE = defaultdict(lambda: 'reserved', {
    0b000: 'no error',
    0b001: 'sensor not detected',
    0b010: 'sensor failure',
    0b100: 'temperature error'
})


def error(status: int) -> Tuple[str, str]:
    return DAQ_TYPE[status & 0b111 << 13], SENSOR_TYPE[status & 0b111 << 10]

###


AXES = ('Fx', 'Fy', 'Fz', 'Tx', 'Ty', 'Tz')


def overloaded_axes(status: int) -> List[str]:
    """
    >>> overloaded_axes(2**9 + 2**5)
    ['Fx', 'Ty']
    """
    return [axis for i, axis in enumerate(AXES) if (status >> (9 - i)) & 0b1 == 0b1]

###


def single_multiple(status: int):
    if status & 0b1000:
        return 'multiple sensors have errors'
    else:
        return 'only a single sensor has error (or no error)'


def sensor_number(status: int):
    sensornum = status & 0b111
    if sensornum == 0:
        return 'no sensor has error'
    elif sensornum <= 4:
        return f'sensor #{sensornum}'
    else:
        return 'reserved'


def multiple_sensor_selection(status: int) -> Tuple[str, str]:
    return single_multiple(status), sensor_number(status)

###


def check_status(status: int):
    """
    Check the status of a frame. Returns:
    Tuple[
        Tuple[daq_status: str, sensor_status: str],
        List[overloaded_axes: str],
        Tuple[single_or_multiple: str, sensor_number: str],
    ]
    """
    return error(status), overloaded_axes(status), multiple_sensor_selection(status)
