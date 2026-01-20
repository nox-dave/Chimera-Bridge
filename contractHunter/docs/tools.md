Template Minimal Onboarding Filled Out:


Minimal Smart Contract Security Review Onboarding
Table of Contents
Minimal Smart Contract Security Review Onboarding
Table of Contents
About the project / Documentation
Stats
Setup
Requirements
Testing
Security Review Scope
Commit Hash
Repo URL
In scope vs out of scope contracts
Compatibilities
Roles
Known Issues
About the project / Documentation
Summary of the project. The more documentation, the better.

Stats
Use something like solidity metrics or cloc to get these.

nSLOC: XX
Complexity Score: XX
Security Review Timeline: Date -> Date
Setup
Requirements
What tools are needed to setup the codebase & test suite?

Example:

forge init
forge install OpenZeppelin/openzeppelin-contracts --no-commit
forge install vectorized/solady --no-commit
forge build
Testing
How to run tests. How to see test coverage.

Example:

forge test
Security Review Scope
The specific details of the security review. Nail down exactly what the protocol is planning on deploying, and how they plan on deploying it.

Commit Hash
Repo URL
In scope vs out of scope contracts
Compatibilities
Solc Version: XXX
Chain(s) to deploy contract to:
XXX (ie: ETH)
XXX (ie: Arbitrum)
Tokens:
XXX (ie: ERC20s)
XXX (ie: LINK: )
XXX (ie: USDC: )
XXX (ie: ERC721s)
XXX (ie: CryptoKitties: )
List expected ERC20s and other specific tokens. If a protocol is expected to work with multiple or any tokens of a certain standard, you could do something like "All ERC20s". Or an ordered list like "USDC: " etc
Roles
What are the different actors of the system? What are their powers? What should/shouldn't they do?

Example:​

Actors:
    Buyer: The purchaser of services, in this scenario, a project purchasing an audit.
    Seller: The seller of services, in this scenario, an auditor willing to audit a project.
    Arbiter: An impartial, trusted actor who can resolve disputes between the Buyer and Seller.
    The Arbiter is only compensated the arbiterFee amount if a dispute occurs.
Known Issues
List any issues that the protocol team is aware of and will not be acknowledging/fixing.

============================================================================================

CLOC: https://github.com/AlDanial/cloc          (Good estimated time for how long an audit will take)

============================================================================================

Fuzzers:

Slither
Mithril
etc.

=============================================================================================