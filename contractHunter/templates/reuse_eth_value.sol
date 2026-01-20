// SPDX-License-Identifier: MIT
pragma solidity 0.8.30;

import "forge-std/Test.sol";
import "../challenges/{challenge_folder}/{main_contract}.sol";

contract {test_contract_name} is Test {{
    {target_contract} public target;
    address public attacker = address(0x1337);
    
    uint256 constant DEPOSIT_AMOUNT = {deposit_amount};

    function setUp() public {{
        target = new {target_contract}();
        vm.deal(address(attacker), DEPOSIT_AMOUNT * 2);
        {setup_code}
    }}

    function testExploit() public {{
        uint256 attackerBalanceBefore = address(attacker).balance;
        
        vm.startPrank(attacker);
        {exploit_call}
        vm.stopPrank();
        
        {final_assertion}
    }}
}}