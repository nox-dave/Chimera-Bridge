// SPDX-License-Identifier: MIT
pragma solidity 0.8.30;

abstract contract ERC20 {
    event Transfer(address indexed src, address indexed dst, uint256 amount);
    event Approval(
        address indexed owner,
        address indexed spender,
        uint256 amount
    );

    string public name;
    string public symbol;
    uint8 public immutable decimals;

    uint256 public totalSupply;
    mapping(address => uint256) public balanceOf;
    mapping(address => mapping(address => uint256)) public allowance;

    constructor(string memory _name, string memory _symbol, uint8 _decimals) {
        name = _name;
        symbol = _symbol;
        decimals = _decimals;
    }

    function approve(
        address spender,
        uint256 amount
    ) public virtual returns (bool) {
        allowance[msg.sender][spender] = amount;

        emit Approval(msg.sender, spender, amount);

        return true;
    }

    function transfer(
        address dst,
        uint256 amount
    ) public virtual returns (bool) {
        balanceOf[msg.sender] -= amount;
        balanceOf[dst] += amount;

        emit Transfer(msg.sender, dst, amount);

        return true;
    }

    function transferFrom(
        address src,
        address dst,
        uint256 amount
    ) public virtual returns (bool) {
        uint256 allowed = allowance[src][msg.sender];
        if (allowed != type(uint256).max) {
            allowance[src][msg.sender] = allowed - amount;
        }

        balanceOf[src] -= amount;
        balanceOf[dst] += amount;

        emit Transfer(src, dst, amount);

        return true;
    }

    function _mint(address dst, uint256 amount) internal virtual {
        totalSupply += amount;
        balanceOf[dst] += amount;
        emit Transfer(address(0), dst, amount);
    }

    function _burn(address src, uint256 amount) internal virtual {
        totalSupply -= amount;
        balanceOf[src] -= amount;
        emit Transfer(src, address(0), amount);
    }
}

contract Token is ERC20 {
    constructor(
        string memory _name,
        string memory _symbol,
        uint8 _decimals
    ) ERC20(_name, _symbol, _decimals) {}

    function mint(address to, uint256 amount) external {
        _mint(to, amount);
    }

    function burn(address from, uint256 amount) external {
        _burn(from, amount);
    }
}
