from brownie import (
    Contract,
    accounts,
    ElectionManager,
    PumpToken,
    PumpTokenV2,
    PumpTreasury,
    network,
    config,
    ProxyAdmin,
    TransparentUpgradeableProxy,
    VPumpToken,
    PoolManager,
)
from .util import get_account, encode_function_data, upgrade

contract_to_name = {
    ElectionManager: "ElectionManager",
    PoolManager: "PoolManager",
    PumpToken: "PumpToken",
    PumpTreasury: "PumpTreasury",
    VPumpToken: "VPumpToken"
}

# BSC mainnet addr from https://github.com/pinkmoonfinance/pink-antibot-guide
PINK_ANTI_BOT = '0x8EFDb3b642eb2a20607ffe0A56CFefF6a95Df002'

def main():
    pump_token_proxy = TransparentUpgradeableProxy.at("0xe9d9D72691a8929d6AEdA5b44F2BC12C2ff1235E")
    pump_token_proxy_admin = ProxyAdmin.at("0x6FAaAED1cCc4882d2Fe2a3dcdD7F091DC609BCc4")
    account = accounts.load('nico-bsc')
    pump_v2_impl = PumpTokenV2.deploy(
        {"from": account, 'required_confs': 2},
        publish_source=True
    )
    upgrade(account, pump_token_proxy, pump_v2_impl, pump_token_proxy_admin)
    return Contract.from_abi('PumpV2', pump_token_proxy.address, PumpTokenV2.abi)
