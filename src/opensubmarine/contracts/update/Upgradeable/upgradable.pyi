from algopy import ARC4Contract, Account, UInt64

class Upgradeable(ARC4Contract):
    owner: Account
    contract_version: UInt64
    deployment_version: UInt64
    updatable: bool
    upgrader: Account
