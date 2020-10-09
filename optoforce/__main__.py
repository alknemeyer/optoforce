import logging
from datetime import datetime
import argparse
from . import OptoForce

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="""
    Gets temperature, humidity and pressure from BME280 sensor on a Raspberry Pi. 
    Can push informations to a  MongpDB Atlas Storage. 
    """)
    parser.add_argument(
        '-f', '--filename',
        default='raw-opto-log.csv',
        help='Name of the file to log to (default: "raw-opto-log.csv")'
    )

    filename = parser.parse_args().filename

    logging.basicConfig(
        format='%(asctime)s | %(levelname)s | %(name)s: %(message)s',
        datefmt='%I:%M:%S',
        level=logging.INFO)

    with OptoForce() as force_sensor, open(filename, 'w+') as outfile:
        outfile.write('time [H:M:S:f],Fx [N],Fy [N],Fz [N]\n')
        print(f'Logging to {filename} - press ctrl-c to stop...')

        while True:
            fx, fy, fz = force_sensor.read(only_latest_data=False)
            t = datetime.now().strftime('%H:%M:%S:%f')
            outfile.write(f'{t},{fx},{fy},{fz}\n')
