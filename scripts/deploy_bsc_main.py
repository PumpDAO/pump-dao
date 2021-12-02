from brownie import Contract, accounts, ElectionManager, PumpToken, ICO, PSCannon
from .deploy_util import deploy_pump_token, deploy_vote_handler, create_proposal, deploy_ico


# These addresses are the deployed BSC TestNet addresses.
PS_SWAP_ROUTER = "0x10ED43C718714eb63d5aA57B78B54704E256024E"
WBNB_ADDR = "0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c"

# Useful for testing on mainnet
# cannon = Contract.from_abi("cannon", "0x3b5874A22D2e8122aD578014e33c3104C328B22C", PSCannon.abi)
# election_manager = Contract.from_abi("vote", "0x0809fa713340A3A36A895640de64deE4A1e5bBB8", ElectionManager.abi)
# pump_token = Contract.from_abi("Pump", "0x165b51bF3d8520B54Af58aB56c30041B5556aB57", PumpToken.abi)
# a = accounts.load('primary')


def main():
    acct = accounts.load('primary')

    print("Deploying ICO and Pump Token...")
    pump_token = deploy_pump_token(acct)

    print("Deploying ElectionManager and Cannon...")
    vote_handler = ElectionManager.deploy(pump_token.address, {'from': acct})
    cannon = PSCannon.deploy(vote_handler.address, pump_token.address, WBNB_ADDR, PS_SWAP_ROUTER, {'from': acct})
    pump_token.setCannonAddress(cannon.address, {'from': acct})

    return pump_token, vote_handler, cannon

