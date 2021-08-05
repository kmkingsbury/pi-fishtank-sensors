import os
import logging
import yaml
import json
import time
import paho.mqtt.client as mqtt
from influxdb import InfluxDBClient


def on_connect(client, userdata, flags, rc):
    # Print result of connection attempt
    logger.debug("Connected with result code {0}".format(str(rc)))

    # Subscribe to the topic, receive any messages published on it
    client.subscribe(cfg['mqtt']['topic'])

    # Print result of connection attempt
    logger.debug("Subscribed to: " + cfg['mqtt']['topic'])


def on_message(client, userdata, message):
    # logging.debug("message received :" + str(message.payload.decode()))
    # logging.debug("message topic=", message.topic)
    # logging.debug("message qos=", message.qos)
    # logging.debug("message retain flag=", message.retain)

    global errorcount
    data = json.loads(message.payload.decode())
    logger.debug("JSON from MQTT:" + str(data))
    timestamp = data["datetime"]
    temp = data["koi_temperature"]
    dist = data["koi_distance"]
    json_body = []
    if str(temp) != 'None':
        json_body.append({
            "measurement": 'temperature',
            "tags": {
                "sensorlocation": 'koi fishtank',
                "sensorId": str(cfg['climate']['sensorid'])
            },
            "timestamp": timestamp.replace(" ", "T") + "Z",
            "fields": {
                'value': float(temp)
            }
        })
    if str(dist) != 'None':
        json_body.append({
            "measurement": 'water level',
            "tags": {
                "sensorlocation": 'koi fishtank',
                "sensorId": "RCWL-1601-A"
            },
            "timestamp": timestamp.replace(" ", "T") + "Z",
            "fields": {
                'value': float(dist)
            }
        })
    logger.debug("JSON Block: " + str(json_body))
    if len(json_body) >= 1:
        try:
            influxclient.write_points(json_body)
        except InfluxDBClientError:
            logger.debug('Error saving event "%s" to InfluxDB', json_body)


def writePidFile():
    pid = str(os.getpid())
    currentFile = open('/tmp/writeinfluxdb.pid', 'w')
    currentFile.write(pid)
    currentFile.close()


logger = logging.getLogger('writeinfluxdb')
logger.setLevel(logging.DEBUG)

fh = logging.FileHandler('/tmp/writeinfluxdb.log')
fh.setLevel(logging.DEBUG)

ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)

logger.addHandler(fh)
logger.addHandler(ch)

writePidFile()

with open("config.yml", 'r') as ymlfile:
    cfg = yaml.load(ymlfile, Loader=yaml.FullLoader)

influxclient = InfluxDBClient(host=cfg['influxdb']['host'],
                              port=cfg['influxdb']['port'])
influxclient.switch_database(cfg['influxdb']['dbname'])
# client.create_database('writetest')


# Setup MQTT
client = mqtt.Client("writeinfluxdb")  # create new instance
# Loop start: These functions implement a threaded interface to the network
# loop. Calling loop_start() once, before or after connect*(), runs a thread
# in the background to call loop() automatically. This frees up the main
# thread for other work that may be blocking.
# client.loop_start()

# Define callback function for successful connection
client.on_connect = on_connect

# Define callback function for receipt of a message
client.on_message = on_message

client.connect(cfg['mqtt']['host'])  # connect to broker
client.loop_forever()  # Start networking daemon
while True:
    time.sleep(0.01)
