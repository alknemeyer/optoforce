"""
Produce the figure in the README:

    python test-plot.py

"""
import matplotlib.pyplot as plt  # type: ignore
import optoforce
from optoforce.status import no_errors
import serial
from tests.test_all import SerialTester

serial.Serial = SerialTester

plt.style.use('seaborn')

with optoforce.OptoForce16(port='test-data.bin') as force_sensor:
    data = force_sensor.read_all_packets_in_buffer()
    data = [
        d for d in data if d.valid_checksum and no_errors(d.status)
    ]
    counts = [d.count for d in data]
    plt.plot(counts, [d.Fx for d in data])
    plt.plot(counts, [d.Fy for d in data])
    plt.plot(counts, [d.Fz for d in data])
    plt.legend(['$F_x$', '$F_y$', '$F_z$'])
    plt.ylabel('Force [N]')
    plt.xlabel('Count')
    plt.show()
