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

    PumpToken public pumpToken;
    IPancakeRouter02 public pancakeRouter;
    IBEP20 public wBNB;
    address public electionMangerAddr;

    event PumpSell(address _caller, uint256 _amount);
    event BuyProposedToken(address _tokenAddress, uint256 wBNBAmt);

    modifier onlyElectionManager() {
        require(electionMangerAddr == msg.sender, "Caller is not ElectionManager");
        _;
    }

    constructor(
        PumpToken _pumpToken,
        address _wBNBAddr,
        address _pancakeRouterAddr
    ) {
        pumpToken = _pumpToken;
        pancakeRouter = IPancakeRouter02(_pancakeRouterAddr);
        wBNB = IBEP20(_wBNBAddr);
    }

    function setElectionManagerAddress(address _addr) public onlyOwner {
        electionMangerAddr = _addr;
    }

    function swapPumpForBNB(uint256 _amount) public {
        emit PumpSell(msg.sender, _amount);
        _performSwap(address(pumpToken), address(wBNB), _amount);
    }

    function buyProposedToken(address _tokenAddr) public onlyElectionManager returns (uint256) {
        // Each buy uses 1% of the available treasury
        uint256 buySize = wBNB.balanceOf(address(this)) / 100;

        uint256 startingAmt = IBEP20(_tokenAddr).balanceOf(address(this));
        _performSwap(address(wBNB), _tokenAddr, buySize);
        uint256 endingAmt = IBEP20(_tokenAddr).balanceOf(address(this));
        emit BuyProposedToken(_tokenAddr, buySize);

        return endingAmt - startingAmt;
    }

    function sellProposedToken(address _tokenAddr, uint256 _amt) public onlyElectionManager {
        // Each buy uses 1% of the available treasury
        _performSwap(_tokenAddr, address(wBNB), _amt);

        // TODO -- buy back pump, stake and burn
        // TODO -- emit event

    }


    function _performSwap(
        address tokenIn,
        address tokenOut,
        uint256 amount
    ) internal {
        uint256 blockNumber = block.number;
        IBEP20(tokenIn).approve(address(pancakeRouter), amount);
        address[] memory path = new address[](2);
        path[0] = tokenIn;
        path[1] = tokenOut;
        pancakeRouter.swapExactTokensForTokensSupportingFeeOnTransferTokens(
            amount, // amountIn
            0, // amountOutMin
            path, // path
            address(this), // to
            blockNumber // deadline
        );
    }

//    // TODO -- implement
//    function _addPumpLiquidity(
//        uint256 _pumpAmount
//    ) internal returns (bool) {
//        return true;
//    }
}
