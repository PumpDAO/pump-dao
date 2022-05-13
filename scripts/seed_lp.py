from brownie import Contract, accounts, ElectionManager, PumpToken, PumpTreasury, PoolManager, VPumpToken, chain

PS_SWAP_ROUTER = ''
WBNB_ADDR = ''
PS_FACTORY = ''
PUMP_PROXY = ''
VPUMP_PROXY = ''
EM_PROXY = ''
VPUMP_PROXY = ''
POOL_MANAGER = ''
LP_TOKEN_ADDR = ''

def main():
    acct = accounts.load('primary')
    # wbnb = Contract.from_explorer(WBNB_ADDR)
    # pump = Contract.from_abi('Pump Token', PUMP_PROXY, PumpToken.abi)
    vpump = Contract.from_abi('vPump Token', VPUMP_PROXY, VPumpToken.abi)
    # factory = Contract.from_explorer(PS_FACTORY)
    # router = Contract.from_explorer(PS_SWAP_ROUTER)
    #
    # setup_liquidity_pool(acct, factory, router, wbnb, pump)
    #
    # height = (chain.height)

    print("setting up pool manager....")
    pool_manager = Contract.from_abi('Pool Manager', POOL_MANAGER, PoolManager.abi)
    # pool_manager.setStartEnd(chain.height, chain.height + 100000000, {'from': acct})
    # pool_manager.add(100, LP_TOKEN_ADDR, False, {'from': acct})
    lp = Contract.from_explorer(LP_TOKEN_ADDR)

    print("depositing into staking pool")
    lp.approve(pool_manager, 1*10**18, {'from': acct})
    pool_manager.deposit(0, 1*10**18, {'from': acct})

    print("setting up election manager")
    election_manager = Contract.from_abi('Election Manager', EM_PROXY, ElectionManager.abi)
    election_manager.startFirstElection(chain.height, {'from': acct})

    print("creating proposal...")
    election_manager.createProposal(0, '', {'from': acct, 'value': 0.025 * 10 ** 18})

    print("voting....")
    vpump.approve(election_manager, 10000000000000, {'from': acct})
    election_manager.vote(0, '', 100)


def setup_liquidity_pool(account, factory, router, wbnb, pump):
    print("Creating LP...")
    factory.createPair(pump.address, wbnb.address, {'from': account})

    print("Approving ERC20 transfers...")
    pump.approve(router, 50 * 10 ** 6 * 10**18, {'from': account})
    wbnb.deposit({'from': account, 'value': 0.05*10**18})
    wbnb.approve(router, 0.05*10**18, {'from': account})

    print("Adding liquidity...")
    router.addLiquidity(
        pump.address,
        wbnb.address,
        50 * 10**6 * 10 ** 18,
        0.05 * 10 ** 18,
        0,
        0,
        account,
        99999999999,
        {'from': account, 'gas': 9000000}
    )
