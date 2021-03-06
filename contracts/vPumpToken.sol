// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "./lib/SafeMath.sol";
import "@openzeppelin-upgradeable/contracts/access/OwnableUpgradeable.sol";


contract VPumpToken is OwnableUpgradeable {
    using SafeMath for uint256;

    string public symbol;
    string public name;
    uint256 public decimals;
    uint256 public totalSupply;
    address public canMintBurn;
    address public electionManager;


    mapping(address => uint256) public balances;
    mapping(address => mapping(address => uint256)) public allowed;

    event Transfer(address indexed _from, address indexed _to, uint256 _value);
    event Approval(address indexed _owner, address indexed _spender, uint256 _value);

    modifier onlyCanMintBurn {
      require(msg.sender == canMintBurn, "Must have mintBurn role");
      _;
    }

    function initialize() public initializer {
       symbol = "vPUMP";
       name = "Voting Pump";
       decimals = 18;
       totalSupply = 0;
       canMintBurn = msg.sender;
       balances[msg.sender] = totalSupply;
       emit Transfer(address(0), msg.sender, totalSupply);
       __Ownable_init();
    }

    function setCanMintBurn(address _canMintBurn) public onlyOwner {
        canMintBurn = _canMintBurn;
    }

    function setElectionManagerAddress(address _electionManager) public onlyOwner {
        electionManager = _electionManager;
    }

    /**
        @notice Approve an address to spend the specified amount of tokens on behalf of msg.sender
        @dev Beware that changing an allowance with this method brings the risk that someone may use both the old
             and the new allowance by unfortunate transaction ordering. One possible solution to mitigate this
             race condition is to first reduce the spender's allowance to 0 and set the desired value afterwards:
             https://github.com/ethereum/EIPs/issues/20#issuecomment-263524729
        @param _spender The address which will spend the funds.
        @param _value The amount of tokens to be spent.
        @return Success boolean
     */
    function approve(address _spender, uint256 _value) public returns (bool) {
        allowed[msg.sender][_spender] = _value;
        emit Approval(msg.sender, _spender, _value);
        return true;
    }

    /**
        @notice Transfer tokens to a specified address
        @param _to The address to transfer to
        @param _value The amount to be transferred
        @return Success boolean
     */
    function transfer(address _to, uint256 _value) public returns (bool) {
        _transfer(msg.sender, _to, _value);
        return true;
    }

    /**
        @notice Transfer tokens from one address to another
        @param _from The address which you want to send tokens from
        @param _to The address which you want to transfer to
        @param _value The amount of tokens to be transferred
        @return Success boolean
     */
    function transferFrom(
        address _from,
        address _to,
        uint256 _value
    )
        public
        returns (bool)
    {
        require(allowed[_from][msg.sender] >= _value, "Insufficient allowance");
        allowed[_from][msg.sender] = allowed[_from][msg.sender].sub(_value);
        _transfer(_from, _to, _value);
        return true;
    }

    function mint(address _to, uint256 _value) public onlyCanMintBurn returns (bool) {
        totalSupply = totalSupply.add(_value);
        balances[_to] = balances[_to].add(_value);
        emit Transfer(address(0), _to, _value);
        return true;
    }

    function burn(address _from, uint256 _value) public onlyCanMintBurn returns(bool) {
        require(balances[_from] >= _value, "Insufficient balance");
        totalSupply = totalSupply.sub(_value);
        balances[_from] = balances[_from].sub(_value);
        emit Transfer(_from, address(0), _value);
        return true;
    }

    /**
        @notice Getter to check the current balance of an address
        @param _owner Address to query the balance of
        @return Token balance
     */
    function balanceOf(address _owner) public view returns (uint256) {
        return balances[_owner];
    }

    /**
        @notice Getter to check the amount of tokens that an owner allowed to a spender
        @param _owner The address which owns the funds
        @param _spender The address which will spend the funds
        @return The amount of tokens still available for the spender
     */
    function allowance(
        address _owner,
        address _spender
    )
    public
    view
    returns (uint256)
    {
        return allowed[_owner][_spender];
    }

    /** shared logic for transfer and transferFrom */
    // Note: _vPump is deliberately non-transferable unless it is to or from the electionManager contract
    // this is to avoid secondary markets from popping up
    function _transfer(address _from, address _to, uint256 _value) internal {
        require(balances[_from] >= _value, "Insufficient balance");
        require(_from == electionManager || _to == electionManager, "Only transfer electionManager");
        balances[_from] = balances[_from].sub(_value);
        balances[_to] = balances[_to].add(_value);
        emit Transfer(_from, _to, _value);
    }
}
