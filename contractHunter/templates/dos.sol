// SPDX-License-Identifier: MIT
pragma solidity 0.8.30;

import "forge-std/Test.sol";
import "../challenges/{challenge_folder}/{main_contract}.sol";

contract {test_contract_name} is Test {{
    {target_contract} public target;
    DoSAttacker public attacker;
    address public victim = address(0x9999);

    function setUp() public {{
        target = new {target_contract}();
        attacker = new DoSAttacker(address(target));
        vm.deal(address(attacker), 10 ether);
        vm.deal(address(victim), 10 ether);
        {setup_code}
    }}

    function testExploit() public {{
        vm.prank(victim);
        {victim_call}
        
        vm.prank(address(attacker));
        attacker.attack();
        
        vm.prank(victim);
        vm.expectRevert();
        {victim_call_should_fail}
    }}
}}

contract DoSAttacker {{
    address public target;
    
    constructor(address _target) {{
        target = _target;
    }}
    
    function attack() external payable {{
        {attack_logic}
    }}
    
    receive() external payable {{
        {receive_logic}
    }}
}}