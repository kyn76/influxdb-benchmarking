import random as rd
import numpy as np
import os
from time import sleep
from flask import Flask, render_template, request
import json 
app = Flask(__name__)





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
PORT_LOAD_BALANCER = os.getenv("PORT_LOAD_BALANCER")
FREQUENCE_PAR_DEFAUT = int(os.getenv("FREQUENCE_PAR_DEFAUT"))

global bandes_temporelles_actuellement_requetees
bandes_temporelles_actuellement_requetees = {
        "1" : [],
        "2" : [],
        "3" : []
}


@app.route("/choix_bdd", methods=['POST'])
def choix_bdd():
    if request.args.get("start_date") is not None:
        start_date = int(request.args.get("start_date"))
        nb_points = int(request.args.get("nb_points"))
        bdd = int(request.args.get("bdd"))
    else:
        
        start_date = int(request.form.get("start_date"))
        nb_points = int(request.form.get("nb_points"))
        bdd = int(request.form.get("bdd"))

    if bdd == 0:
        bande_temporelle_a_requeter = (start_date, start_date + nb_points*FREQUENCE_PAR_DEFAUT)

        bdd_minimisante = minimise_chevauchements(bande_temporelle_a_requeter)

        response = app.response_class(
            response=json.dumps({"bdd_minimisante": bdd_minimisante}),
            status=200,
            mimetype='application/json'
        )
    else:
        response = app.response_class(
            response=json.dumps({"bdd_minimisante": bdd}),
            status=200,
            mimetype='application/json'
        )

    return response

@app.route("/ecriture_bande_temporelle", methods=['POST'])
def ecriture_bande_temporelle():
    if request.args.get("start_date") is not None:
        start_date = int(request.args.get("start_date"))
        nb_points = int(request.args.get("nb_points"))
        bdd = request.args.get("bdd")

    else:
        start_date = int(request.form.get("start_date"))
        nb_points = int(request.form.get("nb_points"))
        bdd = request.form.get("bdd")


    bande_temporelle_a_requeter = (start_date, start_date + nb_points*FREQUENCE_PAR_DEFAUT)
    print("Avant ajout\n\t",bandes_temporelles_actuellement_requetees)
    bandes_temporelles_actuellement_requetees[bdd].append(bande_temporelle_a_requeter)
    print("Apres ajout\n\t",bandes_temporelles_actuellement_requetees)

    return json.dumps({'success':True}), 200, {'ContentType':'application/json'}

@app.route("/liberation_bande_temporelle", methods=['POST'])
def liberation_bande_temporelle():
    if request.args.get("start_date") is not None:
        start_date = int(request.args.get("start_date"))
        nb_points = int(request.args.get("nb_points"))
        bdd = request.args.get("bdd")
    else:
        
        start_date = int(request.form.get("start_date"))
        nb_points = int(request.form.get("nb_points"))
        bdd = request.form.get("bdd")

    bande_temporelle_a_requeter = (start_date, start_date + nb_points*FREQUENCE_PAR_DEFAUT)
    print("Avant libération\n\t",bandes_temporelles_actuellement_requetees)
    bandes_temporelles_actuellement_requetees[bdd].remove(bande_temporelle_a_requeter)
    print("Apres libération\n\t",bandes_temporelles_actuellement_requetees)

    return json.dumps({'success':True}), 200, {'ContentType':'application/json'}

def minimise_chevauchements(bande_temporelle_a_requeter):
    
    minimum_chevauchement, bdd_minimum_chevauchement = float("inf"), "1"

    for BDD in bandes_temporelles_actuellement_requetees:
        bandes_temporelles_bdd = bandes_temporelles_actuellement_requetees[BDD]
        chevauchement = calcul_chevauchement(bandes_temporelles_bdd, bande_temporelle_a_requeter)
        if chevauchement < minimum_chevauchement:
            minimum_chevauchement = chevauchement
            bdd_minimum_chevauchement = BDD
    
    return bdd_minimum_chevauchement

def calcul_chevauchement(bandes_temporelles_bdd, bande_temporelle_a_requeter):
    somme_chevauchement = 0

    for bande_temporelle_actuellement_requetee in bandes_temporelles_bdd:
        ensemble_points_actuellement_requetes = set(np.arange(bande_temporelle_actuellement_requetee[0], bande_temporelle_actuellement_requetee[1] + FREQUENCE_PAR_DEFAUT, FREQUENCE_PAR_DEFAUT))
        ensemble_points_a_requeter = set(np.arange(bande_temporelle_a_requeter[0], bande_temporelle_a_requeter[1] + FREQUENCE_PAR_DEFAUT, FREQUENCE_PAR_DEFAUT))
        nb_intersections_bandes_temporelles = len(ensemble_points_actuellement_requetes.intersection(ensemble_points_a_requeter))
        somme_chevauchement += nb_intersections_bandes_temporelles

    return somme_chevauchement
            
if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=PORT_LOAD_BALANCER)