#!/usr/bin/python3

import brownie, pytest


@pytest.mark.parametrize("idx", range(5))
def test_initial_approval_is_zero(pump_token, accounts, idx):
    assert pump_token.allowance(accounts[0], accounts[idx]) == 0


def test_approve(pump_token, accounts):
    pump_token.approve(accounts[1], 10**19, {'from': accounts[0]})

    assert pump_token.allowance(accounts[0], accounts[1]) == 10**19


def test_modify_approve(pump_token, accounts):
    pump_token.approve(accounts[1], 10**19, {'from': accounts[0]})
    pump_token.approve(accounts[1], 12345678, {'from': accounts[0]})

    assert pump_token.allowance(accounts[0], accounts[1]) == 12345678


def test_revoke_approve(pump_token, accounts):
    pump_token.approve(accounts[1], 10**19, {'from': accounts[0]})
    pump_token.approve(accounts[1], 0, {'from': accounts[0]})

    assert pump_token.allowance(accounts[0], accounts[1]) == 0


def test_approve_self(pump_token, accounts):
    pump_token.approve(accounts[0], 10**19, {'from': accounts[0]})

    assert pump_token.allowance(accounts[0], accounts[0]) == 10**19


def test_only_affects_target(pump_token, accounts):
    pump_token.approve(accounts[1], 10**19, {'from': accounts[0]})

    assert pump_token.allowance(accounts[1], accounts[0]) == 0


def test_returns_true(pump_token, accounts):
    tx = pump_token.approve(accounts[1], 10**19, {'from': accounts[0]})

    assert tx.return_value is True


def test_approval_event_fires(accounts, pump_token):
    tx = pump_token.approve(accounts[1], 10**19, {'from': accounts[0]})

    assert len(tx.events) == 1
    assert tx.events["Approval"].values() == [accounts[0], accounts[1], 10**19]


def test_sender_balance_decreases(accounts, pump_token):
    sender_balance = pump_token.balanceOf(accounts[0])
    amount = sender_balance // 4

    pump_token.transfer(accounts[1], amount, {'from': accounts[0]})

    assert pump_token.balanceOf(accounts[0]) == sender_balance - amount


def test_receiver_balance_increases(accounts, pump_token):
    receiver_balance = pump_token.balanceOf(accounts[1])
    amount = pump_token.balanceOf(accounts[0]) // 4

    pump_token.transfer(accounts[1], amount, {'from': accounts[0]})

    assert pump_token.balanceOf(accounts[1]) == receiver_balance + (amount * 0.97)


def test_total_supply_not_affected(accounts, pump_token):
    total_supply = pump_token.totalSupply()
    amount = pump_token.balanceOf(accounts[0])

    pump_token.transfer(accounts[1], amount, {'from': accounts[0]})

    assert pump_token.totalSupply() == total_supply


def test_returns_true(accounts, pump_token):
    amount = pump_token.balanceOf(accounts[0])
    tx = pump_token.transfer(accounts[1], amount, {'from': accounts[0]})

    assert tx.return_value is True


def test_transfer_full_balance(accounts, pump_token):
    amount = pump_token.balanceOf(accounts[0])
    receiver_balance = pump_token.balanceOf(accounts[1])

    pump_token.transfer(accounts[1], amount, {'from': accounts[0]})

    assert pump_token.balanceOf(accounts[0]) == 0
    assert pump_token.balanceOf(accounts[1]) == receiver_balance + (amount * 0.97)


def test_transfer_zero_pump_tokens(accounts, pump_token):
    sender_balance = pump_token.balanceOf(accounts[0])
    receiver_balance = pump_token.balanceOf(accounts[1])

    pump_token.transfer(accounts[1], 0, {'from': accounts[0]})

    assert pump_token.balanceOf(accounts[0]) == sender_balance
    assert pump_token.balanceOf(accounts[1]) == receiver_balance


def test_transfer_to_self(accounts, pump_token):
    sender_balance = pump_token.balanceOf(accounts[0])
    amount = sender_balance // 4

    pump_token.transfer(accounts[0], amount, {'from': accounts[0]})

    assert pump_token.balanceOf(accounts[0]) == sender_balance - (amount * 0.03)


def test_insufficient_balance(accounts, pump_token):
    balance = pump_token.balanceOf(accounts[0])

    with brownie.reverts():
        pump_token.transfer(accounts[1], balance + 1, {'from': accounts[0]})


def test_transfer_event_fires(accounts, pump_token):
    amount = pump_token.balanceOf(accounts[0])
    tx = pump_token.transfer(accounts[1], amount, {'from': accounts[0]})

    assert len(tx.events) == 2
    assert tx.events["Transfer"].values() == [accounts[0], accounts[1], (amount * 0.97)]


def test_sender_balance_decreases(accounts, pump_token):
    sender_balance = pump_token.balanceOf(accounts[0])
    amount = sender_balance // 4

    pump_token.approve(accounts[1], amount, {'from': accounts[0]})
    pump_token.transferFrom(accounts[0], accounts[2], amount, {'from': accounts[1]})

    assert pump_token.balanceOf(accounts[0]) == sender_balance - amount


def test_receiver_balance_increases(accounts, pump_token):
    receiver_balance = pump_token.balanceOf(accounts[2])
    amount = pump_token.balanceOf(accounts[0]) // 4

    pump_token.approve(accounts[1], amount, {'from': accounts[0]})
    pump_token.transferFrom(accounts[0], accounts[2], amount, {'from': accounts[1]})

    assert pump_token.balanceOf(accounts[2]) == receiver_balance + (amount * 0.97)


def test_caller_balance_not_affected(accounts, pump_token):
    caller_balance = pump_token.balanceOf(accounts[1])
    amount = pump_token.balanceOf(accounts[0])

    pump_token.approve(accounts[1], amount, {'from': accounts[0]})
    pump_token.transferFrom(accounts[0], accounts[2], amount, {'from': accounts[1]})

    assert pump_token.balanceOf(accounts[1]) == caller_balance


def test_caller_approval_affected(accounts, pump_token):
    approval_amount = pump_token.balanceOf(accounts[0])
    transfer_amount = approval_amount // 4

    pump_token.approve(accounts[1], approval_amount, {'from': accounts[0]})
    pump_token.transferFrom(accounts[0], accounts[2], transfer_amount, {'from': accounts[1]})

    assert pump_token.allowance(accounts[0], accounts[1]) == approval_amount - transfer_amount


def test_receiver_approval_not_affected(accounts, pump_token):
    approval_amount = pump_token.balanceOf(accounts[0])
    transfer_amount = approval_amount // 4

    pump_token.approve(accounts[1], approval_amount, {'from': accounts[0]})
    pump_token.approve(accounts[2], approval_amount, {'from': accounts[0]})
    pump_token.transferFrom(accounts[0], accounts[2], transfer_amount, {'from': accounts[1]})

    assert pump_token.allowance(accounts[0], accounts[2]) == approval_amount


def test_total_supply_not_affected(accounts, pump_token):
    total_supply = pump_token.totalSupply()
    amount = pump_token.balanceOf(accounts[0])

    pump_token.approve(accounts[1], amount, {'from': accounts[0]})
    pump_token.transferFrom(accounts[0], accounts[2], amount, {'from': accounts[1]})

    assert pump_token.totalSupply() == total_supply


def test_returns_true(accounts, pump_token):
    amount = pump_token.balanceOf(accounts[0])
    pump_token.approve(accounts[1], amount, {'from': accounts[0]})
    tx = pump_token.transferFrom(accounts[0], accounts[2], amount, {'from': accounts[1]})

    assert tx.return_value is True


def test_transfer_full_balance(accounts, pump_token):
    amount = pump_token.balanceOf(accounts[0])
    receiver_balance = pump_token.balanceOf(accounts[2])

    pump_token.approve(accounts[1], amount, {'from': accounts[0]})
    pump_token.transferFrom(accounts[0], accounts[2], amount, {'from': accounts[1]})

    assert pump_token.balanceOf(accounts[0]) == 0
    assert pump_token.balanceOf(accounts[2]) == receiver_balance + (amount * 0.97)


def test_transfer_zero_pump_tokens(accounts, pump_token):
    sender_balance = pump_token.balanceOf(accounts[0])
    receiver_balance = pump_token.balanceOf(accounts[2])

    pump_token.approve(accounts[1], sender_balance, {'from': accounts[0]})
    pump_token.transferFrom(accounts[0], accounts[2], 0, {'from': accounts[1]})

    assert pump_token.balanceOf(accounts[0]) == sender_balance
    assert pump_token.balanceOf(accounts[2]) == receiver_balance


def test_transfer_zero_pump_tokens_without_approval(accounts, pump_token):
    sender_balance = pump_token.balanceOf(accounts[0])
    receiver_balance = pump_token.balanceOf(accounts[2])

    pump_token.transferFrom(accounts[0], accounts[2], 0, {'from': accounts[1]})

    assert pump_token.balanceOf(accounts[0]) == sender_balance
    assert pump_token.balanceOf(accounts[2]) == receiver_balance


def test_insufficient_balance(accounts, pump_token):
    balance = pump_token.balanceOf(accounts[0])

    pump_token.approve(accounts[1], balance + 1, {'from': accounts[0]})
    with brownie.reverts():
        pump_token.transferFrom(accounts[0], accounts[2], balance + 1, {'from': accounts[1]})


def test_insufficient_approval(accounts, pump_token):
    balance = pump_token.balanceOf(accounts[0])

    pump_token.approve(accounts[1], balance - 1, {'from': accounts[0]})
    with brownie.reverts():
        pump_token.transferFrom(accounts[0], accounts[2], balance, {'from': accounts[1]})


def test_no_approval(accounts, pump_token):
    balance = pump_token.balanceOf(accounts[0])

    with brownie.reverts():
        pump_token.transferFrom(accounts[0], accounts[2], balance, {'from': accounts[1]})


def test_revoked_approval(accounts, pump_token):
    balance = pump_token.balanceOf(accounts[0])

    pump_token.approve(accounts[1], balance, {'from': accounts[0]})
    pump_token.approve(accounts[1], 0, {'from': accounts[0]})

    with brownie.reverts():
        pump_token.transferFrom(accounts[0], accounts[2], balance, {'from': accounts[1]})


def test_transfer_to_self(accounts, pump_token):
    sender_balance = pump_token.balanceOf(accounts[0])
    amount = sender_balance // 4

    pump_token.approve(accounts[0], sender_balance, {'from': accounts[0]})
    pump_token.transferFrom(accounts[0], accounts[0], amount, {'from': accounts[0]})

    assert pump_token.balanceOf(accounts[0]) == sender_balance - (amount * 0.03)
    assert pump_token.allowance(accounts[0], accounts[0]) == sender_balance - amount


def test_transfer_to_self_no_approval(accounts, pump_token):
    amount = pump_token.balanceOf(accounts[0])

    with brownie.reverts():
        pump_token.transferFrom(accounts[0], accounts[0], amount, {'from': accounts[0]})


def test_transfer_event_fires(accounts, pump_token):
    amount = pump_token.balanceOf(accounts[0])

    pump_token.approve(accounts[1], amount, {'from': accounts[0]})
    tx = pump_token.transferFrom(accounts[0], accounts[2], amount, {'from': accounts[1]})

    assert len(tx.events) == 2
