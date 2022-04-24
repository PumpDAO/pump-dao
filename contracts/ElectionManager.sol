pragma solidity ^0.8.0;

import "./BuyProposal.sol";
import "./PumpToken.sol";
import "./PumpTreasury.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "./vPumpToken.sol";

// TODO -- what type should electionIdx be

contract ElectionManager is Ownable {
    // The number of blocks between when voting ends
    // and a winner is declared. Prevents flash loan attacks.
    uint256 public winnerDelay = (60 * 60) / 3; // 1 hour
    uint256 public blocksPerDay = (60 * 60 * 24) / 3;
    uint256 public electionLength = blocksPerDay * 7;


    struct ProposalMetadata {
        address proposer;
        uint256 createdAt;
        uint256 totalVotes;
        mapping(address => uint256) votes;
    }

    struct ElectionMetadata {
        uint256 votingStartBlock;
        uint256 votingEndBlock;
        uint256 winnerDeclaredBlock;
        mapping(address => bool) validProposals;
        mapping(address => ProposalMetadata) proposals;
        address[] proposedTokens;
        bool winnerDeclared;
        address winner;
    }

    uint256 public currElectionIdx;
    mapping(uint256 => ElectionMetadata) elections;
    VPumpToken private vPumpToken;
    uint256 public proposalCreationTax = 1 * 10**18;
    address treasuryAddr;


    constructor(VPumpToken _vPumpToken, uint256 _startBlock) {
        currElectionIdx = 0;
        ElectionMetadata storage firstElection = elections[0];
        firstElection.votingStartBlock = _startBlock;
        firstElection.votingEndBlock = _startBlock + electionLength - winnerDelay;
        firstElection.winnerDeclaredBlock = _startBlock + electionLength;
        vPumpToken = _vPumpToken;
    }

    /**
        @notice Set the address of the PumpCannon
        @param _cannonAddr The PumpCannon's address
     */
    function setCannonAddress(address _cannonAddr) public onlyOwner {
        treasuryAddr = _cannonAddr;
    }

    function createProposal(address _tokenAddr)
        public
        payable
    {
        ElectionMetadata storage electionMetadata = elections[currElectionIdx];
        require(
            !electionMetadata.validProposals[_tokenAddr],
            "BuyProposal has already been created"
        );
        require(
            msg.value >= proposalCreationTax,
            "BuyProposal creation tax not met. Please include enough BNB in call."
        );

        // TODO -- make sure this actually changes the state
        electionMetadata.validProposals[_tokenAddr] = true;
        electionMetadata.proposals[_tokenAddr].proposer = msg.sender;
        electionMetadata.proposals[_tokenAddr].createdAt = block.number;
        electionMetadata.proposedTokens.push(_tokenAddr);

        // TODO -- add event
    }

    // TODO -- measure the cost of gas on this
    function vote(uint256 _electionIdx, address _tokenAddr, uint256 _amt) public {
        require(
            vPumpToken.allowance(msg.sender, address(this)) >= _amt,
            "ElectionManager not approved to transfer enough PUMP"
        );
        require(
            _electionIdx == currElectionIdx,
            "Can only vote for active election"
        );
        ElectionMetadata storage electionMetadata = elections[currElectionIdx];
        require(
            block.number <= electionMetadata.votingEndBlock,
            "Voting has already ended"
        );
        require(
            electionMetadata.validProposals[_tokenAddr],
            "Can only vote for valid proposals"
        );
        ProposalMetadata storage proposal = electionMetadata.proposals[_tokenAddr];
        proposal.votes[msg.sender] += _amt;
        proposal.totalVotes += _amt;
        vPumpToken.transferFrom(msg.sender, address(this), _amt);
        // TODO - emit event
    }

    function withdrawVote(uint256 _electionIdx, address _tokenAddr, uint256 _amt) public {
        require(
            _electionIdx == currElectionIdx,
            "Can only vote for active election"
        );
        ElectionMetadata storage electionMetadata = elections[currElectionIdx];
        require(
            electionMetadata.validProposals[_tokenAddr],
            "Can only withdraw votes from a valid proposals"
        );
        ProposalMetadata storage proposal = electionMetadata.proposals[_tokenAddr];
        require(
            proposal.votes[msg.sender] >= _amt,
            "Cannot withdraw more votes than cast"
        );
        proposal.votes[msg.sender] -= _amt;
        proposal.totalVotes -= _amt;
        vPumpToken.transfer(msg.sender, _amt);
        // TODO - emit event
    }

    function withdrawAllVotes() public {
        // TODO implement me
    }

    // TODO we may want to make this MEVable
    function declareWinner(uint256 _electionIdx) public {
        require(
            _electionIdx == currElectionIdx,
            "Can only declare winner for current election"
        );
        ElectionMetadata storage electionMetadata = elections[currElectionIdx];
        require(
            block.number >= electionMetadata.winnerDeclaredBlock,
            "Can only declare winner for election after it has finished"
        );

        // TODO -- what happend when the list is empty?
        address winningToken = electionMetadata.proposedTokens[0];
        uint256 winningVotes = electionMetadata.proposals[winningToken].totalVotes;
        // TODO this for loop is a pretty big vulnerability. If the number of active proposals in a single
        // election grows too large this for loop could fully exhaust the maximum per tx gas meaning
        // it would be impossible for a call to getWinner to succeed.
        for (uint256 i = 0; i < electionMetadata.proposedTokens.length; i++) {
            address tokenAddr = electionMetadata.proposedTokens[i];
            ProposalMetadata storage proposal = electionMetadata.proposals[tokenAddr];
            if (proposal.totalVotes > winningVotes) {
                winningToken = tokenAddr;
                winningVotes = proposal.totalVotes;
            }
        }

        electionMetadata.winnerDeclared = true;
        electionMetadata.winner = winningToken;
        currElectionIdx += 1;
        ElectionMetadata storage nextElection = elections[currElectionIdx];
        nextElection.votingStartBlock = electionMetadata.winnerDeclaredBlock + 1;
        nextElection.votingEndBlock = electionMetadata.winnerDeclaredBlock + electionLength - winnerDelay;
        nextElection.winnerDeclaredBlock = electionMetadata.winnerDeclaredBlock + electionLength;

        // TODO -- emit event
    }

}
