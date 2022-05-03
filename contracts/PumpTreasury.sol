pragma solidity ^0.8.0;
pragma abicoder v2;

// SPDX-License-Identifier: MIT

import "./ElectionManager.sol";
import "./PumpToken.sol";
import "./lib/SafeBEP20.sol";
import "@pancake-swap-lib/contracts/token/BEP20/IBEP20.sol";
import "@pancake-swap-periphery/contracts/interfaces/IPancakeRouter02.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/proxy/utils/Initializable.sol";

contract PumpTreasury is Ownable, Initializable {
    using SafeMath for uint256;
    using SafeBEP20 for IBEP20;

    PumpToken public pumpToken;
    IPancakeRouter02 public pancakeRouter;
    IBEP20 public wBNB;
    address public electionMangerAddr;

    event TreasurySwap(address _caller, uint256 _amount);
    event BuyProposedToken(address _tokenAddress, uint256 _wBNBAmt);
    event SellAndStake(address _tokenSold, uint256 _pumpStaked, uint256 _bnbStaked);

    modifier onlyElectionManager() {
        require(electionMangerAddr == msg.sender, "Caller is not ElectionManager");
        _;
    }

    function initialize(
        PumpToken _pumpToken,
        address _wBNBAddr,
        address _pancakeRouterAddr
    ) public initializer {
        pumpToken = _pumpToken;
        pancakeRouter = IPancakeRouter02(_pancakeRouterAddr);
        wBNB = IBEP20(_wBNBAddr);
    }

    function setElectionManagerAddress(address _addr) public onlyOwner {
        electionMangerAddr = _addr;
    }

    function swapPumpForBNB(uint256 _amount) public {
        emit TreasurySwap(msg.sender, _amount);
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
        // First sell the position and record how much BNB we receive for it
        uint256 initialBalance = address(this).balance;
        _performSwap(_tokenAddr, address(wBNB), _amt);
        uint256 newBalance = address(this).balance;
        // TODO -- should we be checking BNB here or WBNB
        uint256 receivedBNB = newBalance - initialBalance;

        // Now, use half the BNB to buy PUMP -- also recording how much PUMP we receive
        uint256 initialPump = pumpToken.balanceOf(address(this));
        _performSwap(address(wBNB), address(pumpToken), receivedBNB / 2);
        uint256 newPump = pumpToken.balanceOf(address(this));
        uint256 receivedPump = newPump - initialPump;

        // Now stake the received PUMP against the remaining BNB
        _addPumpLiquidity(receivedPump, receivedBNB / 2);
        emit SellAndStake(_tokenAddr, receivedPump, receivedBNB / 2);
    }

    function _addPumpLiquidity(uint256 _pumpAmount, uint256 _bnbAmount) internal {
        // add the liquidity
        pancakeRouter.addLiquidityETH{value: _bnbAmount}(
            address(pumpToken),
            _pumpAmount,
            0, // slippage is unavoidable
            0, // slippage is unavoidable
            address(this),
            block.timestamp
        );
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
            block.timestamp // deadline
        );
    }
}
