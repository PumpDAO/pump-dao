from brownie import chain, VPumpToken, PumpToken


def _deposit_and_assert(pool_manager, test_lp_token, vpump, account, amount):
    prev_vpump = vpump.balanceOf(account)
    prev_lp = test_lp_token.balanceOf(account)

    test_lp_token.approve(pool_manager, amount, {'from': account})
    pool_manager.deposit(0, amount, {'from': account})

    assert vpump.balanceOf(account) == prev_vpump + amount
    assert test_lp_token.balanceOf(account) == prev_lp - amount


def _withdraw_and_assert(pool_manager, test_lp_token, vpump, pump, account, amount):
    prev_vpump = vpump.balanceOf(account)
    prev_lp = test_lp_token.balanceOf(account)

    pool_manager.withdraw(0, amount, {'from': account})

    assert vpump.balanceOf(account) == prev_vpump - amount
    assert test_lp_token.balanceOf(account) == prev_lp + amount


def test_multi_user_staking(pool_manager, test_lp_token, accounts):
    dev_account, acc1, acc2 = accounts[0], accounts[1], accounts[2]
    vpump = VPumpToken.at(pool_manager.vPumpToken())
    pump = PumpToken.at(pool_manager.pumpToken())
    # alloc_points, lp_token, _withUpdate
    pump_per_block = 100
    pool_manager.add(pump_per_block, test_lp_token, False, {'from': dev_account})

    ######## Setup accounts
    test_lp_token.transfer(acc1, 5_000, {'from': dev_account})
    test_lp_token.transfer(acc2, 1_000, {'from': dev_account})

    _deposit_and_assert(pool_manager, test_lp_token, vpump, dev_account, 10_000)

    chain.mine(10)
    assert  pool_manager.pendingPump(0, dev_account) == 10 * pump_per_block
    assert  pool_manager.pendingPump(0, acc1) == 0
    assert pool_manager.pendingPump(0, acc2) == 0

    _deposit_and_assert(pool_manager, test_lp_token, vpump, acc1, 5_000)

    dev_base = pool_manager.pendingPump(0, dev_account)
    acc1_base = pool_manager.pendingPump(0, acc1)
    acc2_base = pool_manager.pendingPump(0, acc2)
    chain.mine(10)
    assert pool_manager.pendingPump(0, dev_account) == dev_base + 10 * pump_per_block * (10_000 / 15_000)
    assert pool_manager.pendingPump(0, acc1) == acc1_base + 10 * pump_per_block * (5_000 / 15_000)
    assert pool_manager.pendingPump(0, acc2) == acc2_base + 10 * pump_per_block * (0 / 20_000)

    _deposit_and_assert(pool_manager, test_lp_token, vpump, dev_account, 5_000)
    assert pump.balanceOf(dev_account) == 2000

    dev_base = pool_manager.pendingPump(0, dev_account)
    acc1_base = pool_manager.pendingPump(0, acc1)
    acc2_base = pool_manager.pendingPump(0, acc2)
    chain.mine(10)
    assert pool_manager.pendingPump(0, dev_account) == dev_base + 10 * pump_per_block * (15_000 / 20_000)
    assert pool_manager.pendingPump(0, acc1) == acc1_base + 10 * pump_per_block * (5_000 / 20_000)
    assert pool_manager.pendingPump(0, acc2) == acc2_base + 10 * pump_per_block * (0 / 20_000)

    _withdraw_and_assert(pool_manager, test_lp_token, vpump, pump, dev_account, 15_000)

    dev_base = pool_manager.pendingPump(0, dev_account)
    acc1_base = pool_manager.pendingPump(0, acc1)
    acc2_base = pool_manager.pendingPump(0, acc2)
    chain.mine(10)
    assert pool_manager.pendingPump(0, dev_account) == dev_base + 10 * pump_per_block * (0 / 5_000)
    assert pool_manager.pendingPump(0, acc1) == acc1_base + 10 * pump_per_block * (5_000 / 5_000)
    assert pool_manager.pendingPump(0, acc2) == acc2_base + 10 * pump_per_block * (0 / 5_000)

def test_single_user_staking(pool_manager, test_lp_token, accounts):
    account = accounts[0]
    vpump = VPumpToken.at(pool_manager.vPumpToken())
    pump = PumpToken.at(pool_manager.pumpToken())
    # alloc_points, lp_token, _withUpdate
    pump_per_block = 100
    pool_manager.add(pump_per_block, test_lp_token, False, {'from': account})

    # We run this twice to make sure that the first iter doesn't break
    # future staking
    for _ in range(2):
        initial_lp = test_lp_token.balanceOf(account)
        account_lp_stake = 1000
        test_lp_token.approve(pool_manager, account_lp_stake, {'from': account})
        pool_manager.deposit(0, account_lp_stake, {'fom': account})

        # Assert that account has received the vPump
        assert vpump.balanceOf(account) == account_lp_stake
        assert test_lp_token.balanceOf(account) == initial_lp - account_lp_stake

        # Skip forward 10 blocks
        skip_blocks = 10
        chain.mine(skip_blocks)
        pending_reward = pool_manager.pendingPump(0, account)
        assert pending_reward == skip_blocks * pump_per_block

        prev_pump_amt = pump.balanceOf(account)
        pool_manager.withdraw(0, account_lp_stake, {'from': account})

        assert vpump.balanceOf(account) == 0
        assert pump.balanceOf(account) == prev_pump_amt + pending_reward + pump_per_block
        assert test_lp_token.balanceOf(account) == initial_lp

        # skip some number of blocks and then run it all back
        chain.mine(10)