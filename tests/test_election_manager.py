from brownie import chain, ElectionManager, VPumpToken, reverts


# def test_create_proposal(election_manager, test_token_1, accounts):
#     assert len(election_manager.getActiveProposals()) == 1
#     election_manager.createProposal(0, test_token_1, {'from': accounts[0], 'value': 1 * 10 ** 18})
#     proposals = election_manager.getActiveProposals()
#     assert len(proposals) == 2
#     assert proposals[1] == test_token_1
#
#
# def test_create_proposal_wrong_election(election_manager, test_token_1, accounts):
#     assert len(election_manager.getActiveProposals()) == 1
#     with reverts("Can only create proposals for current election"):
#         election_manager.createProposal(1, test_token_1, {'from': accounts[0], 'value': 1 * 10 ** 18})
#     assert len(election_manager.getActiveProposals()) == 1
#
#
# def test_create_proposal_insufficient_value(election_manager, test_token_1, accounts):
#     assert len(election_manager.getActiveProposals()) == 1
#     with reverts("BuyProposal creation tax not met"):
#         election_manager.createProposal(0, test_token_1, {'from': accounts[0], 'value': 0.9 * 10 ** 18})
#     assert len(election_manager.getActiveProposals()) == 1
#
#
# ############################################################################
# ############################################################################
#
#
# def test_vote_vpump_not_approved(election_manager, test_token_1, accounts):
#     vpump = VPumpToken.at(election_manager.vPumpToken())
#     election_manager.createProposal(0, test_token_1, {'from': accounts[0], 'value': 1 * 10 ** 18})
#
#     prev_vpump = vpump.balanceOf(accounts[0])
#     with reverts("ElectionManager not approved to transfer enough vPUMP"):
#         election_manager.vote(0, test_token_1, 1000, {'from': accounts[0]})
#
#     assert vpump.balanceOf(accounts[0]) == prev_vpump
#     assert election_manager.getProposal(0, test_token_1)["totalVotes"] == 0
#
#
# def test_vote_wrong_election(election_manager, test_token_1, accounts):
#     vpump = VPumpToken.at(election_manager.vPumpToken())
#     election_manager.createProposal(0, test_token_1, {'from': accounts[0], 'value': 1 * 10 ** 18})
#
#     vpump.approve(election_manager, 1000, {'from': accounts[0]})
#     prev_vpump = vpump.balanceOf(accounts[0])
#     with reverts("Can only vote for active election"):
#         election_manager.vote(1, test_token_1, 1000, {'from': accounts[0]})
#
#     assert vpump.balanceOf(accounts[0]) == prev_vpump
#     assert election_manager.getProposal(0, test_token_1)["totalVotes"] == 0
#
#
# def test_vote_voting_ended(election_manager, test_token_1, accounts):
#     vpump = VPumpToken.at(election_manager.vPumpToken())
#     election_manager.createProposal(0, test_token_1, {'from': accounts[0], 'value': 1 * 10 ** 18})
#
#     vpump.approve(election_manager, 1000, {'from': accounts[0]})
#     prev_vpump = vpump.balanceOf(accounts[0])
#     chain.mine(90)
#     with reverts("Voting has already ended"):
#         election_manager.vote(0, test_token_1, 1000, {'from': accounts[0]})
#
#     assert vpump.balanceOf(accounts[0]) == prev_vpump
#     assert election_manager.getProposal(0, test_token_1)["totalVotes"] == 0
#
#
# def test_vote_invalid_proposal(election_manager, test_token_1, accounts):
#     vpump = VPumpToken.at(election_manager.vPumpToken())
#     election_manager.createProposal(0, test_token_1, {'from': accounts[0], 'value': 1 * 10 ** 18})
#
#     vpump.approve(election_manager, 1000, {'from': accounts[0]})
#     prev_vpump = vpump.balanceOf(accounts[0])
#     with reverts("Can only vote for valid proposals"):
#         election_manager.vote(0, accounts[1], 1000, {'from': accounts[0]})
#
#     assert vpump.balanceOf(accounts[0]) == prev_vpump
#     assert election_manager.getProposal(0, test_token_1)["totalVotes"] == 0
#
#
# def test_vote(election_manager, test_token_1, accounts):
#     vpump = VPumpToken.at(election_manager.vPumpToken())
#     election_manager.createProposal(0, test_token_1, {'from': accounts[0], 'value': 1 * 10 ** 18})
#
#     prev_vpump = vpump.balanceOf(accounts[0])
#     vpump.approve(election_manager, 1000, {'from': accounts[0]})
#     election_manager.vote(0, test_token_1, 1000, {'from': accounts[0]})
#
#     assert vpump.balanceOf(accounts[0]) == prev_vpump - 1000
#     assert election_manager.getProposal(0, test_token_1)["totalVotes"] == 1000
#
#     prev_vpump = vpump.balanceOf(accounts[0])
#     vpump.approve(election_manager, 1000, {'from': accounts[0]})
#     election_manager.vote(0, test_token_1, 1000, {'from': accounts[0]})
#
#     assert vpump.balanceOf(accounts[0]) == prev_vpump - 1000
#     assert election_manager.getProposal(0, test_token_1)["totalVotes"] == 2000
#
#     vpump.transfer(accounts[1], 100, {'from': accounts[0]})
#     vpump.approve(election_manager, 100, {'from': accounts[1]})
#     election_manager.vote(0, test_token_1, 100, {'from': accounts[1]})
#
#     assert vpump.balanceOf(accounts[1]) == 0
#     assert election_manager.getProposal(0, test_token_1)["totalVotes"] == 2100
#
#
# ############################################################################
# ############################################################################
#
# def test_withdraw_vote_invalid_proposals(election_manager, test_token_1, accounts):
#     with reverts("Can only withdraw votes from a valid proposals"):
#         election_manager.withdrawVote(1, test_token_1, 1000, {'from': accounts[0]})
#
#
# def test_withdraw_vote_more_than_cast(election_manager, test_token_1, accounts):
#     vpump = VPumpToken.at(election_manager.vPumpToken())
#     election_manager.createProposal(0, test_token_1, {'from': accounts[0], 'value': 1 * 10 ** 18})
#
#     vpump.approve(election_manager, 1000, {'from': accounts[0]})
#     election_manager.vote(0, test_token_1, 1000, {'from': accounts[0]})
#     with reverts("Cannot withdraw more votes than cast"):
#         election_manager.withdrawVote(0, test_token_1, 10000, {'from': accounts[0]})
#
#
# def test_withdraw_vote_only_voter(election_manager, test_token_1, accounts):
#     vpump = VPumpToken.at(election_manager.vPumpToken())
#     election_manager.createProposal(0, test_token_1, {'from': accounts[0], 'value': 1 * 10 ** 18})
#
#     vpump.approve(election_manager, 1000, {'from': accounts[0]})
#     election_manager.vote(0, test_token_1, 1000, {'from': accounts[0]})
#
#     prev_vpump = vpump.balanceOf(accounts[0])
#     prev_votes = election_manager.getProposal(0, test_token_1)["totalVotes"]
#
#     election_manager.withdrawVote(0, test_token_1, 500, {'from': accounts[0]})
#
#     assert vpump.balanceOf(accounts[0]) == prev_vpump + 500
#     assert election_manager.getProposal(0, test_token_1)["totalVotes"] == prev_votes - 500
#
#     vpump.transfer(accounts[1], 100, {'from': accounts[0]})
#     vpump.approve(election_manager, 100, {'from': accounts[1]})
#     election_manager.vote(0, test_token_1, 100, {'from': accounts[1]})
#
#     prev_vpump = vpump.balanceOf(accounts[1])
#     prev_votes = election_manager.getProposal(0, test_token_1)["totalVotes"]
#
#     election_manager.withdrawVote(0, test_token_1, 100, {'from': accounts[1]})
#
#     assert vpump.balanceOf(accounts[1]) == prev_vpump + 100
#     assert election_manager.getProposal(0, test_token_1)["totalVotes"] == prev_votes - 100
#
# ############################################################################
# ############################################################################
#
# def test_declare_winner_wrong_election(election_manager, accounts):
#     with reverts("Can only declare winner for current election"):
#         election_manager.declareWinner(1, {'from': accounts[0]})
#
#
# def test_declare_winner_before_end(election_manager, accounts):
#     with reverts("Can only declare winner for election after it has finished"):
#         election_manager.declareWinner(0, {'from': accounts[0]})
#
#
# def test_declare_winner_no_proposals(election_manager, accounts):
#     election_metadata = election_manager.getElectionMetadata(0)
#     assert not election_metadata["winnerDeclared"]
#     chain.mine(100)
#     election_manager.declareWinner(0, {'from': accounts[0]})
#     election_metadata = election_manager.getElectionMetadata(0)
#     assert election_metadata["winnerDeclared"]
#     assert election_metadata["winner"] == election_manager.defaultProposal()
#
# def test_declare_winner_with_proposals(election_manager, test_token_1, test_token_2, accounts):
#     vpump = VPumpToken.at(election_manager.vPumpToken())
#     election_manager.createProposal(0, test_token_1, {'from': accounts[0], 'value': 1 * 10 ** 18})
#
#     prev_vpump = vpump.balanceOf(accounts[0])
#     vpump.approve(election_manager, 1000, {'from': accounts[0]})
#     election_manager.vote(0, test_token_1, 1000, {'from': accounts[0]})
#
#     assert vpump.balanceOf(accounts[0]) == prev_vpump - 1000
#     assert election_manager.getProposal(0, test_token_1)["totalVotes"] == 1000
#
#     prev_vpump = vpump.balanceOf(accounts[0])
#     vpump.approve(election_manager, 1000, {'from': accounts[0]})
#     election_manager.vote(0, test_token_1, 1000, {'from': accounts[0]})
#
#     assert vpump.balanceOf(accounts[0]) == prev_vpump - 1000
#     assert election_manager.getProposal(0, test_token_1)["totalVotes"] == 2000
#
#     vpump.transfer(accounts[1], 100, {'from': accounts[0]})
#     vpump.approve(election_manager, 100, {'from': accounts[1]})
#     election_manager.createProposal(0, test_token_2, {'from': accounts[1], 'value': 1 * 10 ** 18})
#     election_manager.vote(0, test_token_2, 100, {'from': accounts[1]})
#
#     chain.mine(100)
#     election_manager.declareWinner(0, {'from': accounts[0]})
#     election_metadata = election_manager.getElectionMetadata(0)
#     assert election_metadata["winnerDeclared"]
#     assert election_metadata["winner"] == test_token_1
#

#######################################################################################################
#######################################################################################################

def test_execute_buy_proposal_no_winner(election_manager, accounts):
    with reverts("Can't execute until a winner is declared."):
        election_manager.executeBuyProposal(0, {'from': accounts[0]})


def test_execute_buy(election_manager, test_token_1, accounts):
    vpump = VPumpToken.at(election_manager.vPumpToken())
    election_manager.createProposal(0, test_token_1, {'from': accounts[0], 'value': 1 * 10 ** 18})

    vpump.approve(election_manager, 1000, {'from': accounts[0]})
    election_manager.vote(0, test_token_1, 1000, {'from': accounts[0]})

    chain.mine(100)
    election_manager.declareWinner(0, {'from': accounts[0]})

    election_manager.executeBuyProposal(0, {'from': accounts[0]})
