# Access Control Challenge

## What's the Bug?

Missing or incorrect access control checks allow unauthorized users to call privileged functions.

## How to Exploit?

Depends on the specific vulnerability - could be:
- Missing `onlyOwner` modifier
- Incorrect owner check
- Public function that should be restricted

## The Fix

- Use OpenZeppelin's `Ownable` or `AccessControl`
- Verify permissions before executing privileged functions
- Use modifiers consistently
