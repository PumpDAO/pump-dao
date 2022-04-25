#!/usr/bin/python3

import pytest
from brownie import chain


@pytest.fixture(scope="function", autouse=True)
def isolate(fn_isolation):
    # perform a chain rewind after completing each test, to ensure proper isolation
    # https://eth-brownie.readthedocs.io/en/v1.10.3/tests-pytest-intro.html#isolation-fixtures
    pass


@pytest.fixture(scope="module")
def token(PumpToken, accounts):
    return PumpToken.deploy({'from': accounts[0]})


@pytest.fixture(scope="module")
def pool_manager(PoolManager, PumpToken, VPumpToken, accounts):
    pump_token = PumpToken.deploy({'from': accounts[0]})
    vpump_token = VPumpToken.deploy({'from': accounts[0]})
    pool_manager = PoolManager.deploy(pump_token, vpump_token, accounts[0], 100, 0, {'from': accounts[0]})
    pump_token.excludeAddress(pool_manager, {'from': accounts[0]})
    pump_token.transfer(pool_manager, 100 * 10**6 * 10**18, {'from': accounts[0]})
    return pool_manager

@pytest.fixture(scope="module")
def test_lp_token(TestToken, accounts):
    return TestToken.deploy("Fake LP", "Pump-LP", 18, 100 * 10**18, {'from': accounts[0]})

@pytest.fixture(scope="module")
def election_manager(VPumpToken, ElectionManager, accounts):
    vpump_token = VPumpToken.deploy({'from': accounts[0]})
    vpump_token.mint(accounts[0], 10_000, {'from': accounts[0]})
    return ElectionManager.deploy(vpump_token, 0, 10, 100, accounts[9], {'from': accounts[0]})


@pytest.fixture(scope="module")
def test_token_1(TestToken, accounts):
    return TestToken.deploy("T1", "T1", 18, 100 * 10**18, {'from': accounts[0]})


@pytest.fixture(scope="module")
def test_token_2(TestToken, accounts):
    return TestToken.deploy("T2", "T2", 18, 100 * 10**18, {'from': accounts[0]})
