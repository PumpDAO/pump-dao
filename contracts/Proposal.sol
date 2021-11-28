pragma solidity ^0.8.0;

import "./PumpToken.sol";
import "./SafeMath.sol";

contract Proposal {
    using SafeMath for uint256;

    uint256 public pollIdx;
    PumpToken public pumpToken;

    // Maps an address to the amount of pump able to be withdrawn
    mapping(address => uint256) public votes;

    constructor(uint256 _pollIdx, address _pumpTokenAddr) {
        pollIdx = _pollIdx;
        pumpToken = PumpToken(_pumpTokenAddr);
    }

    function vote(uint256 _amount) public {
        require(
            pumpToken.allowance(msg.sender, address(this)) >= _amount,
            "Need to approve proposal to spend pump before you can vote."
        );
        votes[msg.sender] = votes[msg.sender].add(_amount);
        pumpToken.transferFrom(msg.sender, address(this), _amount);
    }

    function withdrawVote(uint256 _amount) public {
        // TODO need to figure out if this is a reentrancy vulnerability
        require(
            _amount <= votes[msg.sender],
            "Cannot withdraw more votes than cast"
        );
        votes[msg.sender] = votes[msg.sender].sub(_amount);
        pumpToken.transfer(msg.sender, _amount);
    }
}
