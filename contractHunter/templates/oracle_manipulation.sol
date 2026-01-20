// SPDX-License-Identifier: MIT
pragma solidity 0.8.30;

import "forge-std/Test.sol";
import "../challenges/{challenge_folder}/{main_contract}.sol";

contract {test_contract_name} is Test {{
    {target_contract} public target;
    {token_contract} public token;
    address public attacker = address(0x1337);
    
    uint256 constant INITIAL_BALANCE = {initial_balance};

    function setUp() public {{
        token = new {token_contract}();
        target = new {target_contract}(address(token));
        token.mint(address(target), INITIAL_BALANCE);
        token.mint(address(attacker), {attacker_balance});
        {setup_code}
    }}

    function testExploit() public {{
        vm.startPrank(attacker);
        
        {price_manipulation}
        
        {exploit_call}
        
        vm.stopPrank();
        
        {final_assertion}
    }}
}}