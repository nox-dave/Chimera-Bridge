// SPDX-License-Identifier: MIT
pragma solidity 0.8.30;

import "forge-std/Test.sol";
import "../challenges/{challenge_folder}/{main_contract}.sol";
import "../challenges/{challenge_folder}/Token.sol";

contract VulnerableLendingPool is ILendingPool {{
    address public immutable token;
    
    constructor(address _token) {{
        token = _token;
    }}
    
    function flashLoan(
        uint256 amount,
        address target,
        bytes calldata data
    ) external {{
        (bool success, ) = target.call(data);
        require(success, "Flash loan callback failed");
    }}
}}

contract {test_contract_name} is Test {{
    LendingPoolExploit public exploit;
    Token public token;
    VulnerableLendingPool public pool;
    
    uint256 constant POOL_BALANCE = {pool_balance};

    function setUp() public {{
        token = new Token("Test Token", "TEST", 18);
        pool = new VulnerableLendingPool(address(token));
        token.mint(address(pool), POOL_BALANCE);
        exploit = new LendingPoolExploit(address(pool));
    }}

    function testExploit() public {{
        assertEq(token.balanceOf(address(pool)), POOL_BALANCE, "Pool should have tokens");
        assertEq(token.balanceOf(address(exploit)), 0, "Exploit should start empty");
        
        exploit.pwn();
        
        assertEq(token.balanceOf(address(pool)), 0, "Pool should be drained");
        assertEq(token.balanceOf(address(exploit)), POOL_BALANCE, "Exploit should have tokens");
    }}
}}
