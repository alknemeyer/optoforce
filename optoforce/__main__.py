import logging
from datetime import datetime
import argparse
from . import OptoForce16 as OptoForce
from . import status

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Stream force data from an OptoForce16 to a csv file"
    )
    parser.add_argument(
        '-f', '--filename',
        default='raw-opto-log.csv',
        help='name of the file to log to (default: "raw-opto-log.csv")'
    )

    filename = parser.parse_args().filename

    logging.basicConfig(
        format='%(asctime)s | %(levelname)s | %(name)s: %(message)s',
        datefmt='%I:%M:%S',
        level=logging.INFO,
    )

    with OptoForce() as force_sensor, open(filename, 'w+') as outfile:
        outfile.write('time [H:M:S:f],Fx [N],Fy [N],Fz [N]\n')
        print(f'Writing data to {filename} - press ctrl-c to stop...')

        try:
            while True:
                # take a measurement
                m = force_sensor.read(only_latest_data=False)

                # check that the checksum is valid, and that there weren't any errors
                if not m.valid_checksum:
                    logging.warning("Got message with invalid checksum")

                    continue
                if not status.no_errors(m.status):
                    logging.warning("Got errors in the measurement status")
                    continue

                t = datetime.now().strftime('%H:%M:%S:%f')
                outfile.write(f'{t},{m.Fx},{m.Fy},{m.Fz}\n')
        except KeyboardInterrupt:
            pass
