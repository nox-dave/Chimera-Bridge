// SPDX-License-Identifier: MIT
pragma solidity 0.8.30;

import "forge-std/Test.sol";
import "../challenges/{challenge_folder}/{main_contract}.sol";

contract {test_contract_name} is Test {{
    {target_contract} public target;
    address public attacker = address(0x1337);
    
    uint256 constant INITIAL_BALANCE = {initial_balance};

    function setUp() public {{
        target = new {target_contract}{{value: INITIAL_BALANCE}}();
        vm.deal(address(attacker), 1 ether);
        {setup_code}
    }}

    function testExploit() public {{
        uint256 targetBalanceBefore = address(target).balance;
        
        vm.prank(attacker);
        {exploit_contract}.pwn();
        
        assertEq(address(target).balance, 0, "Target should be drained");
        assertGt(address({exploit_contract}).balance, 0, "Exploit contract should receive funds");
    }}
}}

contract {exploit_contract_name} {{
    address public immutable target;

    constructor(address _target) {{
        target = _target;
    }}

    receive() external payable {{}}

    function pwn() external {{
        bytes4 selector = bytes4(keccak256(bytes("{collision_signature}")));
        {exploit_call}
    }}
}}