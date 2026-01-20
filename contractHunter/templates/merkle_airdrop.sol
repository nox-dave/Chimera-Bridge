// SPDX-License-Identifier: MIT
pragma solidity 0.8.30;

import "forge-std/Test.sol";
import "../challenges/{challenge_folder}/{main_contract}.sol";
import "../challenges/{challenge_folder}/Token.sol";

contract {test_contract_name} is Test {{
    {target_contract} public target;
    {token_contract} public token;
    address public attacker = address(0x1337);
    
    bytes32[] public proof;
    uint256 constant CLAIM_AMOUNT = {claim_amount};

    function setUp() public {{
        token = new {token_contract}();
        target = new {target_contract}(address(token), {merkle_root});
        token.mint(address(target), {total_airdrop_amount});
        {setup_code}
    }}

    function testExploit() public {{
        bytes32 leaf = keccak256(abi.encode(attacker, CLAIM_AMOUNT));
        
        vm.prank(attacker);
        target.claim(proof, attacker, CLAIM_AMOUNT);
        
        assertEq(token.balanceOf(attacker), CLAIM_AMOUNT, "Attacker should receive tokens");
    }}
}}