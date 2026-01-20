# Flash Loan Challenge

## What's the Bug?

The `flashLoan()` function makes an arbitrary call to any target with any data, allowing an attacker to approve themselves to spend the pool's tokens.

## How to Exploit?

1. Call `flashLoan()` with amount = 0
2. Target the token contract itself
3. Data = `token.approve(attacker, pool_balance)`
4. The pool calls `token.approve()` on behalf of itself
5. Attacker transfers all tokens from pool

## The Fix

- Validate callback target (whitelist or require specific interface)
- Limit what functions can be called
- Use reentrancy guards
- Require non-zero amount
