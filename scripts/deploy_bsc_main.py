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
WBTC = "0x7130d2A12B9BCbFAe4f2634d864A1Ee1Ce3Ead9c"
BLOCKS_PER_MIN = 20

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
        {"from": account, 'required_confs': 2},
        publish_source=True
    )
    proxy_admin = ProxyAdmin.deploy(
        {"from": account, 'required_confs': 2},
        publish_source=True,
    )
    encoded_initializer_function = encode_function_data(
        implementation.initialize, *args
    )
    proxy = TransparentUpgradeableProxy.deploy(
        implementation,
        proxy_admin.address,
        encoded_initializer_function,
        {"from": account, 'required_confs': 2},
        publish_source=True,
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
    pump.setTreasuryAddr(treasury, {'from': account})

    election_manager = deploy_with_proxy(
        account,
        ElectionManager,
        vpump,
        BLOCKS_PER_MIN * 60 * 2,  # winnerDelay
        BLOCKS_PER_MIN * 60 * 24 * 7,  # electionLength
        WBTC,  # default Proposal
        treasury,
        50,  # maxNumBuys
        BLOCKS_PER_MIN * 60,  # buyCooldownBlocks
        BLOCKS_PER_MIN * 60 * 24 * 7,  # sellLockupBlocks
        BLOCKS_PER_MIN * 60 * 24 * 50,  # sellHalflifeBlocks
        0.2 * 10 ** 18,  # proposalCreationTax
        WBNB_ADDR,
    )

    treasury.setElectionManagerAddress(election_manager, {'from': account})
    vpump.setElectionManagerAddress(election_manager, {'from': account})
    pump.setElectionManagerAddr(election_manager, {'from': account})

    pool_manager = deploy_with_proxy(
        account,
        PoolManager,
        pump,
        vpump,
        1.26839167935 * 10**18,  # pumpPerBlock -- equates to 40_000_000 over 3 years
    )

    vpump.setCanMintBurn(pool_manager, {'from': account})

    return pump, vpump, treasury, election_manager, pool_manager
