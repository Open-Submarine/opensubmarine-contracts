#!/usr/bin/env bash

generate_clients() {
  local artifact="${8}"
  algokit compile py \
  --out-dir /artifacts \
  /src/src/contract.py 
  local artifacts=("OSARC200Token" "OSARC200TokenFactory")
  for artifact in "${artifacts[@]}"; do
    algokit generate client "/artifacts/${artifact}.arc32.json" --language typescript --output "/artifacts/${artifact}Client.ts"
    jq '.contract' "/artifacts/${artifact}.arc32.json" > "/artifacts/${artifact,,}.contract.json"
  done
}

generate_clients