"""
Utilities to check the status word of a sensor reading, and decode any errors

The functions correspond to the status word in a packet (and are named to
correspond to the OptoForce documentation), and could be used as follows:

>>> from optoforce.status import no_errors, decode
>>> while True:
...     measurement = force_sensor.read(only_latest_data=False)
...     if no_errors(measurement.status) is False:
...         print(decode(measurement.status))

While these functions _should_ work fine, they haven't been tested on a real
device, so proceed with caution and please report back!
"""
from collections import defaultdict
from typing import List, Tuple

__all__ = ['decode', 'no_errors']

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
    """
    >>> error((0b001 << 13) + (0b010 << 10))
    ('daq error', 'sensor failure')
    """
    return DAQ_TYPE[(status >> 13) & 0b111], SENSOR_TYPE[(status >> 10) & 0b111]  # type: ignore

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
    """
    >>> single_multiple(0b1000)
    'multiple sensors have errors'

    >>> single_multiple(0b0000)
    'only a single sensor has error (or no error)'
    """
    if status & 0b1000:
        return 'multiple sensors have errors'
    else:
        return 'only a single sensor has error (or no error)'


def sensor_number(status: int):
    """
    >>> sensor_number(0b011)
    'sensor #3'
    """
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


def decode(status: int):
    """
    Check the status of a frame. Returns:
    Tuple[
        Tuple[daq_status: str, sensor_status: str],
        List[overloaded_axes: str],
        Tuple[single_or_multiple: str, sensor_number: str],
    ]

    An example of a sensor gone totally wrong:

    >>> decode(0b_010_100_001_110_0_100)
    (('communication error', 'temperature error'),
     ['Fz', 'Tx', 'Ty'],
     ('only a single sensor has error (or no error)', 'sensor #4'))

    An example where everything seems fine:

    >>> check_status(0)
    (('no error', 'no error'),
     [],
     ('only a single sensor has error (or no error)', 'no sensor has error'))
    """
    return error(status), overloaded_axes(status), multiple_sensor_selection(status)


def no_errors(status: int) -> bool:
    """
    >>> no_errors(0)
    True

    >>> no_errors(0b11111111111)
    False
    """
    return status == 0

    # above is a shortcut for:

    # (daq_err, sensor_err), overloaded, (_, errs) = decode(status)
    # return (
    #     daq_err == sensor_err == 'no error'
    #     and len(overloaded) == 0
    #     and errs == 'no sensor has error'
    # )
