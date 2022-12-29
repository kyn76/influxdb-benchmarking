from sys import argv
import os
from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS
import numpy as np
from dotenv import load_dotenv
import time

load_dotenv("../.env")

PORT = os.getenv("PORT_INFLUX")
IPs = {"IP1" : os.getenv("IP_INFLUX_1"),
       "IP2" : os.getenv("IP_INFLUX_2"),
       "IP3" : os.getenv("IP_INFLUX_3")
}

TOKENS = {
    "TOKEN1" : os.getenv("TOKEN_INFLUX_BDA1"),
    "TOKEN2" : os.getenv("TOKEN_INFLUX_BDA2"),
    "TOKEN3" : os.getenv("TOKEN_INFLUX_BDA3")
}

ORG = os.getenv("ORG")
BUCKET = os.getenv("BUCKET")


def main():
    if len(argv) < 5:
        usage()
        exit(1)

    nb_points = int(argv[1])
    start_date = int(argv[2])
    freq = int(argv[3])
    db_id = int(argv[4])
    IP = IPs[f"IP{db_id}"]
    TOKEN = TOKENS[f"TOKEN{db_id}"]
    client = InfluxDBClient(url=f"http://{IP}:{PORT}", token=TOKEN, org=ORG)
    write_api = client.write_api(write_options=SYNCHRONOUS)
    generate(nb_points, start_date, freq, write_api)
    client.close()


def usage():
    print("usage : python3 generate_data.py <nb_points> <start_date (epoch in s)> <frequence (sec)> <db_id>")
    print("example: python3 generate_data.py 100 1666000000 60 1")


def epoch_to_string(epoch_time):
    return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(epoch_time))


def generate(nb_points, start_date, freq, write_api, random=False):
    dates = [start_date + k*freq for k in range(nb_points)]
    T = 10
    X = np.linspace(0, 100, nb_points)
    y = 100 * ( np.sin(X) + np.sin(2*np.pi*(1/T)*X) ) + np.random.normal(20, 5, size=X.shape[0]) 
    #double périodicité (2 sin avec périodes différentes) et bruit
    index_dates = np.arange(nb_points)
    if random:
        np.random.shuffle(index_dates)
    
    records = []
    for i in index_dates:
        date = dates[i]
        value = y[i]
        record = {}
        record["measurement"] = "my_metric"
        record["time"] = epoch_to_string(date)
        record["fields"] = {"value": value}
        records.append(record)
    
    write_api.write(bucket=BUCKET, record=records)
    
if __name__ == "__main__":
    main()
