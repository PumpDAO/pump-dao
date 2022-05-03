import brownie


def test_only_owner_sets_em_address(pump_treasury, accounts):
    with brownie.reverts("Ownable: caller is not the owner"):
        # Set some arbitrary valid address
        pump_treasury.setElectionManagerAddress(
            accounts[0],
            {'from': accounts[1]}
        )

    # Can call as the owner
    pump_treasury.setElectionManagerAddress(
        accounts[0],
        {'from': accounts[0]}
    )


def test_buy_proposed_token(pump_treasury, test_token_1, accounts):
    with brownie.reverts("Caller is not ElectionManager"):
        # Set some arbitrary valid address
        pump_treasury.buyProposedToken(
            accounts[0],
            {'from': accounts[0]}
        )

    # Give accounts[0] election_manager privs
    pump_treasury.setElectionManagerAddress(
        accounts[0],
        {'from': accounts[0]}
    )

    print(pump_treasury.electionMangerAddr())
    print(accounts[0])

    # Can now call buy proposed token
    pump_treasury.buyProposedToken(
        test_token_1,
        {'from': accounts[0]}
    )
