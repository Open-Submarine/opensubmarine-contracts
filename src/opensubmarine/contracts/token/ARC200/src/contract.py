# import typing
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
from opensubmarine.utils.algorand import require_payment, close_offline_on_delete
from opensubmarine.utils.types import Bytes8, Bytes32
from opensubmarine import (
    Stakeable,
    Upgradeable,
    Deployable,
    BaseFactory,
    FactoryCreated,
)

mint_fee = 1000000
mint_cost = 31300

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


class OSARC200Token(ARC200Token, Upgradeable, Stakeable):
    def __init__(self) -> None:  # pragma: no cover
        # arc200 state
        self.name = String()
        self.symbol = String()
        self.decimals = UInt64()
        self.totalSupply = BigUInt()
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
        assert Txn.sender == Global.creator_address, "must be creator"
        assert self.owner == Global.zero_address, "owner not initialized"
        assert self.name == "", "name not initialized"
        assert self.symbol == "", "symbol not initialized"
        assert self.totalSupply == 0, "total supply not initialized"
        payment_amount = require_payment(Txn.sender)
        assert payment_amount >= 28500, "payment amount accurate"
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

    # terminal methods
    # only works if upgrader and there are no boxes
    @arc4.abimethod(allow_actions=[OnCompleteAction.DeleteApplication])
    def kill(self) -> None:
        """
        Kill contract
        """
        assert Txn.sender == self.upgrader, "must be upgrader"
        close_offline_on_delete(Txn.sender)


class ARC200TokenScaffold(ARC200Token, Upgradeable, Deployable, Stakeable):
    """
    Scaffold for ARC200Token
    """

    def __init__(self) -> None:  # pragma: no cover
        # arc200 state
        self.name = String()
        self.symbol = String()
        self.decimals = UInt64()
        self.totalSupply = BigUInt()
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

    # terminal methods
    # only works if upgrader and there are no boxes
    @arc4.abimethod(allow_actions=[OnCompleteAction.DeleteApplication])
    def kill(self) -> None:
        """
        Kill contract
        """
        assert Txn.sender == self.upgrader, "must be upgrader"
        close_offline_on_delete(Txn.sender)


class OSARC200TokenFactory(BaseFactory, Upgradeable):
    def __init__(self) -> None:
        # upgradeable state
        self.contract_version = UInt64(1)
        self.deployment_version = UInt64()
        self.updatable = bool(1)
        self.upgrader = Global.creator_address

    @arc4.abimethod
    def create(
        self,
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
        self.get_initial_payment(UInt64(mint_cost))
        ##########################################
        compiled = compile_contract(
            ARC200TokenScaffold, extra_program_pages=3
        )  # max extra pages
        base_app = arc4.arc4_create(ARC200TokenScaffold, compiled=compiled).created_app
        arc4.emit(FactoryCreated(arc4.UInt64(base_app.id)))
        arc4.abi_call(  # inherit upgrader
            ARC200TokenScaffold.grant_upgrader,
            Global.creator_address,
            app_id=base_app,
        )
        itxn.Payment(
            receiver=base_app.address,
            amount=op.Global.min_balance + UInt64(mint_cost),
            fee=0,
        ).submit()
        ##########################################
        return base_app.id
