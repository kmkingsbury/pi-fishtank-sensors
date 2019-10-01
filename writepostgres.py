import os, sys
import time
import logging
import yaml
import json
import psycopg2
import datetime

logging.basicConfig(level=logging.INFO, format=' %(asctime)s - %(levelname)s - %(message)s')


def on_disconnect(client, userdata, rc):
    logging.info("MQTT Client Got Disconnected")

def on_connect(client, userdata, flags, rc):
    logging.info("MQTT Connected With Result Code "+str(rc))
    logging.info("MQTT Subscribing to topic: " + cfg['mqtt']['topic'])
    client.subscribe(cfg['mqtt']['topic'])

def on_log(client, userdata, level, buf):
    logging.debug("log: " + str(buf))

def on_message(client, userdata, message):
    logging.debug("message received :" + str(message.payload.decode()))
    #logging.debug("message topic=",message.topic)
    #logging.debug("message qos=",message.qos)
    #logging.debug("message retain flag=",message.retain)
    global errorcount
    data = json.loads(message.payload.decode())
    logging.debug("JSON:" + str(data))	
    timestamp = data["datetime"]
    temp = data["koi_temperature"]
    sql = """INSERT into fishtanksensordata (measurement_timestamp,temperature_degf) values (%s,%s)"""
    logging.info("Wrote Message - Timestamp:" + str(timestamp) + ", Data: "  + str(temp) + ", errorcount:" + str(errorcount))
    try:
      cursor.execute(sql, (timestamp, temp))
      conn.commit()
      errorcount = 0
    except (Exception, psycopg2.DatabaseError) as error:
      print(error)
      print("SQL statement:" + sql)
      print("Data: " + str(temp))
      #conn.rollback()
      errorcount = errorcount + 1
      if (errorcount > 5):
         sys.exit()

def writePidFile():
    pid = str(os.getpid())
    currentFile = open('/tmp/writepostgres.pid', 'w')
    currentFile.write(pid)
    currentFile.close()
	
errorcount = 0

with open("config.yml", 'r') as ymlfile:
    cfg = yaml.load(ymlfile)

logging.info("Connecting to Postgres as: " +  cfg['postgres']['user'] )

try:
        connect_str = "dbname='"+ cfg['postgres']['dbname'] +"' user='"+ cfg['postgres']['user'] +"' " + \
                  "host='"+ cfg['postgres']['host'] +"' password='"+ cfg['postgres']['password'] +"'"
        # use our connection values to establish a connection
        conn = psycopg2.connect(connect_str)

        # create a psycopg2 cursor that can execute queries
        cursor = conn.cursor()

except Exception as e:
        print("Uh oh, can't connect. Invalid dbname, user or password?")
        print(e)
        sys.exit()

writePidFile()
logging.info("MQTT Setup - Host: " + cfg['mqtt']['host'] + ", Topic: " + cfg['mqtt']['topic'] )

# MQTT Client setup:
if cfg['mqtt']['enabled'] == True:
   import paho.mqtt.client as mqtt

   # clean_session = True. clean_session is a Boolean value set to True by default. If set to True, the broker removes all the information about the client during disconnection & reconnection. If set to False the broker will retain the subscription information & queued messages during disconnection & reconnection.
   client = mqtt.Client("writepostgres", clean_session=True) #create new instance
   
   # attach functions to callback
   # client.on_log=on_log #useful for debug
   client.on_message = on_message
   client.on_connect = on_connect
   client.on_disconnect = on_disconnect  

   client.connect(cfg['mqtt']['host']) #connect to broker

client.loop_forever()
