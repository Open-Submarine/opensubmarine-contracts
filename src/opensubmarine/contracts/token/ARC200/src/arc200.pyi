from typing import Any
from algopy import ARC4Contract, Account, String, UInt64, BigUInt, Bytes

class ARC200Token(ARC4Contract):
    name: String
    symbol: String
    decimals: UInt64
    totalSupply: BigUInt
    balances: dict[Account, BigUInt]
    approvals: dict[Bytes, BigUInt]
