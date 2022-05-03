#!/usr/bin/python3

import pytest
from brownie import chain


# These addresses are for test -- their values are irrelevant, just need properly formatted addr
DEFAULT_TOKEN = "0x10ED43C718714eb63d5aA57B78B54704E256024E"

@pytest.fixture(scope="function", autouse=True)
def isolate(fn_isolation):
    # perform a chain rewind after completing each test, to ensure proper isolation
    # https://eth-brownie.readthedocs.io/en/v1.10.3/tests-pytest-intro.html#isolation-fixtures
    pass


@pytest.fixture(scope="module")
def pump_token(PumpToken, accounts):
    return PumpToken.deploy({'from': accounts[0]})


@pytest.fixture(scope="module")
def pool_manager(PoolManager, PumpToken, VPumpToken, accounts):
    pump_token = PumpToken.deploy({'from': accounts[0]})
    vpump_token = VPumpToken.deploy({'from': accounts[0]})
    pool_manager = PoolManager.deploy(pump_token, vpump_token, accounts[0], 100, 0, {'from': accounts[0]})
    vpump_token.setCanMintBurn(pool_manager, {'from': accounts[0]})
    pump_token.excludeAddress(pool_manager, {'from': accounts[0]})
    pump_token.transfer(pool_manager, 100 * 10**6 * 10**18, {'from': accounts[0]})
    return pool_manager


@pytest.fixture(scope="module")
def test_lp_token(TestToken, accounts):
    return TestToken.deploy("Fake LP", "Pump-LP", 18, 100 * 10**18, {'from': accounts[0]})


@pytest.fixture(scope="module")
def election_manager(PumpToken, TestToken, PumpTreasury, VPumpToken, ElectionManager, MockPSRouter, accounts):
    mock_router = MockPSRouter.deploy({'from': accounts[0]})

    pump_token = PumpToken.deploy({'from': accounts[0]})
    test_wbnb = TestToken.deploy("TEST_WBNB", "TEST_WBNB", 18, 100 * 10**18, {'from': accounts[0]})
    pump_treasury = PumpTreasury.deploy(pump_token, test_wbnb, mock_router, {'from': accounts[0]})
    test_wbnb.transfer(pump_treasury, 100_000, {'from': accounts[0]})

    vpump_token = VPumpToken.deploy({'from': accounts[0]})
    vpump_token.mint(accounts[0], 10_000, {'from': accounts[0]})

    election_manager = ElectionManager.deploy(
        vpump_token,
        0,
        10,
        100,
        DEFAULT_TOKEN,
        pump_treasury,
        2,  # _maxNumBuys
        10,  # _buyCooldownBlocks
        10,  # _sellLockupBlocks
        10,  # _sellHalflifeBlocks
        {'from': accounts[0]}
    )
    pump_treasury.setElectionManagerAddress(election_manager, {'from': accounts[0]})
    vpump_token.setElectionManagerAddress(election_manager, {'from': accounts[0]})

    return election_manager


@pytest.fixture(scope="module")
def broken_election_manager(PumpToken, TestToken, PumpTreasury, VPumpToken, ElectionManager, MockPSRouterError, accounts):
    broken_router = MockPSRouterError.deploy({'from': accounts[0]})

    pump_token = PumpToken.deploy({'from': accounts[0]})
    test_wbnb = TestToken.deploy("TEST_WBNB", "TEST_WBNB", 18, 100 * 10**18, {'from': accounts[0]})
    pump_treasury = PumpTreasury.deploy(pump_token, test_wbnb, broken_router, {'from': accounts[0]})
    test_wbnb.transfer(pump_treasury, 100_000, {'from': accounts[0]})

    vpump_token = VPumpToken.deploy({'from': accounts[0]})
    vpump_token.mint(accounts[0], 10_000, {'from': accounts[0]})

    election_manager_error = ElectionManager.deploy(
        vpump_token,
        0,
        10,
        100,
        DEFAULT_TOKEN,
        pump_treasury,
        2,  # _maxNumBuys
        10,  # _buyCooldownBlocks
        10,  # _sellLockupBlocks
        10,  # _sellHalflifeBlocks
        {'from': accounts[0]}
    )
    pump_treasury.setElectionManagerAddress(election_manager_error, {'from': accounts[0]})
    vpump_token.setElectionManagerAddress(election_manager_error, {'from': accounts[0]})

    return election_manager_error


@pytest.fixture(scope="module")
def test_token_1(TestToken, accounts):
    return TestToken.deploy("T1", "T1", 18, 100 * 10**18, {'from': accounts[0]})


@pytest.fixture(scope="module")
def test_token_2(TestToken, accounts):
    return TestToken.deploy("T2", "T2", 18, 100 * 10**18, {'from': accounts[0]})


@pytest.fixture(scope="module")
def pump_treasury(TestToken, MockPSRouter, PumpTreasury, pump_token, accounts):
    wbnb = TestToken.deploy("WBNB", "WBNB", 18, 100 * 10**18, {'from': accounts[0]})
    mock_router = MockPSRouter.deploy({'from': accounts[0]})

    return PumpTreasury.deploy(pump_token, wbnb, mock_router, {'from': accounts[0]})
