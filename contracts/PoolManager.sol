// SPDX-License-Identifier: MIT

pragma solidity ^0.8;

import "./lib/SafeMath.sol";
import "./lib/SafeBEP20.sol";
import "@openzeppelin-upgradeable/contracts/access/OwnableUpgradeable.sol";
import "@openzeppelin-upgradeable/contracts/security/ReentrancyGuardUpgradeable.sol";
import "@pancake-swap-lib/contracts/token/BEP20/IBEP20.sol";
import "./PumpToken.sol";
import "./vPumpToken.sol";


contract PoolManager is OwnableUpgradeable, ReentrancyGuardUpgradeable {
    using SafeMath for uint256;
    using SafeBEP20 for IBEP20;

    // Info of each user.
    struct UserInfo {
        uint256 amount;         // How many LP tokens the user has provided.
        uint256 rewardDebt;     // Reward debt. See explanation below.
        //
        // We do some fancy math here. Basically, any point in time, the amount of PUMP
        // entitled to a user but is pending to be distributed is:
        //
        //   pending reward = (user.amount * pool.accPumpPerShare) - user.rewardDebt
        //
        // Whenever a user deposits or withdraws LP tokens to a pool. Here's what happens:
        //   1. The pool's `accPumpPerShare` (and `lastRewardBlock`) gets updated.
        //   2. User receives the pending reward sent to his/her address.
        //   3. User's `amount` gets updated.
        //   4. User's `rewardDebt` gets updated.
    }

    // Info of each pool.
    struct PoolInfo {
        IBEP20 lpToken;           // Address of LP token contract.
        uint256 allocPoint;       // How many allocation points assigned to this pool. PUMP to distribute per block.
        uint256 lastRewardBlock;  // Last block number that PUMP distribution occurs.
        uint256 accPumpPerShare;   // Accumulated PUMP per share, times 1e12. See below.
    }

    PumpToken public pumpToken;
    VPumpToken public vPumpToken;
    address public devAddr;
    uint256 public pumpPerBlock;

    // Info of each pool.
    PoolInfo[] public poolInfo;
    // Info of each user that stakes LP tokens.
    mapping(uint256 => mapping(address => UserInfo)) public userInfo;
    // Total allocation points. Must be the sum of all allocation points in all pools.
    uint256 public totalAllocPoint;
    // Bool indicating whether the start and end blocks have been set.
    bool public startEndSet;
    // The block number when PUMP mining starts.
    uint256 public startBlock;
    // The block number when PUMP mining can be publicly shut off
    uint256 public endBlock;
    mapping(IBEP20 => bool) public poolExistence;

    event Deposit(address indexed user, uint256 indexed pid, uint256 amount);
    event Withdraw(address indexed user, uint256 indexed pid, uint256 amount);
    event EmergencyWithdraw(address indexed user, uint256 indexed pid, uint256 amount);
    event SetFeeAddress(address indexed user, address indexed newAddress);
    event SetDevAddress(address indexed user, address indexed newAddress);
    event UpdateEmissionRate(address indexed user, uint256 goosePerBlock);

    function initialize(
        PumpToken _pumpToken,
        VPumpToken _vPumpToken,
        uint256 _pumpPerBlock
    ) public initializer {
        pumpToken = _pumpToken;
        vPumpToken = _vPumpToken;
        devAddr = msg.sender;
        pumpPerBlock = _pumpPerBlock;
        totalAllocPoint = 0;

        __Ownable_init();
    }

    // View function to see pending PUMP on frontend.
    function pendingPump(uint256 _pid, address _user) external view returns (uint256) {
        PoolInfo storage pool = poolInfo[_pid];
        UserInfo storage user = userInfo[_pid][_user];
        uint256 accPumpPerShare = pool.accPumpPerShare;
        uint256 lpSupply = pool.lpToken.balanceOf(address(this));
        if (block.number > pool.lastRewardBlock && lpSupply != 0) {
            uint256 numElapsedBlocks = block.number.sub(pool.lastRewardBlock);
            uint256 pumpReward = numElapsedBlocks.mul(pumpPerBlock).mul(pool.allocPoint).div(totalAllocPoint);
            accPumpPerShare = accPumpPerShare.add(pumpReward.mul(1e12).div(lpSupply));
        }
        uint256 ret = user.amount.mul(accPumpPerShare).div(1e12).sub(user.rewardDebt);
        return ret;
    }

    // Add a new lp to the pool. Can only be called by the owner.
    function add(uint256 _allocPoint, IBEP20 _lpToken, bool _withUpdate) public onlyOwner {
        require(startEndSet, "Not yet initialized");
        require(poolExistence[_lpToken] == false, "nonDuplicated: duplicated");
        if (_withUpdate) {
            massUpdatePools();
        }
        uint256 lastRewardBlock = block.number > startBlock ? block.number : startBlock;
        totalAllocPoint = totalAllocPoint.add(_allocPoint);
        poolExistence[_lpToken] = true;
        poolInfo.push(PoolInfo({
            lpToken : _lpToken,
            allocPoint : _allocPoint,
            lastRewardBlock : lastRewardBlock,
            accPumpPerShare : 0
        }));
    }

    function setStartEnd(uint256 _start, uint256 _end) public onlyOwner {
        require(!startEndSet, "Already set");
        startEndSet = true;
        startBlock = _start;
        endBlock = _end;
    }

    // Update the given pool's PUMP allocation point and deposit fee. Can only be called by the owner.
    function set(uint256 _pid, uint256 _allocPoint, bool _withUpdate) public onlyOwner {
        if (_withUpdate) {
            massUpdatePools();
        }
        totalAllocPoint = totalAllocPoint.sub(poolInfo[_pid].allocPoint).add(_allocPoint);
        poolInfo[_pid].allocPoint = _allocPoint;
    }

    // Update reward variables for all pools. Be careful of gas spending!
    function massUpdatePools() public {
        uint256 length = poolInfo.length;
        for (uint256 pid = 0; pid < length; ++pid) {
            updatePool(pid);
        }
    }

    // Update reward variables of the given pool to be up-to-date.
    function updatePool(uint256 _pid) public {
        PoolInfo storage pool = poolInfo[_pid];
        if (block.number <= pool.lastRewardBlock) {
            return;
        }
        uint256 lpSupply = pool.lpToken.balanceOf(address(this));
        if (lpSupply == 0 || pool.allocPoint == 0) {
            pool.lastRewardBlock = block.number;
            return;
        }
        uint256 numElapsedBlocks = block.number.sub(pool.lastRewardBlock);
        uint256 pumpReward = numElapsedBlocks.mul(pumpPerBlock).mul(pool.allocPoint).div(totalAllocPoint);
        pool.accPumpPerShare = pool.accPumpPerShare.add(pumpReward.mul(1e12).div(lpSupply));
        pool.lastRewardBlock = block.number;
    }

    // Deposit LP tokens to PoolManager for PUMP allocation.
    function deposit(uint256 _pid, uint256 _amount) public nonReentrant {
        PoolInfo storage pool = poolInfo[_pid];
        UserInfo storage user = userInfo[_pid][msg.sender];
        updatePool(_pid);
        if (user.amount > 0) {
            uint256 pending = user.amount.mul(pool.accPumpPerShare).div(1e12).sub(user.rewardDebt);
            if (pending > 0) {
                safePumpTransfer(msg.sender, pending);
            }
        }
        if (_amount > 0) {
            pool.lpToken.safeTransferFrom(address(msg.sender), address(this), _amount);
            // mint vPump and send to the depositor. Used for governance
            vPumpToken.mint(msg.sender, _amount);
            user.amount = user.amount.add(_amount);
        }
        user.rewardDebt = user.amount.mul(pool.accPumpPerShare).div(1e12);
        emit Deposit(msg.sender, _pid, _amount);
    }

    function withdraw(uint256 _pid, uint256 _amount) public nonReentrant {
        PoolInfo storage pool = poolInfo[_pid];
        UserInfo storage user = userInfo[_pid][msg.sender];
        require(user.amount >= _amount, "withdraw: not good");
        updatePool(_pid);
        uint256 pending = user.amount.mul(pool.accPumpPerShare).div(1e12).sub(user.rewardDebt);
        if (pending > 0) {
            safePumpTransfer(msg.sender, pending);
        }
        if (_amount > 0) {
            user.amount = user.amount.sub(_amount);
            pool.lpToken.safeTransfer(address(msg.sender), _amount);
            vPumpToken.burn(address(msg.sender), _amount);
        }
        user.rewardDebt = user.amount.mul(pool.accPumpPerShare).div(1e12);
        emit Withdraw(msg.sender, _pid, _amount);
    }

    //Pancake has to add hidden dummy pools inorder to alter the emission, make it simple and transparent to all.
    function updateEmissionRate(uint256 _pumpPerBlock) public onlyOwner {
        massUpdatePools();
        pumpPerBlock = _pumpPerBlock;
        emit UpdateEmissionRate(msg.sender, _pumpPerBlock);
    }

    function endEmission() public {
        require(block.number >= endBlock, "Must wait to end farming");
        massUpdatePools();
        pumpPerBlock = 0;
        emit UpdateEmissionRate(msg.sender, 0);
    }

    // Update dev address by the previous dev.
    function dev(address _devAddr) public {
        require(msg.sender == devAddr, "dev: wut?");
        devAddr = _devAddr;
        emit SetDevAddress(msg.sender, _devAddr);
    }

    // Withdraw without caring about rewards. EMERGENCY ONLY.
    function emergencyWithdraw(uint256 _pid) public nonReentrant {
        PoolInfo storage pool = poolInfo[_pid];
        UserInfo storage user = userInfo[_pid][msg.sender];
        uint256 amount = user.amount;
        user.amount = 0;
        user.rewardDebt = 0;
        pool.lpToken.safeTransfer(address(msg.sender), amount);
        emit EmergencyWithdraw(msg.sender, _pid, amount);
    }

    // Safe pump transfer function, just in case if rounding error causes pool to not have enough PUMP
    function safePumpTransfer(address _to, uint256 _amount) internal {
        uint256 pumpBal = pumpToken.balanceOf(address(this));
        bool transferSuccess = false;
        if (_amount > pumpBal) {
            transferSuccess = pumpToken.transfer(_to, pumpBal);
        } else {
            transferSuccess = pumpToken.transfer(_to, _amount);
        }
        require(transferSuccess, "transfer failed");
    }
}
