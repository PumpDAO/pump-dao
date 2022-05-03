pragma solidity ^0.8.0;

import "./PumpToken.sol";
import "./PumpTreasury.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/proxy/utils/Initializable.sol";
import "./vPumpToken.sol";

contract ElectionManager is Ownable, Initializable {
    // View only struct -- used to group data returned by view functions
    struct BuyProposalMetadata {
        address proposer;
        uint256 createdAt;
        uint256 totalVotes;
    }

    // View only struct -- used to group data returned by view functions
    struct SellProposalMetadata {
        bool valid;
        uint256 totalVotes;
        uint256 createdAt;
    }

    struct Election {
        // The first block on which votes for this election can be cast
        uint256 votingStartBlock;
        // The last block on which votes for this election will be accepted, after this calls to vote will revert
        uint256 votingEndBlock;
        // The first block where a winner for the election can be declared. Intentionally different than votingEndBlock
        // in order to prevent flash loan attacks
        uint256 winnerDeclaredBlock;
        // Mapping from proposed taken address to bool indicating if this token has been proposed in this election
        mapping(address => bool) validProposals;
        // Mapping from proposed token address to data about the proposal
        mapping(address => BuyProposal) proposals;
        // Array of proposed token addresses -- useful for iterating over all proposals
        address[] proposedTokens;
        // Bool indicating if the winner has already been declared for this proposal
        bool winnerDeclared;
        // The address of the winning token
        address winner;
        // The amount of the winning token that has been purchased as a result of this election
        uint256 purchasedAmt;
        // The number of buys made for this election. Should never exceed the global maxBuys
        uint8 numBuysMade;
        // The next block on which a buy order can be made for this election
        uint256 nextValidBuyBlock;
        // The number of attempted buys that have failed for this election
        uint8 numFailures;
        // Indicates if sell proposal votes can be cast for this election
        bool sellProposalActive;
        // The total number of sell votes that have been cast for the sell proposal
        uint256 sellProposalTotalVotes;
        // The block number on which this sell proposal was created
        uint256 sellProposalCreatedAt;
        // Mapping from account to the number of sell votes they have cast for this election
        mapping(address => uint256) sellVotes;
    }

    // View only struct -- used to group data returned by view functions
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

    // Data related to a single buy proposal within an election
    struct BuyProposal {
        // Address of the accounts / contract that proposed the token
        address proposer;
        // The block that the proposal was created
        uint256 createdAt;
        // The total number of votes cast for this proposal
        uint256 totalVotes;
        // Mapping from account to the number of votes they have cast for this proposal
        mapping(address => uint256) votes;
    }

    // The number of blocks between when voting ends and a winner is declared. Prevents flash loan attacks.
    uint256 public winnerDelay;
    // Time between the start of an election and when the winner is declared
    uint256 public electionLength;
    // Address of the token for which a proposal will always be created by default
    address public defaultProposal;
    // The number of buys that will be made for each winning token (assuming the maxBuyFailures is not hit)
    uint256 public maxNumBuys;
    // The number of blocks to wait between each buy is made
    uint256 public buyCooldownBlocks;
    // The number of allowed buy failures after which a sell proposal becomes valid
    uint8 public maxBuyFailures = 2;
    // The number of blocks to wait before the sell proposal quorum requirements begin to decay
    uint256 public sellLockupBlocks;
    // The half life of the sell proposal quorum requirements
    uint256 public sellHalfLifeBlocks;
    // The index of the current election
    uint256 public currElectionIdx;
    // Mapping from election Idx to data about the election
    mapping(uint256 => Election) public elections;
    VPumpToken public vPumpToken;
    // Fee required in order to create a proposal
    uint256 public proposalCreationTax = 0.25 * 10**18;
    PumpTreasury public treasury;
    // The maximum number of allowed proposals per election.
    uint8 maxProposalsPerElection = 100;


    event ProposalCreated(uint16 electionIdx, address tokenAddr);
    event BuyVoteDeposited(uint16 electionIdx, address tokenAddr, uint256 amt);
    event SellVoteDeposited(uint16 electionIdx, address tokenAddr, uint256 amt);
    event BuyVoteWithdrawn(uint16 electionIdx, address tokenAddr, uint256 amt);
    event SellVoteWithdrawn(uint16 electionIdx, address tokenAddr, uint256 amt);
    event WinnerDeclared(uint16 electionIdx, address winner, uint256 numVotes);
    event SellProposalExecuted(uint16 electionIdx);

    // Initialize takes the place of constructor in order to use a proxy pattern to upgrade later
    function initialize(
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
    ) public initializer {
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
            "Must use currentElectionIdx"
        );
        Election storage electionMetadata = elections[currElectionIdx];
        require(
            !electionMetadata.validProposals[_tokenAddr],
            "Proposal already created"
        );
        require(
            msg.value >= proposalCreationTax,
            "BuyProposal creation tax not met"
        );
        require(
            electionMetadata.proposedTokens.length <= maxProposalsPerElection,
            "Proposal limit hit"
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
            "vPUMP transfer not approved"
        );
        require(
            _electionIdx == currElectionIdx,
            "Must use currElectionIdx"
        );
        Election storage electionMetadata = elections[currElectionIdx];
        require(
            block.number <= electionMetadata.votingEndBlock,
            "Voting has already ended"
        );
        require(
            electionMetadata.validProposals[_tokenAddr],
            "Must be valid proposal"
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
            "Must be valid proposal"
        );
        BuyProposal storage proposal = electionMetadata.proposals[_tokenAddr];
        require(
            proposal.votes[msg.sender] >= _amt,
            "More votes than cast"
        );
        proposal.votes[msg.sender] -= _amt;
        proposal.totalVotes -= _amt;
        vPumpToken.transfer(msg.sender, _amt);

        emit BuyVoteWithdrawn(_electionIdx, _tokenAddr, _amt);
    }

    function declareWinner(uint16 _electionIdx) public {
        require(
            _electionIdx == currElectionIdx,
            "Must be currElectionIdx"
        );
        Election storage electionMetadata = elections[currElectionIdx];
        require(
            block.number >= electionMetadata.winnerDeclaredBlock,
            "Voting not finished"
        );

        // If no proposals were made, the default proposal wins
        address winningToken = electionMetadata.proposedTokens[0];
        uint256 winningVotes = electionMetadata.proposals[winningToken].totalVotes;
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

    function voteSell(uint16 _electionIdx, uint256 _amt) public {
        require(
            vPumpToken.allowance(msg.sender, address(this)) >= _amt,
            "vPUMP transfer not approved"
        );
        Election storage electionData = elections[_electionIdx];
        require(electionData.sellProposalActive, "SellProposal not active");

        electionData.sellVotes[msg.sender] += _amt;
        electionData.sellProposalTotalVotes += _amt;
        vPumpToken.transferFrom(msg.sender, address(this), _amt);

        emit SellVoteDeposited(_electionIdx, electionData.winner, _amt);
    }

    function withdrawSellVote(uint16 _electionIdx, uint256 _amt) public {
        Election storage electionData = elections[_electionIdx];
        require(
            electionData.sellVotes[msg.sender] >= _amt,
            "More votes than cast"
        );

        electionData.sellVotes[msg.sender] -= _amt;
        electionData.sellProposalTotalVotes -= _amt;
        vPumpToken.transfer(msg.sender, _amt);

        emit SellVoteWithdrawn(_electionIdx, electionData.winner, _amt);
    }

    function executeBuyProposal(uint16 _electionIdx) public returns (bool) {
        Election storage electionData = elections[_electionIdx];
        require(electionData.winnerDeclared, "Winner not declared");
        require(electionData.numBuysMade < maxNumBuys, "Can't exceed maxNumBuys");
        require(electionData.nextValidBuyBlock <= block.number, "Must wait before executing");
        require(electionData.numFailures < maxBuyFailures, "Max fails exceeded");
        require(!electionData.sellProposalActive, "Sell Proposal already active");

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
        require(electionData.sellProposalActive, "SellProposal not active");
        uint256 requiredVotes = _getRequiredSellVPump(electionData.sellProposalCreatedAt);
        require(electionData.sellProposalTotalVotes >= requiredVotes, "Not enough votes to execute");

        treasury.sellProposedToken(electionData.winner, electionData.purchasedAmt);
        // After we've sold, mark the sell proposal as inactive so we don't sell again
        electionData.sellProposalActive = false;
        emit SellProposalExecuted(_electionIdx);
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
        BuyProposal storage proposal = elections[_electionIdx].proposals[_tokenAddr];
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
