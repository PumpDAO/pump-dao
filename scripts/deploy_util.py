from brownie import Contract, ElectionManager, PumpToken, ICO
from distutils.dir_util import copy_tree
import json


def deploy_pump_token(account):
    return PumpToken.deploy({'from': account})


def deploy_ico(account):
    return ICO.deploy({'from': account})


def deploy_vote_handler(pump_address, account):
    vote_handler = ElectionManager.deploy(pump_address, {'from': account})
    return vote_handler


def create_proposal(vote_hanlder_address, erc20_address):
    vote_handler = ElectionManager(vote_hanlder_address)
    return vote_handler.createProposal(erc20_address)


def update_contracts_for_web():
    from_directory = "./build/contracts"
    to_directory = "../web/src/contracts"
    copy_tree(from_directory, to_directory)


def write_addresses(pump_addr, vote_addr, cannon_addr):
    data = {'PUMP': pump_addr, 'VOTE': vote_addr, 'CANNON': cannon_addr}
    with open('../web/src/contracts/addresses.json', 'w') as outfile:
        json.dump(data, outfile)


