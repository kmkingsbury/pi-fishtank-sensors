import os
import glob
import time
import logging
import yaml
import psycopg2
 
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

	

with open("config.yml", 'r') as ymlfile:
    cfg = yaml.load(ymlfile)

logging.debug("DB User  " +  cfg['postgres']['user'] )

try:
        connect_str = "dbname='"+ cfg['postgres']['dbname'] +"' user='"+ cfg['postgres']['user'] +"' " + \
                  "host='"+ cfg['postgres']['host'] +"' password='"+ cfg['postgres']['password'] +"'"
        # use our connection values to establish a connection
        conn = psycopg2.connect(connect_str)

        # create a psycopg2 cursor that can execute queries
        cursor = conn.cursor()

        # create a new table with a single column called "name"
        # cursor.execute("""CREATE TABLE tutorials (name char(40));""")

        # run a SELECT statement - no data in there, but we can try it
        # cursor.execute("""SELECT * from weatherdata""")
        # rows = cursor.fetchall()
        # print("fetch all: " + str(rows))
except Exception as e:
        print("Uh oh, can't connect. Invalid dbname, user or password?")
        print(e)





while True:
	print("Temp (C,F): " + str(read_temp()))	
	time.sleep(1)
