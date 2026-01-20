// SPDX-License-Identifier: MIT
pragma solidity 0.8.30;

import "forge-std/Test.sol";
import "../challenges/{challenge_folder}/{main_contract}.sol";

contract {test_contract_name} is Test {{
    {target_contract} public target;
    MaliciousImplementation public malicious;
    address public attacker = address(0x1337);

    function setUp() public {{
        target = new {target_contract}();
        malicious = new MaliciousImplementation();
        {setup_code}
    }}

    function testExploit() public {{
        {initial_assertion}
        
        vm.prank(attacker);
        {exploit_call}
        
        {final_assertion}
    }}
}}

contract MaliciousImplementation {{
    {malicious_storage_layout}
    
    function {malicious_function}() external {{
        {malicious_code}
    }}
}}