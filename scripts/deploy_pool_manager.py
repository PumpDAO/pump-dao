from brownie import Token, PumpToken, PoolManager, Contract, accounts

def main():
    acct = accounts[0]
    pump_token = PumpToken.deploy({'from': acct})
    test_token = Token.deploy("TEST", "TST", 18, 100*10**18, {'from': acct})
    pool_manager = PoolManager.deploy(pump_token, acct, acct, 100, 0, {'from': acct})
    pump_token.approve(pool_manager, 100000000000000, {'from': acct})
    test_token.approve(pool_manager, 100000000000000, {'from': acct})
    pool_manager.add(100, test_token, 0, False, {'from': acct})
    return acct, pump_token, pool_manager