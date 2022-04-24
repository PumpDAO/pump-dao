from brownie import chain, ElectionManager

def test_something(election_manager, test_lp_token, accounts):
    assert len(election_manager.getActiveProposals()) == 0

    election_manager.createProposal(test_lp_token, {'from': accounts[0], 'value': 1*10**18})

    print(election_manager.getActiveProposals())
    assert False