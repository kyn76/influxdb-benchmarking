#!/bin/python3

from generate_data import *
import numpy as np
import matplotlib.pyplot as plt
from sys import argv
from time import time, sleep
from datetime import datetime
from influxdb_client.client.util.date_utils import get_date_helper
from influxdb_client.client.write_api import SYNCHRONOUS
from generate_data import generate
import os
import requests
import json

METHODS = "BLOCS, RANDOMS"
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
IP_MODEL_API = os.getenv("IP_MODEL_API")
PORT_MODEL_API = os.getenv("PORT_MODEL_API")

def main():
    
    taille_min = 500
    taille_max = 3000
    tailles_echantillons = np.geomspace(taille_min, taille_max, 8)
    tailles_echantillons = tailles_echantillons.astype(int)

    offset = 5000
    

    entrainement_sans = chrono_entrainements(tailles_echantillons, offset, bdd_minimisante=2)
    sleep(600)
    entrainement_avec = chrono_entrainements(tailles_echantillons, offset, bdd_minimisante=0)
    

    _ = plt.figure(figsize=(12,8))
    _ = plt.plot(tailles_echantillons, entrainement_sans, label="Sans load-balancer actif")
    _ = plt.plot(tailles_echantillons, entrainement_avec, label="Avec load-balancer actif")
    _ = plt.legend()
    _ = plt.title(f"Temps d'entraînement en fonction de la taille\nà d'entraînemnt avec et sans load-balancer")
    _ = plt.xlabel("Taille de l'échantillon")
    _ = plt.ylabel("Temps d'entraînement de l'échantillon (s)")
    plt.savefig("benchmarks_model_api.jpg")
    plt.show()

def chrono_entrainements(tailles_echantillons=[900], offset=100, bdd_minimisante=0):
    temps_entrainements = []
    for taille_echantillon in tailles_echantillons:
        
        data = {
            "train_size": taille_echantillon,
            "offset": offset,
            "bdd": bdd_minimisante
        }

        start_train = time()
        response = requests.get(url=f"http://{IP_MODEL_API}:{PORT_MODEL_API}/api/train", data=data)
        end_train = time()

        temps_entrainements.append(end_train - start_train)

    return temps_entrainements



if __name__ == "__main__":
    main()
