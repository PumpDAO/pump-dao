#!/usr/bin/python3

import pytest
from brownie import chain


# These addresses are for test -- their values are irrelevant, just need properly formatted addr
WBNB = "0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c"
PANCAKE_ROUTER_ADDR = "0x10ED43C718714eb63d5aA57B78B54704E256024E"
DEFAULT_TOKEN = "0x10ED43C718714eb63d5aA57B78B54704E256024E"



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
def election_manager(PumpToken, PumpTreasury, VPumpToken, ElectionManager, MockPSRouter, accounts):
    mock_router = MockPSRouter.deploy({'from': accounts[0]})

    pump_token = PumpToken.deploy({'from': accounts[0]})
    pump_treasury = PumpTreasury.deploy(pump_token, WBNB, mock_router, {'from': accounts[0]})

    vpump_token = VPumpToken.deploy({'from': accounts[0]})
    vpump_token.mint(accounts[0], 10_000, {'from': accounts[0]})

    election_manager = ElectionManager.deploy(vpump_token, 0, 10, 100, DEFAULT_TOKEN, pump_treasury, 2, 10, {'from': accounts[0]})
    pump_treasury.setElectionManagerAddress(election_manager, {'from': accounts[0]})

    return election_manager


@pytest.fixture(scope="module")
def test_token_1(TestToken, accounts):
    return TestToken.deploy("T1", "T1", 18, 100 * 10**18, {'from': accounts[0]})


@pytest.fixture(scope="module")
def test_token_2(TestToken, accounts):
    return TestToken.deploy("T2", "T2", 18, 100 * 10**18, {'from': accounts[0]})
