# Smart Contract Token (ARC72)

Implementation of smart contract token for the [ARC72 standard](https://arc.algorand.foundation/ARCs/arc-0072).

## requirements

- algokit >= version 2.0.3
- python >= 3.12.3
- node >= v20.12.2
- puyapy >= 2.2.0

## commands

Import the commands in the shell

```shell
source commands.sh
```

### build all using docker

Build docker image

```shell
arc72-build-image
```
 
Build artifacts

```shell
arc72-build-artifacts
```

Build all
  
```shell
arc72-build-all
```

### unit test

```shell
arc72-pytest
```

### GitHub Actions

To run the GitHub Action workflows locally use [act](https://github.com/nektos/act) to simulate the GitHub Actions environment.

```bash
act -s GITHUB_TOKEN="$(gh auth token)" --container-architecture linux/amd64
```