from brownie import Cannon, Contract, accounts, ElectionManager, PumpToken, ICO, PSCannon
from .deploy_util import deploy_pump_token, deploy_vote_handler, create_proposal, deploy_ico


# These addresses are the deployed BSC TestNet addresses.
PS_SWAP_ROUTER = "0x10ED43C718714eb63d5aA57B78B54704E256024E"
WBNB_ADDR = "0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c"


def main():
    acct = accounts.load('brownie-acc-1')

    print("Deploying ICO and Pump Token...")
    ico = deploy_ico(acct)
    pump_token = deploy_pump_token(acct)
    ico.setPumpAddress(pump_token.address)

    print("Deploying ElectionManager and Cannon...")
    vote_handler = ElectionManager.deploy(pump_token.address, {'from': acct})
    cannon = PSCannon.deploy(vote_handler.address, pump_token.address, WBNB_ADDR, PS_SWAP_ROUTER, {'from': acct})
    pump_token.setCannonAddress(cannon.address, {'from': acct})

    return pump_token, ico, vote_handler, cannon