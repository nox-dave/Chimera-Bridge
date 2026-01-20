// SPDX-License-Identifier: MIT
pragma solidity 0.8.30;

import "forge-std/Test.sol";
import "../challenges/{challenge_folder}/{main_contract}.sol";
{additional_imports}

{additional_contracts}

contract {test_contract_name} is Test {{
    {state_variables}

    function setUp() public {{
        {setup_code}
    }}

    function testExploit() public {{
        {test_code}
    }}
}}
