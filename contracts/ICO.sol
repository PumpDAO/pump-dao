pragma solidity ^0.8.0;

import "./PumpToken.sol";
import "./SafeMath.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract ICO is Ownable {
    PumpToken public pumpToken;
    uint256 public pumpPerEth = 420 * 10**3;

    // In order to promote a distributed launch, the ICO contract restricts the total amount
    // of PUMP the wallet can have and still participate.
    uint256 public maxICOPump = 50 * 10**3 * 10**18;

    event PumpPurchased(uint256 eth, uint256 pump);
    event Log(uint256);

    function buyPump() public payable {
        require(msg.value > 0.0, "Buying PUMP requires ETH");

        uint256 purchaseAmount = SafeMath.mul(msg.value, pumpPerEth);
        emit Log(purchaseAmount);
        require(
            pumpToken.balanceOf(address(this)) >= purchaseAmount,
            "Cannot purchase more than the remaining available."
        );
        require(
            pumpToken.balanceOf(msg.sender) + purchaseAmount < maxICOPump,
            "Cannot exceed 50k PUMP through ICO."
        );

        pumpToken.transfer(msg.sender, purchaseAmount);
    }

    function setPumpAddress(address _pumpAddr) public onlyOwner {
        pumpToken = PumpToken(_pumpAddr);
    }

    function remainingPump() public view returns (uint256) {
        return pumpToken.balanceOf(address(this));
    }
}
