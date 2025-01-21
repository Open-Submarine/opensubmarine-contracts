from algopy import ARC4Contract, Account

class Stakeable(ARC4Contract):
    delegate: Account
    stakeable: bool
    def __init__(self) -> None: ...

