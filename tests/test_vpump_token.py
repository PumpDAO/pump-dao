from brownie import VPumpToken, reverts


def test_only_election_manager_can_transfer(election_manager, accounts):
    vpump = VPumpToken.at(election_manager.vPumpToken())

    initial_vpump = vpump.balanceOf(accounts[0])
    assert initial_vpump > 0
    with reverts('Can only transfer to electionManager'):
        vpump.transfer(accounts[1], 1, {'from': accounts[0]})

    assert vpump.balanceOf(accounts[0]) == initial_vpump
    assert vpump.balanceOf(accounts[1]) == 0

    initial_em_vpump = vpump.balanceOf(election_manager)
    vpump.transfer(election_manager, 1, {'from': accounts[0]})

    assert vpump.balanceOf(accounts[0]) == initial_vpump - 1
    assert vpump.balanceOf(election_manager) == initial_em_vpump + 1
