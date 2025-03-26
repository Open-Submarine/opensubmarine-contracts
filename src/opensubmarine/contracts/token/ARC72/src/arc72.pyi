from algopy import Account, ARC4Contract, BigUInt, Bytes
from opensubmarine import arc72_nft_data, arc72_holder_data

class ARC72Token(ARC4Contract):
    totalSupply: BigUInt
    nft_data: dict[BigUInt, arc72_nft_data]
    nft_operators: dict[Bytes, bool]
    nft_index: dict[BigUInt, BigUInt]
    holder_data: dict[Account, arc72_holder_data]