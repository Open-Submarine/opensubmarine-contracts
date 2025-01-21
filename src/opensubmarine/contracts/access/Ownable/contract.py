from typing import Type
from algopy import ARC4Contract, Account, Txn, arc4

##################################################
# Ownable
#   allows contract to be owned
##################################################


class OwnershipTransferred(arc4.Struct):
    previousOwner: arc4.Address
    newOwner: arc4.Address


class OwnableInterface(ARC4Contract):
    """
    Interface for all abimethods operated by owner.
    """

    def __init__(self) -> None:  # pragma: no cover
        self.owner = Account()

    @arc4.abimethod
    def transfer(self, new_owner: arc4.Address) -> None:  # pragma: no cover
        """
        Transfer ownership of the contract to a new owner. Emits OwnershipTransferred event.
        """
        pass


class Ownable(OwnableInterface):
    def __init__(self) -> None:  # pragma: no cover
        super().__init__()

    @arc4.abimethod
    def transfer(self, new_owner: arc4.Address) -> None:
        assert Txn.sender == self.owner, "must be owner"
        arc4.emit(OwnershipTransferred(arc4.Address(self.owner), new_owner))
        self.owner = new_owner.native
