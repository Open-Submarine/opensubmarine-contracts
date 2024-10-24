#!/bin/bash
arc200-build-image() {
  docker build . -t algokit-builder
}
arc200-build-artifacts() {
  docker run -v $(pwd):/src -v $(pwd)/artifacts:/artifacts algokit-builder && 
  cp -v artifacts/OSARC200TokenClient.ts ./src/scripts/clients/ && 
  cp -v artifacts/OSARC200TokenFactoryClient.ts ./src/scripts/clients/ && 
}
arc200-build-all() {
  arc200-build-image && arc200-build-artifacts
}
arc200-simulate() {
  (
    cd src
    python simulate.py
  )
}
arc200-cli() {
  (
    cd src/scripts
    source demo/utils.sh
    npx tsc
    cli ${@}
  )
}
arc200-check-mab() {
  (
    bash check_mab.sh
  )
}
arc200-pytest() {
  (
    cd src
    pytest
  )
}
arc200-demo() {
  (
    cd src/scripts
    npx tsc
    case ${1} in
      "airdrop") {
        bash demo/demo-contract-${1}.sh
      } ;;
      "staking") {
        bash demo/demo-contract-${1}.sh
      } ;;
      "compensation") {
        bash demo/demo-contract-${1}.sh
      } ;;
      *) {
        echo "demo not found"
        false
      } ;;
    esac
  )
}
arc200-mocha() {
  (
    set -e
    cd src/scripts
    npx tsc
    test ${#} -eq 0 && {
      npm test
      true
    } || {
      npm run test-${1}
    }
  )
}
arc200-plot() {
  (
    cd src
    python plot-staking.py
  )
}
arc200-program() {
  (
    set -e
    cd src/scripts/program
    npx tsc 
    case ${1} in
      airdrop|airdrop2|staking) {
        node ${1}.js ${@:2}
      } ;;
      *) {
        cat << EOF
arc200-program

  execute a program

  USAGE scs-program airdrop [command] [args]

EOF
        false
      } ;;
    esac
  )
}
