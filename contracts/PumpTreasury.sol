pragma solidity ^0.8.0;
pragma abicoder v2;

// SPDX-License-Identifier: MIT

import "./ElectionManager.sol";
import "./PumpToken.sol";
import "./lib/SafeBEP20.sol";
import "@pancake-swap-lib/contracts/token/BEP20/IBEP20.sol";
import "@pancake-swap-periphery/contracts/interfaces/IPancakeRouter02.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "./ElectionManager.sol";

contract PumpTreasury is Ownable {
    using SafeMath for uint256;
    using SafeBEP20 for IBEP20;

    PumpToken pumpToken;
    IPancakeRouter02 pancakeRouter;
    IBEP20 wBNB;
    address electionManger;

    event PumpSell(address _caller, uint256 _amount);
    event BuyProposedToken(address _tokenAddress, uint256 wBNBAmt);

    constructor(
        PumpToken _pumpToken,
        address _wBNBAddr,
        address _pancakeRouterAddr,
        address _electionManagerAddr
    ) {
        pumpToken = _pumpToken;
        pancakeRouter = IPancakeRouter02(_pancakeRouterAddr);
        wBNB = IBEP20(_wBNBAddr);
        electionManger = _electionManagerAddr;
    }

    modifier onlyElectionManager() {
        require(electionManger == msg.sender, "Caller is not ElectionManager");
        _;
    }

    function swapPumpForBNB(uint256 _amount) public {
        emit PumpSell(msg.sender, _amount);
        _performSwap(address(pumpToken), address(wBNB), _amount);
    }

    function buyProposedToken(address _tokenAddr) public onlyElectionManager {
        // Each buy uses 1% of the available treasury
        uint256 buySize = wBNB.balanceOf(address(this)) / 100;
        _performSwap(address(wBNB), _tokenAddr, buySize);
        emit BuyProposedToken(_tokenAddr, buySize);
    }

    function _performSwap(
        address tokenIn,
        address tokenOut,
        uint256 amount
    ) internal returns (bool) {
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
