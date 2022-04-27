pragma solidity ^0.8.0;

import "./SafeMath.sol";
import "./interfaces/IBEP20.sol";
import "./vPumpToken.sol";

// TODO -- add events where it makes sense
contract SellProposal {
    using SafeMath for uint256;

    uint256 public purchaseBlock;
    uint256 public holdingSize;
    IBEP20 public pumpHolding;
    VPumpToken public vPumpToken;

    // 3 seconds per block
    uint256 public blocksPerDay = (60 * 60 * 24) / 3;
    // Impossible to sell in the first 7 days
    uint256 public lockupDays = 7;
    uint256 public halfLifeBlocks = blocksPerDay * 45;

    mapping(address => uint256) public votes;

    constructor(
        uint256 _purchaseBlock,
        uint256 _holdingSize,
        IBEP20 _pumpHolding,
        VPumpToken _vPumpToken
    ) {
        purchaseBlock = _purchaseBlock;
        holdingSize = _holdingSize;
        pumpHolding = _pumpHolding;
        vPumpToken = _vPumpToken;
    }

    function vote(uint256 _amount) public {
        require(
            vPumpToken.allowance(msg.sender, address(this)) >= _amount,
            "Need to approve proposal to spend pump before you can vote."
        );
        votes[msg.sender] = votes[msg.sender].add(_amount);
        // TODO -- wtf happens if this fails?
        vPumpToken.transferFrom(msg.sender, address(this), _amount);
    }

    function withdrawVote(uint256 _amount) public {
        require(
            _amount <= votes[msg.sender],
            "More votes than cast"
        );
        votes[msg.sender] = votes[msg.sender].sub(_amount);
        // TODO -- wtf happens if this fails?
        vPumpToken.transfer(msg.sender, _amount);
    }

    // TODO -- write a unit test for this specifically
    function getRequiredVPump() public view returns (uint256) {
        uint256 outstandingVPump = vPumpToken.totalSupply();
        uint256 elapsedBlocks = block.number.sub(purchaseBlock);
        if (elapsedBlocks <= blocksPerDay.mul(lockupDays)) {
            return outstandingVPump;
        }
        uint256 decayPeriodBlocks = elapsedBlocks.sub(blocksPerDay.mul(lockupDays));
        return appxDecay(outstandingVPump, decayPeriodBlocks, halfLifeBlocks);
    }


    // TODO -- write a unit test for this specifically
    function appxDecay(
        uint256 _startValue,
        uint256 _elapsedTime,
        uint256 _halfLife
    ) internal view returns (uint256) {
        uint256 ret = _startValue >> (_elapsedTime.div(_halfLife));
        ret -= ret * (_elapsedTime % _halfLife) / _halfLife / 2;
        return ret;
    }
}
