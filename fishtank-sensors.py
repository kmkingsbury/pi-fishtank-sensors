import os
import glob
import time
import logging
import yaml
import datetime
from gpiozero import DistanceSensor
# from gpiozero.pins.pigpio import PiGPIOFactory


# Pull in 1 Wire capablities
os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')

# Without a 1-wire device recognized here the code will crash/exit.
base_dir = '/sys/bus/w1/devices/'
device_folder = glob.glob(base_dir + '28*')[0]
device_file = device_folder + '/w1_slave'

# Setup Logger
# logging.disable(logging.DEBUG)
logging.basicConfig(level=logging.DEBUG,
                    format=' %(asctime)s - %(levelname)s - %(message)s')

# keep decimal to ensure float
sleeptime = 5.0

# Pins for the sensor.
echo_pin = 23
trigger_pin = 24

# Switch from default to potentially more accurate readings.
# factory = PiGPIOFactory()
# need pigpio daemon:
# sudo pigpiod

# Create empty list-type variable so we can
# store measurements
sensor_measurements = []

# For the Distance Sensor
# Declare these variables at a top level so you can
# easily edit them once for your whole script to
# test performance
upper_reasonable_bound = 200
lower_reasonable_bound = 0
rolling_average_size = 10

# Limits for temperature sensor
temp_low = 25
temp_high = 95


# 1-wire read
def read_temp_raw():
    f = open(device_file, 'r')
    lines = f.readlines()
    f.close()
    return lines


# 1-wire read and convert
def read_temp():
    lines = read_temp_raw()
    # Example:
    # Lines: ['a0 01 4b 46 7f ff 0c 10 cf : crc=cf YES\n', 'a0 01 4b 46 7f ff 0c 10 cf t=26000\n']
    # print("Lines: " + str(lines))
    if (len(lines) < 1 or len(lines[0]) < 3): return None, None
    while lines[0].strip()[-3:] != 'YES':
        time.sleep(0.2)
        lines = read_temp_raw()
    equals_pos = lines[1].find('t=')
    if equals_pos != -1:
        temp_string = lines[1][equals_pos+2:]
        temp_c = float(temp_string) / 1000.0
        temp_f = temp_c * 9.0 / 5.0 + 32.0

        # Check that temperature is within limits.
        if temp_f > temp_high or temp_f < temp_low: 
            return None, None
        return temp_c, temp_f


# PID file for monit
def writePidFile():
    pid = str(os.getpid())
    currentFile = open('/tmp/1-wire.pid', 'w')
    currentFile.write(pid)
    currentFile.close()


def average(measurements):
    """
    Use the builtin functions sum and len to make a quick average function
    """
    # Handle division by zero error
    if len(measurements) != 0:
        return sum(measurements)/len(measurements)
    else:
        # When you use the average later, make sure to include something like
        # sensor_average = rolling_average(sensor_measurements)
        # if (conditions) and sensor_average > -1:
        # This way, -1 can be used as an "invalid" value
        return -1


def rolling_average(measurement, measurements):
    # Update rolling average if measurement is ok, otherwise
    # skip to returning the average from previous values
    if lower_reasonable_bound < measurement < upper_reasonable_bound:
        # Remove first item from list if it's full according to our chosen size
        if len(measurements) >= rolling_average_size:
            measurements.pop(0)
        measurements.append(measurement)
    return average(measurements)


errorcount = 0

# device configs
with open("config.yml", 'r') as ymlfile:
    cfg = yaml.load(ymlfile, Loader=yaml.FullLoader)

# Setup MQTT
client = ''
if cfg['mqtt']['enabled'] is True:
    import paho.mqtt.client as mqtt
    client = mqtt.Client("P1")  # create new instance
    client.connect(cfg['mqtt']['host'])  # connect to broker
    # Loop start: These functions implement a threaded interface
    # to the network loop. Calling loop_start() once, before or after
    # connect*(), runs a thread in the background to call loop()
    # automatically. This frees up the main thread for other work
    # that may be blocking.
    client.loop_start()

writePidFile()
dist_sensor = DistanceSensor(echo=echo_pin, trigger=trigger_pin)  #, pin_factory=factory)
starttime = time.time()
while True:
    # 1 -wire read:
    temps = read_temp()
    # print("Temp (C,F): " + str(temps))

    # Distance Sensor measurement
    sensor_measurement = (dist_sensor.distance * 100)
    sensor_value = rolling_average(sensor_measurement, sensor_measurements)

    # fix for JSON, MQTT, InfluxDB
    s = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')
    timestamp = s[:-3]
    logging.debug("Timestamp, Data: " + str(timestamp) + ", " + str(temps[1])
                  + ", Distance: " + str("{:.2f}".format(sensor_value)))
    if cfg['mqtt']['enabled'] is True:
        client.publish(cfg['mqtt']['topic'],  '{ "koi_temperature":"' +
                       str(temps[1]) + '", "datetime":"' + str(timestamp) +
                       '", "koi_distance":"' +
                       str("{:.2f}".format(sensor_value))
                       + '" }')  # publish to mqtt
    time.sleep(sleeptime - ((time.time() - starttime) % sleeptime))
