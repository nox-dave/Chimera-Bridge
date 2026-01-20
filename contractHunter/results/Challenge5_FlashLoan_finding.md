## Finding: Flash Loan Attack

**Severity:** Critical

**Contract:** LendingPoolExploit

**Location:** pwn function

### Description

The contract allows an attacker to exploit the flash loan feature of the lending pool. By calling the `flashLoan` function with a zero amount, the attacker can approve the contract to spend the entire balance of the token held by the pool. This can lead to unauthorized transfer of tokens from the pool to the attacker's contract, effectively draining the pool of its funds. The lack of checks on the amount being borrowed and the approval process makes this a critical vulnerability, as it allows for the manipulation of token allowances without any collateral or risk to the attacker.

### Proof of Concept

See: test/Challenge5_FlashLoan_Exploit.t.sol

### Recommendation

To mitigate this vulnerability, it is recommended to implement the following changes:

1. **Require a Non-Zero Amount for Flash Loans**: Modify the `flashLoan` function to require that the amount borrowed is greater than zero. This prevents the approval of the entire token balance when a zero amount is specified.

   ```solidity
   function flashLoan(
       uint256 amount,
       address target,
       bytes calldata data
   ) external {
       require(amount > 0, "Flash loan amount must be greater than zero");
       // existing logic...
   }
   ```

2. **Implement Reentrancy Guards**: Use a reentrancy guard to prevent reentrant calls during the execution of the flash loan. This can help mitigate the risk of similar attacks.

   ```solidity
   import "@openzeppelin/contracts/security/ReentrancyGuard.sol";

   contract LendingPool is ReentrancyGuard {
       // existing code...
   }
   ```

3. **Limit Approval Amounts**: Ensure that the approval of token allowances is limited to the exact amount being borrowed rather than allowing full balance approvals.

By implementing these recommendations, the contract can significantly reduce the risk of flash loan attacks and improve overall security.