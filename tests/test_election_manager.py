from brownie import chain, ElectionManager, VPumpToken, reverts


def test_create_proposal(election_manager, test_token_1, accounts):
    assert len(election_manager.getActiveProposals()) == 1
    election_manager.createProposal(0, test_token_1, {'from': accounts[0], 'value': 1 * 10 ** 18})
    proposals = election_manager.getActiveProposals()
    assert len(proposals) == 2
    assert proposals[1] == test_token_1


def test_create_proposal_wrong_election(election_manager, test_token_1, accounts):
    assert len(election_manager.getActiveProposals()) == 1
    with reverts("Must use currentElectionIdx"):
        election_manager.createProposal(1, test_token_1, {'from': accounts[0], 'value': 1 * 10 ** 18})
    assert len(election_manager.getActiveProposals()) == 1


def test_create_proposal_insufficient_value(election_manager, test_token_1, accounts):
    assert len(election_manager.getActiveProposals()) == 1
    with reverts("BuyProposal creation tax not met"):
        election_manager.createProposal(0, test_token_1, {'from': accounts[0], 'value': 0.1 * 10 ** 18})
    assert len(election_manager.getActiveProposals()) == 1


############################################################################
############################################################################


def test_vote_vpump_not_approved(election_manager, test_token_1, accounts):
    vpump = VPumpToken.at(election_manager.vPumpToken())
    election_manager.createProposal(0, test_token_1, {'from': accounts[0], 'value': 1 * 10 ** 18})

    prev_vpump = vpump.balanceOf(accounts[0])
    with reverts("vPUMP transfer not approved"):
        election_manager.vote(0, test_token_1, 1000, {'from': accounts[0]})

    assert vpump.balanceOf(accounts[0]) == prev_vpump
    assert election_manager.getProposal(0, test_token_1)["totalVotes"] == 0


def test_vote_wrong_election(election_manager, test_token_1, accounts):
    vpump = VPumpToken.at(election_manager.vPumpToken())
    election_manager.createProposal(0, test_token_1, {'from': accounts[0], 'value': 1 * 10 ** 18})

    vpump.approve(election_manager, 1000, {'from': accounts[0]})
    prev_vpump = vpump.balanceOf(accounts[0])
    with reverts("Must use currElectionIdx"):
        election_manager.vote(1, test_token_1, 1000, {'from': accounts[0]})

    assert vpump.balanceOf(accounts[0]) == prev_vpump
    assert election_manager.getProposal(0, test_token_1)["totalVotes"] == 0


def test_vote_voting_ended(election_manager, test_token_1, accounts):
    vpump = VPumpToken.at(election_manager.vPumpToken())
    election_manager.createProposal(0, test_token_1, {'from': accounts[0], 'value': 1 * 10 ** 18})

    vpump.approve(election_manager, 1000, {'from': accounts[0]})
    prev_vpump = vpump.balanceOf(accounts[0])
    chain.mine(90)
    with reverts("Voting has already ended"):
        election_manager.vote(0, test_token_1, 1000, {'from': accounts[0]})

    assert vpump.balanceOf(accounts[0]) == prev_vpump
    assert election_manager.getProposal(0, test_token_1)["totalVotes"] == 0


def test_vote_invalid_proposal(election_manager, test_token_1, accounts):
    vpump = VPumpToken.at(election_manager.vPumpToken())
    election_manager.createProposal(0, test_token_1, {'from': accounts[0], 'value': 1 * 10 ** 18})

    vpump.approve(election_manager, 1000, {'from': accounts[0]})
    prev_vpump = vpump.balanceOf(accounts[0])
    with reverts("Must be valid proposal"):
        election_manager.vote(0, accounts[1], 1000, {'from': accounts[0]})

    assert vpump.balanceOf(accounts[0]) == prev_vpump
    assert election_manager.getProposal(0, test_token_1)["totalVotes"] == 0


def test_vote(election_manager, test_token_1, accounts):
    vpump = VPumpToken.at(election_manager.vPumpToken())
    election_manager.createProposal(0, test_token_1, {'from': accounts[0], 'value': 1 * 10 ** 18})

    prev_vpump = vpump.balanceOf(accounts[0])
    vpump.approve(election_manager, 1000, {'from': accounts[0]})
    election_manager.vote(0, test_token_1, 1000, {'from': accounts[0]})

    assert vpump.balanceOf(accounts[0]) == prev_vpump - 1000
    assert election_manager.getProposal(0, test_token_1)["totalVotes"] == 1000

    prev_vpump = vpump.balanceOf(accounts[0])
    vpump.approve(election_manager, 1000, {'from': accounts[0]})
    election_manager.vote(0, test_token_1, 1000, {'from': accounts[0]})

    assert vpump.balanceOf(accounts[0]) == prev_vpump - 1000
    assert election_manager.getProposal(0, test_token_1)["totalVotes"] == 2000

    vpump.mint(accounts[1], 100, {'from': accounts[0]})
    vpump.approve(election_manager, 100, {'from': accounts[1]})
    election_manager.vote(0, test_token_1, 100, {'from': accounts[1]})

    assert vpump.balanceOf(accounts[1]) == 0
    assert election_manager.getProposal(0, test_token_1)["totalVotes"] == 2100


############################################################################
############################################################################

def test_withdraw_vote_invalid_proposals(election_manager, test_token_1, accounts):
    with reverts("Must be valid proposal"):
        election_manager.withdrawVote(1, test_token_1, 1000, {'from': accounts[0]})


def test_withdraw_vote_more_than_cast(election_manager, test_token_1, accounts):
    vpump = VPumpToken.at(election_manager.vPumpToken())
    election_manager.createProposal(0, test_token_1, {'from': accounts[0], 'value': 1 * 10 ** 18})

    vpump.approve(election_manager, 1000, {'from': accounts[0]})
    election_manager.vote(0, test_token_1, 1000, {'from': accounts[0]})
    with reverts("More votes than cast"):
        election_manager.withdrawVote(0, test_token_1, 10000, {'from': accounts[0]})


def test_withdraw_vote_only_voter(election_manager, test_token_1, accounts):
    vpump = VPumpToken.at(election_manager.vPumpToken())
    election_manager.createProposal(0, test_token_1, {'from': accounts[0], 'value': 1 * 10 ** 18})

    vpump.approve(election_manager, 1000, {'from': accounts[0]})
    election_manager.vote(0, test_token_1, 1000, {'from': accounts[0]})

    prev_vpump = vpump.balanceOf(accounts[0])
    prev_votes = election_manager.getProposal(0, test_token_1)["totalVotes"]

    election_manager.withdrawVote(0, test_token_1, 500, {'from': accounts[0]})

    assert vpump.balanceOf(accounts[0]) == prev_vpump + 500
    assert election_manager.getProposal(0, test_token_1)["totalVotes"] == prev_votes - 500

    vpump.mint(accounts[1], 100, {'from': accounts[0]})
    vpump.approve(election_manager, 100, {'from': accounts[1]})
    election_manager.vote(0, test_token_1, 100, {'from': accounts[1]})

    prev_vpump = vpump.balanceOf(accounts[1])
    prev_votes = election_manager.getProposal(0, test_token_1)["totalVotes"]

    election_manager.withdrawVote(0, test_token_1, 100, {'from': accounts[1]})

    assert vpump.balanceOf(accounts[1]) == prev_vpump + 100
    assert election_manager.getProposal(0, test_token_1)["totalVotes"] == prev_votes - 100

############################################################################
############################################################################

def test_declare_winner_wrong_election(election_manager, accounts):
    with reverts("Must be currElectionIdx"):
        election_manager.declareWinner(1, {'from': accounts[0]})


def test_declare_winner_before_end(election_manager, accounts):
    with reverts("Voting not finished"):
        election_manager.declareWinner(0, {'from': accounts[0]})


def test_declare_winner_no_proposals(election_manager, accounts):
    election_metadata = election_manager.getElectionMetadata(0)
    assert not election_metadata["winnerDeclared"]
    chain.mine(100)
    election_manager.declareWinner(0, {'from': accounts[0]})
    election_metadata = election_manager.getElectionMetadata(0)
    assert election_metadata["winnerDeclared"]
    assert election_metadata["winner"] == election_manager.defaultProposal()

def test_declare_winner_with_proposals(election_manager, test_token_1, test_token_2, accounts):
    vpump = VPumpToken.at(election_manager.vPumpToken())
    election_manager.createProposal(0, test_token_1, {'from': accounts[0], 'value': 1 * 10 ** 18})

    prev_vpump = vpump.balanceOf(accounts[0])
    vpump.approve(election_manager, 1000, {'from': accounts[0]})
    election_manager.vote(0, test_token_1, 1000, {'from': accounts[0]})

    assert vpump.balanceOf(accounts[0]) == prev_vpump - 1000
    assert election_manager.getProposal(0, test_token_1)["totalVotes"] == 1000

    prev_vpump = vpump.balanceOf(accounts[0])
    vpump.approve(election_manager, 1000, {'from': accounts[0]})
    election_manager.vote(0, test_token_1, 1000, {'from': accounts[0]})

    assert vpump.balanceOf(accounts[0]) == prev_vpump - 1000
    assert election_manager.getProposal(0, test_token_1)["totalVotes"] == 2000

    vpump.mint(accounts[1], 100, {'from': accounts[0]})
    vpump.approve(election_manager, 100, {'from': accounts[1]})
    election_manager.createProposal(0, test_token_2, {'from': accounts[1], 'value': 1 * 10 ** 18})
    election_manager.vote(0, test_token_2, 100, {'from': accounts[1]})

    chain.mine(100)
    election_manager.declareWinner(0, {'from': accounts[0]})
    election_metadata = election_manager.getElectionMetadata(0)
    assert election_metadata["winnerDeclared"]
    assert election_metadata["winner"] == test_token_1


#######################################################################################################
#######################################################################################################

def test_execute_buy_proposal_no_winner(election_manager, accounts):
    with reverts("Winner not declared"):
        election_manager.executeBuyProposal(0, {'from': accounts[0]})


def test_execute_buy(election_manager, test_token_1, accounts):
    vpump = VPumpToken.at(election_manager.vPumpToken())
    election_manager.createProposal(0, test_token_1, {'from': accounts[0], 'value': 1 * 10 ** 18})

    vpump.approve(election_manager, 1000, {'from': accounts[0]})
    election_manager.vote(0, test_token_1, 1000, {'from': accounts[0]})

    chain.mine(100)
    election_manager.declareWinner(0, {'from': accounts[0]})

    assert election_manager.executeBuyProposal(0, {'from': accounts[0]}).return_value

    with reverts("Must wait before executing"):
        election_manager.executeBuyProposal(0, {'from': accounts[0]})

    assert not election_manager.getElectionMetadata(0)["sellProposalActive"]
    chain.mine(10)

    assert election_manager.executeBuyProposal(0, {'from': accounts[0]}).return_value
    assert election_manager.getElectionMetadata(0)["sellProposalActive"]

    chain.mine(10)
    with reverts("Can't exceed maxNumBuys"):
        election_manager.executeBuyProposal(0, {'from': accounts[0]})

    # Now move onto voting to sell
    with reverts("Not enough votes to execute"):
        election_manager.executeSellProposal(0, {'from': accounts[0]})

    election_manager.withdrawVote(0, test_token_1, 1000, {'from': accounts[0]})
    vpump.approve(election_manager, 10000, {'from': accounts[0]})
    election_manager.voteSell(0, 10000, {'from': accounts[0]})

    # We should not be able to exeucte the sell proposal
    election_manager.executeSellProposal(0, {'from': accounts[0]})
    # Which should mark the sell proposal as inactive
    assert not election_manager.getElectionMetadata(0)["sellProposalActive"]
    election_manager.withdrawSellVote(0, 1000, {'from': accounts[0]})
    # And prevent us from voting on it again
    vpump.approve(election_manager, 10000, {'from': accounts[0]})
    with reverts("SellProposal not active"):
        election_manager.voteSell(0, 10000, {'from': accounts[0]})


def test_execute_buy_fails(broken_election_manager, test_token_1, accounts):
    vpump = VPumpToken.at(broken_election_manager.vPumpToken())
    broken_election_manager.createProposal(0, test_token_1, {'from': accounts[0], 'value': 1 * 10 ** 18})

    vpump.approve(broken_election_manager, 1000, {'from': accounts[0]})
    broken_election_manager.vote(0, test_token_1, 1000, {'from': accounts[0]})

    chain.mine(100)
    broken_election_manager.declareWinner(0, {'from': accounts[0]})

    assert broken_election_manager.getElectionMetadata(0)["numFailures"] == 0
    assert not broken_election_manager.executeBuyProposal(0, {'from': accounts[0]}).return_value

    # The fail count should now be 1
    assert broken_election_manager.getElectionMetadata(0)["numFailures"] == 1
    # But the sell proposal should _not_ be active
    assert not broken_election_manager.getElectionMetadata(0)["sellProposalActive"]

    # But if we fail again
    assert not broken_election_manager.executeBuyProposal(0, {'from': accounts[0]}).return_value
    # Then it should be active
    assert broken_election_manager.getElectionMetadata(0)["sellProposalActive"]


#######################################################################################################
#######################################################################################################
