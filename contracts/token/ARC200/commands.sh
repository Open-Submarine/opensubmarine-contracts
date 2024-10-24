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
arc200-cli() {
  (
    cd src/scripts
    npx tsc
    node main.js ${@}
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
