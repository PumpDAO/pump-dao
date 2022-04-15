from brownie import chain, VPumpToken, PumpToken

def _deposit_and_assert(pool_manager, test_lp_token, vpump, account, amount):
    prev_vpump = vpump.balanceOf(account)
    prev_lp = test_lp_token.balanceOf(account)

    test_lp_token.approve(pool_manager, amount, {'from': account})
    tx = pool_manager.deposit(0, amount, {'from': account})
    #
    # for e in tx.events:
    #     print(e)
    #
    # assert False
    assert vpump.balanceOf(account) == prev_vpump + amount
    assert test_lp_token.balanceOf(account) == prev_lp - amount


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
    dev_account_pending_pump = pool_manager.pendingPump(0, dev_account)
    assert dev_account_pending_pump == 10 * pump_per_block

    _deposit_and_assert(pool_manager, test_lp_token, vpump, acc1, 5_000)


#
# def test_single_user_staking(pool_manager, test_lp_token, accounts):
#     account = accounts[0]
#     vpump = VPumpToken.at(pool_manager.vPumpToken())
#     pump = PumpToken.at(pool_manager.pumpToken())
#     # alloc_points, lp_token, _withUpdate
#     pump_per_block = 100
#     pool_manager.add(pump_per_block, test_lp_token, False, {'from': account})
#
#     # We run this twice to make sure that the first iter doesn't break
#     # future staking
#     for _ in range(2):
#         initial_lp = test_lp_token.balanceOf(account)
#         account_lp_stake = 1000
#         test_lp_token.approve(pool_manager, account_lp_stake, {'from': account})
#         pool_manager.deposit(0, account_lp_stake, {'fom': account})
#
#         # Assert that account has received the vPump
#         assert vpump.balanceOf(account) == account_lp_stake
#         assert test_lp_token.balanceOf(account) == initial_lp - account_lp_stake
#
#         # Skip forward 10 blocks
#         skip_blocks = 10
#         chain.mine(skip_blocks)
#         pending_reward = pool_manager.pendingPump(0, account)
#         assert pending_reward == skip_blocks * pump_per_block
#
#         prev_pump_amt = pump.balanceOf(account)
#         pool_manager.withdraw(0, account_lp_stake, {'from': account})
#
#         assert vpump.balanceOf(account) == 0
#         assert pump.balanceOf(account) == prev_pump_amt + pending_reward
#         assert test_lp_token.balanceOf(account) == initial_lp
#
#         # skip some number of blocks and then run it all back
#         chain.mine(10)
