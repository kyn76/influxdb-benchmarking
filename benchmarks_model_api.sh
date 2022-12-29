#!/bin/bash
set -x
if [ "$#" -ne 1  ]; then
    echo "usage: $0 NB_PROCESS"
    exit
fi

export $(cat .env | xargs)

NB_PROCESS=$1


for (( i=1; i<=$NB_PROCESS ; i++ ))
do 
    nohup python3 bda_src/benchmarks_model_api.py &
done
