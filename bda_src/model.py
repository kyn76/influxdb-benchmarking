from influxdb_client import InfluxDBClient
from dotenv import load_dotenv
from statsmodels.tsa.arima.model import ARIMA, ARIMAResults
import os
import pandas as pd
from joblib import dump, load
import requests

class ForecastModel():

    def __init__(self):
        load_dotenv("../.env")
        self.METHODS = "BLOCS, RANDOMS"
        self.PORT = os.getenv("PORT_INFLUX")
        self.IPs = {
            "IP1" : os.getenv("IP_INFLUX_1"),
            "IP2" : os.getenv("IP_INFLUX_2"),
            "IP3" : os.getenv("IP_INFLUX_3")
        }
        self.TOKENS = {
            "TOKEN1" : os.getenv("TOKEN_INFLUX_BDA1"),
            "TOKEN2" : os.getenv("TOKEN_INFLUX_BDA2"),
            "TOKEN3" : os.getenv("TOKEN_INFLUX_BDA3")
        }
        self.IP = ""
        self.TOKEN = ""
        self.ORG = os.getenv("ORG")
        self.BUCKET = os.getenv("BUCKET")
        self.IP_LOAD_BALANCER = os.getenv("IP_LOAD_BALANCER")
        self.PORT_LOAD_BALANCER = os.getenv("PORT_LOAD_BALANCER")
        self.FREQUENCE_PAR_DEFAUT = int(os.getenv("FREQUENCE_PAR_DEFAUT"))


    def fit(self, train_size, offset, bdd):
        """
        Entraîne un modèle ARIMA sur les *train_size* dernières données, avec un offset de *offset* entrées.
        Ex : les arguments "train_size=10, offset=3" vont induire un entraînement du modèle sur les 10 données 
        qui précèdent la 3e entrée la plus récente
        """
        ## trouver start_date et nb_points
        start_date = (50000 - int(offset))*self.FREQUENCE_PAR_DEFAUT
        nb_points = train_size
        
        data = {
            'start_date': start_date,
            'nb_points': nb_points,
            'bdd': bdd
        }

        # Interroge le load-balancer pour savoir quelle BDD interroger étant donnée la requête
        response = requests.post(url=f"http://{self.IP_LOAD_BALANCER}:{self.PORT_LOAD_BALANCER}/choix_bdd", data=data)
        response.raise_for_status()

        # Récupère la réponse JSON et écrit la bande temporelle sur la structure de données du load-balancer
        jsonResponse = response.json()
        bdd_minimisante = jsonResponse["bdd_minimisante"]

        data["bdd"] = bdd_minimisante
        requests.post(url=f"http://{self.IP_LOAD_BALANCER}:{self.PORT_LOAD_BALANCER}/ecriture_bande_temporelle", data=data)

        self.IP = self.IPs[f"IP{bdd_minimisante}"]
        self.TOKEN = self.TOKENS[f"TOKEN{bdd_minimisante}"]
        
        
        client = InfluxDBClient(url=f"http://{self.IP}:{self.PORT}", token=self.TOKEN, org=self.ORG)
        
        
        query_api = client.query_api()

        
        
        # requete qui prend les points les plus récents avec l'offset spécifié, 
        # les garde dans l'ordre chronologique et en fait une table avec les colonnes _time et value (via pivot pour meilleures performances) :
        flux_query = f"""from(bucket:"mybucket")
                            |> range(start: 0, stop: now())
                            |> filter(fn: (r) => r._measurement == "my_metric")
                            |> sort(columns: ["_time"], desc: true)
                            |> limit(n: {1000}, offset: {1000})
                            |> sort(columns: ["_time"], desc: false)
                            |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
                            |> keep(columns: ["_time", "value"])
                    """
        
        records = query_api.query(flux_query)[0]
        
        client.close()

        # Deletion de la bande temporelle requêtée
        
        requests.post(url=f"http://{self.IP_LOAD_BALANCER}:{self.PORT_LOAD_BALANCER}/liberation_bande_temporelle", data=data)

        

        dic = {"timestamp":[], "value":[]}
        for record in records:
            dic["timestamp"].append(record.get_time())
            dic["value"].append(record.values["value"])
        df_train = pd.DataFrame(dic)
        df_train["timestamp"] = pd.to_datetime(df_train["timestamp"])
        df_train.set_index("timestamp", inplace=True)

        arima_model = ARIMA(endog=df_train, order=(1,1,2))
        arima_fitted = arima_model.fit()
        dump(arima_fitted, "../models/arima.joblib")

    
    def predict(self, predict_size):
        """
        Prédit les *predict_size* points suivants à partir du modèle arima entraîné et stocké 
        """
        predict_size=int(predict_size)
        arima_fitted = load("../models/arima.joblib")
        df_pred = arima_fitted.forecast(steps=predict_size)
        df_pred.to_csv(f"../predict/predict_{predict_size}.csv")




        