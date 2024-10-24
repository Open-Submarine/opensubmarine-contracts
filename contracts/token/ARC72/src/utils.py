from algopy import (
    Account,
    Bytes,
    Global,
    OnCompleteAction,
    Txn,
    UInt64,
    gtxn,
    itxn,
    op,
    subroutine,
)


##############################################
# function: require_payment (internal)
# arguments: None
# purpose: check payment
# pre-conditions: None
# post-conditions: None
##############################################
@subroutine
def require_payment(who: Account) -> UInt64:
    ref_group_index = Txn.group_index
    assert ref_group_index > 0, "group index greater than zero"
    payment_group_index = ref_group_index - 1
    assert (
        gtxn.PaymentTransaction(payment_group_index).sender == who
    ), "payment sender accurate"
    assert (
        gtxn.PaymentTransaction(payment_group_index).receiver
        == Global.current_application_address
    ), "payment receiver accurate"
    return gtxn.PaymentTransaction(payment_group_index).amount


##############################################
# function: get_available_balance (internal)
# purpose: get available balance
# returns: app balance available for spending
##############################################
@subroutine
def get_available_balance() -> UInt64:
    balance = op.balance(Global.current_application_address)
    min_balance = op.Global.min_balance
    available_balance = balance - min_balance
    return available_balance


##############################################
@subroutine
def close_offline_on_delete(close_remainder_to: Account) -> None:
    oca = Txn.on_completion
    if oca == OnCompleteAction.DeleteApplication:
        keyreg_txn = itxn.KeyRegistration(
            non_participation=True,
            vote_key=Bytes.from_base64("AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="),
            selection_key=Bytes.from_base64(
                "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="
            ),
            vote_first=UInt64(0),
            vote_last=UInt64(0),
            vote_key_dilution=UInt64(0),
            state_proof_key=Bytes.from_base64(
                "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=="
            ),
            fee=0,
        )
        pmt_txn = itxn.Payment(
            receiver=Global.creator_address,
            close_remainder_to=close_remainder_to,
            fee=0,
            amount=op.Global.min_balance,
        )
        itxn.submit_txns(keyreg_txn, pmt_txn)
    else:
        op.err()
