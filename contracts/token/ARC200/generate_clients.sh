#!/usr/bin/env bash

generate_clients() {
  local artifact="${8}"
  /root/.local/bin/pipenv run algokit compile py \
  --out-dir /artifacts \
  /src/src/contract.py 
  local artifacts=("OSARC200Token" "OSARC200TokenFactory")
  for artifact in "${artifacts[@]}"; do
    /root/.local/bin/pipenv run algokit generate client "/artifacts/${artifact}.arc32.json" --language typescript --output "/artifacts/${artifact}Client.ts"
    jq '.contract' "/artifacts/${artifact}.arc32.json" > "/artifacts/${artifact,,}.contract.json"
  done
}

generate_clients