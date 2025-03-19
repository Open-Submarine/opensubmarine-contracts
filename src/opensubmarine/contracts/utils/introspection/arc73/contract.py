from algopy import ARC4Contract, arc4, Bytes, subroutine
from opensubmarine.utils.types import Bytes4


class IARC73SupportsInterface(ARC4Contract):
    @arc4.abimethod(readonly=True)
    def supportsInterface(self, interface_id: Bytes4) -> arc4.Bool:
        return arc4.Bool(self._supportsInterface(interface_id.bytes))

    @subroutine
    def _supportsInterface(self, interface_id: Bytes) -> bool:
        return False


class ARC73SupportsInterface(IARC73SupportsInterface):
    @subroutine
    def _supportsInterface(self, interface_id: Bytes) -> bool:
        if interface_id == Bytes.from_hex("4e22a3ba"):  # ARC73 supports interface
            return True
        elif interface_id == Bytes.from_hex("ffffffff"):  # mask
            return False
        else:
            return False
