pragma solidity ^0.8.0;
pragma abicoder v2;

// SPDX-License-Identifier: MIT

import "./ElectionManager.sol";
import "./PumpToken.sol";
import "./interfaces/IBEP20.sol";
import "@pancake-swap-periphery/contracts/interfaces/IPancakeRouter02.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract PumpTreasury is Ownable {
    ElectionManager electionManager;
    PumpToken pumpToken;
    IPancakeRouter02 pancakeRouter;
    address wBNBAddr;
    // Percent of cannon balance to roll into next voting period
    uint256 rolloverPercent = 10;
    event PumpSell(address _caller, uint256 _amount);

    constructor(
        address _electionManagerAddr,
        address _pumpTokenAddr,
        address _wBNBAddr,
        address _pancakeRouterAddr
    ) {
        electionManager = ElectionManager(_electionManagerAddr);
        pumpToken = PumpToken(_pumpTokenAddr);
        pancakeRouter = IPancakeRouter02(_pancakeRouterAddr);
        wBNBAddr = _wBNBAddr;
    }

    function swapPumpForBNB(uint256 _amount) public onlyOwner returns (bool) {
        emit PumpSell(msg.sender, _amount);
        return _performSwap(address(pumpToken), wBNBAddr, _amount);
    }

//    function fireCannon(uint256 amount) public onlyOwner returns (bool) {
//        // TODO need to add timing (or size) requirements to this call
//        address winningToken = electionManager.getWinner().tokenToPumpAddr;
//        // TODO this is the wrong percent and also isn't used
//        uint256 fireAmount = SafeMath.div(
//            // This is the wrong amount
//            SafeMath.mul(address(this).balance, rolloverPercent),
//            100
//        );
//        _performSwap(wBNBAddr, winningToken, amount);
//        // TODO emit an event
//        return true;
//    }

    function _performSwap(
        address tokenIn,
        address tokenOut,
        uint256 amount
    ) internal returns (bool) {
        // TODO possible we need a strong mechanism here
        IBEP20(tokenIn).approve(address(pancakeRouter), amount);
        address[] memory path = new address[](2);
        path[0] = tokenIn;
        path[1] = tokenOut;
        // TODO -- how does it work when this fails? What do we do?
        pancakeRouter.swapExactTokensForTokensSupportingFeeOnTransferTokens(
            amount, // amountIn
            0, // amountOutMin
            path, // path
            address(this), // to
            99999999999 // deadline
        );
        return true;
    }

    // TODO -- implement
    function _addPumpLiquidity(
        uint256 _pumpAmount
    ) internal returns (bool) {
        return true;
    }

    function donate() public payable {}
}
