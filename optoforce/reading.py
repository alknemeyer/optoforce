from typing import NamedTuple
import struct

FX_SCALE = 1/7925 * 300   # ~= 1/26.42
FY_SCALE = 1/8641 * 300   # ~= 1/28.8
FZ_SCALE = 1/6049 * 2000  # ~= 1/3.02


class Reading16(NamedTuple):
    count: int
    status: int
    Fx: float
    Fy: float
    Fz: float
    checksum: int
    valid_checksum: bool


def read_16bytes(header: bytes, data: bytes):
    count, status, Fx, Fy, Fz, checksum = struct.unpack('>HH3hH', data)
    valid_checksum = sum(header) + sum(data[:-2]) == checksum
    return Reading16(count, status, Fx*FX_SCALE, Fy*FY_SCALE, Fz*FZ_SCALE, checksum, valid_checksum)

###


class Reading34(NamedTuple):
    count: int
    status: int
    Fx1: float
    Fy1: float
    Fz1: float
    Fx2: float
    Fy2: float
    Fz2: float
    Fx3: float
    Fy3: float
    Fz3: float
    Fx4: float
    Fy4: float
    Fz4: float
    checksum: int
    valid_checksum: bool


def read_34bytes(header: bytes, data: bytes):
    count, status, Fx1, Fy1, Fz1, Fx2, Fy2, Fz2, Fx3, Fy3, Fz3, Fx4, Fy4, Fz4, checksum = (
        struct.unpack('>HH12hH', data)
    )
    valid_checksum = sum(header) + sum(data[:-2]) == checksum
    return Reading34(count, status,
                     Fx1*FX_SCALE, Fy1*FY_SCALE, Fz1*FZ_SCALE,
                     Fx2*FX_SCALE, Fy2*FY_SCALE, Fz2*FZ_SCALE,
                     Fx3*FX_SCALE, Fy3*FY_SCALE, Fz3*FZ_SCALE,
                     Fx4*FX_SCALE, Fy4*FY_SCALE, Fz4*FZ_SCALE, checksum, valid_checksum)

###


class Reading22(NamedTuple):
    count: int
    status: int
    Fx: float
    Fy: float
    Fz: float
    Tx: int
    Ty: int
    Tz: int
    checksum: int
    valid_checksum: bool


def read_22bytes(header: bytes, data: bytes):
    count, status, Fx, Fy, Fz, Tx, Ty, Tz, checksum = (
        struct.unpack('>HH6hH', data)
    )
    valid_checksum = sum(header) + sum(data[:-2]) == checksum
    return Reading22(count, status, Fx*FX_SCALE, Fy*FY_SCALE, Fz*FZ_SCALE, Tx, Ty, Tz, checksum, valid_checksum)
