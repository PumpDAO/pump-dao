from brownie import Contract, accounts, ElectionManager, PumpToken, ICO, PSCannon, Proposal
from .deploy_util import deploy_pump_token, deploy_vote_handler, create_proposal, deploy_ico, write_addresses, update_contracts_for_web

# These addresses are the actual deployed BSC addresses. They are used here
# because the script is expected to be run only in forked BSC envs.
WETH_ADDR = "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2"
UNI_SWAP_ROUTER = "0xE592427A0AEce92De3Edee1F18E0157C05861564"
UNI_FACTORY = "0x1F98431c8aD98523631AE4a59f267346ea31F984"


# Deploys to the a local BSC Hard Fork. I have not gotten LP to work in this context
# so this code only deals with PumpDAO specific contracts
def main():
    acct = accounts[0]

    print("Deploying ICO and Pump Token...")
    ico = deploy_ico(acct)
    pump_token = deploy_pump_token(acct)
    ico.setPumpAddress(pump_token.address)

    print("Deploying ElectionManager and Cannon...")
    vote_handler = deploy_vote_handler(pump_token.address, acct)
    pump_token.setElectionManagerAddr(vote_handler.address)
    vote_handler.createProposal("0XD2877702675E6CEB975B4A1DFF9FB7BAF4C91EA9")

    cannon = PSCannon.deploy(vote_handler.address, pump_token.address, WETH_ADDR, UNI_SWAP_ROUTER, {'from': acct})
    vote_handler.setCannonAddress(cannon.address, {'from': acct})
    pump_token.setElectionManagerAddr(vote_handler.address)


    update_contracts_for_web()
    write_addresses(pump_token.address, vote_handler.address, cannon.address)

    return pump_token, ico, vote_handler, cannon
