#!/bin/python3

from generate_data import *
import numpy as np
import matplotlib.pyplot as plt
from sys import argv
from time import time
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
IP_LOAD_BALANCER = os.getenv("IP_LOAD_BALANCER")
PORT_LOAD_BALANCER = os.getenv("PORT_LOAD_BALANCER")

def main():
    if len(argv) != 6:
        usage()
        exit()
    
    
    taille_min = int(argv[1])
    taille_max = int(argv[2])
    nb_echantillons = int(argv[3])
    affichage = int(argv[4])
    db_id = int(argv[5])

    tailles_echantillons = np.geomspace(taille_min, taille_max, nb_echantillons)
    tailles_echantillons = tailles_echantillons.astype(int)
    methodes = ["BLOCS", "RANDOM"]
    bench_par_methode = {}

    for methode in methodes:
        bench_par_methode[methode] = {} 

    bench_par_methode["BLOCS"]["ecritures"], bench_par_methode["BLOCS"]["lectures"], bench_par_methode["BLOCS"]["deletions"] = ecriture_blocs(tailles_echantillons, random=False, bdd_minimisante=db_id)
    
    bench_par_methode["RANDOM"]["ecritures"], bench_par_methode["RANDOM"]["lectures"], bench_par_methode["RANDOM"]["deletions"] = ecriture_blocs(tailles_echantillons, random=True, bdd_minimisante=db_id)
    

    if affichage == 1:
        _ = plt.figure(figsize=(18,8))
        plt.subplot(1,3,1)
        for methode in methodes:
            ecritures = bench_par_methode[methode]["ecritures"]
            _ = plt.plot(tailles_echantillons, ecritures, label=methode)
        _ = plt.legend()
        _ = plt.title(f"Temps d'écriture en fonction de la taille\nà écrire pour toutes les méthodes")
        _ = plt.xlabel("Taille de l'échantillon")
        _ = plt.ylabel("Temps d'écritures de l'échantillon (s)")

        
        plt.subplot(1,3,2)
        for methode in methodes:
            lectures = bench_par_methode[methode]["lectures"]
            _ = plt.plot(tailles_echantillons, lectures, label=methode)
        _ = plt.legend()
        _ = plt.title(f"Temps de lecture en fonction de la taille\nà lire pour toutes les méthodes")
        _ = plt.xlabel("Taille de l'échantillon")
        _ = plt.ylabel("Temps de lecture de l'échantillon (s)")

        plt.subplot(1,3,3)
        for methode in methodes:
            deletions = bench_par_methode[methode]["deletions"]
            _ = plt.plot(tailles_echantillons, deletions, label=methode)
        _ = plt.legend()
        _ = plt.title(f"Temps de délétions en fonction de la taille\nà supprimer pour toutes les méthodes")
        _ = plt.xlabel("Taille de l'échantillon")
        _ = plt.ylabel("Temps de délétions de l'échantillon (s)")
        plt.savefig("benchmarks.jpg")
        plt.show()
    else:
        return ecritures_times, lectures_times, deletions_times


def usage():
    print(f"usage: {argv[0]} TAILLE_MIN TAILLE_MAX NB_POINTS_GRAPHIQUES AFFICHAGE DB_ID")
    print(f"example: python3 benchmarks 100 1000000 100 1 1")


def ecriture_blocs(tailles_echantillons, random=False, bdd_minimisante=0):
    ecritures_times = []
    deletions_times = []
    lectures_times = []
    for taille_echantillon in tailles_echantillons:
        data = {
            'start_date': 0,
            'nb_points': taille_echantillon,
            'bdd': bdd_minimisante
        }

        # Interroge le load-balancer pour savoir quelle BDD interroger étant donnée la requête 
        response = requests.post(url=f"http://{IP_LOAD_BALANCER}:{PORT_LOAD_BALANCER}/choix_bdd", data=data)
        response.raise_for_status()

        # Récupère la réponse JSON et établit la connection correspondante
        jsonResponse = response.json()
        bdd_minimisante = jsonResponse["bdd_minimisante"]
        data['bdd'] = bdd_minimisante

        IP = IPs[f"IP{bdd_minimisante}"]
        TOKEN = TOKENS[f"TOKEN{bdd_minimisante}"]
        
        client = InfluxDBClient(url=f"http://{IP}:{PORT}", token=TOKEN, org=ORG)
        
        # Récupération des API du client en question
        write_api = client.write_api(write_options=SYNCHRONOUS)
        delete_api = client.delete_api()
        query_api = client.query_api()

        # Borne le pas de temps où nous allons écrire 
        date_helper = get_date_helper()
        start_database = date_helper.to_utc(datetime(1970, 1, 1, 0, 0, 0, 0))
        stop_database = date_helper.to_utc(datetime(2200, 1, 1, 0, 0, 0, 0)) # Un poil large :)
        
        delete_api.delete(start_database, stop_database, '_measurement="my_metric"', bucket=BUCKET, org=ORG)

    # Ecrit les différents batch et les chronomètre
        requests.post(url=f"http://{self.IP_LOAD_BALANCER}:{self.PORT_LOAD_BALANCER}/ecriture_bande_temporelle", data=data)

        start_ecriture = time()
        generate(nb_points=taille_echantillon, start_date=0, freq=60, write_api=write_api, random=random)
        end_ecriture = time()
        ecritures_times.append(end_ecriture - start_ecriture)

        # Lecture des données écrites et les times
        query = 'from(bucket:"mybucket")\
                |> range(start: 0)\
                |> filter(fn:(r) => r._measurement == "my_metric")\
                |> filter(fn:(r) => r._field == "value")'
        start_lecture = time()
        result = query_api.query(org=ORG, query=query)
        end_lecture = time()
        lectures_times.append(end_lecture - start_lecture)

        # Supprime les données écrite et les times
        start_deletion = time()
        delete_api.delete(start_database, stop_database, '_measurement="my_metric"', bucket=BUCKET, org=ORG)
        end_deletion = time()
        deletions_times.append(end_deletion - start_deletion)
        #print(f"= {taille_echantillon} données =\n  Ecriture: {end_ecriture-start_ecriture:.4f} s\n  Lecture: {end_lecture-start_lecture:.4f} s\n  Deletion: {end_deletion - start_deletion:.4f} s")
        
        requests.post(url=f"http://{self.IP_LOAD_BALANCER}:{self.PORT_LOAD_BALANCER}/liberation_bande_temporelle", data=data)
        client.close()
    return ecritures_times, lectures_times, deletions_times



if __name__ == "__main__":
    main()
