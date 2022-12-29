
# Annexe technique
## API du modèle  
Lancer l'API depuis bda_src sur MIDDLEWARE1:  
```bash
python3 model_api.py 
```

Lancer l'entraînement d'un modèle ARIMA sur les dernières 900 entrées avec un offset de 100 entrées (on ignore les 100 plus récentes, on prend les 900 qui précèdent) en passant par le load-balancer pour choisir la bdd:  
```bash
curl "http://${IP_MODEL_API}:${PORT_MODEL_API}/api/train?train_size=900&offset=100&bdd=0"
```

Idem mais en forçant la sélection de la BDD 1 par le load-balancer:  
```bash
curl "http://${IP_MODEL_API}:${PORT_MODEL_API}/api/train?train_size=900&offset=100&bdd=I"
```

Lancer la prédiction sur les 100 prochaines valeurs :  
```bash
curl "http://${IP_MODEL_API}:${PORT_MODEL_API}/api/predict?predict_size=100"
```
## API du Load-Balancer
Lancer l'API du load-balancer sur MIDDLEWARE2:
```bash
python3 bda_src/load-balancer.py
```

Savoir quelle BDD minimisera la quantité de chevauchement pour une date initiale de 10000 (timestamp), et un nombre de points donné de 1000:  
```bash
curl "http://${IP_LOAD_BALANCER}:${PORT_LOAD_BALANCER}/choix_bdd?start_date=10000&nb_points=1000&bdd=0"
```

Forcer à passer par la BDD BDA1 pour une date initiale de 10000 (timestamp), et un nombre de points donné de 1000:  
```bash
curl "http://${IP_LOAD_BALANCER}:${PORT_LOAD_BALANCER}/choix_bdd?start_date=10000&nb_points=1000&bdd=1"
```

Ecrire que l'on va requêter la bande temporelle pour la BDD BDA1 pour une date initiale de 10000 (timestamp), et un nombre de points donné de 1000:  
```bash
curl "http://${IP_LOAD_BALANCER}:${PORT_LOAD_BALANCER}/ecriture_bande_temporelle?start_date=10000&nb_points=1000&bdd=1"
```

Ecrire que l'on a libéré la bande temporelle pour la BDD BDA1 pour une date initiale de 10000 (timestamp), et un nombre de points donné de 1000:  
```bash
curl "http://${IP_LOAD_BALANCER}:${PORT_LOAD_BALANCER}/ecriture_bande_temporelle?start_date=10000&nb_points=1000&bdd=1"
```

## Génération et Bench
Générer 50000 points dans les 3 BDD en partant de la timestamp 0 avec une fréquence de 10 secondes:  
```bash
python3 bda_src/generate_data.py 50000 0 10 1 && \
python3 bda_src/generate_data.py 50000 0 10 2 && \
python3 bda_src/generate_data.py 50000 0 10 3
```

Lancer un tir contre les BDD sans utiliser le modèle après avoir lancé les deux API tel qu'indiqué au dessus, en tant que ubuntu sur la machine `middleware` (ssh config) avec 100 points minimum, 50000 points maximum, 15 points sur le graphique, la sauvegarde du png (1) et en utilisant le load-balancer (0):   
```bash
bash benchmarks.sh 44 /mnt/c/Users/Nathan/Desktop/benchs ubuntu middleware 100 50000 15 1 0
```

Lancer un tir sur le temps d'entraînement du modèle avec 8 processus concurrents après avoir lancé les deux API tel qu'indiqué au dessus:  
```bash
bash benchmarks_model_api.sh 8
```