from algopy import UInt64, arc4, subroutine, Txn, op, ARC4Contract
from opensubmarine.utils.algorand import require_payment

##################################################
# BaseFactory
#   factory for airdrop also serves as a base for
#   upgrading contracts if applicable
##################################################


class FactoryCreated(arc4.Struct):
    created_app: arc4.UInt64


class BaseFactory(ARC4Contract):
    """
    Base factory for all factories.
    """

    @subroutine
    def get_initial_payment(self, mbr_increase: UInt64) -> UInt64:
        """
        Get initial payment.
        When creating a contract, the creator must pay a fee to the factory.
        """
        payment_amount = require_payment(Txn.sender)
        min_balance = op.Global.min_balance  # 100000
        min_balance = op.Global.min_balance  # 100000
        assert (
            payment_amount >= mbr_increase + min_balance
        ), "payment amount accurate"  # 131300
        initial = payment_amount - mbr_increase - min_balance
        return initial
