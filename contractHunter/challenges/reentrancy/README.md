# Reentrancy Challenge

## What's the Bug?

The `withdraw()` function makes an external call before updating the balance, allowing an attacker to recursively call `withdraw()` and drain the contract.

## How to Exploit?

1. Deploy an attacker contract with a `receive()` function
2. Deposit funds into the vulnerable contract
3. Call `withdraw()` - the receive() function will recursively call `withdraw()` before balance is updated
4. Drain all funds

## The Fix

Use the CEI (Checks-Effects-Interactions) pattern:
1. **Checks**: Validate inputs
2. **Effects**: Update state (balance = 0)
3. **Interactions**: Make external calls last
