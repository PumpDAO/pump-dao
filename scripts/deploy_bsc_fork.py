from brownie import Contract, accounts, ElectionManager, PumpToken, ICO, PSCannon, Proposal
from .deploy_util import deploy_pump_token, deploy_vote_handler, create_proposal, deploy_ico

# These addresses are the actual deployed BSC addresses. They are used here
# because the script is expected to be run only in forked BSC envs.
WBNB_ADDR = "0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c"
PS_SWAP_ROUTER = "0x10ED43C718714eb63d5aA57B78B54704E256024E"
PS_FACTORY = "0xBCfCcbde45cE874adCB698cC183deBcF17952812"


# Deploys to the a local BSC Hard Fork. I have not gotten LP to work in this context
# so this code only deals with PumpDAO specific contracts
def main():
    acct = accounts[0]

    print("Deploying ICO and Pump Token...")
    ico = deploy_ico(acct)
    pump_token = deploy_pump_token(acct)
    ico.setPumpAddress(pump_token.address)

    print("Fetching up PS Contracts...")
    router = Contract.from_explorer(PS_SWAP_ROUTER)
    factory = Contract.from_explorer(PS_FACTORY)

    print("Deploying ElectionManager and Cannon...")
    vote_handler = deploy_vote_handler(pump_token.address, acct)
    cannon = PSCannon.deploy(vote_handler.address, pump_token.address, WBNB_ADDR, PS_SWAP_ROUTER, {'from': acct})
    vote_handler.setCannonAddress(cannon.address, {'from': acct})
    pump_token.setElectionManagerAddr(vote_handler.address)

    return pump_token, ico, vote_handler, cannon, factory, router
