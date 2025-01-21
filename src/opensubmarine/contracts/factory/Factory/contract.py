from algopy import UInt64, Global, arc4, subroutine, Txn, op
from opensubmarine import Upgradeable
from opensubmarine.utils.algorand import require_payment

##################################################
# BaseFactory
#   factory for airdrop also serves as a base for
#   upgrading contracts if applicable
##################################################

class FactoryCreated(arc4.Struct):
    created_app: arc4.UInt64


class BaseFactory(Upgradeable):
    """
    Base factory for all factories.
    """

    def __init__(self) -> None:  # pragma: no cover
        """
        Initialize factory.
        """
        super().__init__()
        # upgradeable state
        # self.contract_version = UInt64()
        # self.deployment_version = UInt64()
        # self.updatable = bool(1)
        # self.upgrader = Global.creator_address

        ##############################################
        # @arc4.abimethod
        # def create(self, *args) -> UInt64:
        #    return UInt64()
        ##############################################

    @subroutine
    def get_initial_payment(self) -> UInt64:
        """
        Get initial payment.
        When creating a contract, the creator must pay a fee to the factory.
        """
        payment_amount = require_payment(Txn.sender)
        mbr_increase = UInt64(31300) 
        min_balance = op.Global.min_balance  # 100000
        assert (
            payment_amount >= mbr_increase + min_balance
        ), "payment amount accurate"  # 131300
        initial = payment_amount - mbr_increase - min_balance
        return initial
