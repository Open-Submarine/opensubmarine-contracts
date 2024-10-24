import typing
from algopy import (
    Application,
    ARC4Contract,
    Account,
    BigUInt,
    Box,
    BoxMap,
    Bytes,
    Global,
    OnCompleteAction,
    String,
    Txn,
    UInt64,
    arc4,
    itxn,
    op,
    subroutine,
)
from utils import require_payment, close_offline_on_delete

Bytes4: typing.TypeAlias = arc4.StaticArray[arc4.Byte, typing.Literal[4]]
Bytes8: typing.TypeAlias = arc4.StaticArray[arc4.Byte, typing.Literal[8]]
Bytes32: typing.TypeAlias = arc4.StaticArray[arc4.Byte, typing.Literal[32]]
Bytes64: typing.TypeAlias = arc4.StaticArray[arc4.Byte, typing.Literal[64]]
Bytes256: typing.TypeAlias = arc4.StaticArray[arc4.Byte, typing.Literal[256]]

mint_fee = 0
mint_cost = 336700


class PartKeyInfo(arc4.Struct):
    address: arc4.Address
    vote_key: Bytes32
    selection_key: Bytes32
    vote_first: arc4.UInt64
    vote_last: arc4.UInt64
    vote_key_dilution: arc4.UInt64
    state_proof_key: Bytes64


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
# Lockable
#   allows contract to be lock network tokens
##################################################


class LockableInterface(ARC4Contract):
    """
    Interface for all methods of lockable contracts.
    This class defines the basic interface for all types of lockable contracts.
    Subclasses must implement these methods to provide concrete behavior
    """

    @arc4.abimethod
    def withdraw(self, amount: arc4.UInt64) -> UInt64:  # pragma: no cover
        """
        Withdraw funds from contract. Should be called by owner.
        """
        return UInt64()


##################################################
# ARC73
#   supports interface
##################################################


class ARC73SupportsInterfaceInterface(ARC4Contract):
    @arc4.abimethod(readonly=True)
    def supportsInterface(self, interface_id: Bytes4) -> arc4.Bool:
        return arc4.Bool(False)


class ARC73SupportsInterface(ARC73SupportsInterfaceInterface):
    @arc4.abimethod(readonly=True)
    def supportsInterface(self, interface_id: Bytes4) -> arc4.Bool:
        return arc4.Bool(self._supportsInterface(interface_id.bytes))

    @subroutine
    def _supportsInterface(self, interface_id: Bytes) -> bool:
        if interface_id == Bytes.from_hex("4e22a3ba"):  # ARC73 supports interface
            return True
        elif interface_id == Bytes.from_hex("ffffffff"):  # mask
            return False
        else:
            return False


##################################################
# ARC72Token
#   nft contract
##################################################


class arc72_nft_data(arc4.Struct):
    owner: arc4.Address
    approved: arc4.Address
    index: arc4.UInt256
    token_id: arc4.UInt256
    metadata: Bytes256


class arc72_holder_data(arc4.Struct):
    holder: arc4.Address
    balance: arc4.UInt256


# {
#   "name": "ARC-72",
#   "desc": "Smart Contract NFT Base Interface",
#   "methods": [
#     {
#       "name": "arc72_ownerOf",
#       "desc": "Returns the address of the current owner of the NFT with the given tokenId",
#       "readonly": true,
#       "args": [
#         { "type": "uint256", "name": "tokenId", "desc": "The ID of the NFT" },
#       ],
#       "returns": { "type": "address", "desc": "The current owner of the NFT." }
#     },
#     {
#       "name": "arc72_transferFrom",
#       "desc": "Transfers ownership of an NFT",
#       "readonly": false,
#       "args": [
#         { "type": "address", "name": "from" },
#         { "type": "address", "name": "to" },
#         { "type": "uint256", "name": "tokenId" }
#       ],
#       "returns": { "type": "void" }
#     },
#   ],
#   "events": [
#     {
#       "name": "arc72_Transfer",
#       "desc": "Transfer ownership of an NFT",
#       "args": [
#         {
#           "type": "address",
#           "name": "from",
#           "desc": "The current owner of the NFT"
#         },
#         {
#           "type": "address",
#           "name": "to",
#           "desc": "The new owner of the NFT"
#         },
#         {
#           "type": "uint256",
#           "name": "tokenId",
#           "desc": "The ID of the transferred NFT"
#         }
#       ]
#     }
#   ]
# }


class arc72_Transfer(arc4.Struct):
    sender: arc4.Address
    recipient: arc4.Address
    tokenId: arc4.UInt256


class ARC72TokenCoreInterface(ARC4Contract):
    @arc4.abimethod(readonly=True)
    def arc72_ownerOf(self, tokenId: arc4.UInt256) -> arc4.Address:
        """
        Returns the address of the current owner of the NFT with the given tokenId
        """
        return arc4.Address(Global.zero_address)

    @arc4.abimethod
    def arc72_transferFrom(
        self, from_: arc4.Address, to: arc4.Address, tokenId: arc4.UInt256
    ) -> None:
        """
        Transfers ownership of an NFT
        """
        pass


# {
#   "name": "ARC-72 Metadata Extension",
#   "desc": "Smart Contract NFT Metadata Interface",
#   "methods": [
#     {
#       "name": "arc72_tokenURI",
#       "desc": "Returns a URI pointing to the NFT metadata",
#       "readonly": true,
#       "args": [
#         { "type": "uint256", "name": "tokenId", "desc": "The ID of the NFT" },
#       ],
#       "returns": { "type": "byte[256]", "desc": "URI to token metadata." }
#     }
#   ],
# }


class ARC72TokenMetadataInterface(ARC4Contract):
    @arc4.abimethod(readonly=True)
    def arc72_tokenURI(self, tokenId: arc4.UInt256) -> Bytes256:
        """
        Returns a URI pointing to the NFT metadata
        """
        return Bytes256.from_bytes(Bytes())


# {
#   "name": "ARC-72 Transfer Management Extension",
#   "desc": "Smart Contract NFT Transfer Management Interface",
#   "methods": [
#     {
#       "name": "arc72_approve",
#       "desc": "Approve a controller for a single NFT",
#       "readonly": false,
#       "args": [
#         { "type": "address", "name": "approved", "desc": "Approved controller address" },
#         { "type": "uint256", "name": "tokenId", "desc": "The ID of the NFT" },
#       ],
#       "returns": { "type": "void" }
#     },
#     {
#       "name": "arc72_setApprovalForAll",
#       "desc": "Approve an operator for all NFTs for a user",
#       "readonly": false,
#       "args": [
#         { "type": "address", "name": "operator", "desc": "Approved operator address" },
#         { "type": "bool", "name": "approved", "desc": "true to give approval, false to revoke" },
#       ],
#       "returns": { "type": "void" }
#     },
#     {
#       "name": "arc72_getApproved",
#       "desc": "Get the current approved address for a single NFT",
#       "readonly": true,
#       "args": [
#         { "type": "uint256", "name": "tokenId", "desc": "The ID of the NFT" },
#       ],
#       "returns": { "type": "address", "desc": "address of approved user or zero" }
#     },
#     {
#       "name": "arc72_isApprovedForAll",
#       "desc": "Query if an address is an authorized operator for another address",
#       "readonly": true,
#       "args": [
#         { "type": "address", "name": "owner" },
#         { "type": "address", "name": "operator" },
#       ],
#       "returns": { "type": "bool", "desc": "whether operator is authorized for all NFTs of owner" }
#     },
#   ],
#   "events": [
#     {
#       "name": "arc72_Approval",
#       "desc": "An address has been approved to transfer ownership of the NFT",
#       "args": [
#         {
#           "type": "address",
#           "name": "owner",
#           "desc": "The current owner of the NFT"
#         },
#         {
#           "type": "address",
#           "name": "approved",
#           "desc": "The approved user for the NFT"
#         },
#         {
#           "type": "uint256",
#           "name": "tokenId",
#           "desc": "The ID of the NFT"
#         }
#       ]
#     },
#     {
#       "name": "arc72_ApprovalForAll",
#       "desc": "Operator set or unset for all NFTs defined by this contract for an owner",
#       "args": [
#         {
#           "type": "address",
#           "name": "owner",
#           "desc": "The current owner of the NFT"
#         },
#         {
#           "type": "address",
#           "name": "operator",
#           "desc": "The approved user for the NFT"
#         },
#         {
#           "type": "bool",
#           "name": "approved",
#           "desc": "Whether operator is authorized for all NFTs of owner "
#         }
#       ]
#     },
#   ]
# }


class arc72_Approval(arc4.Struct):
    owner: arc4.Address
    approved: arc4.Address
    tokenId: arc4.UInt256


class arc72_ApprovalForAll(arc4.Struct):
    owner: arc4.Address
    operator: arc4.Address
    approved: arc4.Bool


class ARC72TokenTransferManagementInterface(ARC4Contract):
    @arc4.abimethod
    def arc72_approve(self, approved: arc4.Address, tokenId: arc4.UInt256) -> None:
        pass

    @arc4.abimethod
    def arc72_setApprovalForAll(
        self, operator: arc4.Address, approved: arc4.Bool
    ) -> None:
        pass

    @arc4.abimethod(readonly=True)
    def arc72_getApproved(self, tokenId: arc4.UInt256) -> arc4.Address:
        return arc4.Address(Global.zero_address)

    @arc4.abimethod(readonly=True)
    def arc72_isApprovedForAll(
        self, owner: arc4.Address, operator: arc4.Address
    ) -> arc4.Bool:
        return arc4.Bool(False)


# {
#   "name": "ARC-72 Enumeration Extension",
#   "desc": "Smart Contract NFT Enumeration Interface",
#   "methods": [
#     {
#       "name": "arc72_balanceOf",
#       "desc": "Returns the number of NFTs owned by an address",
#       "readonly": true,
#       "args": [
#         { "type": "address", "name": "owner" },
#       ],
#       "returns": { "type": "uint256" }
#     },
#     {
#       "name": "arc72_totalSupply",
#       "desc": "Returns the number of NFTs currently defined by this contract",
#       "readonly": true,
#       "args": [],
#       "returns": { "type": "uint256" }
#     },
#     {
#       "name": "arc72_tokenByIndex",
#       "desc": "Returns the token ID of the token with the given index among all NFTs defined by the contract",
#       "readonly": true,
#       "args": [
#         { "type": "uint256", "name": "index" },
#       ],
#       "returns": { "type": "uint256" }
#     },
#   ],
# }


class ARC72TokenEnumerationInterface(ARC4Contract):
    @arc4.abimethod(readonly=True)
    def arc72_balanceOf(self, owner: arc4.Address) -> arc4.UInt256:
        return arc4.UInt256(0)

    @arc4.abimethod(readonly=True)
    def arc72_totalSupply(self) -> arc4.UInt256:
        return arc4.UInt256(0)

    @arc4.abimethod(readonly=True)
    def arc72_tokenByIndex(self, index: arc4.UInt256) -> arc4.UInt256:
        return arc4.UInt256(0)


class ARC72Token(
    ARC72TokenCoreInterface,
    ARC72TokenMetadataInterface,
    ARC72TokenTransferManagementInterface,
    ARC72TokenEnumerationInterface,
    ARC73SupportsInterface,
):
    def __init__(self) -> None:  # pragma: no cover
        # state (core, metadata)
        self.nft_data = BoxMap(BigUInt, arc72_nft_data)
        self.nft_operators = BoxMap(Bytes, bool)
        # enumeration state
        self.totalSupply = BigUInt()
        self.nft_index = BoxMap(BigUInt, BigUInt)
        self.holder_data = BoxMap(Account, arc72_holder_data)

    # core methods

    @arc4.abimethod(readonly=True)
    def arc72_ownerOf(self, tokenId: arc4.UInt256) -> arc4.Address:
        """
        Returns the address of the current owner of the NFT with the given tokenId
        """
        return self._ownerOf(tokenId.native)

    @subroutine
    def _ownerOf(self, tokenId: BigUInt) -> arc4.Address:
        return self._nft_owner(tokenId)

    @arc4.abimethod
    def arc72_transferFrom(
        self, from_: arc4.Address, to: arc4.Address, tokenId: arc4.UInt256
    ) -> None:
        """
        Transfers ownership of an NFT
        """
        self._transferFrom(from_.native, to.native, tokenId.native)

    @subroutine
    def _transferFrom(
        self, sender: Account, recipient: Account, tokenId: BigUInt
    ) -> None:
        assert self._nft_index(tokenId) != 0, "token id not exists"
        owner = self._ownerOf(tokenId)
        assert owner == sender, "sender must be owner"
        assert (
            Txn.sender == sender
            or Txn.sender == Account.from_bytes(self._getApproved(tokenId).bytes)
            or self._isApprovedForAll(Account.from_bytes(owner.bytes), Txn.sender)
        ), "sender must be owner or approved"
        nft = self.nft_data.get(key=tokenId, default=self._invalid_nft_data()).copy()
        nft.owner = arc4.Address(recipient)
        nft.approved = arc4.Address(Global.zero_address)
        self.nft_data[tokenId] = nft.copy()
        self._holder_increment_balance(recipient)
        self._holder_decrement_balance(sender)
        arc4.emit(
            arc72_Transfer(
                arc4.Address(sender),
                arc4.Address(recipient),
                arc4.UInt256(tokenId),
            )
        )

    # metadata methods

    @arc4.abimethod(readonly=True)
    def arc72_tokenURI(self, tokenId: arc4.UInt256) -> Bytes256:
        return self._tokenURI(tokenId.native)

    @subroutine
    def _tokenURI(self, tokenId: BigUInt) -> Bytes256:
        return self._nft_metadata(tokenId)

    # transfer management methods

    @arc4.abimethod
    def arc72_approve(self, approved: arc4.Address, tokenId: arc4.UInt256) -> None:
        self._approve(Txn.sender, approved.native, tokenId.native)

    @arc4.abimethod
    def arc72_setApprovalForAll(
        self, operator: arc4.Address, approved: arc4.Bool
    ) -> None:
        self._setApprovalForAll(Txn.sender, operator.native, approved.native)

    @arc4.abimethod(readonly=True)
    def arc72_getApproved(self, tokenId: arc4.UInt256) -> arc4.Address:
        return self._getApproved(tokenId.native)

    @arc4.abimethod(readonly=True)
    def arc72_isApprovedForAll(
        self, owner: arc4.Address, operator: arc4.Address
    ) -> arc4.Bool:
        return arc4.Bool(self._isApprovedForAll(owner.native, operator.native))

    @subroutine
    def _approve(self, owner: Account, approved: Account, tokenId: BigUInt) -> None:
        nft = self.nft_data.get(key=tokenId, default=self._invalid_nft_data()).copy()
        assert nft.owner == owner, "owner must be owner"
        nft.approved = arc4.Address(approved)
        self.nft_data[tokenId] = nft.copy()
        arc4.emit(
            arc72_Approval(
                arc4.Address(owner),
                arc4.Address(approved),
                arc4.UInt256(tokenId),
            )
        )

    @subroutine
    def _setApprovalForAll(
        self, owner: Account, approved: Account, approval: bool
    ) -> None:
        operator_key = op.sha256(approved.bytes + owner.bytes)
        self.nft_operators[operator_key] = approval
        arc4.emit(
            arc72_ApprovalForAll(
                arc4.Address(owner),
                arc4.Address(approved),
                arc4.Bool(approval),
            )
        )

    @subroutine
    def _getApproved(self, tokenId: BigUInt) -> arc4.Address:
        return self.nft_data.get(key=tokenId, default=self._invalid_nft_data()).approved

    @subroutine
    def _isApprovedForAll(self, owner: Account, operator: Account) -> bool:
        operator_key = op.sha256(operator.bytes + owner.bytes)
        return self.nft_operators.get(key=operator_key, default=False)

    # enumeration methods

    @arc4.abimethod(readonly=True)
    def arc72_balanceOf(self, owner: arc4.Address) -> arc4.UInt256:
        return self._balanceOf(owner.native)

    @subroutine
    def _balanceOf(self, owner: Account) -> arc4.UInt256:
        return self._holder_balance(owner)

    @arc4.abimethod(readonly=True)
    def arc72_totalSupply(self) -> arc4.UInt256:
        return arc4.UInt256(self._totalSupply())

    @subroutine
    def _totalSupply(self) -> BigUInt:
        return self.totalSupply

    @arc4.abimethod(readonly=True)
    def arc72_tokenByIndex(self, index: arc4.UInt256) -> arc4.UInt256:
        return arc4.UInt256(self._tokenByIndex(index.native))

    @subroutine
    def _tokenByIndex(self, index: BigUInt) -> BigUInt:
        return self.nft_index.get(key=index, default=BigUInt(0))

    # supports methods

    # override _supports_interface
    @subroutine
    def _supportsInterface(self, interface_id: Bytes) -> bool:
        if interface_id == Bytes.from_hex("4e22a3ba"):  # supports interface
            return True
        elif interface_id == Bytes.from_hex("ffffffff"):  # mask
            return False
        elif interface_id == Bytes.from_hex("53f02a40"):  # ARC72 core
            return True
        elif interface_id == Bytes.from_hex("c3c1fc00"):  # ARC72 metadata
            return True
        elif interface_id == Bytes.from_hex("b9c6f696"):  # ARC72 transfer management
            return True
        elif interface_id == Bytes.from_hex("a57d4679"):  # ARC72 enumeration
            return True
        else:
            return False

    # invalid methods

    @subroutine
    def _invalid_nft_data(self) -> arc72_nft_data:
        """
        Returns invalid NFT data
        """
        invalid_nft_data = arc72_nft_data(
            owner=arc4.Address(Global.zero_address),
            approved=arc4.Address(Global.zero_address),
            index=arc4.UInt256(0),
            token_id=arc4.UInt256(0),
            metadata=Bytes256.from_bytes(
                Bytes.from_base64(
                    "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
                )
            ),
        )
        return invalid_nft_data

    @subroutine
    def _invalid_holder_data(self) -> arc72_holder_data:
        """
        Returns invalid holder data
        """
        invalid_holder_data = arc72_holder_data(
            holder=arc4.Address(Global.zero_address),
            balance=arc4.UInt256(0),
        )
        return invalid_holder_data

    # nft methods

    @subroutine
    def _nft_data(self, tokenId: BigUInt) -> arc72_nft_data:
        """
        Returns the NFT data
        """
        return self.nft_data.get(key=tokenId, default=self._invalid_nft_data())

    @subroutine
    def _nft_index(self, tokenId: BigUInt) -> BigUInt:
        """
        Returns the index of the NFT
        """
        return BigUInt.from_bytes(self._nft_data(tokenId).index.bytes)

    @subroutine
    def _nft_metadata(self, tokenId: BigUInt) -> Bytes256:
        """
        Returns the metadata of the NFT
        """
        return Bytes256.from_bytes(self._nft_data(tokenId).metadata.bytes[:256])

    @subroutine
    def _nft_owner(self, tokenId: BigUInt) -> arc4.Address:
        """
        Returns the owner of the NFT
        """
        return self._nft_data(tokenId).owner

    # holder methods

    @subroutine
    def _holder_data(self, holder: Account) -> arc72_holder_data:
        """
        Returns the holder data
        """
        return self.holder_data.get(key=holder, default=self._invalid_holder_data())

    @subroutine
    def _holder_balance(self, holder: Account) -> arc4.UInt256:
        """
        Returns the number of NFTs owned by an address
        """
        return self._holder_data(holder).balance

    @subroutine
    def _holder_increment_balance(self, holder: Account) -> BigUInt:
        """
        Increment balance of holder
        """
        previous_balance = BigUInt.from_bytes(self._holder_balance(holder).bytes)
        next_balance = previous_balance + 1
        new_holder_data = arc72_holder_data(
            holder=arc4.Address(holder),
            balance=arc4.UInt256(previous_balance + 1),
        )
        self.holder_data[holder] = new_holder_data.copy()
        return next_balance

    @subroutine
    def _holder_decrement_balance(self, holder: Account) -> BigUInt:
        """
        Decrement balance of holder
        """
        previous_balance = BigUInt.from_bytes(self._holder_balance(holder).bytes)
        next_balance = previous_balance - 1
        if next_balance == 0:
            del self.holder_data[holder]
        else:
            new_holder_data = arc72_holder_data(
                holder=arc4.Address(holder),
                balance=arc4.UInt256(next_balance),
            )
            self.holder_data[holder] = new_holder_data.copy()
        return next_balance

    # supply methods

    @subroutine
    def _increment_totalSupply(self) -> BigUInt:
        """
        Increment total supply
        """
        new_totalSupply = self.totalSupply + 1
        self.totalSupply = new_totalSupply
        return new_totalSupply

    @subroutine
    def _decrement_totalSupply(self) -> BigUInt:
        """
        Decrement total supply
        """
        new_totalSupply = self.totalSupply - 1
        self.totalSupply = new_totalSupply
        return new_totalSupply

    # counter methods

    @subroutine
    def _increment_counter(self) -> BigUInt:
        """
        Increment counter
        """
        counter_box = Box(BigUInt, key=b"arc72_counter")
        counter = counter_box.get(default=BigUInt(0))
        new_counter = counter + 1
        counter_box.value = new_counter
        return new_counter


class staking_data(arc4.Struct):
    delegate: arc4.Address


class OSARC72Token(ARC72Token, Upgradeable, Stakeable):
    def __init__(self) -> None:
        super().__init__()
        # ownable state
        self.owner = Account()
        # upgradeable state
        self.contract_version = UInt64()
        self.deployment_version = UInt64()
        self.updatable = bool(1)
        self.upgrader = Global.creator_address
        # stakeable state
        self.delegate = Account()
        self.stakeable = bool(1)

    @arc4.abimethod
    def mint(
        self,
        to: arc4.Address,
        tokenId: arc4.UInt256,
        metadata: Bytes256,
    ) -> arc4.UInt256:
        """
        Mint a new NFT
        """
        return arc4.UInt256(self._mint(to.native, tokenId.native, metadata.bytes))

    @subroutine
    def _mint(self, to: Account, tokenId: BigUInt, metadata: Bytes) -> BigUInt:
        # TODO require auth to mint
        nft_data = self._nft_data(tokenId)
        assert nft_data.index == 0, "token must not exist"
        payment_amount = require_payment(Txn.sender)
        assert payment_amount >= mint_cost + mint_fee, "payment amount accurate"
        # TODO transfer mint_fee to treasury
        index = arc4.UInt256(self._increment_counter()).native # BigUInt to BigUInt(UInt256)
        self._increment_totalSupply()
        self.nft_index[index] = tokenId
        self.nft_data[tokenId] = arc72_nft_data(
            owner=arc4.Address(to),
            approved=arc4.Address(Global.zero_address),
            index=arc4.UInt256(index),
            token_id=arc4.UInt256(tokenId),
            metadata=Bytes256.from_bytes(metadata),
        )
        self._holder_increment_balance(to)
        arc4.emit(
            arc72_Transfer(
                arc4.Address(Global.zero_address),
                arc4.Address(to),
                arc4.UInt256(tokenId),
            )
        )
        return index

    @arc4.abimethod
    def burn(self, tokenId: arc4.UInt256) -> None:
        """
        Burn an NFT
        """
        self._burn(tokenId.native)

    @subroutine
    def _burn(self, tokenId: BigUInt) -> None:
        nft_data = self._nft_data(tokenId)
        assert nft_data.index != 0, "token exists"
        owner = nft_data.owner
        assert owner == Txn.sender, "sender must be owner"
        del self.nft_index[BigUInt.from_bytes(self._nft_data(tokenId).index.bytes)]
        del self.nft_data[tokenId]
        self._holder_decrement_balance(owner.native)
        self._decrement_totalSupply()
        arc4.emit(
            arc72_Transfer(
                owner,
                arc4.Address(Global.zero_address),
                arc4.UInt256(tokenId),
            )
        )

    @arc4.abimethod(allow_actions=[OnCompleteAction.DeleteApplication])
    def kill(self) -> None:
        """
        Kill contract
        """
        assert Txn.sender == self.upgrader, "must be upgrader"
        close_offline_on_delete(Txn.sender)

    @arc4.abimethod
    def post_update(self) -> None:
        """
        Post update
        """
        assert Txn.sender == self.upgrader, "must be upgrader"
        self._post_update()

    @subroutine
    def _post_update(self) -> None:
        pass
