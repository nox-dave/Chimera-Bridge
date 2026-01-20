## Finding: Insecure Role Management

**Severity:** High

**Contract:** AccessControl

**Location:** grantRole function

### Description

The `AccessControl` contract implements a role-based access control mechanism that allows users with the ADMIN role to grant and revoke roles to other addresses. However, the design allows for a potential exploit where an attacker could deploy the `Challenge2Exploit` contract and gain the ADMIN role through a vulnerability in the system. If the attacker successfully obtains the ADMIN role, they can call the `grantRole` function to assign themselves or any other address any role, including the USER role, thereby gaining unauthorized access and control over the system. This could lead to severe security breaches, including the ability to manipulate contract states or perform unauthorized actions.

### Proof of Concept

See: test/Challenge2_Access_Exploit.t.sol

### Recommendation

To mitigate this vulnerability, ensure that the `grantRole` function can only be called by trusted addresses or through a secure mechanism. Consider implementing the following recommendations:

1. **Restrict Contract Deployment**: Ensure that only the intended contract can deploy the `Challenge2Exploit` contract or any similar contracts.

2. **Use a Factory Pattern**: Implement a factory pattern that controls the creation of new contracts and ensures that only authorized contracts can interact with the `AccessControl` contract.

3. **Role Management Improvements**: Consider adding a mechanism to prevent the ADMIN role from being granted to untrusted contracts. For example, you could maintain a whitelist of addresses that are allowed to hold the ADMIN role.

4. **Code Example**:
   ```solidity
   modifier onlyTrustedContract() {
       require(msg.sender == trustedContractAddress, "not a trusted contract");
       _;
   }

   function grantRole(bytes32 role, address account) external onlyRole(ADMIN) onlyTrustedContract {
       _grantRole(role, account);
   }
   ```

By implementing these recommendations, you can significantly enhance the security of the role management system and prevent unauthorized access.