from brownie import Contract, accounts, ElectionManager, PumpToken, ICO, PSCannon
from .deploy_util import deploy_pump_token, deploy_vote_handler, create_proposal, deploy_ico


# These addresses are the deployed BSC TestNet addresses.
BUSD_ADDR = "0x3382f1eb52d3caa32e281eac539c48bb0a3d6290"
PS_SWAP_ROUTER = "0xCc7aDc94F3D80127849D2b41b6439b7CF1eB4Ae0"
WBNB_ADDR = "0x0dE8FCAE8421fc79B29adE9ffF97854a424Cad09"
PS_FACTORY = "0x6725F303b657a9451d8BA641348b6761A6CC7a17"


def main():
    acct = accounts.load('brownie-acc-1')

    print("Deploying ICO and Pump Token...")
    ico = deploy_ico(acct)
    pump_token = deploy_pump_token(acct)
    ico.setPumpAddress(pump_token.address)

    print("Fetching up PS Contracts...")
    router = Contract.from_explorer(PS_SWAP_ROUTER)
    factory = Contract.from_explorer(PS_FACTORY)

    print("Deploying ElectionManager and Cannon...")
    vote_handler = ElectionManager.deploy(pump_token.address, {'from': acct})
    cannon = PSCannon.deploy(vote_handler.address, pump_token.address, WBNB_ADDR, PS_SWAP_ROUTER, {'from': acct})
    pump_token.setCannonAddress(cannon.address, {'from': acct})

    wbnb = Contract.from_explorer(WBNB_ADDR)
    setup_liquidity_pool(acct, factory, router, wbnb, pump_token)

    return pump_token, ico, vote_handler, cannon, wbnb


def setup_liquidity_pool(account, factory, router, wbnb, pump):
    print("Creating LP...")
    factory.createPair(pump.address, wbnb.address, {'from': account})

    print("Approving ERC20 transfers...")
    pump.approve(router, 100 * 10 ** 6 * 10**18, {'from': account})
    wbnb.deposit({'from': account, 'value': 0.1*10**18})
    wbnb.approve(router, 100*10**18, {'from': account})

    print("Adding liquidity...")
    router.addLiquidity(
        pump.address,
        wbnb.address,
        1000 * 10 ** 18,
        0.1 * 10 ** 18,
        0,
        0,
        account,
        99999999999,
        {'from': account, 'gas': 9000000}
    )
