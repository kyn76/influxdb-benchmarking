#!/bin/bash
set -x
if [ "$#" -ne 7  ]; then
    echo "usage: $0 USER_TO_CONNECT_AS HOST_TO_LAUNCH_ON TAILLE_MIN TAILLE_MAX NB_POINTS NB_PROCESS BDD_VISEE"
    exit
fi

export $(cat .env | xargs)

USER=$1
HOST=$2
TAILLE_MIN=$3
TAILLE_MAX=$4
NB_POINTS=$5
NB_PROCESS=$6
BDD_VISEE=$7



for (( i=1; i<=$NB_PROCESS ; i++ ))
do 
    nohup ssh ${USER}@${HOST} "export $(cat .env | xargs) ; python3 bda_src/benchmarks.py $TAILLE_MIN $TAILLE_MAX $NB_POINTS 1 $BDD_VISEE" &
done
