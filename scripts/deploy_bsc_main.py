from brownie import (
    Contract,
    accounts,
    ElectionManager,
    PumpToken,
    PumpTreasury,
    network,
    config,
    ProxyAdmin,
    TransparentUpgradeableProxy,
    VPumpToken,
    PoolManager,
)
from .util import get_account, encode_function_data

# These addresses are the deployed BSC Main addresses.
PS_SWAP_ROUTER_ADDR = "0x10ED43C718714eb63d5aA57B78B54704E256024E"
WBNB_ADDR = "0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c"


# Useful for testing on mainnet
# cannon = Contract.from_abi("cannon", "0x3b5874A22D2e8122aD578014e33c3104C328B22C", PumpTreasury.abi)
# election_manager = Contract.from_abi("vote", "0x0809fa713340A3A36A895640de64deE4A1e5bBB8", ElectionManager.abi)
# pump_token = Contract.from_abi("Pump", "0x165b51bF3d8520B54Af58aB56c30041B5556aB57", PumpToken.abi)
# a = accounts.load('primary')

contract_to_name = {
    ElectionManager: "ElectionManager",
    PoolManager: "PoolManager",
    PumpToken: "PumpToken",
    PumpTreasury: "PumpTreasury",
    VPumpToken: "VPumpToken"
}


def deploy_with_proxy(account, contract, *args):
    print(f"Deploying to {network.show_active()}")
    implementation = contract.deploy(
        {"from": account, 'required_confs': 3},
        publish_source=True
    )
    proxy_admin = ProxyAdmin.deploy(
        {"from": account, 'required_confs': 3},
        # publish_source=True,
    )
    encoded_initializer_function = encode_function_data(
        implementation.initialize, *args
    )
    proxy = TransparentUpgradeableProxy.deploy(
        implementation,
        proxy_admin.address,
        encoded_initializer_function,
        {"from": account, 'required_confs': 3},
        # publish_source=True,
    )
    print(f"Proxy deployed to {proxy}")
    proxy_abi = Contract.from_abi(contract_to_name[contract], proxy.address, contract.abi)

    print(f"""
        Final: {contract} deployment info:
        impl: {implementation}
        proxy_admin: {proxy_admin}
        proxy: {proxy}
    """)

    return proxy_abi


def main():
    account = get_account()
    pump = deploy_with_proxy(account, PumpToken)
    vpump = deploy_with_proxy(account, VPumpToken)

    treasury = deploy_with_proxy(
        account,
        PumpTreasury,
        pump,
        WBNB_ADDR,
        PS_SWAP_ROUTER_ADDR,
    )

    election_manager = deploy_with_proxy(
        account,
        ElectionManager,
        vpump,
        0,  # startBlock
        180,  # winnerDelay
        360,  # electionLength
        WBNB_ADDR,  # electionLength
        treasury,
        5,  # maxNulBuys
        10,  # buyCooldownBlocks
        0,  # sellLockupBlocks
        10,  # sellHalflifeBlocks
    )

    treasury.setElectionManagerAddress(election_manager, {'from': account})
    vpump.setElectionManagerAddress(election_manager, {'from': account})

    pool_manager = deploy_with_proxy(
        account,
        PoolManager,
        pump,
        vpump,
        1 * 10**18,  # pumpPerBlock
        17523000,  # startBlock
    )

    vpump.setCanMintBurn(pool_manager, {'from': account})
    pump.transfer(pool_manager, 100_000 * 10**18, {'from': account})

    return pump, vpump, treasury, election_manager, pool_manager
