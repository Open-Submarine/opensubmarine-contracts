#!/bin/bash
arc72-build-image() {
  docker build . -t algokit-builder
}
arc72-build-artifacts() {
  docker run -v $(pwd):/src -v $(pwd)/artifacts:/artifacts algokit-builder && 
  cp -v artifacts/OSARC72TokenClient.ts ./src/scripts/clients/ 
}
arc72-build-all() {
  arc72-build-image && arc72-build-artifacts
}
arc72-simulate() {
  (
    cd src
    python simulate.py
  )
}
arc72-cli() {
  (
    cd src/scripts
    source demo/utils.sh
    npx tsc
    cli ${@}
  )
}
arc72-check-mab() {
  (
    bash check_mab.sh
  )
}
arc72-pytest() {
  (
    cd src
    pytest
  )
}
arc72-demo() {
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
arc72-mocha() {
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
arc72-plot() {
  (
    cd src
    python plot-staking.py
  )
}
arc72-program() {
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
arc72-program

  execute a program

  USAGE scs-program airdrop [command] [args]

EOF
        false
      } ;;
    esac
  )
}
