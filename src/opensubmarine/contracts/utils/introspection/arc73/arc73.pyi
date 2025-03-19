from algopy import ARC4Contract, arc4

class ARC73SupportsInterface(ARC4Contract):
    def supportsInterface(self, interface_id: arc4.Bytes) -> arc4.Bool: ...
