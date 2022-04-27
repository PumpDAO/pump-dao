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
    uint8 maxBuyFailures = 2;

    uint256 public sellLockupBlocks;
    uint256 public sellHalfLifeBlocks;

    struct BuyProposal {
        address proposer;
        uint256 createdAt;
        uint256 totalVotes;
        mapping(address => uint256) votes;
    }

    // View only
    struct BuyProposalMetadata {
        address proposer;
        uint256 createdAt;
        uint256 totalVotes;
    }

    // View Only
    struct SellProposalMetadata {
        bool valid;
        uint256 totalVotes;
        uint256 createdAt;
    }

    // TODO -- comment each field across all structs
    struct Election {
        uint256 votingStartBlock;
        uint256 votingEndBlock;
        uint256 winnerDeclaredBlock;
        mapping(address => bool) validProposals;
        mapping(address => BuyProposal) proposals;
        address[] proposedTokens;
        bool winnerDeclared;
        address winner;
        uint256 purchasedAmt;
        // Buy related Data
        uint8 numBuysMade;
        uint256 nextValidBuyBlock;
        uint8 numFailures;

        // Sell related data
        bool sellProposalActive;
        uint256 sellProposalTotalVotes;
        uint256 sellProposalCreatedAt;
        mapping(address => uint256) sellVotes;
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
        uint8 numFailures;
        // Sell related data
        bool sellProposalActive;
        uint256 sellProposalTotalVotes;
        uint256 sellProposalCreatedAt;
    }

    uint256 public currElectionIdx;
    mapping(uint256 => Election) public elections;
    VPumpToken public vPumpToken;
    uint256 public proposalCreationTax = 1 * 10**18;
    PumpTreasury public treasury;


    event ProposalCreated(uint16 electionIdx, address tokenAddr);
    event BuyVoteDeposited(uint16 electionIdx, address tokenAddr, uint256 amt);
    event SellVoteDeposited(uint16 electionIdx, address tokenAddr, uint256 amt);
    event BuyVoteWithdrawn(uint16 electionIdx, address tokenAddr, uint256 amt);
    event SellVoteWithdrawn(uint16 electionIdx, address tokenAddr, uint256 amt);
    event WinnerDeclared(uint16 electionIdx, address winner, uint256 numVotes);
    event SellProposalExecuted(uint16 electionIdx);

    constructor(
        VPumpToken _vPumpToken,
        uint256 _startBlock,
        uint256 _winnerDelay,
        uint256 _electionLength,
        address _defaultProposal,
        PumpTreasury _treasury,
        uint256 _maxNumBuys,
        uint256 _buyCooldownBlocks,
        uint256 _sellLockupBlocks,
        uint256 _sellHalfLifeBlocks
    ) {

        winnerDelay = _winnerDelay;
        electionLength = _electionLength;
        defaultProposal = _defaultProposal;
        vPumpToken = _vPumpToken;
        currElectionIdx = 0;
        treasury = _treasury;
        maxNumBuys = _maxNumBuys;
        buyCooldownBlocks = _buyCooldownBlocks;
        sellLockupBlocks = _sellLockupBlocks;
        sellHalfLifeBlocks = _sellHalfLifeBlocks;

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
        BuyProposal storage proposal = electionMetadata.proposals[_tokenAddr];
        proposal.votes[msg.sender] += _amt;
        proposal.totalVotes += _amt;
        vPumpToken.transferFrom(msg.sender, address(this), _amt);

        emit BuyVoteDeposited(_electionIdx, _tokenAddr, _amt);
    }

    function withdrawVote(uint16 _electionIdx, address _tokenAddr, uint256 _amt) public {
        Election storage electionMetadata = elections[_electionIdx];
        require(
            electionMetadata.validProposals[_tokenAddr],
            "Can only withdraw votes from a valid proposals"
        );
        BuyProposal storage proposal = electionMetadata.proposals[_tokenAddr];
        require(
            proposal.votes[msg.sender] >= _amt,
            "Cannot withdraw more votes than cast"
        );
        proposal.votes[msg.sender] -= _amt;
        proposal.totalVotes -= _amt;
        vPumpToken.transfer(msg.sender, _amt);

        emit BuyVoteWithdrawn(_electionIdx, _tokenAddr, _amt);
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
            BuyProposal storage proposal = electionMetadata.proposals[tokenAddr];
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
    ) public view returns (BuyProposalMetadata memory) {
        require(
            elections[currElectionIdx].validProposals[_tokenAddr],
            "No valid proposal for args"
        );
        BuyProposal storage proposal = elections[currElectionIdx].proposals[_tokenAddr];
        return BuyProposalMetadata({
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
            nextValidBuyBlock: election.nextValidBuyBlock,
            numFailures: election.numFailures,
            sellProposalActive: election.sellProposalActive,
            sellProposalTotalVotes: election.sellProposalTotalVotes,
            sellProposalCreatedAt: election.sellProposalCreatedAt
        });
    }

    function voteSell(uint16 _electionIdx, uint256 _amt) public {
        require(
            vPumpToken.allowance(msg.sender, address(this)) >= _amt,
            "ElectionManager not approved to transfer enough vPUMP"
        );
        Election storage electionData = elections[_electionIdx];
        require(electionData.sellProposalActive, "Can only vote on active sell proposals");

        electionData.sellVotes[msg.sender] += _amt;
        electionData.sellProposalTotalVotes += _amt;
        vPumpToken.transferFrom(msg.sender, address(this), _amt);

        emit SellVoteDeposited(_electionIdx, electionData.winner, _amt);
    }

    function withdrawSellVote(uint16 _electionIdx, uint256 _amt) public {
        Election storage electionData = elections[_electionIdx];
        require(
            electionData.sellVotes[msg.sender] >= _amt,
            "Cannot withdraw more votes than cast"
        );

        electionData.sellVotes[msg.sender] -= _amt;
        electionData.sellProposalTotalVotes -= _amt;
        vPumpToken.transfer(msg.sender, _amt);

        emit SellVoteWithdrawn(_electionIdx, electionData.winner, _amt);
    }

    function executeBuyProposal(uint16 _electionIdx) public returns (bool) {
        Election storage electionData = elections[_electionIdx];
        require(electionData.winnerDeclared, "Can't execute until a winner is declared.");
        require(electionData.numBuysMade < maxNumBuys, "Can't exceed maxNumBuys");
        require(electionData.nextValidBuyBlock <= block.number, "Must wait before executing");
        require(electionData.numFailures < maxBuyFailures, "Proposal has already failed too many times.");
        require(!electionData.sellProposalActive, "Sell Proposal already active.");

        try treasury.buyProposedToken(electionData.winner) returns (uint256 _purchasedAmt) {
            electionData.purchasedAmt += _purchasedAmt;
            electionData.numBuysMade += 1;
            electionData.nextValidBuyBlock = block.number + buyCooldownBlocks;
            // If we've now made the max number of buys, mark the associatedSellProposal
            // as active and mark the amount of accumulated hilding token
            if (electionData.numBuysMade >= maxNumBuys) {
                electionData.sellProposalActive = true;
                electionData.sellProposalCreatedAt = block.number;
            }
            return true;
        } catch Error(string memory) {
            electionData.numFailures += 1;
            // If we've exceeded the number of allowed failures
            if (electionData.numFailures >= maxBuyFailures) {
                electionData.sellProposalActive = true;
                electionData.sellProposalCreatedAt = block.number;
            }
            return false;
        }

        // This return is never hit and is a hack to appease IDE sol static analyzer
        return true;
    }

    function executeSellProposal(uint16 _electionIdx) public {
        Election storage electionData = elections[_electionIdx];
        require(electionData.sellProposalActive, "Can only execute an active sellProposal");
        uint256 requiredVotes = _getRequiredSellVPump(electionData.sellProposalCreatedAt);
        require(electionData.sellProposalTotalVotes >= requiredVotes, "Not enough votes to execute");

        treasury.sellProposedToken(electionData.winner, electionData.purchasedAmt);
        // After we've sold, mark the sell proposal as inactive so we don't sell again
        electionData.sellProposalActive = false;
        emit SellProposalExecuted(_electionIdx);
    }

    function _getRequiredSellVPump(uint256 _startBlock) public view returns (uint256) {
        uint256 outstandingVPump = vPumpToken.totalSupply();
        uint256 elapsedBlocks = block.number - _startBlock;
        if (elapsedBlocks <= sellLockupBlocks) {
            return outstandingVPump;
        }
        uint256 decayPeriodBlocks = elapsedBlocks - sellLockupBlocks;
        return _appxDecay(outstandingVPump, decayPeriodBlocks, sellHalfLifeBlocks);
    }

    function _appxDecay(
        uint256 _startValue,
        uint256 _elapsedTime,
        uint256 _halfLife
    ) internal view returns (uint256) {
        uint256 ret = _startValue >> (_elapsedTime / _halfLife);
        ret -= ret * (_elapsedTime % _halfLife) / _halfLife / 2;
        return ret;
    }
}
