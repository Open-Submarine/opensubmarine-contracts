import typing
from algopy import (
    ARC4Contract,
    Account,
    BigUInt,
    BoxMap,
    Bytes,
    Global,
    OnCompleteAction,
    String,
    Txn,
    UInt64,
    arc4,
    compile_contract,
    itxn,
    op,
    subroutine,
)
from utils import require_payment, close_offline_on_delete

Bytes8: typing.TypeAlias = arc4.StaticArray[arc4.Byte, typing.Literal[8]]
Bytes32: typing.TypeAlias = arc4.StaticArray[arc4.Byte, typing.Literal[32]]
Bytes64: typing.TypeAlias = arc4.StaticArray[arc4.Byte, typing.Literal[64]]

mint_fee = 1000000
mint_cost = 31300


class PartKeyInfo(arc4.Struct):
    address: arc4.Address
    vote_key: Bytes32
    selection_key: Bytes32
    vote_first: arc4.UInt64
    vote_last: arc4.UInt64
    vote_key_dilution: arc4.UInt64
    state_proof_key: Bytes64


##################################################
# Receiver
#   reference to messenger
##################################################


class ReceiverInterface(ARC4Contract):
    """
    Interface for all abimethods of receiver contract.
    """

    def __init__(self) -> None:  # pragma: no cover
        self.messenger_id = UInt64()


class Receiver(ReceiverInterface):
    def __init__(self) -> None:  # pragma: no cover
        super().__init__()


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


##################################################
# Stakeable
#   allows contract to participate in consensus,
#   stake
##################################################


class DelegateUpdated(arc4.Struct):
    previousDelegate: arc4.Address
    newDelegate: arc4.Address


class Participated(arc4.Struct):
    who: arc4.Address
    partkey: PartKeyInfo


class StakeableInterface(ARC4Contract):
    """
    Interface for all abimethods of stakeable contract.
    """

    def __init__(self) -> None:  # pragma: no cover
        self.delegate = Account()
        self.stakeable = bool(1)

    @arc4.abimethod
    def set_delegate(self, delegate: arc4.Address) -> None:  # pragma: no cover
        """
        Set delegate.
        """
        pass

    @arc4.abimethod
    def participate(
        self,
        vote_k: Bytes32,
        sel_k: Bytes32,
        vote_fst: arc4.UInt64,
        vote_lst: arc4.UInt64,
        vote_kd: arc4.UInt64,
        sp_key: Bytes64,
    ) -> None:  # pragma: no cover
        """
        Participate in consensus.
        """
        pass


class Stakeable(StakeableInterface, OwnableInterface):
    def __init__(self) -> None:  # pragma: no cover
        # ownable state
        self.owner = Account()
        # stakeable state
        self.delegate = Account()  # zero address
        self.stakeable = bool(1)  # 1 (Default unlocked)

    @arc4.abimethod
    def set_delegate(self, delegate: arc4.Address) -> None:
        assert (
            Txn.sender == self.owner or Txn.sender == Global.creator_address
        ), "must be owner or creator"
        arc4.emit(DelegateUpdated(arc4.Address(self.delegate), delegate))
        self.delegate = delegate.native

    @arc4.abimethod
    def participate(
        self,
        vote_k: Bytes32,
        sel_k: Bytes32,
        vote_fst: arc4.UInt64,
        vote_lst: arc4.UInt64,
        vote_kd: arc4.UInt64,
        sp_key: Bytes64,
    ) -> None:
        ###########################################
        assert (
            Txn.sender == self.owner or Txn.sender == self.delegate
        ), "must be owner or delegate"
        ###########################################
        key_reg_fee = Global.min_txn_fee
        # require payment of min fee to prevent draining
        assert require_payment(Txn.sender) == key_reg_fee, "payment amout accurate"
        ###########################################
        arc4.emit(
            Participated(
                arc4.Address(Txn.sender),
                PartKeyInfo(
                    address=arc4.Address(Txn.sender),
                    vote_key=vote_k,
                    selection_key=sel_k,
                    vote_first=vote_fst,
                    vote_last=vote_lst,
                    vote_key_dilution=vote_kd,
                    state_proof_key=sp_key,
                ),
            )
        )
        itxn.KeyRegistration(
            vote_key=vote_k.bytes,
            selection_key=sel_k.bytes,
            vote_first=vote_fst.native,
            vote_last=vote_lst.native,
            vote_key_dilution=vote_kd.native,
            state_proof_key=sp_key.bytes,
            fee=key_reg_fee,
        ).submit()


##################################################
# Upgradeable
#   allows contract to be updated
##################################################


class VersionUpdated(arc4.Struct):
    contract_version: arc4.UInt64
    deployment_version: arc4.UInt64


class UpdateApproved(arc4.Struct):
    who: arc4.Address
    approval: arc4.Bool


class UpgraderGranted(arc4.Struct):
    previousUpgrader: arc4.Address
    newUpgrader: arc4.Address


class UpgradeableInterface(ARC4Contract):
    """
    Interface for all abimethods of upgradeable contract.
    """

    def __init__(self) -> None:  # pragma: no cover
        self.contract_version = UInt64()
        self.deployment_version = UInt64()
        self.updatable = bool(1)
        self.upgrader = Account()

    @arc4.abimethod
    def set_version(
        self, contract_version: arc4.UInt64, deployment_version: arc4.UInt64
    ) -> None:  # pragma: no cover
        """
        Set contract and deployment version.
        """
        pass

    @arc4.abimethod
    def on_update(self) -> None:  # pragma: no cover
        """
        On update.
        """
        pass

    @arc4.abimethod
    def approve_update(self, approval: arc4.Bool) -> None:  # pragma: no cover
        """
        Approve update.
        """
        pass

    @arc4.abimethod
    def grant_upgrader(self, upgrader: arc4.Address) -> None:  # pragma: no cover
        """
        Grant upgrader.
        """
        pass

    ##############################################
    # @arc4.abimethod
    # def update(self) -> None:
    #      pass
    ##############################################


class Upgradeable(UpgradeableInterface, OwnableInterface):
    def __init__(self) -> None:  # pragma: no cover
        # ownable state
        self.owner = Account()
        # upgradeable state
        self.contract_version = UInt64()
        self.deployment_version = UInt64()
        self.updatable = bool(1)
        self.upgrader = Global.creator_address

    @arc4.abimethod
    def set_version(
        self, contract_version: arc4.UInt64, deployment_version: arc4.UInt64
    ) -> None:
        assert Txn.sender == self.upgrader, "must be upgrader"
        arc4.emit(VersionUpdated(contract_version, deployment_version))
        self.contract_version = contract_version.native
        self.deployment_version = deployment_version.native

    @arc4.baremethod(allow_actions=["UpdateApplication"])
    def on_update(self) -> None:
        ##########################################
        # WARNING: This app can be updated by the creator
        ##########################################
        assert Txn.sender == self.upgrader, "must be upgrader"
        assert self.updatable == UInt64(1), "not approved"
        ##########################################

    @arc4.abimethod
    def approve_update(self, approval: arc4.Bool) -> None:
        assert Txn.sender == self.owner, "must be owner"
        arc4.emit(UpdateApproved(arc4.Address(self.owner), approval))
        self.updatable = approval.native

    @arc4.abimethod
    def grant_upgrader(self, upgrader: arc4.Address) -> None:
        assert Txn.sender == Global.creator_address, "must be creator"
        arc4.emit(UpgraderGranted(arc4.Address(self.upgrader), upgrader))
        self.upgrader = upgrader.native


##################################################
# Deployable
#   ensures that contract is created by factory
#   and recorded
##################################################


class DeployableInterface(ARC4Contract):
    """
    Interface for all abimethods of deployable contract.
    """

    def __init__(self) -> None:  # pragma: no cover
        self.parent_id = UInt64()
        self.deployer = Account()

    @arc4.abimethod(create="require")
    def on_create(self) -> None:  # pragma: no cover
        """
        Execute on create.
        """
        pass


class Deployable(DeployableInterface):
    def __init__(self) -> None:  # pragma: no cover
        super().__init__()

    @arc4.baremethod(create="require")
    def on_create(self) -> None:
        caller_id = Global.caller_application_id
        assert caller_id > 0, "must be created by factory"
        self.parent_id = caller_id


##################################################
# ARC200Token
#   token contract
##################################################


class arc200_Transfer(arc4.Struct):
    sender: arc4.Address
    recipient: arc4.Address
    amount: arc4.UInt256


class arc200_Approval(arc4.Struct):
    owner: arc4.Address
    spender: arc4.Address
    amount: arc4.UInt256


class arc200_approval(arc4.Struct):
    owner: arc4.Address
    spender: arc4.Address


class ARC200TokenInterface(ARC4Contract):
    def __init__(self) -> None:
        # arc200 state
        self.name = String()
        self.symbol = String()
        self.decimals = UInt64()
        self.totalSupply = BigUInt()
        self.balances = BoxMap(Account, BigUInt)
        self.approvals = BoxMap(Bytes, BigUInt)

    @arc4.abimethod(readonly=True)
    def arc200_name(self) -> Bytes32:
        """
        Get name of token.
        """
        return Bytes32.from_bytes(Bytes())

    @arc4.abimethod(readonly=True)
    def arc200_symbol(self) -> Bytes8:
        """
        Get symbol of token.
        """
        return Bytes8.from_bytes(Bytes())

    @arc4.abimethod(readonly=True)
    def arc200_decimals(self) -> arc4.UInt8:
        """
        Get decimals of token.
        """
        return arc4.UInt8(UInt64())

    @arc4.abimethod(readonly=True)
    def arc200_totalSupply(self) -> arc4.UInt256:
        """
        Get total supply of token.
        """
        return arc4.UInt256(self.totalSupply)

    @arc4.abimethod(readonly=True)
    def arc200_balanceOf(self, account: arc4.Address) -> arc4.UInt256:
        """
        Get balance of account.
        """
        return arc4.UInt256(0)

    @arc4.abimethod
    def arc200_transferFrom(
        self, sender: arc4.Address, recipient: arc4.Address, amount: arc4.UInt256
    ) -> arc4.Bool:
        """
        Transfer tokens from sender to recipient.
        """
        return arc4.Bool(True)

    @arc4.abimethod
    def arc200_approve(self, spender: arc4.Address, amount: arc4.UInt256) -> arc4.Bool:
        """
        Approve spender to spend amount.
        """
        return arc4.Bool(True)

    @arc4.abimethod(readonly=True)
    def arc200_allowance(
        self, owner: arc4.Address, spender: arc4.Address
    ) -> arc4.UInt256:
        """
        Get allowance of spender.
        """
        return arc4.UInt256(0)


class ARC200Token(ARC200TokenInterface):
    def __init__(self) -> None:  # pragma: no cover
        super().__init__()

    @arc4.abimethod(readonly=True)
    def arc200_name(self) -> Bytes32:
        return Bytes32.from_bytes(self.name.bytes)

    @arc4.abimethod(readonly=True)
    def arc200_symbol(self) -> Bytes8:
        return Bytes8.from_bytes(self.symbol.bytes)

    @arc4.abimethod(readonly=True)
    def arc200_decimals(self) -> arc4.UInt8:
        return arc4.UInt8(self.decimals)

    @arc4.abimethod(readonly=True)
    def arc200_totalSupply(self) -> arc4.UInt256:
        return arc4.UInt256(self.totalSupply)

    @arc4.abimethod(readonly=True)
    def arc200_balanceOf(self, account: arc4.Address) -> arc4.UInt256:
        return arc4.UInt256(self._balanceOf(account.native))

    @subroutine
    def _balanceOf(self, account: Account) -> BigUInt:
        return self.balances.get(key=account, default=BigUInt(0))

    @arc4.abimethod(readonly=True)
    def arc200_allowance(
        self, owner: arc4.Address, spender: arc4.Address
    ) -> arc4.UInt256:
        return arc4.UInt256(self._allowance(owner.native, spender.native))

    @subroutine
    def _allowance(self, owner: Account, spender: Account) -> BigUInt:
        return self.approvals.get(
            key=op.sha256(owner.bytes + spender.bytes),
            default=BigUInt(0),
        )

    @arc4.abimethod
    def arc200_transferFrom(
        self, sender: arc4.Address, recipient: arc4.Address, amount: arc4.UInt256
    ) -> arc4.Bool:
        self._transferFrom(sender.native, recipient.native, amount.native)
        return arc4.Bool(True)

    @subroutine
    def _transferFrom(
        self, sender: Account, recipient: Account, amount: BigUInt
    ) -> None:
        spender = Txn.sender
        spender_allowance = self._allowance(sender, spender)
        assert spender_allowance >= amount, "insufficient approval"
        new_spender_allowance = spender_allowance - amount
        self._approve(sender, spender, new_spender_allowance)
        self._transfer(sender, recipient, amount)

    @arc4.abimethod
    def arc200_transfer(
        self, recipient: arc4.Address, amount: arc4.UInt256
    ) -> arc4.Bool:
        self._transfer(Txn.sender, recipient.native, amount.native)
        return arc4.Bool(True)

    @subroutine
    def _transfer(self, sender: Account, recipient: Account, amount: BigUInt) -> None:
        sender_balance = self._balanceOf(sender)
        recipient_balance = self._balanceOf(recipient)
        assert sender_balance >= amount, "insufficient balance"
        if sender == recipient:  # prevent self-transfer balance increments
            self.balances[sender] = sender_balance  # current balance or zero
        else:
            self.balances[sender] = sender_balance - amount
            self.balances[recipient] = recipient_balance + amount
        arc4.emit(
            arc200_Transfer(
                arc4.Address(sender), arc4.Address(recipient), arc4.UInt256(amount)
            )
        )

    @arc4.abimethod
    def arc200_approve(self, spender: arc4.Address, amount: arc4.UInt256) -> arc4.Bool:
        self._approve(Txn.sender, spender.native, amount.native)
        return arc4.Bool(True)

    @subroutine
    def _approve(self, owner: Account, spender: Account, amount: BigUInt) -> None:
        self.approvals[op.sha256(owner.bytes + spender.bytes)] = amount
        arc4.emit(
            arc200_Approval(
                arc4.Address(owner), arc4.Address(spender), arc4.UInt256(amount)
            )
        )


class OSARC200Token(ARC200Token, Upgradeable, Deployable, Stakeable):
    def __init__(self) -> None:  # pragma: no cover
        # arc200 state
        self.name = String()
        self.symbol = String()
        self.decimals = UInt64()
        self.totalSupply = BigUInt()
        # balances
        # approvals
        # deployable state
        self.parent_id = UInt64()
        self.deployer = Account()
        # ownable state
        self.owner = Account()
        # upgradeable state
        self.contract_version = UInt64(1)
        self.deployment_version = UInt64()
        self.updatable = bool(1)
        self.upgrader = Global.creator_address
        # stakeable state
        self.delegate = Account()
        self.stakeable = bool(1)

    @arc4.abimethod
    def mint(
        self,
        receiver: arc4.Address,
        name: Bytes32,
        symbol: Bytes8,
        decimals: arc4.UInt8,
        totalSupply: arc4.UInt256,
    ) -> None:
        """
        Mint tokens
        """
        assert self.owner == Global.zero_address, "owner not initialized"
        assert self.name == "", "name not initialized"
        assert self.symbol == "", "symbol not initialized"
        assert self.totalSupply == 0, "total supply not initialized"
        payment_amount = require_payment(Txn.sender)
        assert payment_amount >= mint_fee, "payment amount accurate"
        self.owner = Global.creator_address
        self.name = String.from_bytes(name.bytes)
        self.symbol = String.from_bytes(symbol.bytes)
        self.decimals = decimals.native
        self.totalSupply = totalSupply.native
        self.balances[receiver.native] = totalSupply.native
        arc4.emit(
            arc200_Transfer(
                arc4.Address(Global.zero_address),
                receiver,
                totalSupply,
            )
        )
        itxn.Payment(receiver=Global.creator_address, amount=mint_fee, fee=0).submit()

    @arc4.abimethod(allow_actions=[OnCompleteAction.DeleteApplication])
    def kill(self) -> None:
        """
        Kill contract
        """
        assert Txn.sender == self.upgrader, "must be upgrader"
        close_offline_on_delete(Txn.sender)


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
        # upgradeable state
        self.contract_version = UInt64()
        self.deployment_version = UInt64()
        self.updatable = bool(1)
        self.upgrader = Global.creator_address

        ##############################################
        # @arc4.abimethod
        # def create(self, *args) -> UInt64:
        #    return UInt64()
        ##############################################

    @subroutine
    def get_initial_payment(self) -> UInt64:
        """
        Get initial payment.
        """
        payment_amount = require_payment(Txn.sender)
        mbr_increase = UInt64(mint_cost)
        min_balance = op.Global.min_balance  # 100000
        assert (
            payment_amount >= mbr_increase + min_balance
        ), "payment amount accurate"  # 131300
        initial = payment_amount - mbr_increase - min_balance
        return initial


##################################################


class OSARC200TokenFactory(BaseFactory):
    def __init__(self) -> None:
        super().__init__()

    @arc4.abimethod
    def create(
        self,
        # name: Bytes32,
        # symbol: Bytes8,
        # decimals: arc4.UInt8,
        # totalSupply: arc4.UInt256,
    ) -> UInt64:
        """
        Create airdrop.

        Arguments:
        - owner, who is the beneficiary
        - funder, who funded the contract
        - deadline, funding deadline
        - initial, initial funded value not including lockup bonus

        Returns:
        - app id
        """
        ##########################################
        self.get_initial_payment()
        ##########################################
        compiled = compile_contract(
            OSARC200Token, extra_program_pages=3
        )  # max extra pages
        base_app = arc4.arc4_create(OSARC200Token, compiled=compiled).created_app
        arc4.emit(FactoryCreated(arc4.UInt64(base_app.id)))
        arc4.abi_call(  # inherit upgrader
            OSARC200Token.grant_upgrader,
            Global.creator_address,
            app_id=base_app,
        )
        itxn.Payment(
            receiver=base_app.address, amount=op.Global.min_balance + 31300, fee=0
        ).submit()
        ##########################################
        return base_app.id
