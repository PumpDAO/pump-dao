#!/usr/bin/python3

import pytest
from brownie import chain


# These addresses are for test -- their values are irrelevant, just need properly formatted addr
DEFAULT_TOKEN_ADDR = "0x10ED43C718714eb63d5aA57B78B54704E256024E"


def _deploy_init_pump(PumpToken, acct):
    pump_token = PumpToken.deploy({'from': acct})
    pump_token.initialize({'from': acct})
    return pump_token


def _deploy_init_vpump(VPumpToken, acct):
    vpump_token = VPumpToken.deploy({'from': acct})
    vpump_token.initialize({'from': acct})
    return vpump_token


def _deploy_init_pool_manager(PoolManager, pump, vpump, pump_per_block, start_block, acct):
    pool_manager = PoolManager.deploy({'from': acct})
    pool_manager.initialize(pump, vpump, pump_per_block, {'from': acct})
    pool_manager.setStartEnd(start_block, 999999999, {'from': acct})
    return pool_manager


def _deploy_init_pump_treasury(PumpTreasury, pump, wbnb, router, acct):
    pump_treasury = PumpTreasury.deploy({'from': acct})
    pump_treasury.initialize(pump, wbnb, router, {'from': acct})
    return pump_treasury


def _deploy_init_election_manager(
        ElectionManager,
        vpump,
        winner_delay,
        election_length,
        default_proposal,
        treasury,
        max_num_buys,
        buy_cooldown,
        sell_lockup,
        sell_halflife,
        proposal_creation_tax,
        acct):
    election_manager = ElectionManager.deploy({'from': acct})
    election_manager.initialize(
        vpump,
        winner_delay,
        election_length,
        default_proposal,
        treasury,
        max_num_buys,
        buy_cooldown,
        sell_lockup,
        sell_halflife,
        proposal_creation_tax,
        "0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c",
        {'from': acct}
    )
    return election_manager


@pytest.fixture(scope="function", autouse=True)
def isolate(fn_isolation):
    # perform a chain rewind after completing each test, to ensure proper isolation
    # https://eth-brownie.readthedocs.io/en/v1.10.3/tests-pytest-intro.html#isolation-fixtures
    pass


@pytest.fixture(scope="module")
def pump_token(PumpToken, accounts):
    return _deploy_init_pump(PumpToken, accounts[0])


@pytest.fixture(scope="module")
def pool_manager(PoolManager, PumpToken, VPumpToken, accounts):
    pump_token = _deploy_init_pump(PumpToken, accounts[0])
    vpump_token = _deploy_init_vpump(VPumpToken, accounts[0])
    pool_manager = _deploy_init_pool_manager(PoolManager, pump_token, vpump_token, 100, 0, accounts[0])
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
    pump_token = _deploy_init_pump(PumpToken, accounts[0])
    test_wbnb = TestToken.deploy("TEST_WBNB", "TEST_WBNB", 18, 100 * 10**18, {'from': accounts[0]})
    pump_treasury = _deploy_init_pump_treasury(PumpTreasury, pump_token, test_wbnb, mock_router, accounts[0])
    test_wbnb.transfer(pump_treasury, 100_000, {'from': accounts[0]})

    vpump_token = _deploy_init_vpump(VPumpToken, accounts[0])
    vpump_token.mint(accounts[0], 10_000, {'from': accounts[0]})

    election_manager = _deploy_init_election_manager(
        ElectionManager,
        vpump_token,
        10, # winnerDelay
        100, # electionLength
        DEFAULT_TOKEN_ADDR, # default Proposal address
        pump_treasury, # treasury
        2,  # _maxNumBuys
        10,  # _buyCooldownBlocks
        10,  # _sellLockupBlocks
        10,  # _sellHalflifeBlocks,
        0.25 * 10 ** 18,  # proposalCreationTax
        accounts[0]
    )
    election_manager.startFirstElection(0, {'from': accounts[0]})
    pump_treasury.setElectionManagerAddress(election_manager, {'from': accounts[0]})
    vpump_token.setElectionManagerAddress(election_manager, {'from': accounts[0]})

    return election_manager


@pytest.fixture(scope="module")
def broken_election_manager(PumpToken, TestToken, PumpTreasury, VPumpToken, ElectionManager, MockPSRouterError, accounts):
    mock_router = MockPSRouterError.deploy({'from': accounts[0]})
    pump_token = _deploy_init_pump(PumpToken, accounts[0])
    test_wbnb = TestToken.deploy("TEST_WBNB", "TEST_WBNB", 18, 100 * 10 ** 18, {'from': accounts[0]})
    pump_treasury = _deploy_init_pump_treasury(PumpTreasury, pump_token, test_wbnb, mock_router, accounts[0])
    test_wbnb.transfer(pump_treasury, 100_000, {'from': accounts[0]})

    vpump_token = _deploy_init_vpump(VPumpToken, accounts[0])
    vpump_token.mint(accounts[0], 10_000, {'from': accounts[0]})

    election_manager = _deploy_init_election_manager(
        ElectionManager,
        vpump_token,
        10,  # winnerDelay
        100,  # electionLength
        DEFAULT_TOKEN_ADDR,  # default Proposal address
        pump_treasury,  # treasury
        2,  # _maxNumBuys
        10,  # _buyCooldownBlocks
        10,  # _sellLockupBlocks
        10,  # _sellHalflifeBlocks
        0.25 * 10 ** 18,  # proposalCreationTax
        accounts[0]
    )
    election_manager.startFirstElection(0, {'from': accounts[0]})
    pump_treasury.setElectionManagerAddress(election_manager, {'from': accounts[0]})
    vpump_token.setElectionManagerAddress(election_manager, {'from': accounts[0]})

    return election_manager


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

    return _deploy_init_pump_treasury(PumpTreasury, pump_token, wbnb, mock_router, accounts[0])
