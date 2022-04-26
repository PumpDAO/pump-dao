pragma solidity ^0.8.0;

import "./PumpToken.sol";
import "./PumpTreasury.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "./vPumpToken.sol";

// TODO -- run solhint across project
contract ElectionManager is Ownable {
    // The number of blocks between when voting ends
    // and a winner is declared. Prevents flash loan attacks.
    uint256 public winnerDelay;
    uint256 public electionLength;
    address public defaultProposal;
    uint256 maxNumBuys;
    uint256 buyCooldownBlocks;


    struct Proposal {
        address proposer;
        uint256 createdAt;
        uint256 totalVotes;
        mapping(address => uint256) votes;
    }

    // View only
    struct ProposalMetadata {
        address proposer;
        uint256 createdAt;
        uint256 totalVotes;
    }

    // TODO -- comment each fiels
    struct Election {
        uint256 votingStartBlock;
        uint256 votingEndBlock;
        uint256 winnerDeclaredBlock;
        mapping(address => bool) validProposals;
        mapping(address => Proposal) proposals;
        address[] proposedTokens;
        bool winnerDeclared;
        address winner;
        // Buy related Data
        uint8 numBuysMade;
        uint256 nextValidBuyBlock;
    }

    // View only
    struct ElectionMetadata {
        uint256 votingStartBlock;
        uint256 votingEndBlock;
        uint256 winnerDeclaredBlock;
        bool winnerDeclared;
        address winner;
        // Buy related Data
        uint8 numBuysMade;
        uint256 nextValidBuyBlock;
    }

    uint256 public currElectionIdx;
    mapping(uint256 => Election) public elections;
    VPumpToken public vPumpToken;
    uint256 public proposalCreationTax = 1 * 10**18;
    PumpTreasury public treasury;


    event ProposalCreated(uint16 electionIdx, address tokenAddr);
    event VoteDeposited(uint16 electionIdx, address tokenAddr, uint256 amt);
    event VoteWithdrawn(uint16 electionIdx, address tokenAddr, uint256 amt);
    event WinnerDeclared(uint16 electionIdx, address winner, uint256 numVotes);
    event BuyProposalExecuted(uint256 electionIdx, uint256 wBNBAmt);

    constructor(
        VPumpToken _vPumpToken,
        uint256 _startBlock,
        uint256 _winnerDelay,
        uint256 _electionLength,
        address _defaultProposal,
        PumpTreasury _treasury,
        uint256 _maxNumBuys,
        uint256 _buyCooldownBlocks
    ) {

        winnerDelay = _winnerDelay;
        electionLength = _electionLength;
        defaultProposal = _defaultProposal;
        vPumpToken = _vPumpToken;
        currElectionIdx = 0;
        treasury = _treasury;
        maxNumBuys = _maxNumBuys;
        buyCooldownBlocks = _buyCooldownBlocks;

        Election storage firstElection = elections[0];
        firstElection.votingStartBlock = _startBlock;
        firstElection.votingEndBlock = _startBlock + electionLength - winnerDelay;
        firstElection.winnerDeclaredBlock = _startBlock + electionLength;

        firstElection.validProposals[defaultProposal] = true;
        firstElection.proposals[defaultProposal].proposer = address(this);
        firstElection.proposals[defaultProposal].createdAt = block.number;
        firstElection.proposedTokens.push(defaultProposal);

    }

    function createProposal(uint16 _electionIdx, address _tokenAddr)
        public
        payable
    {
        require(
            _electionIdx == currElectionIdx,
            "Can only create proposals for current election"
        );
        Election storage electionMetadata = elections[currElectionIdx];
        require(
            !electionMetadata.validProposals[_tokenAddr],
            "BuyProposal has already been created"
        );
        require(
            msg.value >= proposalCreationTax,
            "BuyProposal creation tax not met"
        );

        electionMetadata.validProposals[_tokenAddr] = true;
        electionMetadata.proposals[_tokenAddr].proposer = msg.sender;
        electionMetadata.proposals[_tokenAddr].createdAt = block.number;
        electionMetadata.proposedTokens.push(_tokenAddr);

        emit ProposalCreated(_electionIdx, _tokenAddr);
    }

    // TODO -- measure the cost of gas on this
    function vote(uint16 _electionIdx, address _tokenAddr, uint256 _amt) public {
        require(
            vPumpToken.allowance(msg.sender, address(this)) >= _amt,
            "ElectionManager not approved to transfer enough vPUMP"
        );
        require(
            _electionIdx == currElectionIdx,
            "Can only vote for active election"
        );
        Election storage electionMetadata = elections[currElectionIdx];
        require(
            block.number <= electionMetadata.votingEndBlock,
            "Voting has already ended"
        );
        require(
            electionMetadata.validProposals[_tokenAddr],
            "Can only vote for valid proposals"
        );
        Proposal storage proposal = electionMetadata.proposals[_tokenAddr];
        proposal.votes[msg.sender] += _amt;
        proposal.totalVotes += _amt;
        vPumpToken.transferFrom(msg.sender, address(this), _amt);

        emit VoteDeposited(_electionIdx, _tokenAddr, _amt);
    }

    function withdrawVote(uint16 _electionIdx, address _tokenAddr, uint256 _amt) public {
        Election storage electionMetadata = elections[currElectionIdx];
        require(
            electionMetadata.validProposals[_tokenAddr],
            "Can only withdraw votes from a valid proposals"
        );
        Proposal storage proposal = electionMetadata.proposals[_tokenAddr];
        require(
            proposal.votes[msg.sender] >= _amt,
            "Cannot withdraw more votes than cast"
        );
        proposal.votes[msg.sender] -= _amt;
        proposal.totalVotes -= _amt;
        vPumpToken.transfer(msg.sender, _amt);

        emit VoteWithdrawn(_electionIdx, _tokenAddr, _amt);
    }

    function withdrawAllVotes() public {
        // TODO implement me
    }

    // TODO we may want to make this MEVable
    function declareWinner(uint16 _electionIdx) public {
        require(
            _electionIdx == currElectionIdx,
            "Can only declare winner for current election"
        );
        Election storage electionMetadata = elections[currElectionIdx];
        require(
            block.number >= electionMetadata.winnerDeclaredBlock,
            "Can only declare winner for election after it has finished"
        );

        // If no proposals were made, the default proposal wins
        address winningToken = electionMetadata.proposedTokens[0];
        uint256 winningVotes = electionMetadata.proposals[winningToken].totalVotes;
        // TODO this for loop is a pretty big vulnerability. If the number of active proposals in a single
        // election grows too large this for loop could fully exhaust the maximum per tx gas meaning
        // it would be impossible for a call to getWinner to succeed.
        for (uint256 i = 0; i < electionMetadata.proposedTokens.length; i++) {
            address tokenAddr = electionMetadata.proposedTokens[i];
            Proposal storage proposal = electionMetadata.proposals[tokenAddr];
            if (proposal.totalVotes > winningVotes) {
                winningToken = tokenAddr;
                winningVotes = proposal.totalVotes;
            }
        }

        electionMetadata.winnerDeclared = true;
        electionMetadata.winner = winningToken;
        currElectionIdx += 1;
        Election storage nextElection = elections[currElectionIdx];
        nextElection.votingStartBlock = electionMetadata.winnerDeclaredBlock + 1;
        nextElection.votingEndBlock = electionMetadata.winnerDeclaredBlock + electionLength - winnerDelay;
        nextElection.winnerDeclaredBlock = electionMetadata.winnerDeclaredBlock + electionLength;
        // Setup the default proposal
        nextElection.validProposals[defaultProposal] = true;
        nextElection.proposals[defaultProposal].proposer = address(this);
        nextElection.proposals[defaultProposal].createdAt = block.number;
        nextElection.proposedTokens.push(defaultProposal);

        emit WinnerDeclared(_electionIdx, winningToken, winningVotes);
    }

    function getActiveProposals() public view returns (address[] memory) {
        return elections[currElectionIdx].proposedTokens;
    }

    function getProposal(
        uint16 _electionIdx,
        address _tokenAddr
    ) public view returns (ProposalMetadata memory) {
        require(
            elections[currElectionIdx].validProposals[_tokenAddr],
            "No valid proposal for args"
        );
        Proposal storage proposal = elections[currElectionIdx].proposals[_tokenAddr];
        return ProposalMetadata({
            proposer: proposal.proposer,
            createdAt: proposal.createdAt,
            totalVotes: proposal.totalVotes
        });
    }

    function getElectionMetadata(
        uint16 _electionIdx
    ) public view returns (ElectionMetadata memory) {
        require(_electionIdx <= currElectionIdx, "Can't query future election");
        Election storage election = elections[_electionIdx];
        return ElectionMetadata({
            votingStartBlock: election.votingStartBlock,
            votingEndBlock: election.votingEndBlock,
            winnerDeclaredBlock: election.winnerDeclaredBlock,
            winnerDeclared: election.winnerDeclared,
            winner: election.winner,
            numBuysMade: election.numBuysMade,
            nextValidBuyBlock: election.nextValidBuyBlock
        });
    }


    // TODO -- what happens when this fails?
    function executeBuyProposal(uint16 _electionIdx) public {
        Election storage electionData = elections[_electionIdx];
        require(electionData.winnerDeclared, "Can't execute until a winner is declared.");
        require(electionData.numBuysMade < maxNumBuys, "Can't exceed maxNumBuys");
        require(electionData.nextValidBuyBlock <= block.number, "Must wait before executing");

        electionData.numBuysMade += 1;
        electionData.nextValidBuyBlock = block.number + buyCooldownBlocks;

        treasury.buyProposedToken(electionData.winner);
    }

}
