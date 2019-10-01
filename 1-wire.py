import os, sys
import glob
import time
import logging
import yaml
import datetime

os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')
 
base_dir = '/sys/bus/w1/devices/'
device_folder = glob.glob(base_dir + '28*')[0]
device_file = device_folder + '/w1_slave'

#logging.disable(logging.DEBUG)

logging.basicConfig(level=logging.DEBUG, format=' %(asctime)s - %(levelname)s - %(message)s')


def read_temp_raw():
    f = open(device_file, 'r')
    lines = f.readlines()
    f.close()
    return lines

def read_temp():
    lines = read_temp_raw()
    while lines[0].strip()[-3:] != 'YES':
        time.sleep(0.2)
        lines = read_temp_raw()
    equals_pos = lines[1].find('t=')
    if equals_pos != -1:
        temp_string = lines[1][equals_pos+2:]
        temp_c = float(temp_string) / 1000.0
        temp_f = temp_c * 9.0 / 5.0 + 32.0
        return temp_c, temp_f

def writePidFile():
    pid = str(os.getpid())
    currentFile = open('/tmp/1-wire.pid', 'w')
    currentFile.write(pid)
    currentFile.close()
	
errorcount = 0

with open("config.yml", 'r') as ymlfile:
    cfg = yaml.load(ymlfile)

# Setup MQTT
client = ''
if cfg['mqtt']['enabled'] == True:
   import paho.mqtt.client as mqtt
   client = mqtt.Client("P1") #create new instance
   client.connect(cfg['mqtt']['host']) #connect to broker
   # Loop start: These functions implement a threaded interface to the network loop. Calling loop_start() once, before or after connect*(), runs a thread in the background to call loop() automatically. This frees up the main thread for other work that may be blocking.
   client.loop_start()

writePidFile()
while True:
  temps = read_temp()
  print("Temp (C,F): " + str(temps))	
  s = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')
  timestamp =  s[:-3]
  logging.debug("Timestamp, Data: " + str(timestamp) + ", " + str(temps[1]))
  if cfg['mqtt']['enabled'] == True:
    client.publish(cfg['mqtt']['topic'],  '{ "koi_temperature":"' + str(temps[1]) + '", "datetime":"' + str(timestamp) + '" }') # publish to mqtt
  time.sleep(4)
