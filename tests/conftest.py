#!/usr/bin/python3

import pytest


@pytest.fixture(scope="function", autouse=True)
def isolate(fn_isolation):
    # perform a chain rewind after completing each test, to ensure proper isolation
    # https://eth-brownie.readthedocs.io/en/v1.10.3/tests-pytest-intro.html#isolation-fixtures
    pass


@pytest.fixture(scope="module")
def token(PumpToken, accounts):
    return PumpToken.deploy({'from': accounts[0]})

@pytest.fixture(scope="module")
def staking_manager(StakingManager, Token, accounts):
    primary_token = Token.deploy({'from': accounts[0]})
    return StakingManager.deploy({'from': accounts[0]})