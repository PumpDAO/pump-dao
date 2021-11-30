pragma solidity ^0.8.0;

import "./Proposal.sol";
import "./PumpToken.sol";
import "./PSCannon.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract ElectionManager is Ownable {
    struct ProposalMetadata {
        address tokenToPumpAddr;
        address proposalAddr;
    }

    uint256 public currentElectionIdx;
    PumpToken private pumpToken;
    mapping(uint256 => ProposalMetadata[]) public proposalsByElection;
    mapping(uint256 => mapping(address => bool))
        public proposalExistsByElection;
    // The cost associated with creating a new proposal. This cost goes directly to the cannon.
    // TODO I think this should actually be a function that scales with the number of proposals in an election.
    // this is going to depend on the maximum number of proposals we can have in an election
    // need to run the math to figure out how much that actually is.
    uint256 public proposalCreationTax = 0.1 * 10**18;
    address cannonAddr;

    // creatorAddress, pollIdx, TokenToPumpAddr, contractAddress
    event ProposalCreated(address, uint256, address, address);
    // ProposalAddress, PumpTokenAddress, BHOLE Amount
    event CurrentProposalState(address, address, uint256);

    constructor(address _pumpTokenAddr) {
        currentElectionIdx = 0;
        pumpToken = PumpToken(_pumpTokenAddr);
    }

    /**
        @notice Set the address of the PumpCannon
        @param _cannonAddr The PumpCannon's address
     */
    function setCannonAddress(address _cannonAddr) public onlyOwner {
        cannonAddr = _cannonAddr;
    }

    function createProposal(address _tokenToPumpAddr)
        public
        payable
        returns (Proposal)
    {
        require(
            !proposalExistsByElection[currentElectionIdx][_tokenToPumpAddr],
            "Proposal has already been created"
        );
        require(
            msg.value >= proposalCreationTax,
            "Proposal creation tax not met. Please include enough ETH in call."
        );

        Proposal proposal = new Proposal(
            currentElectionIdx,
            address(pumpToken)
        );
        ProposalMetadata memory info = ProposalMetadata(
            _tokenToPumpAddr,
            address(proposal)
        );
        proposalsByElection[currentElectionIdx].push(info);
        proposalExistsByElection[currentElectionIdx][_tokenToPumpAddr] = true;
        // Exclude PumpDAO transactions with the proposal address from cannon taxes
        pumpToken.excludeAddress(address(proposal));
        // Donate the proposalCreationTax to the cannon
        PSCannon(cannonAddr).donateEth{value: msg.value}();
        emit ProposalCreated(
            msg.sender,
            currentElectionIdx,
            _tokenToPumpAddr,
            address(proposal)
        );
        return proposal;
    }

    function getWinner() public returns (ProposalMetadata memory) {
        ProposalMetadata[] memory activeProposals = proposalsByElection[
            currentElectionIdx
        ];
        ProposalMetadata memory maxProposal = activeProposals[0];
        uint256 maxBhole = pumpToken.balanceOf(maxProposal.proposalAddr);
        uint256 i;
        // TODO this for loop is a pretty big vulnerability. If the number of active proposals in a single
        // election grows too large this for loop could fully exhaust the maximum per tx gas meaning
        // it would be impossible for a call to getWinner to succeed.
        for (i = 0; i < activeProposals.length; i++) {
            ProposalMetadata memory meta = activeProposals[i];
            uint256 bholeCount = pumpToken.balanceOf(meta.proposalAddr);
            emit CurrentProposalState(
                meta.proposalAddr,
                meta.tokenToPumpAddr,
                bholeCount
            );
            if (bholeCount > maxBhole) {
                maxProposal = meta;
                maxBhole = bholeCount;
            }
        }
        return maxProposal;
    }

    function startNextElection() public {
        require(
            msg.sender == cannonAddr,
            "Only the cannon can start new election"
        );
        currentElectionIdx = currentElectionIdx + 1;
    }

    function getActiveProposals()
        public
        view
        returns (ProposalMetadata[] memory)
    {
        return proposalsByElection[currentElectionIdx];
    }
}
