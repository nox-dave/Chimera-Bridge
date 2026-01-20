// File: @openzeppelin/contracts/token/ERC20/IERC20.sol
// SPDX-License-Identifier: MIT
// OpenZeppelin Contracts (last updated v4.6.0) (token/ERC20/IERC20.sol)

pragma solidity ^0.8.0;

/**
 * @dev Interface of the ERC20 standard as defined in the EIP.
 */
interface IERC20 {
    /**
     * @dev Emitted when `value` tokens are moved from one account (`from`) to
     * another (`to`).
     *
     * Note that `value` may be zero.
     */
    event Transfer(address indexed from, address indexed to, uint256 value);

    /**
     * @dev Emitted when the allowance of a `spender` for an `owner` is set by
     * a call to {approve}. `value` is the new allowance.
     */
    event Approval(address indexed owner, address indexed spender, uint256 value);

    /**
     * @dev Returns the amount of tokens in existence.
     */
    function totalSupply() external view returns (uint256);

    /**
     * @dev Returns the amount of tokens owned by `account`.
     */
    function balanceOf(address account) external view returns (uint256);

    /**
     * @dev Moves `amount` tokens from the caller's account to `to`.
     *
     * Returns a boolean value indicating whether the operation succeeded.
     *
     * Emits a {Transfer} event.
     */
    function transfer(address to, uint256 amount) external returns (bool);

    /**
     * @dev Returns the remaining number of tokens that `spender` will be
     * allowed to spend on behalf of `owner` through {transferFrom}. This is
     * zero by default.
     *
     * This value changes when {approve} or {transferFrom} are called.
     */
    function allowance(address owner, address spender) external view returns (uint256);

    /**
     * @dev Sets `amount` as the allowance of `spender` over the caller's tokens.
     *
     * Returns a boolean value indicating whether the operation succeeded.
     *
     * IMPORTANT: Beware that changing an allowance with this method brings the risk
     * that someone may use both the old and the new allowance by unfortunate
     * transaction ordering. One possible solution to mitigate this race
     * condition is to first reduce the spender's allowance to 0 and set the
     * desired value afterwards:
     * https://github.com/ethereum/EIPs/issues/20#issuecomment-263524729
     *
     * Emits an {Approval} event.
     */
    function approve(address spender, uint256 amount) external returns (bool);

    /**
     * @dev Moves `amount` tokens from `from` to `to` using the
     * allowance mechanism. `amount` is then deducted from the caller's
     * allowance.
     *
     * Returns a boolean value indicating whether the operation succeeded.
     *
     * Emits a {Transfer} event.
     */
    function transferFrom(
        address from,
        address to,
        uint256 amount
    ) external returns (bool);
}


// File: @openzeppelin/contracts/utils/math/Math.sol
// SPDX-License-Identifier: MIT
// OpenZeppelin Contracts (last updated v4.7.0) (utils/math/Math.sol)

pragma solidity ^0.8.0;

/**
 * @dev Standard math utilities missing in the Solidity language.
 */
library Math {
    enum Rounding {
        Down, // Toward negative infinity
        Up, // Toward infinity
        Zero // Toward zero
    }

    /**
     * @dev Returns the largest of two numbers.
     */
    function max(uint256 a, uint256 b) internal pure returns (uint256) {
        return a >= b ? a : b;
    }

    /**
     * @dev Returns the smallest of two numbers.
     */
    function min(uint256 a, uint256 b) internal pure returns (uint256) {
        return a < b ? a : b;
    }

    /**
     * @dev Returns the average of two numbers. The result is rounded towards
     * zero.
     */
    function average(uint256 a, uint256 b) internal pure returns (uint256) {
        // (a + b) / 2 can overflow.
        return (a & b) + (a ^ b) / 2;
    }

    /**
     * @dev Returns the ceiling of the division of two numbers.
     *
     * This differs from standard division with `/` in that it rounds up instead
     * of rounding down.
     */
    function ceilDiv(uint256 a, uint256 b) internal pure returns (uint256) {
        // (a + b - 1) / b can overflow on addition, so we distribute.
        return a == 0 ? 0 : (a - 1) / b + 1;
    }

    /**
     * @notice Calculates floor(x * y / denominator) with full precision. Throws if result overflows a uint256 or denominator == 0
     * @dev Original credit to Remco Bloemen under MIT license (https://xn--2-umb.com/21/muldiv)
     * with further edits by Uniswap Labs also under MIT license.
     */
    function mulDiv(
        uint256 x,
        uint256 y,
        uint256 denominator
    ) internal pure returns (uint256 result) {
        unchecked {
            // 512-bit multiply [prod1 prod0] = x * y. Compute the product mod 2^256 and mod 2^256 - 1, then use
            // use the Chinese Remainder Theorem to reconstruct the 512 bit result. The result is stored in two 256
            // variables such that product = prod1 * 2^256 + prod0.
            uint256 prod0; // Least significant 256 bits of the product
            uint256 prod1; // Most significant 256 bits of the product
            assembly {
                let mm := mulmod(x, y, not(0))
                prod0 := mul(x, y)
                prod1 := sub(sub(mm, prod0), lt(mm, prod0))
            }

            // Handle non-overflow cases, 256 by 256 division.
            if (prod1 == 0) {
                return prod0 / denominator;
            }

            // Make sure the result is less than 2^256. Also prevents denominator == 0.
            require(denominator > prod1);

            ///////////////////////////////////////////////
            // 512 by 256 division.
            ///////////////////////////////////////////////

            // Make division exact by subtracting the remainder from [prod1 prod0].
            uint256 remainder;
            assembly {
                // Compute remainder using mulmod.
                remainder := mulmod(x, y, denominator)

                // Subtract 256 bit number from 512 bit number.
                prod1 := sub(prod1, gt(remainder, prod0))
                prod0 := sub(prod0, remainder)
            }

            // Factor powers of two out of denominator and compute largest power of two divisor of denominator. Always >= 1.
            // See https://cs.stackexchange.com/q/138556/92363.

            // Does not overflow because the denominator cannot be zero at this stage in the function.
            uint256 twos = denominator & (~denominator + 1);
            assembly {
                // Divide denominator by twos.
                denominator := div(denominator, twos)

                // Divide [prod1 prod0] by twos.
                prod0 := div(prod0, twos)

                // Flip twos such that it is 2^256 / twos. If twos is zero, then it becomes one.
                twos := add(div(sub(0, twos), twos), 1)
            }

            // Shift in bits from prod1 into prod0.
            prod0 |= prod1 * twos;

            // Invert denominator mod 2^256. Now that denominator is an odd number, it has an inverse modulo 2^256 such
            // that denominator * inv = 1 mod 2^256. Compute the inverse by starting with a seed that is correct for
            // four bits. That is, denominator * inv = 1 mod 2^4.
            uint256 inverse = (3 * denominator) ^ 2;

            // Use the Newton-Raphson iteration to improve the precision. Thanks to Hensel's lifting lemma, this also works
            // in modular arithmetic, doubling the correct bits in each step.
            inverse *= 2 - denominator * inverse; // inverse mod 2^8
            inverse *= 2 - denominator * inverse; // inverse mod 2^16
            inverse *= 2 - denominator * inverse; // inverse mod 2^32
            inverse *= 2 - denominator * inverse; // inverse mod 2^64
            inverse *= 2 - denominator * inverse; // inverse mod 2^128
            inverse *= 2 - denominator * inverse; // inverse mod 2^256

            // Because the division is now exact we can divide by multiplying with the modular inverse of denominator.
            // This will give us the correct result modulo 2^256. Since the preconditions guarantee that the outcome is
            // less than 2^256, this is the final result. We don't need to compute the high bits of the result and prod1
            // is no longer required.
            result = prod0 * inverse;
            return result;
        }
    }

    /**
     * @notice Calculates x * y / denominator with full precision, following the selected rounding direction.
     */
    function mulDiv(
        uint256 x,
        uint256 y,
        uint256 denominator,
        Rounding rounding
    ) internal pure returns (uint256) {
        uint256 result = mulDiv(x, y, denominator);
        if (rounding == Rounding.Up && mulmod(x, y, denominator) > 0) {
            result += 1;
        }
        return result;
    }

    /**
     * @dev Returns the square root of a number. It the number is not a perfect square, the value is rounded down.
     *
     * Inspired by Henry S. Warren, Jr.'s "Hacker's Delight" (Chapter 11).
     */
    function sqrt(uint256 a) internal pure returns (uint256) {
        if (a == 0) {
            return 0;
        }

        // For our first guess, we get the biggest power of 2 which is smaller than the square root of the target.
        // We know that the "msb" (most significant bit) of our target number `a` is a power of 2 such that we have
        // `msb(a) <= a < 2*msb(a)`.
        // We also know that `k`, the position of the most significant bit, is such that `msb(a) = 2**k`.
        // This gives `2**k < a <= 2**(k+1)` → `2**(k/2) <= sqrt(a) < 2 ** (k/2+1)`.
        // Using an algorithm similar to the msb conmputation, we are able to compute `result = 2**(k/2)` which is a
        // good first aproximation of `sqrt(a)` with at least 1 correct bit.
        uint256 result = 1;
        uint256 x = a;
        if (x >> 128 > 0) {
            x >>= 128;
            result <<= 64;
        }
        if (x >> 64 > 0) {
            x >>= 64;
            result <<= 32;
        }
        if (x >> 32 > 0) {
            x >>= 32;
            result <<= 16;
        }
        if (x >> 16 > 0) {
            x >>= 16;
            result <<= 8;
        }
        if (x >> 8 > 0) {
            x >>= 8;
            result <<= 4;
        }
        if (x >> 4 > 0) {
            x >>= 4;
            result <<= 2;
        }
        if (x >> 2 > 0) {
            result <<= 1;
        }

        // At this point `result` is an estimation with one bit of precision. We know the true value is a uint128,
        // since it is the square root of a uint256. Newton's method converges quadratically (precision doubles at
        // every iteration). We thus need at most 7 iteration to turn our partial result with one bit of precision
        // into the expected uint128 result.
        unchecked {
            result = (result + a / result) >> 1;
            result = (result + a / result) >> 1;
            result = (result + a / result) >> 1;
            result = (result + a / result) >> 1;
            result = (result + a / result) >> 1;
            result = (result + a / result) >> 1;
            result = (result + a / result) >> 1;
            return min(result, a / result);
        }
    }

    /**
     * @notice Calculates sqrt(a), following the selected rounding direction.
     */
    function sqrt(uint256 a, Rounding rounding) internal pure returns (uint256) {
        uint256 result = sqrt(a);
        if (rounding == Rounding.Up && result * result < a) {
            result += 1;
        }
        return result;
    }
}


// File: @openzeppelin/contracts/utils/math/SafeMath.sol
// SPDX-License-Identifier: MIT
// OpenZeppelin Contracts (last updated v4.6.0) (utils/math/SafeMath.sol)

pragma solidity ^0.8.0;

// CAUTION
// This version of SafeMath should only be used with Solidity 0.8 or later,
// because it relies on the compiler's built in overflow checks.

/**
 * @dev Wrappers over Solidity's arithmetic operations.
 *
 * NOTE: `SafeMath` is generally not needed starting with Solidity 0.8, since the compiler
 * now has built in overflow checking.
 */
library SafeMath {
    /**
     * @dev Returns the addition of two unsigned integers, with an overflow flag.
     *
     * _Available since v3.4._
     */
    function tryAdd(uint256 a, uint256 b) internal pure returns (bool, uint256) {
        unchecked {
            uint256 c = a + b;
            if (c < a) return (false, 0);
            return (true, c);
        }
    }

    /**
     * @dev Returns the subtraction of two unsigned integers, with an overflow flag.
     *
     * _Available since v3.4._
     */
    function trySub(uint256 a, uint256 b) internal pure returns (bool, uint256) {
        unchecked {
            if (b > a) return (false, 0);
            return (true, a - b);
        }
    }

    /**
     * @dev Returns the multiplication of two unsigned integers, with an overflow flag.
     *
     * _Available since v3.4._
     */
    function tryMul(uint256 a, uint256 b) internal pure returns (bool, uint256) {
        unchecked {
            // Gas optimization: this is cheaper than requiring 'a' not being zero, but the
            // benefit is lost if 'b' is also tested.
            // See: https://github.com/OpenZeppelin/openzeppelin-contracts/pull/522
            if (a == 0) return (true, 0);
            uint256 c = a * b;
            if (c / a != b) return (false, 0);
            return (true, c);
        }
    }

    /**
     * @dev Returns the division of two unsigned integers, with a division by zero flag.
     *
     * _Available since v3.4._
     */
    function tryDiv(uint256 a, uint256 b) internal pure returns (bool, uint256) {
        unchecked {
            if (b == 0) return (false, 0);
            return (true, a / b);
        }
    }

    /**
     * @dev Returns the remainder of dividing two unsigned integers, with a division by zero flag.
     *
     * _Available since v3.4._
     */
    function tryMod(uint256 a, uint256 b) internal pure returns (bool, uint256) {
        unchecked {
            if (b == 0) return (false, 0);
            return (true, a % b);
        }
    }

    /**
     * @dev Returns the addition of two unsigned integers, reverting on
     * overflow.
     *
     * Counterpart to Solidity's `+` operator.
     *
     * Requirements:
     *
     * - Addition cannot overflow.
     */
    function add(uint256 a, uint256 b) internal pure returns (uint256) {
        return a + b;
    }

    /**
     * @dev Returns the subtraction of two unsigned integers, reverting on
     * overflow (when the result is negative).
     *
     * Counterpart to Solidity's `-` operator.
     *
     * Requirements:
     *
     * - Subtraction cannot overflow.
     */
    function sub(uint256 a, uint256 b) internal pure returns (uint256) {
        return a - b;
    }

    /**
     * @dev Returns the multiplication of two unsigned integers, reverting on
     * overflow.
     *
     * Counterpart to Solidity's `*` operator.
     *
     * Requirements:
     *
     * - Multiplication cannot overflow.
     */
    function mul(uint256 a, uint256 b) internal pure returns (uint256) {
        return a * b;
    }

    /**
     * @dev Returns the integer division of two unsigned integers, reverting on
     * division by zero. The result is rounded towards zero.
     *
     * Counterpart to Solidity's `/` operator.
     *
     * Requirements:
     *
     * - The divisor cannot be zero.
     */
    function div(uint256 a, uint256 b) internal pure returns (uint256) {
        return a / b;
    }

    /**
     * @dev Returns the remainder of dividing two unsigned integers. (unsigned integer modulo),
     * reverting when dividing by zero.
     *
     * Counterpart to Solidity's `%` operator. This function uses a `revert`
     * opcode (which leaves remaining gas untouched) while Solidity uses an
     * invalid opcode to revert (consuming all remaining gas).
     *
     * Requirements:
     *
     * - The divisor cannot be zero.
     */
    function mod(uint256 a, uint256 b) internal pure returns (uint256) {
        return a % b;
    }

    /**
     * @dev Returns the subtraction of two unsigned integers, reverting with custom message on
     * overflow (when the result is negative).
     *
     * CAUTION: This function is deprecated because it requires allocating memory for the error
     * message unnecessarily. For custom revert reasons use {trySub}.
     *
     * Counterpart to Solidity's `-` operator.
     *
     * Requirements:
     *
     * - Subtraction cannot overflow.
     */
    function sub(
        uint256 a,
        uint256 b,
        string memory errorMessage
    ) internal pure returns (uint256) {
        unchecked {
            require(b <= a, errorMessage);
            return a - b;
        }
    }

    /**
     * @dev Returns the integer division of two unsigned integers, reverting with custom message on
     * division by zero. The result is rounded towards zero.
     *
     * Counterpart to Solidity's `/` operator. Note: this function uses a
     * `revert` opcode (which leaves remaining gas untouched) while Solidity
     * uses an invalid opcode to revert (consuming all remaining gas).
     *
     * Requirements:
     *
     * - The divisor cannot be zero.
     */
    function div(
        uint256 a,
        uint256 b,
        string memory errorMessage
    ) internal pure returns (uint256) {
        unchecked {
            require(b > 0, errorMessage);
            return a / b;
        }
    }

    /**
     * @dev Returns the remainder of dividing two unsigned integers. (unsigned integer modulo),
     * reverting with custom message when dividing by zero.
     *
     * CAUTION: This function is deprecated because it requires allocating memory for the error
     * message unnecessarily. For custom revert reasons use {tryMod}.
     *
     * Counterpart to Solidity's `%` operator. This function uses a `revert`
     * opcode (which leaves remaining gas untouched) while Solidity uses an
     * invalid opcode to revert (consuming all remaining gas).
     *
     * Requirements:
     *
     * - The divisor cannot be zero.
     */
    function mod(
        uint256 a,
        uint256 b,
        string memory errorMessage
    ) internal pure returns (uint256) {
        unchecked {
            require(b > 0, errorMessage);
            return a % b;
        }
    }
}


// File: contracts/compliance/ComplianceConfigurationService.sol
pragma solidity ^0.8.13;

import "./IDSComplianceConfigurationService.sol";
import "../data-stores/ComplianceConfigurationDataStore.sol";
import "../service/ServiceConsumer.sol";
import "../utils/ProxyTarget.sol";

//SPDX-License-Identifier: UNLICENSED
contract ComplianceConfigurationService is ProxyTarget, IDSComplianceConfigurationService, ServiceConsumer, ComplianceConfigurationDataStore {
    function initialize() public override(IDSComplianceConfigurationService, ServiceConsumer) initializer forceInitializeFromProxy {
        IDSComplianceConfigurationService.initialize();
        ServiceConsumer.initialize();
        VERSIONS.push(8);
    }

    function setCountriesCompliance(string[] memory _countries, uint256[] memory _values) public override onlyTransferAgentOrAbove {
        require(_countries.length <= 35, "Exceeded the maximum number of countries");
        require(_countries.length == _values.length, "Wrong length of parameters");
        for (uint i = 0; i < _countries.length; i++) {
            setCountryCompliance(_countries[i], _values[i]);
        }
    }

    function setCountryCompliance(string memory _country, uint256 _value) public override onlyTransferAgentOrAbove {
        emit DSComplianceStringToUIntMapRuleSet("countryCompliance", _country, countriesCompliances[_country], _value);
        countriesCompliances[_country] = _value;
    }

    function getCountryCompliance(string memory _country) public view override returns (uint256) {
        return countriesCompliances[_country];
    }

    function getTotalInvestorsLimit() public view override returns (uint256) {
        return totalInvestorsLimit;
    }

    function setTotalInvestorsLimit(uint256 _value) public override onlyTransferAgentOrAbove {
        emit DSComplianceUIntRuleSet("totalInvestorsLimit", totalInvestorsLimit, _value);
        totalInvestorsLimit = _value;
    }

    function getMinUSTokens() public view override returns (uint256) {
        return minUSTokens;
    }

    function setMinUSTokens(uint256 _value) public override onlyTransferAgentOrAbove {
        emit DSComplianceUIntRuleSet("minUSTokens", minUSTokens, _value);
        minUSTokens = _value;
    }

    function getMinEUTokens() public view override returns (uint256) {
        return minEUTokens;
    }

    function setMinEUTokens(uint256 _value) public override onlyTransferAgentOrAbove {
        emit DSComplianceUIntRuleSet("minEUTokens", minEUTokens, _value);
        minEUTokens = _value;
    }

    function getUSInvestorsLimit() public view override returns (uint256) {
        return usInvestorsLimit;
    }

    function setUSInvestorsLimit(uint256 _value) public override onlyTransferAgentOrAbove {
        emit DSComplianceUIntRuleSet("usInvestorsLimit", usInvestorsLimit, _value);
        usInvestorsLimit = _value;
    }

    function getJPInvestorsLimit() public view override returns (uint256) {
        return jpInvestorsLimit;
    }

    function setJPInvestorsLimit(uint256 _value) public override onlyTransferAgentOrAbove {
        emit DSComplianceUIntRuleSet("jpInvestorsLimit", jpInvestorsLimit, _value);
        jpInvestorsLimit = _value;
    }

    function getUSAccreditedInvestorsLimit() public view override returns (uint256) {
        return usAccreditedInvestorsLimit;
    }

    function setUSAccreditedInvestorsLimit(uint256 _value) public override onlyTransferAgentOrAbove {
        emit DSComplianceUIntRuleSet("usAccreditedInvestorsLimit", usAccreditedInvestorsLimit, _value);
        usAccreditedInvestorsLimit = _value;
    }

    function getNonAccreditedInvestorsLimit() public view override returns (uint256) {
        return nonAccreditedInvestorsLimit;
    }

    function setNonAccreditedInvestorsLimit(uint256 _value) public override onlyTransferAgentOrAbove {
        emit DSComplianceUIntRuleSet("nonAccreditedInvestorsLimit", nonAccreditedInvestorsLimit, _value);
        nonAccreditedInvestorsLimit = _value;
    }

    function getMaxUSInvestorsPercentage() public view override returns (uint256) {
        return maxUSInvestorsPercentage;
    }

    function setMaxUSInvestorsPercentage(uint256 _value) public override onlyTransferAgentOrAbove {
        emit DSComplianceUIntRuleSet("maxUSInvestorsPercentage", maxUSInvestorsPercentage, _value);
        maxUSInvestorsPercentage = _value;
    }

    function getBlockFlowbackEndTime() public view override returns (uint256) {
        return blockFlowbackEndTime;
    }

    function setBlockFlowbackEndTime(uint256 _value) public override onlyTransferAgentOrAbove {
        emit DSComplianceUIntRuleSet("blockFlowbackEndTime", blockFlowbackEndTime, _value);
        blockFlowbackEndTime = _value;
    }

    function getNonUSLockPeriod() public view override returns (uint256) {
        return nonUSLockPeriod;
    }

    function setNonUSLockPeriod(uint256 _value) public override onlyTransferAgentOrAbove {
        emit DSComplianceUIntRuleSet("nonUSLockPeriod", nonUSLockPeriod, _value);
        nonUSLockPeriod = _value;
    }

    function getMinimumTotalInvestors() public view override returns (uint256) {
        return minimumTotalInvestors;
    }

    function setMinimumTotalInvestors(uint256 _value) public override onlyTransferAgentOrAbove {
        emit DSComplianceUIntRuleSet("minimumTotalInvestors", minimumTotalInvestors, _value);
        minimumTotalInvestors = _value;
    }

    function getMinimumHoldingsPerInvestor() public view override returns (uint256) {
        return minimumHoldingsPerInvestor;
    }

    function setMinimumHoldingsPerInvestor(uint256 _value) public override onlyTransferAgentOrAbove {
        emit DSComplianceUIntRuleSet("minimumHoldingsPerInvestor", minimumHoldingsPerInvestor, _value);
        minimumHoldingsPerInvestor = _value;
    }

    function getMaximumHoldingsPerInvestor() public view override returns (uint256) {
        return maximumHoldingsPerInvestor;
    }

    function setMaximumHoldingsPerInvestor(uint256 _value) public override onlyTransferAgentOrAbove {
        emit DSComplianceUIntRuleSet("maximumHoldingsPerInvestor", maximumHoldingsPerInvestor, _value);
        maximumHoldingsPerInvestor = _value;
    }

    function getEURetailInvestorsLimit() public view override returns (uint256) {
        return euRetailInvestorsLimit;
    }

    function setEURetailInvestorsLimit(uint256 _value) public override onlyTransferAgentOrAbove {
        emit DSComplianceUIntRuleSet("euRetailInvestorsLimit", euRetailInvestorsLimit, _value);
        euRetailInvestorsLimit = _value;
    }

    function getUSLockPeriod() public view override returns (uint256) {
        return usLockPeriod;
    }

    function setUSLockPeriod(uint256 _value) public override onlyTransferAgentOrAbove {
        emit DSComplianceUIntRuleSet("usLockPeriod", usLockPeriod, _value);
        usLockPeriod = _value;
    }

    function getForceFullTransfer() public view override returns (bool) {
        return forceFullTransfer;
    }

    function setForceFullTransfer(bool _value) public override onlyTransferAgentOrAbove {
        emit DSComplianceBoolRuleSet("forceFullTransfer", forceFullTransfer, _value);
        forceFullTransfer = _value;
    }

    function getForceAccreditedUS() public view override returns (bool) {
        return forceAccreditedUS;
    }

    function setForceAccreditedUS(bool _value) public override onlyTransferAgentOrAbove {
        emit DSComplianceBoolRuleSet("forceAccreditedUS", forceAccreditedUS, _value);
        forceAccreditedUS = _value;
    }

    function getForceAccredited() public view override returns (bool) {
        return forceAccredited;
    }

    function setForceAccredited(bool _value) public override onlyTransferAgentOrAbove {
        emit DSComplianceBoolRuleSet("forceAccredited", forceAccredited, _value);
        forceAccredited = _value;
    }

    function getWorldWideForceFullTransfer() public view override returns (bool) {
        return worldWideForceFullTransfer;
    }

    function setWorldWideForceFullTransfer(bool _value) public override onlyTransferAgentOrAbove {
        emit DSComplianceBoolRuleSet("worldWideForceFullTransfer", worldWideForceFullTransfer, _value);
        worldWideForceFullTransfer = _value;
    }

    function getAuthorizedSecurities() public view override returns (uint256) {
        return authorizedSecurities;
    }

    function setAuthorizedSecurities(uint256 _value) public override onlyTransferAgentOrAbove {
        emit DSComplianceUIntRuleSet("authorizedSecurities", authorizedSecurities, _value);
        authorizedSecurities = _value;
    }

    function getDisallowBackDating() public view override returns (bool) {
        return disallowBackDating;
    }

    function setDisallowBackDating(bool _value) public override onlyTransferAgentOrAbove {
        emit DSComplianceBoolRuleSet("disallowBackDating", disallowBackDating, _value);
        disallowBackDating = _value;
    }

    function setAll(uint256[] memory _uint_values, bool[] memory _bool_values) public override onlyTransferAgentOrAbove {
        require(_uint_values.length == 16, "Wrong length of parameters");
        require(_bool_values.length == 5, "Wrong length of parameters");
        setTotalInvestorsLimit(_uint_values[0]);
        setMinUSTokens(_uint_values[1]);
        setMinEUTokens(_uint_values[2]);
        setUSInvestorsLimit(_uint_values[3]);
        setUSAccreditedInvestorsLimit(_uint_values[4]);
        setNonAccreditedInvestorsLimit(_uint_values[5]);
        setMaxUSInvestorsPercentage(_uint_values[6]);
        setBlockFlowbackEndTime(_uint_values[7]);
        setNonUSLockPeriod(_uint_values[8]);
        setMinimumTotalInvestors(_uint_values[9]);
        setMinimumHoldingsPerInvestor(_uint_values[10]);
        setMaximumHoldingsPerInvestor(_uint_values[11]);
        setEURetailInvestorsLimit(_uint_values[12]);
        setUSLockPeriod(_uint_values[13]);
        setJPInvestorsLimit(_uint_values[14]);
        setAuthorizedSecurities(_uint_values[15]);
        setForceFullTransfer(_bool_values[0]);
        setForceAccredited(_bool_values[1]);
        setForceAccreditedUS(_bool_values[2]);
        setWorldWideForceFullTransfer(_bool_values[3]);
        setDisallowBackDating(_bool_values[4]);
    }

    function getAll() public view override returns (uint256[] memory, bool[] memory) {
        uint256[] memory uintValues = new uint256[](16);
        bool[] memory boolValues = new bool[](5);

        uintValues[0] = getTotalInvestorsLimit();
        uintValues[1] = getMinUSTokens();
        uintValues[2] = getMinEUTokens();
        uintValues[3] = getUSInvestorsLimit();
        uintValues[4] = getUSAccreditedInvestorsLimit();
        uintValues[5] = getNonAccreditedInvestorsLimit();
        uintValues[6] = getMaxUSInvestorsPercentage();
        uintValues[7] = getBlockFlowbackEndTime();
        uintValues[8] = getNonUSLockPeriod();
        uintValues[9] = getMinimumTotalInvestors();
        uintValues[10] = getMinimumHoldingsPerInvestor();
        uintValues[11] = getMaximumHoldingsPerInvestor();
        uintValues[12] = getEURetailInvestorsLimit();
        uintValues[13] = getUSLockPeriod();
        uintValues[14] = getJPInvestorsLimit();
        uintValues[15] = getAuthorizedSecurities();
        boolValues[0] = getForceFullTransfer();
        boolValues[1] = getForceAccredited();
        boolValues[2] = getForceAccreditedUS();
        boolValues[3] = getWorldWideForceFullTransfer();
        boolValues[4] = getDisallowBackDating();
        return (uintValues, boolValues);
    }
}


// File: contracts/compliance/ComplianceService.sol
pragma solidity ^0.8.13;

import "../utils/ProxyTarget.sol";
import "./IDSComplianceService.sol";
import "../service/ServiceConsumer.sol";
import "../data-stores/ComplianceServiceDataStore.sol";

/**
 *   @title Compliance service main implementation.
 *
 *   Combines the different implementation files for the compliance service and serves as a base class for
 *   concrete implementation.
 *
 *   To create a concrete implementation of a compliance service, one should inherit from this contract,
 *   and implement the five functions - recordIssuance,checkTransfer,recordTransfer,recordBurn and recordSeize.
 *   The rest of the functions should only be overridden in rare circumstances.
 */
//SPDX-License-Identifier: UNLICENSED
abstract contract ComplianceService is ProxyTarget, Initializable, IDSComplianceService, ServiceConsumer, ComplianceServiceDataStore {
    function initialize() public virtual override(IDSComplianceService, ServiceConsumer) forceInitializeFromProxy {
        IDSComplianceService.initialize();
        ServiceConsumer.initialize();
        VERSIONS.push(7);
    }

    function validateTransfer(
        address _from,
        address _to,
        uint256 _value
    ) public override onlyToken returns (bool) {
        uint256 code;
        string memory reason;

        (code, reason) = preTransferCheck(_from, _to, _value);
        require(code == 0, reason);

        return recordTransfer(_from, _to, _value);
    }

    function validateTransfer(
        address _from,
        address _to,
        uint256 _value,
        bool _paused,
        uint256 _balanceFrom
    ) public virtual override onlyToken returns (bool) {
        uint256 code;
        string memory reason;

        (code, reason) = newPreTransferCheck(_from, _to, _value, _balanceFrom, _paused);
        require(code == 0, reason);

        return recordTransfer(_from, _to, _value);
    }

    function validateIssuance(
        address _to,
        uint256 _value,
        uint256 _issuanceTime
    ) public override onlyToken returns (bool) {
        uint256 code;
        string memory reason;

        uint256 authorizedSecurities = getComplianceConfigurationService().getAuthorizedSecurities();

        require(authorizedSecurities == 0 || getToken().totalSupply() + _value <= authorizedSecurities,
            MAX_AUTHORIZED_SECURITIES_EXCEEDED);

        (code, reason) = preIssuanceCheck(_to, _value);
        require(code == 0, reason);

        uint256 issuanceTime = validateIssuanceTime(_issuanceTime);
        return recordIssuance(_to, _value, issuanceTime);
    }

    function validateIssuanceWithNoCompliance(
        address _to,
        uint256 _value,
        uint256 _issuanceTime
    ) public override onlyToken returns (bool) {
        uint256 authorizedSecurities = getComplianceConfigurationService().getAuthorizedSecurities();

        require(authorizedSecurities == 0 || getToken().totalSupply() + _value <= authorizedSecurities,
            MAX_AUTHORIZED_SECURITIES_EXCEEDED);

        uint256 issuanceTime = validateIssuanceTime(_issuanceTime);
        return recordIssuance(_to, _value, issuanceTime);
    }

    function validateBurn(address _who, uint256 _value) public virtual override onlyToken returns (bool) {
        return recordBurn(_who, _value);
    }

    function validateSeize(
        address _from,
        address _to,
        uint256 _value
    ) public virtual override onlyToken returns (bool) {
        require(getWalletManager().isIssuerSpecialWallet(_to), "Target wallet type error");

        return recordSeize(_from, _to, _value);
    }

    /**
     * @dev Verify disallowBackDating compliance: if set to false returns _issuanceTime parameter, otherwise returns current timestamp
     * @param _issuanceTime.
     * @return issuanceTime
     */
    function validateIssuanceTime(uint256 _issuanceTime) public view override returns (uint256 issuanceTime) {
        if (!getComplianceConfigurationService().getDisallowBackDating()) {
            return _issuanceTime;
        }
        return block.timestamp;
    }

    function newPreTransferCheck(
        address _from,
        address _to,
        uint256 _value,
        uint256 _balanceFrom,
        bool _pausedToken
    ) public view virtual returns (uint256 code, string memory reason) {
        if (_pausedToken) {
            return (10, TOKEN_PAUSED);
        }

        if (_balanceFrom < _value) {
            return (15, NOT_ENOUGH_TOKENS);
        }

        if (getLockManager().getTransferableTokens(_from, block.timestamp) < _value) {
            return (16, TOKENS_LOCKED);
        }

        return checkTransfer(_from, _to, _value);
    }

    function preTransferCheck(
        address _from,
        address _to,
        uint256 _value
    ) public view virtual override returns (uint256 code, string memory reason) {
        if (getToken().isPaused()) {
            return (10, TOKEN_PAUSED);
        }

        if (getToken().balanceOf(_from) < _value) {
            return (15, NOT_ENOUGH_TOKENS);
        }

        if (getLockManager().getTransferableTokens(_from, block.timestamp) < _value) {
            return (16, TOKENS_LOCKED);
        }

        return checkTransfer(_from, _to, _value);
    }

    function preInternalTransferCheck(
        address _from,
        address _to,
        uint256 _value
    ) public view virtual override returns (uint256 code, string memory reason) {
        if (getToken().isPaused()) {
            return (10, TOKEN_PAUSED);
        }

        return checkTransfer(_from, _to, _value);
    }

    function preIssuanceCheck(
        address, /*_to*/
        uint256 /*_value*/
    ) public view virtual override returns (uint256 code, string memory reason) {
        return (0, VALID);
    }

    function adjustInvestorCountsAfterCountryChange(
        string memory, /*_id*/
        string memory, /*_country*/
        string memory /*_prevCountry*/
    ) public virtual override returns (bool) {
        return true;
    }

    // These functions should be implemented by the concrete compliance manager
    function recordIssuance(
        address _to,
        uint256 _value,
        uint256 _issuanceTime
    ) internal virtual returns (bool);

    function recordTransfer(
        address _from,
        address _to,
        uint256 _value
    ) internal virtual returns (bool);

    function recordBurn(address _who, uint256 _value) internal virtual returns (bool);

    function recordSeize(
        address _from,
        address _to,
        uint256 _value
    ) internal virtual returns (bool);

    function checkTransfer(
        address _from,
        address _to,
        uint256 _value
    ) internal view virtual returns (uint256, string memory);
}


// File: contracts/compliance/ComplianceServiceRegulated.sol
pragma solidity ^0.8.13;

import "./ComplianceServiceWhitelisted.sol";
import "@openzeppelin/contracts/utils/math/SafeMath.sol";
import "@openzeppelin/contracts/utils/math/Math.sol";

library ComplianceServiceLibrary {
    uint256 internal constant DS_TOKEN = 0;
    uint256 internal constant REGISTRY_SERVICE = 1;
    uint256 internal constant WALLET_MANAGER = 2;
    uint256 internal constant COMPLIANCE_CONFIGURATION_SERVICE = 3;
    uint256 internal constant LOCK_MANAGER = 4;
    uint256 internal constant COMPLIANCE_SERVICE = 5;
    uint256 internal constant OMNIBUS_TBE_CONTROLLER = 6;
    uint256 internal constant NONE = 0;
    uint256 internal constant US = 1;
    uint256 internal constant EU = 2;
    uint256 internal constant FORBIDDEN = 4;
    uint256 internal constant JP = 8;
    string internal constant TOKEN_PAUSED = "Token paused";
    string internal constant NOT_ENOUGH_TOKENS = "Not enough tokens";
    string internal constant VALID = "Valid";
    string internal constant TOKENS_LOCKED = "Tokens locked";
    string internal constant ONLY_FULL_TRANSFER = "Only full transfer";
    string internal constant FLOWBACK = "Flowback";
    string internal constant WALLET_NOT_IN_REGISTRY_SERVICE = "Wallet not in registry service";
    string internal constant AMOUNT_OF_TOKENS_UNDER_MIN = "Amount of tokens under min";
    string internal constant AMOUNT_OF_TOKENS_ABOVE_MAX = "Amount of tokens above max";
    string internal constant HOLD_UP = "Under lock-up";
    string internal constant DESTINATION_RESTRICTED = "Destination restricted";
    string internal constant MAX_INVESTORS_IN_CATEGORY = "Max investors in category";
    string internal constant ONLY_ACCREDITED = "Only accredited";
    string internal constant ONLY_US_ACCREDITED = "Only us accredited";
    string internal constant NOT_ENOUGH_INVESTORS = "Not enough investors";

    struct CompletePreTransferCheckArgs {
        address from;
        address to;
        uint256 value;
        uint256 fromInvestorBalance;
        uint256 fromRegion;
        bool isPlatformWalletTo;
    }

    using SafeMath for uint256;

    function isRetail(address[] memory _services, address _wallet) internal view returns (bool) {
        IDSRegistryService registry = IDSRegistryService(_services[REGISTRY_SERVICE]);

        return !registry.isQualifiedInvestor(_wallet);
    }

    function isAccredited(address[] memory _services, address _wallet) internal view returns (bool) {
        IDSRegistryService registry = IDSRegistryService(_services[REGISTRY_SERVICE]);

        return registry.isAccreditedInvestor(_wallet);
    }

    function balanceOfInvestor(address[] memory _services, address _wallet) internal view returns (uint256) {
        IDSRegistryService registry = IDSRegistryService(_services[REGISTRY_SERVICE]);
        IDSToken token = IDSToken(_services[DS_TOKEN]);

        return token.balanceOfInvestor(registry.getInvestor(_wallet));
    }

    function isNewInvestor(address[] memory _services, address _to, uint256 _balanceOfInvestorTo) internal view returns (bool) {
        IDSOmnibusTBEController omnibusTBEController = IDSOmnibusTBEController(_services[OMNIBUS_TBE_CONTROLLER]);

        // Return whether this investor has 0 balance and is not an omnibus TBE wallet
        return _balanceOfInvestorTo == 0 && !isOmnibusTBE(omnibusTBEController, _to);
    }

    function getCountry(address[] memory _services, address _wallet) internal view returns (string memory) {
        IDSRegistryService registry = IDSRegistryService(_services[REGISTRY_SERVICE]);

        return registry.getCountry(registry.getInvestor(_wallet));
    }

    function getCountryCompliance(address[] memory _services, address _wallet) internal view returns (uint256) {
        return IDSComplianceConfigurationService(_services[COMPLIANCE_CONFIGURATION_SERVICE]).getCountryCompliance(getCountry(_services, _wallet));
    }

    function getUSInvestorsLimit(address[] memory _services) internal view returns (uint256) {
        ComplianceServiceRegulated complianceService = ComplianceServiceRegulated(_services[COMPLIANCE_SERVICE]);
        IDSComplianceConfigurationService compConfService = IDSComplianceConfigurationService(_services[COMPLIANCE_CONFIGURATION_SERVICE]);

        if (compConfService.getMaxUSInvestorsPercentage() == 0) {
            return compConfService.getUSInvestorsLimit();
        }

        if (compConfService.getUSInvestorsLimit() == 0) {
            return compConfService.getMaxUSInvestorsPercentage().mul(complianceService.getTotalInvestorsCount()).div(100);
        }

        return Math.min(compConfService.getUSInvestorsLimit(), compConfService.getMaxUSInvestorsPercentage().mul(complianceService.getTotalInvestorsCount()).div(100));
    }

    function isOmnibusTBE(IDSOmnibusTBEController _omnibusTBE, address _from) public view returns (bool) {
        if (address(_omnibusTBE) != address(0)) {
            return _omnibusTBE.getOmnibusWallet() == _from;
        }
        return false;
    }

    function checkHoldUp(
        address[] memory _services,
        address _from,
        uint256 _value,
        bool _isUSLockPeriod,
        bool _isPlatformWalletFrom
    ) internal view returns (bool) {
        ComplianceServiceRegulated complianceService = ComplianceServiceRegulated(_services[COMPLIANCE_SERVICE]);
        uint64 lockPeriod;
        if (_isUSLockPeriod) {
            lockPeriod = uint64(IDSComplianceConfigurationService(_services[COMPLIANCE_CONFIGURATION_SERVICE]).getUSLockPeriod());
        } else {
            lockPeriod = uint64(IDSComplianceConfigurationService(_services[COMPLIANCE_CONFIGURATION_SERVICE]).getNonUSLockPeriod());
        }

        return
        !_isPlatformWalletFrom &&
        complianceService.getComplianceTransferableTokens(_from, block.timestamp, lockPeriod) < _value;
    }

    function maxInvestorsInCategoryForNonAccredited(
        address[] memory _services,
        address _from,
        address _to,
        uint256 _value,
        uint256 fromInvestorBalance,
        uint256 toInvestorBalance
    ) internal view returns (bool) {
        uint256 nonAccreditedInvestorLimit = IDSComplianceConfigurationService(_services[COMPLIANCE_CONFIGURATION_SERVICE]).getNonAccreditedInvestorsLimit();
        return
        nonAccreditedInvestorLimit != 0 &&
        ComplianceServiceRegulated(_services[COMPLIANCE_SERVICE]).getTotalInvestorsCount() -
            ComplianceServiceRegulated(_services[COMPLIANCE_SERVICE]).getAccreditedInvestorsCount()
        >=
        nonAccreditedInvestorLimit &&
        isNewInvestor(_services, _to, toInvestorBalance) &&
        (isAccredited(_services, _from) || fromInvestorBalance > _value);
    }

    function newPreTransferCheck(
        address[] memory _services,
        address _from,
        address _to,
        uint256 _value,
        uint256 _balanceFrom,
        bool _paused
    ) public view returns (uint256 code, string memory reason) {
        return doPreTransferCheckRegulated
        (_services, _from, _to, _value, _balanceFrom, _paused);
    }

    function preTransferCheck(
        address[] memory _services,
        address _from,
        address _to,
        uint256 _value
    ) public view returns (uint256 code, string memory reason) {
        return doPreTransferCheckRegulated(_services, _from, _to, _value, IDSToken(_services[DS_TOKEN]).balanceOf(_from), IDSToken(_services[DS_TOKEN]).isPaused());
    }

    function doPreTransferCheckRegulated(
        address[] memory _services,
        address _from,
        address _to,
        uint256 _value,
        uint256 _balanceFrom,
        bool _paused
    ) internal view returns (uint256 code, string memory reason) {

        if (_balanceFrom < _value) {
            return (15, NOT_ENOUGH_TOKENS);
        }

        uint256 fromInvestorBalance = balanceOfInvestor(_services, _from);
        uint256 fromRegion = getCountryCompliance(_services, _from);
        bool isPlatformWalletTo = IDSWalletManager(_services[WALLET_MANAGER]).isPlatformWallet(_to);
        if (isPlatformWalletTo) {
            if (
                ((IDSComplianceConfigurationService(_services[COMPLIANCE_CONFIGURATION_SERVICE]).getForceFullTransfer()
                && (fromRegion == US)) ||
                IDSComplianceConfigurationService(_services[COMPLIANCE_CONFIGURATION_SERVICE]).getWorldWideForceFullTransfer()) &&
                fromInvestorBalance > _value
            ) {
                return (50, ONLY_FULL_TRANSFER);
            }
            return (0, VALID);
        }

        if (_paused && !(isOmnibusTBE(IDSOmnibusTBEController(_services[OMNIBUS_TBE_CONTROLLER]), _from))) {
            return (10, TOKEN_PAUSED);
        }

        CompletePreTransferCheckArgs memory args = CompletePreTransferCheckArgs(_from, _to, _value, fromInvestorBalance, fromRegion, isPlatformWalletTo);
        return completeTransferCheck(_services, args);
    }

    function completeTransferCheck(
        address[] memory _services,
        CompletePreTransferCheckArgs memory _args
    ) internal view returns (uint256 code, string memory reason) {
        (string memory investorFrom, string memory investorTo) = IDSRegistryService(_services[REGISTRY_SERVICE]).getInvestors(_args.from, _args.to);
        if (
            !CommonUtils.isEmptyString(investorFrom) && CommonUtils.isEqualString(investorFrom, investorTo)
        ) {
            return (0, VALID);
        }

        if (!ComplianceServiceRegulated(_services[COMPLIANCE_SERVICE]).checkWhitelisted(_args.to)) {
            return (20, WALLET_NOT_IN_REGISTRY_SERVICE);
        }

        uint256 toRegion = getCountryCompliance(_services, _args.to);
        if (toRegion == FORBIDDEN) {
            return (26, DESTINATION_RESTRICTED);
        }

        if (isOmnibusTBE(IDSOmnibusTBEController(_services[OMNIBUS_TBE_CONTROLLER]), _args.from)) {
            return(0, VALID);
        }

        bool isPlatformWalletFrom = IDSWalletManager(_services[WALLET_MANAGER]).isPlatformWallet(_args.from);
        if (
            !isPlatformWalletFrom &&
        IDSLockManager(_services[LOCK_MANAGER]).getTransferableTokens(_args.from, block.timestamp) < _args.value
        ) {
            return (16, TOKENS_LOCKED);
        }

        if (_args.fromRegion == US) {
            if (checkHoldUp(_services, _args.from, _args.value, true, isPlatformWalletFrom)) {
                return (32, HOLD_UP);
            }

            if (
                _args.fromInvestorBalance > _args.value &&
                _args.fromInvestorBalance - _args.value < IDSComplianceConfigurationService(_services[COMPLIANCE_CONFIGURATION_SERVICE]).getMinUSTokens()
            ) {
                return (51, AMOUNT_OF_TOKENS_UNDER_MIN);
            }

            if (
                IDSComplianceConfigurationService(_services[COMPLIANCE_CONFIGURATION_SERVICE]).getForceFullTransfer() &&
                _args.fromInvestorBalance > _args.value
            ) {
                return (50, ONLY_FULL_TRANSFER);
            }
        } else {
            if (checkHoldUp(_services, _args.from, _args.value, false, isPlatformWalletFrom)) {
                return (33, HOLD_UP);
            }

            if (
                toRegion == US &&
                !isPlatformWalletFrom &&
                isBlockFlowbackEndTimeOk(IDSComplianceConfigurationService(_services[COMPLIANCE_CONFIGURATION_SERVICE]).getBlockFlowbackEndTime())
            ) {
                return (25, FLOWBACK);
            }

            if (
                IDSComplianceConfigurationService(_services[COMPLIANCE_CONFIGURATION_SERVICE]).getWorldWideForceFullTransfer() &&
                _args.fromInvestorBalance > _args.value
            ) {
                return (50, ONLY_FULL_TRANSFER);
            }
        }

        uint256 toInvestorBalance = balanceOfInvestor(_services, _args.to);
        string memory toCountry = getCountry(_services, _args.to);

        if (_args.fromRegion == EU) {
            if (_args.fromInvestorBalance - _args.value < IDSComplianceConfigurationService(_services[COMPLIANCE_CONFIGURATION_SERVICE]).getMinEUTokens() &&
                _args.fromInvestorBalance > _args.value) {
                return (51, AMOUNT_OF_TOKENS_UNDER_MIN);
            }
        }

        bool isAccreditedTo = isAccredited(_services, _args.to);
        if (
            IDSComplianceConfigurationService(_services[COMPLIANCE_CONFIGURATION_SERVICE]).getForceAccredited() && !isAccreditedTo
        ) {
            return (61, ONLY_ACCREDITED);
        }

        if (toRegion == JP) {
            if (
                IDSComplianceConfigurationService(_services[COMPLIANCE_CONFIGURATION_SERVICE]).getJPInvestorsLimit() != 0 &&
                ComplianceServiceRegulated(_services[COMPLIANCE_SERVICE]).getJPInvestorsCount() >=
                IDSComplianceConfigurationService(_services[COMPLIANCE_CONFIGURATION_SERVICE]).getJPInvestorsLimit() &&
                isNewInvestor(_services, _args.to, toInvestorBalance) &&
                (!CommonUtils.isEqualString(getCountry(_services, _args.from), toCountry) || (_args.fromInvestorBalance > _args.value))
            ) {
                return (40, MAX_INVESTORS_IN_CATEGORY);
            }
        } else if (toRegion == EU) {
            if (
                isRetail(_services, _args.to) &&
                ComplianceServiceRegulated(_services[COMPLIANCE_SERVICE]).getEURetailInvestorsCount(toCountry) >=
                IDSComplianceConfigurationService(_services[COMPLIANCE_CONFIGURATION_SERVICE]).getEURetailInvestorsLimit() &&
                isNewInvestor(_services, _args.to, toInvestorBalance) &&
                (!CommonUtils.isEqualString(getCountry(_services, _args.from), toCountry) ||
                (_args.fromInvestorBalance > _args.value && isRetail(_services, _args.from)))
            ) {
                return (40, MAX_INVESTORS_IN_CATEGORY);
            }

            if (
                toInvestorBalance + _args.value < IDSComplianceConfigurationService(_services[COMPLIANCE_CONFIGURATION_SERVICE]).getMinEUTokens()
            ) {
                return (51, AMOUNT_OF_TOKENS_UNDER_MIN);
            }
        } else if (toRegion == US) {
            if (
                IDSComplianceConfigurationService(_services[COMPLIANCE_CONFIGURATION_SERVICE]).getForceAccreditedUS() &&
                !isAccreditedTo
            ) {
                return (62, ONLY_US_ACCREDITED);
            }

            uint256 usInvestorsLimit = getUSInvestorsLimit(_services);
            if (
                usInvestorsLimit != 0 &&
                _args.fromInvestorBalance > _args.value &&
                ComplianceServiceRegulated(_services[COMPLIANCE_SERVICE]).getUSInvestorsCount() >= usInvestorsLimit &&
                isNewInvestor(_services, _args.to, toInvestorBalance)
            ) {
                return (40, MAX_INVESTORS_IN_CATEGORY);
            }

            if (
                IDSComplianceConfigurationService(_services[COMPLIANCE_CONFIGURATION_SERVICE]).getUSAccreditedInvestorsLimit() != 0 &&
                isAccreditedTo &&
                ComplianceServiceRegulated(_services[COMPLIANCE_SERVICE]).getUSAccreditedInvestorsCount() >=
                IDSComplianceConfigurationService(_services[COMPLIANCE_CONFIGURATION_SERVICE]).getUSAccreditedInvestorsLimit() &&
                isNewInvestor(_services, _args.to, toInvestorBalance) &&
                (_args.fromRegion != US || !isAccredited(_services, _args.from) || _args.fromInvestorBalance > _args.value)
            ) {
                return (40, MAX_INVESTORS_IN_CATEGORY);
            }

            if (
                toInvestorBalance + _args.value < IDSComplianceConfigurationService(_services[COMPLIANCE_CONFIGURATION_SERVICE]).getMinUSTokens()
            ) {
                return (51, AMOUNT_OF_TOKENS_UNDER_MIN);
            }
        }

        if (!isAccreditedTo) {
            if (maxInvestorsInCategoryForNonAccredited(_services, _args.from, _args.to, _args.value, _args.fromInvestorBalance, toInvestorBalance)) {
                return (40, MAX_INVESTORS_IN_CATEGORY);
            }
        }

        if (
            IDSComplianceConfigurationService(_services[COMPLIANCE_CONFIGURATION_SERVICE]).getTotalInvestorsLimit() != 0 &&
            _args.fromInvestorBalance > _args.value &&
            ComplianceServiceRegulated(_services[COMPLIANCE_SERVICE]).getTotalInvestorsCount() >=
            IDSComplianceConfigurationService(_services[COMPLIANCE_CONFIGURATION_SERVICE]).getTotalInvestorsLimit() &&
            isNewInvestor(_services, _args.to, toInvestorBalance)
        ) {
            return (40, MAX_INVESTORS_IN_CATEGORY);
        }

        if (
            _args.fromInvestorBalance == _args.value &&
            !isNewInvestor(_services, _args.to, toInvestorBalance) &&
            ComplianceServiceRegulated(_services[COMPLIANCE_SERVICE]).getTotalInvestorsCount() <=
            IDSComplianceConfigurationService(_services[COMPLIANCE_CONFIGURATION_SERVICE]).getMinimumTotalInvestors()
        ) {
            return (71, NOT_ENOUGH_INVESTORS);
        }

        if (
            !isPlatformWalletFrom &&
        _args.fromInvestorBalance - _args.value < IDSComplianceConfigurationService(_services[COMPLIANCE_CONFIGURATION_SERVICE]).getMinimumHoldingsPerInvestor() &&
        _args.fromInvestorBalance > _args.value
        ) {
            return (51, AMOUNT_OF_TOKENS_UNDER_MIN);
        }

        if (
            !_args.isPlatformWalletTo &&
        toInvestorBalance + _args.value < IDSComplianceConfigurationService(_services[COMPLIANCE_CONFIGURATION_SERVICE]).getMinimumHoldingsPerInvestor()
        ) {
            return (51, AMOUNT_OF_TOKENS_UNDER_MIN);
        }

        if (
            isMaximumHoldingsPerInvestorOk(
                IDSComplianceConfigurationService(_services[COMPLIANCE_CONFIGURATION_SERVICE]).getMaximumHoldingsPerInvestor(),
                toInvestorBalance, _args.value)
        ) {
            return (52, AMOUNT_OF_TOKENS_ABOVE_MAX);
        }

        return (0, VALID);
    }


    function preIssuanceCheck(
        address[] memory _services,
        address _to,
        uint256 _value
    ) public view returns (uint256 code, string memory reason) {
        ComplianceServiceRegulated complianceService = ComplianceServiceRegulated(_services[COMPLIANCE_SERVICE]);
        IDSComplianceConfigurationService complianceConfigurationService = IDSComplianceConfigurationService(_services[COMPLIANCE_CONFIGURATION_SERVICE]);
        IDSWalletManager walletManager = IDSWalletManager(_services[WALLET_MANAGER]);
        string memory toCountry = IDSRegistryService(_services[REGISTRY_SERVICE]).getCountry(IDSRegistryService(_services[REGISTRY_SERVICE]).getInvestor(_to));
        uint256 toRegion = complianceConfigurationService.getCountryCompliance(toCountry);

        if (toRegion == FORBIDDEN) {
            return (26, DESTINATION_RESTRICTED);
        }

        if (!complianceService.checkWhitelisted(_to)) {
            return (20, WALLET_NOT_IN_REGISTRY_SERVICE);
        }

        uint256 balanceOfInvestorTo = balanceOfInvestor(_services, _to);
        if (isNewInvestor(_services, _to, balanceOfInvestorTo)) {
            // verify global non accredited limit
            if (!isAccredited(_services, _to)) {
                if (
                    complianceConfigurationService.getNonAccreditedInvestorsLimit() != 0 &&
                    complianceService.getTotalInvestorsCount() - complianceService.getAccreditedInvestorsCount() >=
                    complianceConfigurationService.getNonAccreditedInvestorsLimit()
                ) {
                    return (40, MAX_INVESTORS_IN_CATEGORY);
                }
            }
            // verify global investors limit
            if (
                complianceConfigurationService.getTotalInvestorsLimit() != 0 &&
                complianceService.getTotalInvestorsCount() >= complianceConfigurationService.getTotalInvestorsLimit()
            ) {
                return (40, MAX_INVESTORS_IN_CATEGORY);
            }

            if (toRegion == US) {
                // verify US investors limit is not exceeded
                if (complianceConfigurationService.getUSInvestorsLimit() != 0 && complianceService.getUSInvestorsCount() >= complianceConfigurationService.getUSInvestorsLimit()) {
                    return (40, MAX_INVESTORS_IN_CATEGORY);
                }
                // verify accredited US limit is not exceeded
                if (
                    complianceConfigurationService.getUSAccreditedInvestorsLimit() != 0 &&
                    isAccredited(_services, _to) &&
                    complianceService.getUSAccreditedInvestorsCount() >= complianceConfigurationService.getUSAccreditedInvestorsLimit()
                ) {
                    return (40, MAX_INVESTORS_IN_CATEGORY);
                }
            } else if (toRegion == EU) {
                if (
                    isRetail(_services, _to) &&
                    complianceService.getEURetailInvestorsCount(getCountry(_services, _to)) >= complianceConfigurationService.getEURetailInvestorsLimit()
                ) {
                    return (40, MAX_INVESTORS_IN_CATEGORY);
                }
            } else if (toRegion == JP) {
                if (complianceConfigurationService.getJPInvestorsLimit() != 0 && complianceService.getJPInvestorsCount() >= complianceConfigurationService.getJPInvestorsLimit()) {
                    return (40, MAX_INVESTORS_IN_CATEGORY);
                }
            }
        }

        if (
            !walletManager.isPlatformWallet(_to) &&
        balanceOfInvestorTo + _value < complianceConfigurationService.getMinimumHoldingsPerInvestor()
        ) {
            return (51, AMOUNT_OF_TOKENS_UNDER_MIN);
        }
        if (isMaximumHoldingsPerInvestorOk(
                complianceConfigurationService.getMaximumHoldingsPerInvestor(),
                balanceOfInvestorTo,
                _value)
        ) {
            return (52, AMOUNT_OF_TOKENS_ABOVE_MAX);
        }

        return (0, VALID);
    }

    function isMaximumHoldingsPerInvestorOk(uint256 _maximumHoldingsPerInvestor, uint256 _balanceOfInvestorTo, uint256 _value) internal pure returns (bool) {
        return _maximumHoldingsPerInvestor != 0 && _balanceOfInvestorTo + _value > _maximumHoldingsPerInvestor;
    }

    function isBlockFlowbackEndTimeOk(uint256 _blockFlowBackEndTime) private view returns (bool){
        return  (_blockFlowBackEndTime == 0 || _blockFlowBackEndTime > block.timestamp);
    }
}

/**
 *   @title Concrete compliance service for tokens with regulation
 *
 */
//SPDX-License-Identifier: UNLICENSED
contract ComplianceServiceRegulated is ComplianceServiceWhitelisted {
    function initialize() public virtual override initializer forceInitializeFromProxy {
        super.initialize();
        VERSIONS.push(13);
    }

    function compareInvestorBalance(
        address _who,
        uint256 _value,
        uint256 _compareTo
    ) internal view returns (bool) {
        return (_value != 0 && getToken().balanceOfInvestor(getRegistryService().getInvestor(_who)) == _compareTo);
    }

    function recordTransfer(
        address _from,
        address _to,
        uint256 _value
    ) internal override returns (bool) {
        if (!(ComplianceServiceLibrary.isOmnibusTBE(getOmnibusTBEController(), _from) ||
        ComplianceServiceLibrary.isOmnibusTBE(getOmnibusTBEController(), _to))) {
            if (compareInvestorBalance(_to, _value, 0)) {
                adjustTransferCounts(_to, CommonUtils.IncDec.Increase);
            }
        }

        return true;
    }

    function adjustTransferCounts(
        address _from,
        CommonUtils.IncDec _increase
    ) internal {
        adjustTotalInvestorsCounts(_from, _increase);
    }

    function recordIssuance(
        address _to,
        uint256 _value,
        uint256 _issuanceTime
    ) internal override returns (bool) {
        if (compareInvestorBalance(_to, _value, 0)) {
            adjustTotalInvestorsCounts(_to, CommonUtils.IncDec.Increase);
        }

        return createIssuanceInformation(getRegistryService().getInvestor(_to), _value, _issuanceTime);
    }

    function recordBurn(address /*_who*/, uint256 /*_value*/) internal pure override returns (bool) {
        return true;
    }

    function recordSeize(
        address _from,
        address, /*_to*/
        uint256 _value
    ) internal pure override returns (bool) {
        return recordBurn(_from, _value);
    }

    function adjustInvestorCountsAfterCountryChange(
        string memory _id,
        string memory _country,
        string memory /*_prevCountry*/
    ) public override onlyRegistry returns (bool) {
        if (getToken().balanceOfInvestor(_id) == 0) {
            return false;
        }

        adjustInvestorsCountsByCountry(_country, _id, CommonUtils.IncDec.Increase);

        return true;
    }

    function adjustTotalInvestorsCounts(address _wallet, CommonUtils.IncDec _increase) internal {
        if (!getWalletManager().isSpecialWallet(_wallet)) {
            if (_increase == CommonUtils.IncDec.Increase) {
                totalInvestors++;
            }

            string memory id = getRegistryService().getInvestor(_wallet);
            string memory country = getRegistryService().getCountry(id);

            adjustInvestorsCountsByCountry(country, id, _increase);
        }
    }

    function adjustInvestorsCountsByCountry(
        string memory _country,
        string memory _id,
        CommonUtils.IncDec _increase
    ) internal {
        uint256 countryCompliance = getComplianceConfigurationService().getCountryCompliance(_country);

        if (getRegistryService().isAccreditedInvestor(_id)) {
            if(_increase == CommonUtils.IncDec.Increase) {
                accreditedInvestorsCount++;
            }
            if (countryCompliance == US) {
                if(_increase == CommonUtils.IncDec.Increase) {
                    usAccreditedInvestorsCount++;
                }
            }
        }

        if (countryCompliance == US) {
            if(_increase == CommonUtils.IncDec.Increase) {
                usInvestorsCount++;
            }
        } else if (countryCompliance == EU && !getRegistryService().isQualifiedInvestor(_id)) {
            if(_increase == CommonUtils.IncDec.Increase) {
                euRetailInvestorsCount[_country]++;
            }
        } else if (countryCompliance == JP) {
            if(_increase == CommonUtils.IncDec.Increase) {
                jpInvestorsCount++;
            }
        }
    }

    function createIssuanceInformation(
        string memory _investor,
        uint256 _value,
        uint256 _issuanceTime
    ) internal returns (bool) {
        uint256 issuancesCount = issuancesCounters[_investor];

        issuancesValues[_investor][issuancesCount] = _value;
        issuancesTimestamps[_investor][issuancesCount] = _issuanceTime;
        issuancesCounters[_investor] = issuancesCount + 1;

        return true;
    }

    function preTransferCheck(
        address _from,
        address _to,
        uint256 _value
    ) public view virtual override returns (uint256 code, string memory reason) {
        return ComplianceServiceLibrary.preTransferCheck(getServices(), _from, _to, _value);
    }

    function newPreTransferCheck(
        address _from,
        address _to,
        uint256 _value,
        uint256 _balanceFrom,
        bool _pausedToken
    ) public view virtual override returns (uint256 code, string memory reason) {
        return ComplianceServiceLibrary.newPreTransferCheck(getServices(), _from, _to, _value, _balanceFrom, _pausedToken);
    }

    function preInternalTransferCheck(
        address _from,
        address _to,
        uint256 _value)
    public view override returns (uint256 code, string memory reason) {
        return ComplianceServiceLibrary.preTransferCheck(getServices(), _from, _to, _value);
    }

    function getComplianceTransferableTokens(
        address _who,
        uint256 _time,
        uint64 _lockTime
    ) public view returns (uint256) {
        require(_time != 0, "Time must be greater than zero");
        string memory investor = getRegistryService().getInvestor(_who);

        uint256 balanceOfInvestor = getLockManager().getTransferableTokens(_who, _time);

        uint256 investorIssuancesCount = issuancesCounters[investor];

        //No locks, go to base class implementation
        if (investorIssuancesCount == 0) {
            return balanceOfInvestor;
        }

        uint256 totalLockedTokens = 0;
        for (uint256 i = 0; i < investorIssuancesCount; i++) {
            uint256 issuanceTimestamp = issuancesTimestamps[investor][i];

            if (_lockTime > _time || issuanceTimestamp > SafeMath.sub(_time, _lockTime)) {
                totalLockedTokens = totalLockedTokens + issuancesValues[investor][i];
            }
        }

        //there may be more locked tokens than actual tokens, so the minimum between the two
        uint256 transferable = SafeMath.sub(balanceOfInvestor, Math.min(totalLockedTokens, balanceOfInvestor));

        return transferable;
    }

    function preIssuanceCheck(address _to, uint256 _value) public view override returns (uint256 code, string memory reason) {
        return ComplianceServiceLibrary.preIssuanceCheck(getServices(), _to, _value);
    }

    function getTotalInvestorsCount() public view returns (uint256) {
        return totalInvestors;
    }

    function getUSInvestorsCount() public view returns (uint256) {
        return usInvestorsCount;
    }

    function getUSAccreditedInvestorsCount() public view returns (uint256) {
        return usAccreditedInvestorsCount;
    }

    function getAccreditedInvestorsCount() public view returns (uint256) {
        return accreditedInvestorsCount;
    }

    function getEURetailInvestorsCount(string memory _country) public view returns (uint256) {
        return euRetailInvestorsCount[_country];
    }

    function getJPInvestorsCount() public view returns (uint256) {
        return jpInvestorsCount;
    }

    function setTotalInvestorsCount(uint256 _value) public onlyMasterOrTBEOmnibus returns (bool) {
        totalInvestors = _value;

        return true;
    }

    function setUSInvestorsCount(uint256 _value) public onlyMasterOrTBEOmnibus returns (bool) {
        usInvestorsCount = _value;

        return true;
    }

    function setUSAccreditedInvestorsCount(uint256 _value) public onlyMasterOrTBEOmnibus returns (bool) {
        usAccreditedInvestorsCount = _value;

        return true;
    }

    function setAccreditedInvestorsCount(uint256 _value) public onlyMasterOrTBEOmnibus returns (bool) {
        accreditedInvestorsCount = _value;

        return true;
    }

    function setEURetailInvestorsCount(string memory _country, uint256 _value) public onlyMasterOrTBEOmnibus returns (bool) {
        euRetailInvestorsCount[_country] = _value;

        return true;
    }

    function setJPInvestorsCount(uint256 _value) public onlyMasterOrTBEOmnibus returns (bool) {
        jpInvestorsCount = _value;

        return true;
    }

    function getServices() internal view returns (address[] memory services) {
        services = new address[](7);
        services[0] = getDSService(DS_TOKEN);
        services[1] = getDSService(REGISTRY_SERVICE);
        services[2] = getDSService(WALLET_MANAGER);
        services[3] = getDSService(COMPLIANCE_CONFIGURATION_SERVICE);
        services[4] = getDSService(LOCK_MANAGER);
        services[5] = address(this);
        services[6] = getDSService(OMNIBUS_TBE_CONTROLLER);
    }
}


// File: contracts/compliance/ComplianceServiceWhitelisted.sol
pragma solidity ^0.8.13;

import "./ComplianceService.sol";
import "../registry/IDSRegistryService.sol";

/**
*   @title Concrete compliance service for tokens with whitelisted wallets.
*
*   This simple compliance service is meant to be used for tokens that only need to be validated against an investor registry.
*/
//SPDX-License-Identifier: UNLICENSED
contract ComplianceServiceWhitelisted is ComplianceService {
    function initialize() public virtual override initializer forceInitializeFromProxy {
        ComplianceService.initialize();
        VERSIONS.push(5);
    }
    function newPreTransferCheck(
        address _from,
        address _to,
        uint256 _value,
        uint256 _balanceFrom,
        bool _pausedToken
    ) public view virtual override returns (uint256 code, string memory reason) {
        return doPreTransferCheckWhitelisted(_from, _to, _value, _balanceFrom, _pausedToken);
    }

    function preTransferCheck(
        address _from,
        address _to,
        uint256 _value
    ) public view virtual override returns (uint256 code, string memory reason) {
        return doPreTransferCheckWhitelisted(_from, _to, _value, getToken().balanceOf(_from), getToken().isPaused());
    }

    function checkWhitelisted(address _who) public view returns (bool) {
        return getWalletManager().isPlatformWallet(_who) || !CommonUtils.isEmptyString(getRegistryService().getInvestor(_who));
    }

    function recordIssuance(address, uint256, uint256) internal virtual override returns (bool) {
        return true;
    }

    function recordTransfer(address, address, uint256) internal virtual override returns (bool) {
        return true;
    }

    function checkTransfer(address, address _to, uint256) internal view override returns (uint256, string memory) {
        if (!checkWhitelisted(_to)) {
            return (20, WALLET_NOT_IN_REGISTRY_SERVICE);
        }

        return (0, VALID);
    }

    function preIssuanceCheck(address _to, uint256) public view virtual override returns (uint256, string memory) {
        if (!checkWhitelisted(_to)) {
            return (20, WALLET_NOT_IN_REGISTRY_SERVICE);
        }

        return (0, VALID);
    }

    function recordBurn(address, uint256) internal virtual override returns (bool) {
        return true;
    }

    function recordSeize(address, address, uint256) internal virtual override returns (bool) {
        return true;
    }

    function doPreTransferCheckWhitelisted(
        address _from,
        address _to,
        uint256 _value,
        uint256 _balanceFrom,
        bool _pausedToken
    ) internal view returns (uint256 code, string memory reason) {
        if (_pausedToken) {
            return (10, TOKEN_PAUSED);
        }

        if (_balanceFrom < _value) {
            return (15, NOT_ENOUGH_TOKENS);
        }

        if (!getWalletManager().isPlatformWallet(_from) && getLockManager().getTransferableTokens(_from, block.timestamp) < _value) {
            return (16, TOKENS_LOCKED);
        }

        return checkTransfer(_from, _to, _value);
    }
}


// File: contracts/compliance/IDSComplianceConfigurationService.sol
pragma solidity ^0.8.13;

import "../utils/VersionedContract.sol";
import "../utils/Initializable.sol";

//SPDX-License-Identifier: UNLICENSED
abstract contract IDSComplianceConfigurationService is Initializable, VersionedContract {

    function initialize() public virtual {
        VERSIONS.push(7);
    }

    event DSComplianceUIntRuleSet(string ruleName, uint256 prevValue, uint256 newValue);
    event DSComplianceBoolRuleSet(string ruleName, bool prevValue, bool newValue);
    event DSComplianceStringToUIntMapRuleSet(string ruleName, string keyValue, uint256 prevValue, uint256 newValue);

    function getCountryCompliance(string memory _country) public view virtual returns (uint256);

    function setCountriesCompliance(string[] memory _countries, uint256[] memory _values) public virtual;

    function setCountryCompliance(
        string memory _country,
        uint256 _value /*onlyTransferAgentOrAbove*/
    ) public virtual;

    function getTotalInvestorsLimit() public view virtual returns (uint256);

    function setTotalInvestorsLimit(
        uint256 _value /*onlyTransferAgentOrAbove*/
    ) public virtual;

    function getMinUSTokens() public view virtual returns (uint256);

    function setMinUSTokens(
        uint256 _value /*onlyTransferAgentOrAbove*/
    ) public virtual;

    function getMinEUTokens() public view virtual returns (uint256);

    function setMinEUTokens(
        uint256 _value /*onlyTransferAgentOrAbove*/
    ) public virtual;

    function getUSInvestorsLimit() public view virtual returns (uint256);

    function setUSInvestorsLimit(
        uint256 _value /*onlyTransferAgentOrAbove*/
    ) public virtual;

    function getJPInvestorsLimit() public view virtual returns (uint256);

    function setJPInvestorsLimit(
        uint256 _value /*onlyTransferAgentOrAbove*/
    ) public virtual;

    function getUSAccreditedInvestorsLimit() public view virtual returns (uint256);

    function setUSAccreditedInvestorsLimit(
        uint256 _value /*onlyTransferAgentOrAbove*/
    ) public virtual;

    function getNonAccreditedInvestorsLimit() public view virtual returns (uint256);

    function setNonAccreditedInvestorsLimit(
        uint256 _value /*onlyTransferAgentOrAbove*/
    ) public virtual;

    function getMaxUSInvestorsPercentage() public view virtual returns (uint256);

    function setMaxUSInvestorsPercentage(
        uint256 _value /*onlyTransferAgentOrAbove*/
    ) public virtual;

    function getBlockFlowbackEndTime() public view virtual returns (uint256);

    function setBlockFlowbackEndTime(
        uint256 _value /*onlyTransferAgentOrAbove*/
    ) public virtual;

    function getNonUSLockPeriod() public view virtual returns (uint256);

    function setNonUSLockPeriod(
        uint256 _value /*onlyTransferAgentOrAbove*/
    ) public virtual;

    function getMinimumTotalInvestors() public view virtual returns (uint256);

    function setMinimumTotalInvestors(
        uint256 _value /*onlyTransferAgentOrAbove*/
    ) public virtual;

    function getMinimumHoldingsPerInvestor() public view virtual returns (uint256);

    function setMinimumHoldingsPerInvestor(
        uint256 _value /*onlyTransferAgentOrAbove*/
    ) public virtual;

    function getMaximumHoldingsPerInvestor() public view virtual returns (uint256);

    function setMaximumHoldingsPerInvestor(
        uint256 _value /*onlyTransferAgentOrAbove*/
    ) public virtual;

    function getEURetailInvestorsLimit() public view virtual returns (uint256);

    function setEURetailInvestorsLimit(
        uint256 _value /*onlyTransferAgentOrAbove*/
    ) public virtual;

    function getUSLockPeriod() public view virtual returns (uint256);

    function setUSLockPeriod(
        uint256 _value /*onlyTransferAgentOrAbove*/
    ) public virtual;

    function getForceFullTransfer() public view virtual returns (bool);

    function setForceFullTransfer(
        bool _value /*onlyTransferAgentOrAbove*/
    ) public virtual;

    function getForceAccredited() public view virtual returns (bool);

    function setForceAccredited(
        bool _value /*onlyTransferAgentOrAbove*/
    ) public virtual;

    function setForceAccreditedUS(
        bool _value /*onlyTransferAgentOrAbove*/
    ) public virtual;

    function getForceAccreditedUS() public view virtual returns (bool);

    function setWorldWideForceFullTransfer(
        bool _value /*onlyTransferAgentOrAbove*/
    ) public virtual;

    function getWorldWideForceFullTransfer() public view virtual returns (bool);

    function getAuthorizedSecurities() public view virtual returns (uint256);

    function setAuthorizedSecurities(
        uint256 _value /*onlyTransferAgentOrAbove*/
    ) public virtual;

    function getDisallowBackDating() public view virtual returns (bool);

    function setDisallowBackDating(
        bool _value /*onlyTransferAgentOrAbove*/
    ) public virtual;

    function setAll(
        uint256[] memory _uint_values,
        bool[] memory _bool_values /*onlyTransferAgentOrAbove*/
    ) public virtual;

    function getAll() public view virtual returns (uint256[] memory, bool[] memory);
}


// File: contracts/compliance/IDSComplianceService.sol
pragma solidity ^0.8.13;

import "../utils/VersionedContract.sol";
import "../utils/Initializable.sol";

//SPDX-License-Identifier: UNLICENSED
abstract contract IDSComplianceService is Initializable, VersionedContract {

    function initialize() public virtual {
        VERSIONS.push(7);
    }

    uint256 internal constant NONE = 0;
    uint256 internal constant US = 1;
    uint256 internal constant EU = 2;
    uint256 internal constant FORBIDDEN = 4;
    uint256 internal constant JP = 8;
    string internal constant TOKEN_PAUSED = "Token Paused";
    string internal constant NOT_ENOUGH_TOKENS = "Not Enough Tokens";
    string internal constant TOKENS_LOCKED = "Tokens Locked";
    string internal constant WALLET_NOT_IN_REGISTRY_SERVICE = "Wallet not in registry Service";
    string internal constant DESTINATION_RESTRICTED = "Destination restricted";
    string internal constant VALID = "Valid";
    string internal constant HOLD_UP = "Under lock-up";
    string internal constant ONLY_FULL_TRANSFER = "Only Full Transfer";
    string internal constant FLOWBACK = "Flowback";
    string internal constant MAX_INVESTORS_IN_CATEGORY = "Max Investors in category";
    string internal constant AMOUNT_OF_TOKENS_UNDER_MIN = "Amount of tokens under min";
    string internal constant AMOUNT_OF_TOKENS_ABOVE_MAX = "Amount of tokens above max";
    string internal constant ONLY_ACCREDITED = "Only accredited";
    string internal constant ONLY_US_ACCREDITED = "Only us accredited";
    string internal constant NOT_ENOUGH_INVESTORS = "Not enough investors";
    string internal constant MAX_AUTHORIZED_SECURITIES_EXCEEDED = "Max authorized securities exceeded";

    function adjustInvestorCountsAfterCountryChange(
        string memory _id,
        string memory _country,
        string memory _prevCountry
    ) public virtual returns (bool);

    //*****************************************
    // TOKEN ACTION VALIDATIONS
    //*****************************************

    function validateTransfer(
        address _from,
        address _to,
        uint256 _value /*onlyToken*/
    ) public virtual returns (bool);

    function validateTransfer(
        address _from,
        address _to,
        uint256 _value, /*onlyToken*/
        bool _pausedToken,
        uint256 _balanceFrom
    ) public virtual returns (bool);

    function validateIssuance(
        address _to,
        uint256 _value,
        uint256 _issuanceTime /*onlyToken*/
    ) public virtual returns (bool);

    function validateIssuanceWithNoCompliance(
        address _to,
        uint256 _value,
        uint256 _issuanceTime /*onlyToken*/
    ) public virtual returns (bool);

    function validateBurn(
        address _who,
        uint256 _value /*onlyToken*/
    ) public virtual returns (bool);

    function validateSeize(
        address _from,
        address _to,
        uint256 _value /*onlyToken*/
    ) public virtual returns (bool);

    function preIssuanceCheck(address _to, uint256 _value) public view virtual returns (uint256 code, string memory reason);

    function preTransferCheck(
        address _from,
        address _to,
        uint256 _value
    ) public view virtual returns (uint256 code, string memory reason);

    function preInternalTransferCheck(
        address _from,
        address _to,
        uint256 _value
    ) public view virtual returns (uint256 code, string memory reason);

    function validateIssuanceTime(uint256 _issuanceTime) public view virtual returns (uint256 issuanceTime);
}


// File: contracts/compliance/IDSComplianceServicePartitioned.sol
pragma solidity ^0.8.13;

import "./IDSComplianceService.sol";

//SPDX-License-Identifier: UNLICENSED
abstract contract IDSComplianceServicePartitioned is IDSComplianceService {

    function initialize() public virtual override {
        VERSIONS.push(2);
    }

    function getComplianceTransferableTokens(
        address _who,
        uint256 _time,
        bool _checkFlowback
    ) public view virtual returns (uint256 transferable);

    function getComplianceTransferableTokens(
        address _who,
        uint256 _time,
        bool _checkFlowback,
        bytes32 _partition
    ) public view virtual returns (uint256);

    function getComplianceTransferableTokens(
        address _who,
        uint256 _time,
        address _to
    ) public view virtual returns (uint256 transferable);

    function getComplianceTransferableTokens(
        address _who,
        uint256 _time,
        address _to,
        bytes32 _partition
    ) public view virtual returns (uint256);
}


// File: contracts/compliance/IDSLockManager.sol
pragma solidity ^0.8.13;

import "../utils/VersionedContract.sol";
import "../utils/Initializable.sol";

//SPDX-License-Identifier: UNLICENSED
abstract contract IDSLockManager is Initializable, VersionedContract {

    function initialize() public virtual;

    modifier validLock(uint256 _valueLocked, uint256 _releaseTime) {
        require(_valueLocked > 0, "Value is zero");
        require(_releaseTime == 0 || _releaseTime > uint256(block.timestamp), "Release time is in the past");
        _;
    }

    event Locked(address indexed who, uint256 value, uint256 indexed reason, string reasonString, uint256 releaseTime);
    event Unlocked(address indexed who, uint256 value, uint256 indexed reason, string reasonString, uint256 releaseTime);

    event HolderLocked(string holderId, uint256 value, uint256 indexed reason, string reasonString, uint256 releaseTime);
    event HolderUnlocked(string holderId, uint256 value, uint256 indexed reason, string reasonString, uint256 releaseTime);
    /**
     * @dev creates a lock record for wallet address
     * @param _to address to lock the tokens at
     * @param _valueLocked value of tokens to lock
     * @param _reason reason for lock
     * @param _releaseTime timestamp to release the lock (or 0 for locks which can only released by an unlockTokens call)
     * Note: The user MAY have at a certain time more locked tokens than actual tokens
     */

    function addManualLockRecord(
        address _to,
        uint256 _valueLocked,
        string memory _reason,
        uint256 _releaseTime /*issuerOrAboveOrToken*/
    ) public virtual;

    /**
     * @dev creates a lock record for investor Id
     * @param _investor investor id to lock the tokens at
     * @param _valueLocked value of tokens to lock
     * @param _reasonCode reason code for lock
     * @param _reasonString reason for lock
     * @param _releaseTime timestamp to release the lock (or 0 for locks which can only released by an unlockTokens call)
     * Note: The user MAY have at a certain time more locked tokens than actual tokens
     */

    function createLockForInvestor(
        string memory _investor,
        uint256 _valueLocked,
        uint256 _reasonCode,
        string memory _reasonString,
        uint256 _releaseTime /*onlyIssuerOrAboveOrToken*/
    ) public virtual;

    /**
     * @dev Releases a specific lock record for a wallet
     * @param _to address to release the tokens for
     * @param _lockIndex the index of the lock to remove
     *
     * note - this may change the order of the locks on an address, so if iterating the iteration should be restarted.
     * @return true on success
     */
    function removeLockRecord(
        address _to,
        uint256 _lockIndex /*issuerOrAbove*/
    ) public virtual returns (bool);

    /**
     * @dev Releases a specific lock record for a investor
     * @param _investorId investor id to release the tokens for
     * @param _lockIndex the index of the lock to remove
     *
     * note - this may change the order of the locks on an address, so if iterating the iteration should be restarted.
     * @return true on success
     */
    function removeLockRecordForInvestor(
        string memory _investorId,
        uint256 _lockIndex /*onlyIssuerOrAbove*/
    ) public virtual returns (bool);

    /**
     * @dev Get number of locks currently associated with an address
     * @param _who address to get count for
     *
     * @return number of locks
     *
     * Note - a lock can be inactive (due to its time expired) but still exists for a specific address
     */
    function lockCount(address _who) public view virtual returns (uint256);

    /**
     * @dev Get number of locks currently associated with a investor
     * @param _investorId investor id to get count for
     *
     * @return number of locks
     *
     * Note - a lock can be inactive (due to its time expired) but still exists for a specific address
     */

    function lockCountForInvestor(string memory _investorId) public view virtual returns (uint256);

    /**
     * @dev Get details of a specific lock associated with an address
     * can be used to iterate through the locks of a user
     * @param _who address to get token lock for
     * @param _lockIndex the 0 based index of the lock.
     * @return reasonCode the reason code
     * @return reasonString the reason for the lock
     * @return value the value of tokens locked
     * @return autoReleaseTime the timestamp in which the lock will be inactive (or 0 if it's always active until removed)
     *
     * Note - a lock can be inactive (due to its time expired) but still exists for a specific address
     */
    function lockInfo(address _who, uint256 _lockIndex) public view virtual returns (uint256 reasonCode, string memory reasonString, uint256 value, uint256 autoReleaseTime);

    /**
     * @dev Get details of a specific lock associated with a investor
     * can be used to iterate through the locks of a user
     * @param _investorId investorId to get token lock for
     * @param _lockIndex the 0 based index of the lock.
     * @return reasonCode the reason code
     * @return reasonString the reason for the lock
     * @return value the value of tokens locked
     * @return autoReleaseTime the timestamp in which the lock will be inactive (or 0 if it's always active until removed)
     *
     * Note - a lock can be inactive (due to its time expired) but still exists for a specific address
     */
    function lockInfoForInvestor(
        string memory _investorId,
        uint256 _lockIndex
    ) public view virtual  returns (uint256 reasonCode, string memory reasonString, uint256 value, uint256 autoReleaseTime);

    /**
     * @dev get total number of transferable tokens for a wallet, at a certain time
     * @param _who address to get number of transferable tokens for
     * @param _time time to calculate for
     */
    function getTransferableTokens(address _who, uint256 _time) public view virtual returns (uint256);

    /**
     * @dev get total number of transferable tokens for a investor, at a certain time
     * @param _investorId investor id
     * @param _time time to calculate for
     */
    function getTransferableTokensForInvestor(string memory _investorId, uint256 _time) public view virtual returns (uint256);

    /**
     * @dev pause investor
     * @param _investorId investor id
     */
    function lockInvestor(
        string memory _investorId /*issuerOrAbove*/
    ) public virtual returns (bool);

    /**
     * @dev unpauses investor
     * @param _investorId investor id
     */
    function unlockInvestor(
        string memory _investorId /*issuerOrAbove*/
    ) public virtual returns (bool);

    /**
     * @dev Returns true if paused, otherwise false
     * @param _investorId investor id
     */
    function isInvestorLocked(string memory _investorId) public view virtual returns (bool);
}


// File: contracts/compliance/IDSLockManagerPartitioned.sol
pragma solidity ^0.8.13;

import "./IDSLockManager.sol";

//SPDX-License-Identifier: UNLICENSED
abstract contract IDSLockManagerPartitioned is Initializable, VersionedContract {

    event LockedPartition(address indexed who, uint256 value, uint256 indexed reason, string reasonString, uint256 releaseTime, bytes32 indexed partition);
    event UnlockedPartition(address indexed who, uint256 value, uint256 indexed reason, string reasonString, uint256 releaseTime, bytes32 indexed partition);
    event HolderLockedPartition(string investorId, uint256 value, uint256 indexed reason, string reasonString, uint256 releaseTime, bytes32 indexed partition);
    event HolderUnlockedPartition(string investorId, uint256 value, uint256 indexed reason, string reasonString, uint256 releaseTime, bytes32 indexed partition);

    function createLockForInvestor(
        string memory _investorId,
        uint256 _valueLocked,
        uint256 _reasonCode,
        string memory _reasonString,
        uint256 _releaseTime,
        bytes32 _partition
    ) public virtual;

    function addManualLockRecord(
        address _to,
        uint256 _valueLocked,
        string memory _reason,
        uint256 _releaseTime,
        bytes32 _partition /*issuerOrAboveOrToken*/
    ) public virtual;

    function removeLockRecord(
        address _to,
        uint256 _lockIndex,
        bytes32 _partition /*issuerOrAbove*/
    ) public virtual returns (bool);

    function removeLockRecordForInvestor(
        string memory _investorId,
        uint256 _lockIndex,
        bytes32 _partition /*issuerOrAbove*/
    ) public virtual returns (bool);

    function lockCount(address _who, bytes32 _partition) public view virtual returns (uint256);

    function lockInfo(
        address _who,
        uint256 _lockIndex,
        bytes32 _partition
    )
        public
        view
        virtual
        returns (
            uint256 reasonCode,
            string memory reasonString,
            uint256 value,
            uint256 autoReleaseTime
        );

    function lockCountForInvestor(string memory _investorId, bytes32 _partition) public view virtual returns (uint256);

    function lockInfoForInvestor(
        string memory _investorId,
        uint256 _lockIndex,
        bytes32 _partition
    )
        public
        view
        virtual
        returns (
            uint256 reasonCode,
            string memory reasonString,
            uint256 value,
            uint256 autoReleaseTime
        );

    function getTransferableTokens(
        address _who,
        uint256 _time,
        bytes32 _partition
    ) public view virtual returns (uint256);

    function getTransferableTokensForInvestor(
        string memory _investorId,
        uint256 _time,
        bytes32 _partition
    ) public view virtual returns (uint256);

    /*************** Legacy functions ***************/
    function createLockForHolder(
        string memory _investorId,
        uint256 _valueLocked,
        uint256 _reasonCode,
        string memory _reasonString,
        uint256 _releaseTime,
        bytes32 _partition
    ) public virtual;

    function removeLockRecordForHolder(
        string memory _investorId,
        uint256 _lockIndex,
        bytes32 _partition
    ) public virtual returns (bool);

    function lockCountForHolder(string memory _holderId, bytes32 _partition) public view virtual returns (uint256);

    function lockInfoForHolder(
        string memory _holderId,
        uint256 _lockIndex,
        bytes32 _partition
    )
        public
        view
        virtual
        returns (
            uint256 reasonCode,
            string memory reasonString,
            uint256 value,
            uint256 autoReleaseTime
        );

    function getTransferableTokensForHolder(
        string memory _holderId,
        uint256 _time,
        bytes32 _partition
    ) public view virtual returns (uint256);

    /******************************/
}


// File: contracts/compliance/IDSPartitionsManager.sol
pragma solidity ^0.8.13;

import "../service/IDSServiceConsumer.sol";
import "../utils/Initializable.sol";

//SPDX-License-Identifier: UNLICENSED
abstract contract IDSPartitionsManager is Initializable, IDSServiceConsumer {

    event PartitionCreated(uint256 _date, uint256 _region, bytes32 _partition);

    function initialize() public virtual override {
        VERSIONS.push(2);
    }

    function ensurePartition(
        uint256 _issuanceDate,
        uint256 _region /*onlyIssuerOrAboveOrToken*/
    ) public virtual returns (bytes32 partition);

    function getPartition(bytes32 _partition) public view virtual returns (uint256 date, uint256 region);

    function getPartitionIssuanceDate(bytes32 _partition) public view virtual returns (uint256);

    function getPartitionRegion(bytes32 _partition) public view virtual returns (uint256);
}


// File: contracts/compliance/IDSWalletManager.sol
pragma solidity ^0.8.13;

import "../utils/VersionedContract.sol";
import "../utils/Initializable.sol";

//SPDX-License-Identifier: UNLICENSED
abstract contract IDSWalletManager is Initializable, VersionedContract {

    function initialize() public virtual {
        VERSIONS.push(5);
    }

    // Special wallets constants
    uint8 public constant NONE = 0;
    uint8 public constant ISSUER = 1;
    uint8 public constant PLATFORM = 2;
    uint8 public constant EXCHANGE = 4;

    /**
     * @dev should be emitted when a special wallet is added.
     */
    event DSWalletManagerSpecialWalletAdded(address wallet, uint8 walletType, address sender);
    /**
     * @dev should be emitted when a special wallet is removed.
     */
    event DSWalletManagerSpecialWalletRemoved(address wallet, uint8 walletType, address sender);
    /**
     * @dev should be emitted when the number of reserved slots is set for a wallet.
     */
    event DSWalletManagerReservedSlotsSet(address wallet, string country, uint8 accreditationStatus, uint256 slots, address sender);

    /**
     * @dev Sets a wallet to be an special wallet. (internal)
     * @param _wallet The address of the wallet.
     * @param _type The type of the wallet.
     * @return A boolean that indicates if the operation was successful.
     */
    function setSpecialWallet(address _wallet, uint8 _type) internal virtual returns (bool);

    /**
     * @dev gets a wallet type
     * @param _wallet the address of the wallet to check.
     */
    function getWalletType(address _wallet) public view virtual returns (uint8);

    /**
     * @dev Returns true if it is platform wallet
     * @param _wallet the address of the wallet to check.
     */
    function isPlatformWallet(address _wallet) external view virtual returns (bool);

    /**
     * @dev Returns true if it is special wallet
     * @param _wallet the address of the wallet to check.
     */
    function isSpecialWallet(address _wallet) external view virtual returns (bool);

    /**
     * @dev Returns true if it is issuer special wallet
     * @param _wallet the address of the wallet to check.
     */
    function isIssuerSpecialWallet(address _wallet) external view virtual returns (bool);

    /**
     * @dev Sets a wallet to be an issuer wallet.
     * @param _wallet The address of the wallet.
     * @return A boolean that indicates if the operation was successful.
     */
    function addIssuerWallet(
        address _wallet /*onlyIssuerOrAbove*/
    ) public virtual returns (bool);

    /**
     * @dev Sets an array of wallets to be issuer wallets.
     * @param _wallets The address of the wallets.
     * @return A boolean that indicates if the operation was successful.
     */
    function addIssuerWallets(address[] memory _wallets) public virtual returns (bool);

    /**
     * @dev Sets a wallet to be a platform wallet.
     * @param _wallet The address of the wallet.
     * @return A boolean that indicates if the operation was successful.
     */
    function addPlatformWallet(
        address _wallet /*onlyIssuerOrAbove*/
    ) public virtual returns (bool);

    /**
     * @dev Sets an array of wallets to be platforms wallet.
     * @param _wallets The address of the wallets.
     * @return A boolean that indicates if the operation was successful.
     */
    function addPlatformWallets(address[] memory _wallets) public virtual returns (bool);

    /**
     * @dev Sets a wallet to be an exchange wallet.
     * @param _wallet The address of the wallet.
     * @param _owner The address of the owner.
     * @return A boolean that indicates if the operation was successful.
     */
    function addExchangeWallet(address _wallet, address _owner) public virtual returns (bool);

    /**
     * @dev Removes a special wallet.
     * @param _wallet The address of the wallet.
     * @return A boolean that indicates if the operation was successful.
     */
    function removeSpecialWallet(
        address _wallet /*onlyIssuerOrAbove*/
    ) public virtual returns (bool);
}


// File: contracts/data-stores/ComplianceConfigurationDataStore.sol
pragma solidity ^0.8.13;

import "./ServiceConsumerDataStore.sol";

//SPDX-License-Identifier: UNLICENSED
contract ComplianceConfigurationDataStore is ServiceConsumerDataStore {
    mapping(string => uint256) public countriesCompliances;
    uint256 public totalInvestorsLimit;
    uint256 public minUSTokens;
    uint256 public minEUTokens;
    uint256 public usInvestorsLimit;
    uint256 public jpInvestorsLimit;
    uint256 public usAccreditedInvestorsLimit;
    uint256 public nonAccreditedInvestorsLimit;
    uint256 public maxUSInvestorsPercentage;
    uint256 public blockFlowbackEndTime;
    uint256 public nonUSLockPeriod;
    uint256 public minimumTotalInvestors;
    uint256 public minimumHoldingsPerInvestor;
    uint256 public maximumHoldingsPerInvestor;
    uint256 public euRetailInvestorsLimit;
    uint256 public usLockPeriod;
    bool public forceFullTransfer;
    bool public forceAccreditedUS;
    bool public forceAccredited;
    bool public worldWideForceFullTransfer;
    uint256 public authorizedSecurities;
    bool public disallowBackDating;

    /**
     * @dev This empty reserved space is put in place to allow future versions to add new
     * variables without shifting down storage in the inheritance chain.
     * See https://docs.openzeppelin.com/contracts/4.x/upgradeable#storage_gaps
     */
    uint256[45] private __gap;
}


// File: contracts/data-stores/ComplianceServiceDataStore.sol
pragma solidity ^0.8.13;

import "./ServiceConsumerDataStore.sol";

//SPDX-License-Identifier: UNLICENSED
contract ComplianceServiceDataStore is ServiceConsumerDataStore {
    uint256 internal totalInvestors;
    uint256 internal accreditedInvestorsCount;
    uint256 internal usAccreditedInvestorsCount;
    uint256 internal usInvestorsCount;
    uint256 internal jpInvestorsCount;
    mapping(string => uint256) internal euRetailInvestorsCount;
    mapping(string => uint256) internal issuancesCounters;
    mapping(string => mapping(uint256 => uint256)) issuancesValues;
    mapping(string => mapping(uint256 => uint256)) issuancesTimestamps;
}


// File: contracts/data-stores/OmnibusTBEControllerDataStore.sol
pragma solidity ^0.8.13;

import "./ServiceConsumerDataStore.sol";

//SPDX-License-Identifier: UNLICENSED
contract OmnibusTBEControllerDataStore is ServiceConsumerDataStore {
    address internal omnibusWallet;
    bool internal isPartitionedToken;
}


// File: contracts/data-stores/ServiceConsumerDataStore.sol
pragma solidity ^0.8.13;

import "@openzeppelin/contracts/utils/math/SafeMath.sol";

//SPDX-License-Identifier: UNLICENSED
contract ServiceConsumerDataStore {
    using SafeMath for uint256;

    mapping(uint256 => address) internal services;
}


// File: contracts/data-stores/TokenDataStore.sol
pragma solidity ^0.8.13;

import "./ServiceConsumerDataStore.sol";
import '../token/TokenPartitionsLibrary.sol';
import '../token/TokenLibrary.sol';

//SPDX-License-Identifier: UNLICENSED
contract TokenDataStore is ServiceConsumerDataStore {

    TokenLibrary.TokenData internal tokenData;
    mapping(address => mapping(address => uint256)) internal allowances;
    mapping(uint256 => address) internal walletsList;
    uint256 internal walletsCount;
    mapping(address => uint256) internal walletsToIndexes;
    TokenPartitionsLibrary.TokenPartitions internal partitionsManagement;
    uint256 public cap;
    string public name;
    string public symbol;
    uint8 public decimals;
    TokenLibrary.SupportedFeatures public supportedFeatures;
    bool internal paused;
}


// File: contracts/omnibus/IDSOmnibusTBEController.sol
pragma solidity ^0.8.13;

import "../service/ServiceConsumer.sol";
import "../utils/ProxyTarget.sol";
import "../data-stores/OmnibusTBEControllerDataStore.sol";
import "../utils/VersionedContract.sol";
import "../utils/Initializable.sol";

//SPDX-License-Identifier: UNLICENSED
abstract contract IDSOmnibusTBEController is Initializable, VersionedContract {
    using SafeMath for uint256;

    function initialize(address _omnibusWallet, bool _isPartitionedToken) public virtual;

    function bulkIssuance(uint256 value, uint256 issuanceTime, uint256 totalInvestors, uint256 accreditedInvestors,
        uint256 usAccreditedInvestors, uint256 usTotalInvestors, uint256 jpTotalInvestors, bytes32[] memory euRetailCountries,
        uint256[] memory euRetailCountryCounts) public virtual;

    function bulkBurn(uint256 value, uint256 totalInvestors, uint256 accreditedInvestors,
        uint256 usAccreditedInvestors, uint256 usTotalInvestors, uint256 jpTotalInvestors, bytes32[] memory euRetailCountries,
        uint256[] memory euRetailCountryCounts) public virtual;

    function bulkTransfer(address[] memory wallets, uint256[] memory values) public virtual;

    function adjustCounters(int256 totalDelta, int256 accreditedDelta,
        int256 usAccreditedDelta, int256 usTotalDelta, int256 jpTotalDelta, bytes32[] memory euRetailCountries,
        int256[] memory euRetailCountryDeltas) public virtual;

    function getOmnibusWallet() public view virtual returns (address);
}


// File: contracts/omnibus/IDSOmnibusWalletController.sol
pragma solidity ^0.8.13;

import "../utils/VersionedContract.sol";
import "../utils/Initializable.sol";

//SPDX-License-Identifier: UNLICENSED
abstract contract IDSOmnibusWalletController is Initializable, VersionedContract {
    uint8 public constant BENEFICIARY = 0;
    uint8 public constant HOLDER_OF_RECORD = 1;

    function initialize(address _omnibusWallet) public virtual;

    function setAssetTrackingMode(uint8 _assetTrackingMode) public virtual;

    function getAssetTrackingMode() public view virtual returns (uint8);

    function isHolderOfRecord() public view virtual returns (bool);

    function balanceOf(address _who) public view virtual returns (uint256);

    function transfer(
        address _from,
        address _to,
        uint256 _value /*onlyOperator*/
    ) public virtual;

    function deposit(
        address _to,
        uint256 _value /*onlyToken*/
    ) public virtual;

    function withdraw(
        address _from,
        uint256 _value /*onlyToken*/
    ) public virtual;

    function seize(
        address _from,
        uint256 _value /*onlyToken*/
    ) public virtual;

    function burn(
        address _from,
        uint256 _value /*onlyToken*/
    ) public virtual;
}


// File: contracts/omnibus/OmnibusTBEController.sol
pragma solidity ^0.8.13;

import "../service/ServiceConsumer.sol";
import "../utils/ProxyTarget.sol";
import "../data-stores/OmnibusTBEControllerDataStore.sol";
import "../compliance/ComplianceServiceRegulated.sol";
import "../compliance/ComplianceConfigurationService.sol";

//SPDX-License-Identifier: UNLICENSED
contract OmnibusTBEController is ProxyTarget, Initializable, IDSOmnibusTBEController, ServiceConsumer, OmnibusTBEControllerDataStore {

    using SafeMath for uint256;
    string internal constant MAX_INVESTORS_IN_CATEGORY = "Max investors in category";

    function initialize(address _omnibusWallet, bool _isPartitionedToken) public override initializer forceInitializeFromProxy {
        VERSIONS.push(4);
        ServiceConsumer.initialize();

        omnibusWallet = _omnibusWallet;
        isPartitionedToken = _isPartitionedToken;
    }

    function bulkIssuance(uint256 value, uint256 issuanceTime, uint256 totalInvestors, uint256 accreditedInvestors,
        uint256 usAccreditedInvestors, uint256 usTotalInvestors, uint256 jpTotalInvestors, bytes32[] memory euRetailCountries,
        uint256[] memory euRetailCountryCounts) public override onlyIssuerOrAbove {
        require(euRetailCountries.length == euRetailCountryCounts.length, 'EU Retail countries arrays do not match');
        // Issue tokens
        getToken().issueTokensCustom(omnibusWallet, value, issuanceTime, 0, '', 0);
        addToCounters(totalInvestors, accreditedInvestors,
            usAccreditedInvestors, usTotalInvestors, jpTotalInvestors, euRetailCountries, euRetailCountryCounts, true);
        emitTBEOperationEvent(totalInvestors, accreditedInvestors, usAccreditedInvestors, usTotalInvestors, jpTotalInvestors, true);
    }

    function bulkBurn(uint256 value, uint256 totalInvestors, uint256 accreditedInvestors,
        uint256 usAccreditedInvestors, uint256 usTotalInvestors, uint256 jpTotalInvestors, bytes32[] memory euRetailCountries,
        uint256[] memory euRetailCountryCounts) public override onlyTransferAgentOrAbove {
        require(euRetailCountries.length == euRetailCountryCounts.length, 'EU Retail countries arrays do not match');

        if(isPartitionedToken) {
            IDSTokenPartitioned token = getTokenPartitioned();
            uint256 pendingBurn = value;
            uint256 currentPartitionBalance;
            bytes32 partition;
            while(pendingBurn > 0) {
                require(token.partitionCountOf(omnibusWallet) > 0, 'Not enough tokens in partitions to burn the required value');
                partition = token.partitionOf(omnibusWallet, 0);
                currentPartitionBalance = token.balanceOfByPartition(omnibusWallet, partition);
                require(currentPartitionBalance > 0, 'Not enough tokens in remaining partitions to burn the required value');
                uint256 amountToBurn = currentPartitionBalance >= pendingBurn ? pendingBurn : currentPartitionBalance;
                token.burnByPartition(omnibusWallet, amountToBurn, 'Omnibus burn by partition', partition);
                pendingBurn = pendingBurn - amountToBurn;
            }
        } else {
            // Burn non partitioned tokens
            getToken().burn(omnibusWallet, value, 'Omnibus');
        }

        emitTBEOperationEvent(totalInvestors, accreditedInvestors, usAccreditedInvestors, usTotalInvestors, jpTotalInvestors, false);
    }

    function bulkTransfer(address[] memory wallets, uint256[] memory values) public override onlyIssuerOrTransferAgentOrAbove {
        require(wallets.length == values.length, 'Wallets and values lengths do not match');
        for (uint i = 0; i < wallets.length; i++) {
            getToken().transferFrom(omnibusWallet, wallets[i], values[i]);
        }
    }

    function internalTBETransfer(string memory externalId, int256 totalDelta, int256 accreditedDelta,
        int256 usAccreditedDelta, int256 usTotalDelta, int256 jpTotalDelta, bytes32[] memory euRetailCountries,
        int256[] memory euRetailCountryDeltas) public onlyIssuerOrTransferAgentOrAbove {
        adjustCounters(totalDelta, accreditedDelta, usAccreditedDelta, usTotalDelta, jpTotalDelta,
            euRetailCountries, euRetailCountryDeltas);
        getToken().emitOmnibusTBETransferEvent(omnibusWallet, externalId);
    }

    function adjustCounters(int256 totalDelta, int256 accreditedDelta,
        int256 usAccreditedDelta, int256 usTotalDelta, int256 jpTotalDelta, bytes32[] memory euRetailCountries,
        int256[] memory euRetailCountryDeltas) public override onlyIssuerOrTransferAgentOrAbove {
        require(euRetailCountries.length == euRetailCountryDeltas.length, 'Array lengths do not match');

        addToCounters(
            totalDelta > 0 ? uint256(totalDelta) : 0,
            accreditedDelta > 0 ? uint256(accreditedDelta) : 0,
            usAccreditedDelta > 0 ? uint256(usAccreditedDelta) : 0,
            usTotalDelta > 0 ? uint256(usTotalDelta) : 0,
            jpTotalDelta > 0 ? uint256(jpTotalDelta) : 0,
            euRetailCountries,
            getUintEuCountriesDeltas(euRetailCountryDeltas, true),
            true
        );

        getToken().emitOmnibusTBEEvent(
            omnibusWallet,
            totalDelta,
            accreditedDelta,
            usAccreditedDelta,
            usTotalDelta,
            jpTotalDelta);
    }

    function getOmnibusWallet() public view override returns (address) {
        return omnibusWallet;
    }

    function addToCounters(uint256 _totalInvestors, uint256 _accreditedInvestors,
        uint256 _usAccreditedInvestors, uint256 _usTotalInvestors, uint256 _jpTotalInvestors, bytes32[] memory _euRetailCountries,
        uint256[] memory _euRetailCountryCounts,  bool _increase) internal returns (bool) {
        if(_increase) {
            ComplianceServiceRegulated cs = ComplianceServiceRegulated(getDSService(COMPLIANCE_SERVICE));
            IDSComplianceConfigurationService ccs = IDSComplianceConfigurationService(getDSService(COMPLIANCE_CONFIGURATION_SERVICE));

            require(ccs.getNonAccreditedInvestorsLimit() == 0 || (cs.getTotalInvestorsCount() - cs.getAccreditedInvestorsCount()
             + _totalInvestors - _accreditedInvestors <= ccs.getNonAccreditedInvestorsLimit()), MAX_INVESTORS_IN_CATEGORY);

            cs.setTotalInvestorsCount(increaseCounter(cs.getTotalInvestorsCount(), ccs.getTotalInvestorsLimit(), _totalInvestors));
            cs.setAccreditedInvestorsCount(increaseCounter(cs.getAccreditedInvestorsCount(), ccs.getTotalInvestorsLimit(), _accreditedInvestors));
            cs.setUSAccreditedInvestorsCount(increaseCounter(cs.getUSAccreditedInvestorsCount(), ccs.getUSAccreditedInvestorsLimit(), _usAccreditedInvestors));
            cs.setUSInvestorsCount(increaseCounter(cs.getUSInvestorsCount(), ccs.getUSInvestorsLimit(), _usTotalInvestors));
            cs.setJPInvestorsCount(increaseCounter(cs.getJPInvestorsCount(), ccs.getJPInvestorsLimit(), _jpTotalInvestors));
            for (uint i = 0; i < _euRetailCountries.length; i++) {
                string memory countryCode = bytes32ToString(_euRetailCountries[i]);
                cs.setEURetailInvestorsCount(
                    countryCode,
                    increaseCounter(
                            cs.getEURetailInvestorsCount(countryCode),
                            ccs.getEURetailInvestorsLimit(),
                            _euRetailCountryCounts[i]
                   )
                );
            }
        }

        return true;
    }

    function emitTBEOperationEvent(uint256 _totalInvestors, uint256 _accreditedInvestors,
        uint256 _usAccreditedInvestors, uint256 _usTotalInvestors, uint256 _jpTotalInvestors, bool /* _increase */) internal {
        getToken().emitOmnibusTBEEvent(
            omnibusWallet,
            int256(_totalInvestors),
            int256(_accreditedInvestors),
            int256(_usAccreditedInvestors),
            int256(_usTotalInvestors),
            int256(_jpTotalInvestors)
        );
    }

    function getUintEuCountriesDeltas(int256[] memory euCountryDeltas,  bool increase) internal pure returns (uint256[] memory) {
        uint256[] memory result = new uint256[](euCountryDeltas.length);

        for (uint i = 0; i < euCountryDeltas.length; i++) {
            if (increase) {
                result[i] = euCountryDeltas[i] > 0 ? uint256(euCountryDeltas[i]) : 0;
            } else {
                result[i] = euCountryDeltas[i] < 0 ? uint256(euCountryDeltas[i] * -1) : 0;
            }
        }
        return result;
    }

    function increaseCounter(uint256 currentValue, uint256 currentLimit, uint256 delta) internal pure returns (uint256) {
        uint256 result = currentValue + delta;
        require(currentLimit == 0 || result <= currentLimit, MAX_INVESTORS_IN_CATEGORY);
        return result;
    }

    function bytes32ToString(bytes32 _bytes32) internal pure returns (string memory) {
        uint8 i = 0;
        while(i < 32 && _bytes32[i] != 0) {
            i++;
        }
        bytes memory bytesArray = new bytes(i);
        for (i = 0; i < 32 && _bytes32[i] != 0; i++) {
            bytesArray[i] = _bytes32[i];
        }
        return string(bytesArray);
    }
}


// File: contracts/registry/IDSRegistryService.sol
pragma solidity ^0.8.13;

import "../utils/CommonUtils.sol";
import "../utils/VersionedContract.sol";
import "../utils/Initializable.sol";
import "../omnibus/IDSOmnibusWalletController.sol";

//SPDX-License-Identifier: UNLICENSED
abstract contract IDSRegistryService is Initializable, VersionedContract {

    function initialize() public virtual {
        VERSIONS.push(6);
    }

    event DSRegistryServiceInvestorAdded(string investorId, address sender);
    event DSRegistryServiceInvestorRemoved(string investorId, address sender);
    event DSRegistryServiceInvestorCountryChanged(string investorId, string country, address sender);
    event DSRegistryServiceInvestorAttributeChanged(string investorId, uint256 attributeId, uint256 value, uint256 expiry, string proofHash, address sender);
    event DSRegistryServiceWalletAdded(address wallet, string investorId, address sender);
    event DSRegistryServiceWalletRemoved(address wallet, string investorId, address sender);
    event DSRegistryServiceOmnibusWalletAdded(address omnibusWallet, string investorId, IDSOmnibusWalletController omnibusWalletController);
    event DSRegistryServiceOmnibusWalletRemoved(address omnibusWallet, string investorId);

    uint8 public constant NONE = 0;
    uint8 public constant KYC_APPROVED = 1;
    uint8 public constant ACCREDITED = 2;
    uint8 public constant QUALIFIED = 4;
    uint8 public constant PROFESSIONAL = 8;

    uint8 public constant PENDING = 0;
    uint8 public constant APPROVED = 1;
    uint8 public constant REJECTED = 2;

    uint8 public constant EXCHANGE = 4;

    modifier investorExists(string memory _id) {
        require(isInvestor(_id), "Unknown investor");
        _;
    }

    modifier newInvestor(string memory _id) {
        require(!CommonUtils.isEmptyString(_id), "Investor id must not be empty");
        require(!isInvestor(_id), "Investor already exists");
        _;
    }

    modifier walletExists(address _address) {
        require(isWallet(_address), "Unknown wallet");
        _;
    }

    modifier newWallet(address _address) {
        require(!isWallet(_address), "Wallet already exists");
        _;
    }

    modifier newOmnibusWallet(address _omnibusWallet) {
        require(!isOmnibusWallet(_omnibusWallet), "Omnibus wallet already exists");
        _;
    }

    modifier omnibusWalletExists(address _omnibusWallet) {
        require(isOmnibusWallet(_omnibusWallet), "Unknown omnibus wallet");
        _;
    }

    modifier walletBelongsToInvestor(address _address, string memory _id) {
        require(CommonUtils.isEqualString(getInvestor(_address), _id), "Wallet does not belong to investor");
        _;
    }

    function registerInvestor(
        string memory _id,
        string memory _collision_hash /*onlyExchangeOrAbove newInvestor(_id)*/
    ) public virtual returns (bool);

    function updateInvestor(
        string memory _id,
        string memory _collisionHash,
        string memory _country,
        address[] memory _wallets,
        uint8[] memory _attributeIds,
        uint256[] memory _attributeValues,
        uint256[] memory _attributeExpirations /*onlyIssuerOrAbove*/
    ) public virtual returns (bool);

    function removeInvestor(
        string memory _id /*onlyExchangeOrAbove investorExists(_id)*/
    ) public virtual returns (bool);

    function setCountry(
        string memory _id,
        string memory _country /*onlyExchangeOrAbove investorExists(_id)*/
    ) public virtual returns (bool);

    function getCountry(string memory _id) public view virtual returns (string memory);

    function getCollisionHash(string memory _id) public view virtual returns (string memory);

    function setAttribute(
        string memory _id,
        uint8 _attributeId,
        uint256 _value,
        uint256 _expiry,
        string memory _proofHash /*onlyExchangeOrAbove investorExists(_id)*/
    ) public virtual returns (bool);

    function getAttributeValue(string memory _id, uint8 _attributeId) public view virtual returns (uint256);

    function getAttributeExpiry(string memory _id, uint8 _attributeId) public view virtual returns (uint256);

    function getAttributeProofHash(string memory _id, uint8 _attributeId) public view virtual returns (string memory);

    function addWallet(
        address _address,
        string memory _id /*onlyExchangeOrAbove newWallet(_address)*/
    ) public virtual returns (bool);

    function addWalletByInvestor(address _address) public virtual returns (bool);

    function removeWallet(
        address _address,
        string memory _id /*onlyExchangeOrAbove walletExists walletBelongsToInvestor(_address, _id)*/
    ) public virtual returns (bool);

    function addOmnibusWallet(
        string memory _id,
        address _omnibusWallet,
        IDSOmnibusWalletController _omnibusWalletController /*onlyIssuerOrAbove newOmnibusWallet*/
    ) public virtual;

    function removeOmnibusWallet(
        string memory _id,
        address _omnibusWallet /*onlyIssuerOrAbove omnibusWalletControllerExists*/
    ) public virtual;

    function getOmnibusWalletController(address _omnibusWallet) public view virtual returns (IDSOmnibusWalletController);

    function isOmnibusWallet(address _omnibusWallet) public view virtual returns (bool);

    function getInvestor(address _address) public view virtual returns (string memory);

    function getInvestorDetails(address _address) public view virtual returns (string memory, string memory);

    function getInvestorDetailsFull(string memory _id)
        public
        view
        virtual
        returns (string memory, uint256[] memory, uint256[] memory, string memory, string memory, string memory, string memory);

    function isInvestor(string memory _id) public view virtual returns (bool);

    function isWallet(address _address) public view virtual returns (bool);

    function isAccreditedInvestor(string calldata _id) external view virtual returns (bool);

    function isQualifiedInvestor(string calldata _id) external view virtual returns (bool);

    function isAccreditedInvestor(address _wallet) external view virtual returns (bool);

    function isQualifiedInvestor(address _wallet) external view virtual returns (bool);

    function getInvestors(address _from, address _to) external view virtual returns (string memory, string memory);
}


// File: contracts/service/IDSServiceConsumer.sol
pragma solidity ^0.8.13;

import "../utils/VersionedContract.sol";
import "../utils/Initializable.sol";
import "../omnibus/IDSOmnibusWalletController.sol";

//SPDX-License-Identifier: UNLICENSED
abstract contract IDSServiceConsumer is Initializable, VersionedContract {

    function initialize() public virtual {
        VERSIONS.push(6);
    }

    uint256 public constant TRUST_SERVICE = 1;
    uint256 public constant DS_TOKEN = 2;
    uint256 public constant REGISTRY_SERVICE = 4;
    uint256 public constant COMPLIANCE_SERVICE = 8;
    uint256 public constant UNUSED_1 = 16;
    uint256 public constant WALLET_MANAGER = 32;
    uint256 public constant LOCK_MANAGER = 64;
    uint256 public constant PARTITIONS_MANAGER = 128;
    uint256 public constant COMPLIANCE_CONFIGURATION_SERVICE = 256;
    uint256 public constant TOKEN_ISSUER = 512;
    uint256 public constant WALLET_REGISTRAR = 1024;
    uint256 public constant OMNIBUS_TBE_CONTROLLER = 2048;
    uint256 public constant TRANSACTION_RELAYER = 4096;
    uint256 public constant TOKEN_REALLOCATOR = 8192;
    uint256 public constant SECURITIZE_SWAP = 16384;

    function getDSService(uint256 _serviceId) public view virtual returns (address);

    function setDSService(
        uint256 _serviceId,
        address _address /*onlyMaster*/
    ) public virtual returns (bool);

    event DSServiceSet(uint256 serviceId, address serviceAddress);
}


// File: contracts/service/ServiceConsumer.sol
pragma solidity ^0.8.13;

import "./IDSServiceConsumer.sol";
import "../data-stores/ServiceConsumerDataStore.sol";
import "../token/IDSToken.sol";
import "../token/IDSTokenPartitioned.sol";
import "../compliance/IDSWalletManager.sol";
import "../compliance/IDSLockManager.sol";
import "../compliance/IDSLockManagerPartitioned.sol";
import "../compliance/IDSComplianceService.sol";
import "../compliance/IDSComplianceServicePartitioned.sol";
import "../compliance/IDSPartitionsManager.sol";
import "../compliance/IDSComplianceConfigurationService.sol";
import "../registry/IDSRegistryService.sol";
import "../omnibus/IDSOmnibusTBEController.sol";
import "../trust/IDSTrustService.sol";
import "../utils/Ownable.sol";

//SPDX-License-Identifier: UNLICENSED
abstract contract ServiceConsumer is IDSServiceConsumer, Ownable, ServiceConsumerDataStore {

    // Bring role constants to save gas both in deployment (less bytecode) and usage
    uint8 public constant ROLE_NONE = 0;
    uint8 public constant ROLE_MASTER = 1;
    uint8 public constant ROLE_ISSUER = 2;
    uint8 public constant ROLE_EXCHANGE = 4;
    uint8 public constant ROLE_TRANSFER_AGENT = 8;

    function initialize() public virtual override(IDSServiceConsumer, Ownable) {
        IDSServiceConsumer.initialize();
        Ownable.initialize();

        VERSIONS.push(6);
    }

    modifier onlyMaster {
        IDSTrustService trustManager = getTrustService();
        require(this.contractOwner() == msg.sender || trustManager.getRole(msg.sender) == ROLE_MASTER, "Insufficient trust level");
        _;
    }

    /**
   * @dev Allow invoking functions only by the users who have the MASTER role or the ISSUER role or the TRANSFER AGENT role.
   */
    modifier onlyIssuerOrTransferAgentOrAbove() {
        IDSTrustService trustManager = getTrustService();
        require(trustManager.getRole(msg.sender) == ROLE_TRANSFER_AGENT || trustManager.getRole(msg.sender) == ROLE_ISSUER || trustManager.getRole(msg.sender) == ROLE_MASTER, "Insufficient trust level");
        _;
    }

    modifier onlyIssuerOrAbove {
        IDSTrustService trustManager = getTrustService();
        require(trustManager.getRole(msg.sender) == ROLE_ISSUER || trustManager.getRole(msg.sender) == ROLE_MASTER, "Insufficient trust level");
        _;
    }

    modifier onlyTransferAgentOrAbove {
        IDSTrustService trustManager = getTrustService();
        require(trustManager.getRole(msg.sender) == ROLE_TRANSFER_AGENT || trustManager.getRole(msg.sender) == ROLE_MASTER, "Insufficient trust level");
        _;
    }

    modifier onlyExchangeOrAbove {
        IDSTrustService trustManager = getTrustService();
        require(
            trustManager.getRole(msg.sender) == ROLE_EXCHANGE
            || trustManager.getRole(msg.sender) == ROLE_ISSUER
            || trustManager.getRole(msg.sender) == ROLE_TRANSFER_AGENT
            || trustManager.getRole(msg.sender) == ROLE_MASTER,
            "Insufficient trust level"
        );
        _;
    }

    modifier onlyToken {
        require(msg.sender == getDSService(DS_TOKEN), "This function can only called by the associated token");
        _;
    }

    modifier onlyRegistry {
        require(msg.sender == getDSService(REGISTRY_SERVICE), "This function can only called by the registry service");
        _;
    }

    modifier onlyIssuerOrAboveOrToken {
        if (msg.sender != getDSService(DS_TOKEN)) {
            IDSTrustService trustManager = IDSTrustService(getDSService(TRUST_SERVICE));
            require(trustManager.getRole(msg.sender) == ROLE_ISSUER || trustManager.getRole(msg.sender) == ROLE_MASTER, "Insufficient trust level");
        }
        _;
    }

    modifier onlyTransferAgentOrAboveOrToken {
        if (msg.sender != getDSService(DS_TOKEN)) {
            IDSTrustService trustManager = IDSTrustService(getDSService(TRUST_SERVICE));
            require(trustManager.getRole(msg.sender) == ROLE_TRANSFER_AGENT || trustManager.getRole(msg.sender) == ROLE_MASTER, "Insufficient trust level");
        }
        _;
    }

    modifier onlyOmnibusWalletController(address omnibusWallet, IDSOmnibusWalletController omnibusWalletController) {
        require(getRegistryService().getOmnibusWalletController(omnibusWallet) == omnibusWalletController, "Wrong controller address");
        _;
    }

    modifier onlyTBEOmnibus {
        require(msg.sender == address(getOmnibusTBEController()), "Not authorized");
        _;
    }

    modifier onlyMasterOrTBEOmnibus {
        IDSTrustService trustManager = getTrustService();
        require(msg.sender == address(getOmnibusTBEController()) ||
        this.contractOwner() == msg.sender || trustManager.getRole(msg.sender) == ROLE_MASTER, "Not authorized");
        _;
    }

    modifier onlyOwnerOrExchangeOrAbove {
        if(!isOwner()) {
            IDSTrustService trustManager = getTrustService();
            require(
                trustManager.getRole(msg.sender) == ROLE_EXCHANGE
                || trustManager.getRole(msg.sender) == ROLE_ISSUER
                || trustManager.getRole(msg.sender) == ROLE_TRANSFER_AGENT
                || trustManager.getRole(msg.sender) == ROLE_MASTER,
                "Insufficient trust level"
            );
        }
        _;
    }

    function getDSService(uint256 _serviceId) public view override returns (address) {
        return services[_serviceId];
    }

    function setDSService(uint256 _serviceId, address _address) public override onlyMaster returns (bool) {
        services[_serviceId] = _address;
        emit DSServiceSet(_serviceId, _address);
        return true;
    }

    function getToken() internal view returns (IDSToken) {
        return IDSToken(getDSService(DS_TOKEN));
    }

    function getTrustService() internal view returns (IDSTrustService) {
        return IDSTrustService(getDSService(TRUST_SERVICE));
    }

    function getWalletManager() internal view returns (IDSWalletManager) {
        return IDSWalletManager(getDSService(WALLET_MANAGER));
    }

    function getLockManager() internal view returns (IDSLockManager) {
        return IDSLockManager(getDSService(LOCK_MANAGER));
    }

    function getLockManagerPartitioned() internal view returns (IDSLockManagerPartitioned) {
        return IDSLockManagerPartitioned(getDSService(LOCK_MANAGER));
    }

    function getComplianceService() internal view returns (IDSComplianceService) {
        return IDSComplianceService(getDSService(COMPLIANCE_SERVICE));
    }

    function getRegistryService() internal view returns (IDSRegistryService) {
        return IDSRegistryService(getDSService(REGISTRY_SERVICE));
    }

    function getPartitionsManager() internal view returns (IDSPartitionsManager) {
        return IDSPartitionsManager(getDSService(PARTITIONS_MANAGER));
    }

    function getTokenPartitioned() internal view returns (IDSTokenPartitioned) {
        return IDSTokenPartitioned(getDSService(DS_TOKEN));
    }

    function getComplianceConfigurationService() internal view returns (IDSComplianceConfigurationService) {
        return IDSComplianceConfigurationService(getDSService(COMPLIANCE_CONFIGURATION_SERVICE));
    }

    function getOmnibusTBEController() internal view returns (IDSOmnibusTBEController) {
        return IDSOmnibusTBEController(getDSService(OMNIBUS_TBE_CONTROLLER));
    }
}


// File: contracts/token/DSToken.sol
pragma solidity ^0.8.13;

import "./IDSToken.sol";
import "../utils/ProxyTarget.sol";
import "./StandardToken.sol";

//SPDX-License-Identifier: UNLICENSED
contract DSToken is ProxyTarget, Initializable, StandardToken {
    // using FeaturesLibrary for SupportedFeatures;
    using TokenLibrary for TokenLibrary.SupportedFeatures;
    uint256 internal constant OMNIBUS_NO_ACTION = 0;

    function initialize(string memory _name, string memory _symbol, uint8 _decimals) public virtual initializer forceInitializeFromProxy {
        StandardToken.initialize();

        VERSIONS.push(5);
        name = _name;
        symbol = _symbol;
        decimals = _decimals;
    }

    /******************************
       TOKEN CONFIGURATION
   *******************************/

    function setFeature(uint8 featureIndex, bool enable) public onlyMaster {
        supportedFeatures.setFeature(featureIndex, enable);
    }

    function setFeatures(uint256 features) public onlyMaster {
        supportedFeatures.value = features;
    }

    function setCap(uint256 _cap) public override onlyTransferAgentOrAbove {
        require(cap == 0, "Token cap already set");
        require(_cap > 0);
        cap = _cap;
    }

    function totalIssued() public view returns (uint256) {
        return tokenData.totalIssued;
    }

    /******************************
       TOKEN ISSUANCE (MINTING)
   *******************************/

    /**
     * @dev Issues unlocked tokens
     * @param _to address The address which is going to receive the newly issued tokens
     * @param _value uint256 the value of tokens to issue
     * @return true if successful
     */
    function issueTokens(
        address _to,
        uint256 _value /*onlyIssuerOrAbove*/
    ) public override returns (bool) {
        issueTokensCustom(_to, _value, block.timestamp, 0, "", 0);
        return true;
    }

    /**
     * @dev Issuing tokens from the fund
     * @param _to address The address which is going to receive the newly issued tokens
     * @param _value uint256 the value of tokens to issue
     * @param _valueLocked uint256 value of tokens, from those issued, to lock immediately.
     * @param _reason reason for token locking
     * @param _releaseTime timestamp to release the lock (or 0 for locks which can only released by an unlockTokens call)
     * @return true if successful
     */
    function issueTokensCustom(address _to, uint256 _value, uint256 _issuanceTime, uint256 _valueLocked, string memory _reason, uint64 _releaseTime)
    public
    virtual
    override
    returns (
    /*onlyIssuerOrAbove*/
        bool
    )
    {
        uint256[] memory valuesLocked;
        uint64[] memory releaseTimes;
        if (_valueLocked > 0) {
            valuesLocked = new uint256[](1);
            releaseTimes = new uint64[](1);
            valuesLocked[0] = _valueLocked;
            releaseTimes[0] = _releaseTime;
        }

        issueTokensWithMultipleLocks(_to, _value, _issuanceTime, valuesLocked, _reason, releaseTimes);
        return true;
    }

    function issueTokensWithMultipleLocks(address _to, uint256 _value, uint256 _issuanceTime, uint256[] memory _valuesLocked, string memory _reason, uint64[] memory _releaseTimes)
    public
    virtual
    override
    onlyIssuerOrAbove
    returns (bool)
    {
        TokenLibrary.issueTokensCustom(tokenData, getCommonServices(), getLockManager(), _to, _value, _issuanceTime, _valuesLocked, _releaseTimes, _reason, cap);
        emit Transfer(address(0), _to, _value);

        checkWalletsForList(address(0), _to);
        return true;
    }

    function issueTokensWithNoCompliance(address _to, uint256 _value) public virtual override onlyIssuerOrAbove {
        require(getRegistryService().isWallet(_to), "Unknown wallet");
        TokenLibrary.issueTokensWithNoCompliance(tokenData, getCommonServices(), _to, _value, block.timestamp, cap);
        emit Transfer(address(0), _to, _value);
    }

    //*********************
    // TOKEN BURNING
    //*********************

    function burn(address _who, uint256 _value, string memory _reason) public virtual override onlyIssuerOrTransferAgentOrAbove {
        TokenLibrary.burn(tokenData, getCommonServices(), _who, _value);
        emit Burn(_who, _value, _reason);
        emit Transfer(_who, address(0), _value);
        checkWalletsForList(_who, address(0));
    }

    function omnibusBurn(address _omnibusWallet, address _who, uint256 _value, string memory _reason) public override onlyTransferAgentOrAbove {
        require(_value <= tokenData.walletsBalances[_omnibusWallet]);
        TokenLibrary.omnibusBurn(tokenData, getCommonServices(), _omnibusWallet, _who, _value);
        emit OmnibusBurn(_omnibusWallet, _who, _value, _reason, getAssetTrackingMode(_omnibusWallet));
        emit Burn(_omnibusWallet, _value, _reason);
        emit Transfer(_omnibusWallet, address(0), _value);
        checkWalletsForList(_omnibusWallet, address(0));
    }

    //*********************
    // TOKEN SEIZING
    //*********************

    function seize(address _from, address _to, uint256 _value, string memory _reason) public virtual override onlyTransferAgentOrAbove {
        TokenLibrary.seize(tokenData, getCommonServices(), _from, _to, _value);
        emit Seize(_from, _to, _value, _reason);
        emit Transfer(_from, _to, _value);
        checkWalletsForList(_from, _to);
    }

    function omnibusSeize(address _omnibusWallet, address _from, address _to, uint256 _value, string memory _reason) public override onlyTransferAgentOrAbove {
        TokenLibrary.omnibusSeize(tokenData, getCommonServices(), _omnibusWallet, _from, _to, _value);
        emit OmnibusSeize(_omnibusWallet, _from, _value, _reason, getAssetTrackingMode(_omnibusWallet));
        emit Seize(_omnibusWallet, _to, _value, _reason);
        emit Transfer(_omnibusWallet, _to, _value);
        checkWalletsForList(_omnibusWallet, _to);
    }

    //*********************
    // TRANSFER RESTRICTIONS
    //*********************

    /**
     * @dev Checks whether it can transfer with the compliance manager, if not -throws.
     */
    modifier canTransfer(address _sender, address _receiver, uint256 _value) {
        getComplianceService().validateTransfer(_sender, _receiver, _value, paused, super.balanceOf(_sender));
        _;
    }

    /**
     * @dev override for transfer with modifiers:
     * whether the token is not paused (checked in super class)
     * and that the sender is allowed to transfer tokens
     * @param _to The address that will receive the tokens.
     * @param _value The amount of tokens to be transferred.
     */
    function transfer(address _to, uint256 _value) public virtual override canTransfer(msg.sender, _to, _value) returns (bool) {
        return postTransferImpl(super.transfer(_to, _value), msg.sender, _to, _value);
    }

    /**
     * @dev override for transfer with modifiers:
     * whether the token is not paused (checked in super class)
     * and that the sender is allowed to transfer tokens
     * @param _from The address that will send the tokens.
     * @param _to The address that will receive the tokens.
     * @param _value The amount of tokens to be transferred.
     */
    function transferFrom(address _from, address _to, uint256 _value) public virtual override canTransfer(_from, _to, _value) returns (bool) {
        return postTransferImpl(super.transferFrom(_from, _to, _value), _from, _to, _value);
    }

    function postTransferImpl(bool _superResult, address _from, address _to, uint256 _value) internal returns (bool) {
        if (_superResult) {
            updateInvestorsBalancesOnTransfer(_from, _to, _value);
        }

        checkWalletsForList(_from, _to);

        return _superResult;
    }

    //*********************
    // WALLET ENUMERATION
    //****

    function getWalletAt(uint256 _index) public view override returns (address) {
        require(_index > 0 && _index <= walletsCount);
        return walletsList[_index];
    }

    function walletCount() public view override returns (uint256) {
        return walletsCount;
    }

    function checkWalletsForList(address _from, address _to) private {
        if (super.balanceOf(_from) == 0) {
            removeWalletFromList(_from);
        }
        if (super.balanceOf(_to) > 0) {
            addWalletToList(_to);
        }
    }

    function addWalletToList(address _address) private {
        //Check if it's already there
        uint256 existingIndex = walletsToIndexes[_address];
        if (existingIndex == 0) {
            //If not - add it
            uint256 index = walletsCount + 1;
            walletsList[index] = _address;
            walletsToIndexes[_address] = index;
            walletsCount = index;
        }
    }

    function removeWalletFromList(address _address) private {
        //Make sure it's there
        uint256 existingIndex = walletsToIndexes[_address];
        if (existingIndex != 0) {
            uint256 lastIndex = walletsCount;
            if (lastIndex != existingIndex) {
                //Put the last wallet instead of it (this will work even with 1 wallet in the list)
                address lastWalletAddress = walletsList[lastIndex];
                walletsList[existingIndex] = lastWalletAddress;
                walletsToIndexes[lastWalletAddress] = existingIndex;
            }

            delete walletsToIndexes[_address];
            delete walletsList[lastIndex];
            walletsCount = lastIndex - 1;
        }
    }

    //**************************************
    // MISCELLANEOUS FUNCTIONS
    //**************************************

    function balanceOfInvestor(string memory _id) public view override returns (uint256) {
        return tokenData.investorsBalances[_id];
    }

    function getAssetTrackingMode(address _omnibusWallet) internal view returns (uint8) {
        return getRegistryService().getOmnibusWalletController(_omnibusWallet).getAssetTrackingMode();
    }

    function updateOmnibusInvestorBalance(address _omnibusWallet, address _wallet, uint256 _value, CommonUtils.IncDec _increase)
    public
    override
    onlyOmnibusWalletController(_omnibusWallet, IDSOmnibusWalletController(msg.sender))
    returns (bool)
    {
        return updateInvestorBalance(_wallet, _value, _increase);
    }

    function emitOmnibusTransferEvent(address _omnibusWallet, address _from, address _to, uint256 _value)
    public
    override
    onlyOmnibusWalletController(_omnibusWallet, IDSOmnibusWalletController(msg.sender))
    {
        emit OmnibusTransfer(_omnibusWallet, _from, _to, _value, getAssetTrackingMode(_omnibusWallet));
    }

    function emitOmnibusTBEEvent(address omnibusWallet, int256 totalDelta, int256 accreditedDelta,
        int256 usAccreditedDelta, int256 usTotalDelta, int256 jpTotalDelta) public override onlyTBEOmnibus {
        emit OmnibusTBEOperation(omnibusWallet, totalDelta, accreditedDelta, usAccreditedDelta, usTotalDelta, jpTotalDelta);
    }

    function emitOmnibusTBETransferEvent(address omnibusWallet, string memory externalId) public override onlyTBEOmnibus {
        emit OmnibusTBETransfer(omnibusWallet, externalId);
    }

    function updateInvestorsBalancesOnTransfer(address _from, address _to, uint256 _value) internal {
        uint256 omnibusEvent = TokenLibrary.applyOmnibusBalanceUpdatesOnTransfer(tokenData, getRegistryService(), _from, _to, _value);
        if (omnibusEvent == OMNIBUS_NO_ACTION) {
            updateInvestorBalance(_from, _value, CommonUtils.IncDec.Decrease);
            updateInvestorBalance(_to, _value, CommonUtils.IncDec.Increase);
        }
    }

    function updateInvestorBalance(address _wallet, uint256 _value, CommonUtils.IncDec _increase) internal override returns (bool) {
        string memory investor = getRegistryService().getInvestor(_wallet);
        if (!CommonUtils.isEmptyString(investor)) {
            uint256 balance = balanceOfInvestor(investor);
            if (_increase == CommonUtils.IncDec.Increase) {
                balance += _value;
            } else {
                balance -= _value;
            }
            tokenData.investorsBalances[investor] = balance;
        }

        return true;
    }

    function preTransferCheck(address _from, address _to, uint256 _value) public view override returns (uint256 code, string memory reason) {
        return getComplianceService().preTransferCheck(_from, _to, _value);
    }

    function getCommonServices() internal view returns (address[] memory) {
        address[] memory services = new address[](3);
        services[0] = getDSService(COMPLIANCE_SERVICE);
        services[1] = getDSService(REGISTRY_SERVICE);
        services[2] = getDSService(OMNIBUS_TBE_CONTROLLER);
        return services;
    }
}


// File: contracts/token/IDSToken.sol
pragma solidity ^0.8.13;

import "../utils/CommonUtils.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "../utils/VersionedContract.sol";
import "../utils/Initializable.sol";
import "../omnibus/IDSOmnibusWalletController.sol";

//SPDX-License-Identifier: UNLICENSED
abstract contract IDSToken is IERC20, Initializable, VersionedContract {
    event Issue(address indexed to, uint256 value, uint256 valueLocked);
    event Burn(address indexed burner, uint256 value, string reason);
    event Seize(address indexed from, address indexed to, uint256 value, string reason);
    event OmnibusDeposit(address indexed omnibusWallet, address to, uint256 value, uint8 assetTrackingMode);
    event OmnibusWithdraw(address indexed omnibusWallet, address from, uint256 value, uint8 assetTrackingMode);
    event OmnibusSeize(address indexed omnibusWallet, address from, uint256 value, string reason, uint8 assetTrackingMode);
    event OmnibusBurn(address indexed omnibusWallet, address who, uint256 value, string reason, uint8 assetTrackingMode);
    event OmnibusTransfer(address indexed omnibusWallet, address from, address to, uint256 value, uint8 assetTrackingMode);
    event OmnibusTBEOperation(address indexed omnibusWallet, int256 totalDelta, int256 accreditedDelta,
        int256 usAccreditedDelta, int256 usTotalDelta, int256 jpTotalDelta);
    event OmnibusTBETransfer(address omnibusWallet, string externalId);

    event WalletAdded(address wallet);
    event WalletRemoved(address wallet);

    function initialize() public virtual {
        VERSIONS.push(3);
    }

    /******************************
       CONFIGURATION
   *******************************/

    /**
     * @dev Sets the total issuance cap
     * Note: The cap is compared to the total number of issued token, not the total number of tokens available,
     * So if a token is burned, it is not removed from the "total number of issued".
     * This call cannot be called again after it was called once.
     * @param _cap address The address which is going to receive the newly issued tokens
     */
    function setCap(
        uint256 _cap /*onlyMaster*/
    ) public virtual;

    /******************************
       TOKEN ISSUANCE (MINTING)
   *******************************/

    /**
     * @dev Issues unlocked tokens
     * @param _to address The address which is going to receive the newly issued tokens
     * @param _value uint256 the value of tokens to issue
     * @return true if successful
     */
    function issueTokens(
        address _to,
        uint256 _value /*onlyIssuerOrAbove*/
    ) public virtual returns (bool);

    /**
     * @dev Issuing tokens from the fund
     * @param _to address The address which is going to receive the newly issued tokens
     * @param _value uint256 the value of tokens to issue
     * @param _valueLocked uint256 value of tokens, from those issued, to lock immediately.
     * @param _reason reason for token locking
     * @param _releaseTime timestamp to release the lock (or 0 for locks which can only released by an unlockTokens call)
     * @return true if successful
     */
    function issueTokensCustom(
        address _to,
        uint256 _value,
        uint256 _issuanceTime,
        uint256 _valueLocked,
        string memory _reason,
        uint64 _releaseTime /*onlyIssuerOrAbove*/
    ) public virtual returns (bool);

    function issueTokensWithMultipleLocks(
        address _to,
        uint256 _value,
        uint256 _issuanceTime,
        uint256[] memory _valuesLocked,
        string memory _reason,
        uint64[] memory _releaseTimes /*onlyIssuerOrAbove*/
    ) public virtual returns (bool);

    function issueTokensWithNoCompliance(address _to, uint256 _value) public virtual /*onlyIssuerOrAbove*/;

    //*********************
    // TOKEN BURNING
    //*********************

    function burn(
        address _who,
        uint256 _value,
        string memory _reason /*onlyIssuerOrAbove*/
    ) public virtual;

    function omnibusBurn(
        address _omnibusWallet,
        address _who,
        uint256 _value,
        string memory _reason /*onlyIssuerOrAbove*/
    ) public virtual;

    //*********************
    // TOKEN SIEZING
    //*********************

    function seize(
        address _from,
        address _to,
        uint256 _value,
        string memory _reason /*onlyIssuerOrAbove*/
    ) public virtual;

    function omnibusSeize(
        address _omnibusWallet,
        address _from,
        address _to,
        uint256 _value,
        string memory _reason
        /*onlyIssuerOrAbove*/
    ) public virtual;

    //*********************
    // WALLET ENUMERATION
    //*********************

    function getWalletAt(uint256 _index) public view virtual returns (address);

    function walletCount() public view virtual returns (uint256);

    //**************************************
    // MISCELLANEOUS FUNCTIONS
    //**************************************
    function isPaused() public view virtual returns (bool);

    function balanceOfInvestor(string memory _id) public view virtual returns (uint256);

    function updateOmnibusInvestorBalance(
        address _omnibusWallet,
        address _wallet,
        uint256 _value,
        CommonUtils.IncDec _increase /*onlyOmnibusWalletController*/
    ) public virtual returns (bool);

    function emitOmnibusTransferEvent(
        address _omnibusWallet,
        address _from,
        address _to,
        uint256 _value /*onlyOmnibusWalletController*/
    ) public virtual;

    function emitOmnibusTBEEvent(address omnibusWallet, int256 totalDelta, int256 accreditedDelta,
        int256 usAccreditedDelta, int256 usTotalDelta, int256 jpTotalDelta /*onlyTBEOmnibus*/
    ) public virtual;

    function emitOmnibusTBETransferEvent(address omnibusWallet, string memory externalId) public virtual;

    function updateInvestorBalance(address _wallet, uint256 _value, CommonUtils.IncDec _increase) internal virtual returns (bool);

    function preTransferCheck(address _from, address _to, uint256 _value) public view virtual returns (uint256 code, string memory reason);
}


// File: contracts/token/IDSTokenPartitioned.sol
pragma solidity ^0.8.13;

import "./IDSToken.sol";

//SPDX-License-Identifier: UNLICENSED
abstract contract IDSTokenPartitioned {

    function balanceOfByPartition(address _who, bytes32 _partition) public view virtual returns (uint256);

    function balanceOfInvestorByPartition(string memory _id, bytes32 _partition) public view virtual returns (uint256);

    function partitionCountOf(address _who) public view virtual returns (uint256);

    function partitionOf(address _who, uint256 _index) public view virtual returns (bytes32);

    function transferByPartitions(address _to, uint256 _value, bytes32[] memory _partitions, uint256[] memory _values) public virtual returns (bool);

    function transferFromByPartitions(address _from, address _to, uint256 _value, bytes32[] memory _partitions, uint256[] memory _values) public virtual returns (bool);

    function burnByPartition(
        address _who,
        uint256 _value,
        string memory _reason,
        bytes32 _partition /*onlyIssuerOrAbove*/
    ) public virtual;

    function seizeByPartition(
        address _from,
        address _to,
        uint256 _value,
        string memory _reason,
        bytes32 _partition /*onlyIssuerOrAbove*/
    ) public virtual;

    event TransferByPartition(address indexed from, address indexed to, uint256 value, bytes32 indexed partition);
    event IssueByPartition(address indexed to, uint256 value, bytes32 indexed partition);
    event BurnByPartition(address indexed burner, uint256 value, string reason, bytes32 indexed partition);
    event SeizeByPartition(address indexed from, address indexed to, uint256 value, string reason, bytes32 indexed partition);
}


// File: contracts/token/StandardToken.sol
pragma solidity ^0.8.13;

import "../service/ServiceConsumer.sol";
import "../data-stores/TokenDataStore.sol";
import "../omnibus/OmnibusTBEController.sol";

//SPDX-License-Identifier: UNLICENSED
abstract contract StandardToken is IDSToken, ServiceConsumer, TokenDataStore {
    event Pause();
    event Unpause();

    function initialize() public virtual override(IDSToken, ServiceConsumer) {
        IDSToken.initialize();
        ServiceConsumer.initialize();
        VERSIONS.push(5);
    }

    modifier whenNotPaused() {
        require(!paused, "Contract is paused");
        _;
    }

    modifier whenPaused() {
        require(paused, "Contract is not paused");
        _;
    }

    function pause() public onlyTransferAgentOrAbove whenNotPaused {
        paused = true;
        emit Pause();
    }

    function unpause() public onlyTransferAgentOrAbove whenPaused {
        paused = false;
        emit Unpause();
    }

    function isPaused() public view override returns (bool) {
        return paused;
    }

    /**
     * @dev Gets the balance of the specified address.
     * @param _owner The address to query the the balance of.
     * @return An uint256 representing the amount owned by the passed address.
     */
    function balanceOf(address _owner) public view returns (uint256) {
        return tokenData.walletsBalances[_owner];
    }

    function totalSupply() public view returns (uint256) {
        return tokenData.totalSupply;
    }

    /**
     * @dev transfer token for a specified address
     * @param _to The address to transfer to.
     * @param _value The amount to be transferred.
     */
    function transfer(address _to, uint256 _value) public virtual returns (bool) {
        return transferImpl(msg.sender, _to, _value);
    }

    function transferFrom(
        address _from,
        address _to,
        uint256 _value
    ) public virtual returns (bool) {
        IDSOmnibusTBEController tbeController = getOmnibusTBEController();
        if (!(msg.sender == address(tbeController) && _from == tbeController.getOmnibusWallet())) {
            require(_value <= allowances[_from][msg.sender], "Not enough allowance");
            allowances[_from][msg.sender] -= _value;
        }
        return transferImpl(_from, _to, _value);
    }

    function transferImpl(
        address _from,
        address _to,
        uint256 _value
    ) internal returns (bool) {
        require(_to != address(0));
        require(_value <= tokenData.walletsBalances[_from]);

        tokenData.walletsBalances[_from] -= _value;
        tokenData.walletsBalances[_to] += _value;

        emit Transfer(_from, _to, _value);

        return true;
    }

    function approve(address _spender, uint256 _value) public returns (bool) {
        allowances[msg.sender][_spender] = _value;
        emit Approval(msg.sender, _spender, _value);
        return true;
    }

    function allowance(address _owner, address _spender) public view returns (uint256) {
        return allowances[_owner][_spender];
    }

    function increaseApproval(address _spender, uint256 _addedValue) public returns (bool) {
        allowances[msg.sender][_spender] = allowances[msg.sender][_spender] + _addedValue;
        emit Approval(msg.sender, _spender, allowances[msg.sender][_spender]);
        return true;
    }

    function decreaseApproval(address _spender, uint256 _subtractedValue) public returns (bool) {
        uint256 oldValue = allowances[msg.sender][_spender];
        if (_subtractedValue > oldValue) {
            allowances[msg.sender][_spender] = 0;
        } else {
            allowances[msg.sender][_spender] = oldValue - _subtractedValue;
        }
        emit Approval(msg.sender, _spender, allowances[msg.sender][_spender]);
        return true;
    }
}


// File: contracts/token/TokenLibrary.sol
pragma solidity ^0.8.13;

import "../service/ServiceConsumer.sol";

//SPDX-License-Identifier: UNLICENSED
library TokenLibrary {
    event OmnibusDeposit(address indexed omnibusWallet, address to, uint256 value, uint8 assetTrackingMode);
    event OmnibusWithdraw(address indexed omnibusWallet, address from, uint256 value, uint8 assetTrackingMode);
    event Issue(address indexed to, uint256 value, uint256 valueLocked);

    uint256 internal constant COMPLIANCE_SERVICE = 0;
    uint256 internal constant REGISTRY_SERVICE = 1;
    uint256 internal constant OMNIBUS_NO_ACTION = 0;
    uint256 internal constant OMNIBUS_DEPOSIT = 1;
    uint256 internal constant OMNIBUS_WITHDRAW = 2;
    using SafeMath for uint256;

    struct TokenData {
        mapping(address => uint256) walletsBalances;
        mapping(string => uint256) investorsBalances;
        uint256 totalSupply;
        uint256 totalIssued;
    }

    struct SupportedFeatures {
        uint256 value;
    }

    function setFeature(SupportedFeatures storage supportedFeatures, uint8 featureIndex, bool enable) public {
        uint256 base = 2;
        uint256 mask = base**featureIndex;

        // Enable only if the feature is turned off and disable only if the feature is turned on
        if (enable && (supportedFeatures.value & mask == 0)) {
            supportedFeatures.value = supportedFeatures.value ^ mask;
        } else if (!enable && (supportedFeatures.value & mask >= 1)) {
            supportedFeatures.value = supportedFeatures.value ^ mask;
        }
    }

    function issueTokensCustom(
        TokenData storage _tokenData,
        address[] memory _services,
        IDSLockManager _lockManager,
        address _to,
        uint256 _value,
        uint256 _issuanceTime,
        uint256[] memory _valuesLocked,
        uint64[] memory _releaseTimes,
        string memory _reason,
        uint256 _cap
    ) public returns (bool) {
        //Check input values
        require(_to != address(0), "Invalid address");
        require(_value > 0, "Value is zero");
        require(_valuesLocked.length == _releaseTimes.length, "Wrong length of parameters");

        //Make sure we are not hitting the cap
        require(_cap == 0 || _tokenData.totalIssued + _value <= _cap, "Token Cap Hit");

        //Check issuance is allowed (and inform the compliance manager, possibly adding locks)
        IDSComplianceService(_services[COMPLIANCE_SERVICE]).validateIssuance(_to, _value, _issuanceTime);

        _tokenData.totalSupply += _value;
        _tokenData.totalIssued += _value;
        _tokenData.walletsBalances[_to] += _value;
        updateInvestorBalance(_tokenData, IDSRegistryService(_services[REGISTRY_SERVICE]), _to, _value, CommonUtils.IncDec.Increase);

        uint256 totalLocked = 0;
        for (uint256 i = 0; i < _valuesLocked.length; i++) {
            totalLocked += _valuesLocked[i];
            _lockManager.addManualLockRecord(_to, _valuesLocked[i], _reason, _releaseTimes[i]);
        }
        require(totalLocked <= _value, "valueLocked must be smaller than value");
        emit Issue(_to, _value, totalLocked);
        return true;
    }

    function issueTokensWithNoCompliance(
        TokenData storage _tokenData,
        address[] memory _services,
        address _to,
        uint256 _value,
        uint256 _issuanceTime,
        uint256 _cap
    ) public returns (bool) {
        //Make sure we are not hitting the cap
        require(_cap == 0 || _tokenData.totalIssued + _value <= _cap, "Token Cap Hit");

        //Check and inform issuance
        IDSComplianceService(_services[COMPLIANCE_SERVICE]).validateIssuanceWithNoCompliance(_to, _value, _issuanceTime);

        _tokenData.totalSupply += _value;
        _tokenData.totalIssued += _value;
        _tokenData.walletsBalances[_to] += _value;
        updateInvestorBalance(_tokenData, IDSRegistryService(_services[REGISTRY_SERVICE]), _to, _value, CommonUtils.IncDec.Increase);

        emit Issue(_to, _value, 0);
        return true;
    }

    modifier validSeizeParameters(TokenData storage _tokenData, address _from, address _to, uint256 _value) {
        require(_from != address(0), "Invalid address");
        require(_to != address(0), "Invalid address");
        require(_value <= _tokenData.walletsBalances[_from], "Not enough balance");

        _;
    }

    function burn(TokenData storage _tokenData, address[] memory _services, address _who, uint256 _value) public {
        require(_value <= _tokenData.walletsBalances[_who], "Not enough balance");
        // no need to require value <= totalSupply, since that would imply the
        // sender's balance is greater than the totalSupply, which *should* be an assertion failure

        IDSComplianceService(_services[COMPLIANCE_SERVICE]).validateBurn(_who, _value);

        _tokenData.walletsBalances[_who] -= _value;
        updateInvestorBalance(_tokenData, IDSRegistryService(_services[REGISTRY_SERVICE]), _who, _value, CommonUtils.IncDec.Decrease);
        _tokenData.totalSupply -= _value;
    }

    function seize(TokenData storage _tokenData, address[] memory _services, address _from, address _to, uint256 _value)
    public
    validSeizeParameters(_tokenData, _from, _to, _value)
    {
        IDSRegistryService registryService = IDSRegistryService(_services[REGISTRY_SERVICE]);
        IDSComplianceService(_services[COMPLIANCE_SERVICE]).validateSeize(_from, _to, _value);
        _tokenData.walletsBalances[_from] -= _value;
        _tokenData.walletsBalances[_to] += _value;
        updateInvestorBalance(_tokenData, registryService, _from, _value, CommonUtils.IncDec.Decrease);
        updateInvestorBalance(_tokenData, registryService, _to, _value, CommonUtils.IncDec.Increase);
    }

    function omnibusBurn(TokenData storage _tokenData, address[] memory _services, address _omnibusWallet, address _who, uint256 _value) public {
        IDSRegistryService registryService = IDSRegistryService(_services[REGISTRY_SERVICE]);
        IDSOmnibusWalletController omnibusController = IDSRegistryService(_services[REGISTRY_SERVICE]).getOmnibusWalletController(_omnibusWallet);
        _tokenData.walletsBalances[_omnibusWallet] -= _value;
        omnibusController.burn(_who, _value);
        decreaseInvestorBalanceOnOmnibusSeizeOrBurn(_tokenData, registryService, omnibusController, _omnibusWallet, _who, _value);
        _tokenData.totalSupply -= _value;
    }

    function omnibusSeize(TokenData storage _tokenData, address[] memory _services, address _omnibusWallet, address _from, address _to, uint256 _value)
    public
    validSeizeParameters(_tokenData, _omnibusWallet, _to, _value)
    {
        IDSRegistryService registryService = IDSRegistryService(_services[REGISTRY_SERVICE]);
        IDSOmnibusWalletController omnibusController = registryService.getOmnibusWalletController(_omnibusWallet);

        _tokenData.walletsBalances[_omnibusWallet] -= _value;
        _tokenData.walletsBalances[_to] += _value;
        omnibusController.seize(_from, _value);
        decreaseInvestorBalanceOnOmnibusSeizeOrBurn(_tokenData, registryService, omnibusController, _omnibusWallet, _from, _value);
        updateInvestorBalance(_tokenData, registryService, _to, _value, CommonUtils.IncDec.Increase);
    }

    function decreaseInvestorBalanceOnOmnibusSeizeOrBurn(
        TokenData storage _tokenData,
        IDSRegistryService _registryService,
        IDSOmnibusWalletController _omnibusController,
        address _omnibusWallet,
        address _from,
        uint256 _value
    ) internal {
        if (_omnibusController.isHolderOfRecord()) {
            updateInvestorBalance(_tokenData, _registryService, _omnibusWallet, _value, CommonUtils.IncDec.Decrease);
        } else {
            updateInvestorBalance(_tokenData, _registryService, _from, _value, CommonUtils.IncDec.Decrease);
        }
    }

    function applyOmnibusBalanceUpdatesOnTransfer(TokenData storage _tokenData, IDSRegistryService _registryService, address _from, address _to, uint256 _value)
    public
    returns (uint256)
    {
        if (_registryService.isOmnibusWallet(_to)) {
            IDSOmnibusWalletController omnibusWalletController = _registryService.getOmnibusWalletController(_to);
            omnibusWalletController.deposit(_from, _value);
            emit OmnibusDeposit(_to, _from, _value, omnibusWalletController.getAssetTrackingMode());

            if (omnibusWalletController.isHolderOfRecord()) {
                updateInvestorBalance(_tokenData, _registryService, _from, _value, CommonUtils.IncDec.Decrease);
                updateInvestorBalance(_tokenData, _registryService, _to, _value, CommonUtils.IncDec.Increase);
            }
            return OMNIBUS_DEPOSIT;
        } else if (_registryService.isOmnibusWallet(_from)) {
            IDSOmnibusWalletController omnibusWalletController = _registryService.getOmnibusWalletController(_from);
            omnibusWalletController.withdraw(_to, _value);
            emit OmnibusWithdraw(_from, _to, _value, omnibusWalletController.getAssetTrackingMode());

            if (omnibusWalletController.isHolderOfRecord()) {
                updateInvestorBalance(_tokenData, _registryService, _from, _value, CommonUtils.IncDec.Decrease);
                updateInvestorBalance(_tokenData, _registryService, _to, _value, CommonUtils.IncDec.Increase);
            }
            return OMNIBUS_WITHDRAW;
        }
        return OMNIBUS_NO_ACTION;
    }

    function updateInvestorBalance(TokenData storage _tokenData, IDSRegistryService _registryService, address _wallet, uint256 _value, CommonUtils.IncDec _increase) internal returns (bool) {
        string memory investor = _registryService.getInvestor(_wallet);
        if (!CommonUtils.isEmptyString(investor)) {
            uint256 balance = _tokenData.investorsBalances[investor];
            if (_increase == CommonUtils.IncDec.Increase) {
                balance += _value;
            } else {
                balance -= _value;
            }
            _tokenData.investorsBalances[investor] = balance;
        }

        return true;
    }
}


// File: contracts/token/TokenPartitionsLibrary.sol
pragma solidity ^0.8.13;

import "../utils/CommonUtils.sol";
import "../compliance/IDSComplianceServicePartitioned.sol";
import "../compliance/IDSLockManagerPartitioned.sol";
import "../registry/IDSRegistryService.sol";
import "../compliance/IDSComplianceConfigurationService.sol";
import "../compliance/IDSPartitionsManager.sol";
import "../omnibus/IDSOmnibusTBEController.sol";
import "@openzeppelin/contracts/utils/math/SafeMath.sol";
import "@openzeppelin/contracts/utils/math/Math.sol";

//SPDX-License-Identifier: UNLICENSED
library TokenPartitionsLibrary {
    using SafeMath for uint256;

    uint256 internal constant COMPLIANCE_SERVICE = 0;
    uint256 internal constant REGISTRY_SERVICE = 1;
    uint256 internal constant OMNIBUS_TBE_CONTROLLER = 2;

    event IssueByPartition(address indexed to, uint256 value, bytes32 indexed partition);
    event TransferByPartition(address indexed from, address indexed to, uint256 value, bytes32 indexed partition);
    struct AddressPartitions {
        uint256 count;
        mapping(bytes32 => uint256) toIndex;
        mapping(uint256 => bytes32) partitions;
        mapping(bytes32 => uint256) balances;
    }

    struct TokenPartitions {
        mapping(address => AddressPartitions) walletPartitions;
        mapping(string => mapping(bytes32 => uint256)) investorPartitionsBalances;
    }

    function issueTokensCustom(
        TokenPartitions storage self,
        IDSRegistryService _registry,
        IDSComplianceConfigurationService _compConf,
        IDSPartitionsManager _partitionsManager,
        IDSLockManagerPartitioned _lockManager,
        address _to,
        uint256 _value,
        uint256 _issuanceTime,
        uint256[] memory _valuesLocked,
        string memory _reason,
        uint64[] memory _releaseTimes
    ) public returns (bool) {
        string memory investor = _registry.getInvestor(_to);
        string memory country = _registry.getCountry(investor);
        bytes32 partition = _partitionsManager.ensurePartition(_issuanceTime, _compConf.getCountryCompliance(country));
        emit IssueByPartition(_to, _value, partition);
        transferPartition(self, _registry, address(0), _to, _value, partition);
        uint256 totalLocked = 0;
        for (uint256 i = 0; i < _valuesLocked.length; i++) {
            totalLocked += _valuesLocked[i];
            _lockManager.createLockForInvestor(investor, _valuesLocked[i], 0, _reason, _releaseTimes[i], partition);
        }
        require(totalLocked <= _value, "valueLocked must be smaller than value");

        return true;
    }

    function issueTokensWithNoCompliance(
        TokenPartitions storage self,
        IDSRegistryService _registry,
        IDSComplianceConfigurationService _compConf,
        IDSPartitionsManager _partitionsManager,
        address _to,
        uint256 _value,
        uint256 _issuanceTime
    ) public returns (bool) {
        string memory investor = _registry.getInvestor(_to);
        string memory country = _registry.getCountry(investor);
        bytes32 partition = _partitionsManager.ensurePartition(_issuanceTime, _compConf.getCountryCompliance(country));
        emit IssueByPartition(_to, _value, partition);
        transferPartition(self, _registry, address(0), _to, _value, partition);
        return true;
    }

    function setPartitionToAddressImpl(TokenPartitions storage self, address _who, uint256 _index, bytes32 _partition) internal returns (bool) {
        self.walletPartitions[_who].partitions[_index] = _partition;
        self.walletPartitions[_who].toIndex[_partition] = _index;
        return true;
    }

    function addPartitionToAddress(TokenPartitions storage self, address _who, bytes32 _partition) internal {
        uint256 partitionCount = self.walletPartitions[_who].count;
        setPartitionToAddressImpl(self, _who, self.walletPartitions[_who].count, _partition);
        self.walletPartitions[_who].count = SafeMath.add(partitionCount, 1);
    }

    function removePartitionFromAddress(TokenPartitions storage self, address _from, bytes32 _partition) internal {
        uint256 oldIndex = self.walletPartitions[_from].toIndex[_partition];
        uint256 lastPartitionIndex = SafeMath.sub(self.walletPartitions[_from].count, 1);
        bytes32 lastPartition = self.walletPartitions[_from].partitions[lastPartitionIndex];

        setPartitionToAddressImpl(self, _from, oldIndex, lastPartition);

        delete self.walletPartitions[_from].partitions[lastPartitionIndex];
        delete self.walletPartitions[_from].toIndex[_partition];
        delete self.walletPartitions[_from].balances[_partition];
        self.walletPartitions[_from].count = SafeMath.sub(self.walletPartitions[_from].count, 1);
    }

    function transferPartition(TokenPartitions storage self, IDSRegistryService _registry, address _from, address _to, uint256 _value, bytes32 _partition) public {
        if (_from != address(0)) {
            self.walletPartitions[_from].balances[_partition] = SafeMath.sub(self.walletPartitions[_from].balances[_partition], _value);
            updateInvestorPartitionBalance(self, _registry, _from, _value, CommonUtils.IncDec.Decrease, _partition);
            if (self.walletPartitions[_from].balances[_partition] == 0) {
                removePartitionFromAddress(self, _from, _partition);
            }
        }

        if (_to != address(0)) {
            if (self.walletPartitions[_to].balances[_partition] == 0 && _value > 0) {
                addPartitionToAddress(self, _to, _partition);
            }
            self.walletPartitions[_to].balances[_partition] += _value;
            updateInvestorPartitionBalance(self, _registry, _to, _value, CommonUtils.IncDec.Increase, _partition);
        }
        emit TransferByPartition(_from, _to, _value, _partition);
    }

    function transferPartitions(TokenPartitions storage self, address[] memory _services, address _from, address _to, uint256 _value) public returns (bool) {
        uint256 partitionCount = partitionCountOf(self, _from);
        uint256 index = 0;
        bool skipComplianceCheck = shouldSkipComplianceCheck(IDSRegistryService(_services[REGISTRY_SERVICE]),
            IDSOmnibusTBEController(_services[OMNIBUS_TBE_CONTROLLER]), _from, _to);
        while (_value > 0 && index < partitionCount) {
            bytes32 partition = partitionOf(self, _from, index);
            uint256 transferableInPartition = skipComplianceCheck
                ? self.walletPartitions[_from].balances[partition]
                : IDSComplianceServicePartitioned(_services[COMPLIANCE_SERVICE]).getComplianceTransferableTokens(_from, block.timestamp, _to, partition);
            uint256 transferable = Math.min(_value, transferableInPartition);
            if (transferable > 0) {
                if (self.walletPartitions[_from].balances[partition] == transferable) {
                    unchecked {
                        --index;
                        --partitionCount;
                    }
                }
                transferPartition(self, IDSRegistryService(_services[REGISTRY_SERVICE]), _from, _to, transferable, partition);
                _value -= transferable;
            }
            unchecked {
                ++index;
            }
        }

        require(_value == 0);

        return true;
    }

    function transferPartitions(
        TokenPartitions storage self,
        address[] memory _services,
        address _from,
        address _to,
        uint256 _value,
        bytes32[] memory _partitions,
        uint256[] memory _values
    ) public returns (bool) {
        require(_partitions.length == _values.length);
        bool skipComplianceCheck = shouldSkipComplianceCheck(IDSRegistryService(_services[REGISTRY_SERVICE]),
            IDSOmnibusTBEController(_services[OMNIBUS_TBE_CONTROLLER]), _from, _to);
        for (uint256 index = 0; index < _partitions.length; ++index) {
            if (!skipComplianceCheck) {
                require(_values[index] <= IDSComplianceServicePartitioned(_services[COMPLIANCE_SERVICE]).getComplianceTransferableTokens(_from, block.timestamp, _to, _partitions[index]));
            }
            transferPartition(self, IDSRegistryService(_services[REGISTRY_SERVICE]), _from, _to, _values[index], _partitions[index]);
            _value -= _values[index];
        }

        require(_value == 0);
        return true;
    }

    function balanceOfByPartition(TokenPartitions storage self, address _who, bytes32 _partition) internal view returns (uint256) {
        return self.walletPartitions[_who].balances[_partition];
    }

    function balanceOfInvestorByPartition(TokenPartitions storage self, string memory _id, bytes32 _partition) internal view returns (uint256) {
        return self.investorPartitionsBalances[_id][_partition];
    }

    function partitionCountOf(TokenPartitions storage self, address _who) internal view returns (uint256) {
        return self.walletPartitions[_who].count;
    }

    function partitionOf(TokenPartitions storage self, address _who, uint256 _index) internal view returns (bytes32) {
        return self.walletPartitions[_who].partitions[_index];
    }

    function updateInvestorPartitionBalance(TokenPartitions storage self, IDSRegistryService _registry, address _wallet, uint256 _value, CommonUtils.IncDec _increase, bytes32 _partition)
        internal
        returns (bool)
    {
        string memory investor = _registry.getInvestor(_wallet);
        if (!CommonUtils.isEmptyString(investor)) {
            uint256 balance = self.investorPartitionsBalances[investor][_partition];
            if (_increase == CommonUtils.IncDec.Increase) {
                balance = SafeMath.add(balance, _value);
            } else {
                balance = SafeMath.sub(balance, _value);
            }
            self.investorPartitionsBalances[investor][_partition] = balance;
        }
        return true;
    }

    function shouldSkipComplianceCheck(IDSRegistryService _registry, IDSOmnibusTBEController _omnibusTBEController, address _from, address _to) internal view returns (bool) {
        return CommonUtils.isEqualString(_registry.getInvestor(_from), _registry.getInvestor(_to)) ||
            (address(_omnibusTBEController) != address(0) && (_omnibusTBEController.getOmnibusWallet() == _from ||
                _omnibusTBEController.getOmnibusWallet() == _to));
    }
}


// File: contracts/trust/IDSTrustService.sol
pragma solidity ^0.8.13;

import "../utils/VersionedContract.sol";
import "../utils/Initializable.sol";


/**
 * @title IDSTrustService
 * @dev An interface for a trust service which allows role-based access control for other contracts.
 */
//SPDX-License-Identifier: UNLICENSED
abstract contract IDSTrustService is Initializable, VersionedContract {

    function initialize() public virtual {
        VERSIONS.push(4);
    }

    /**
     * @dev Should be emitted when a role is set for a user.
     */
    event DSTrustServiceRoleAdded(address targetAddress, uint8 role, address sender);
    /**
     * @dev Should be emitted when a role is removed for a user.
     */
    event DSTrustServiceRoleRemoved(address targetAddress, uint8 role, address sender);

    // Role constants
    uint8 public constant NONE = 0;
    uint8 public constant MASTER = 1;
    uint8 public constant ISSUER = 2;
    uint8 public constant EXCHANGE = 4;
    uint8 public constant TRANSFER_AGENT = 8;

    /**
     * @dev Transfers the ownership (MASTER role) of the contract.
     * @param _address The address which the ownership needs to be transferred to.
     * @return A boolean that indicates if the operation was successful.
     */
    function setServiceOwner(
        address _address /*onlyMaster*/
    ) public virtual returns (bool);

    /**
     * @dev Sets a role for an array of wallets.
     * @dev Should not be used for setting MASTER (use setServiceOwner) or role removal (use removeRole).
     * @param _addresses The array of wallet whose role needs to be set.
     * @param _roles The array of role to be set. The lenght and order must match with _addresses
     * @return A boolean that indicates if the operation was successful.
     */
    function setRoles(address[] memory _addresses, uint8[] memory _roles) public virtual returns (bool);

    /**
     * @dev Sets a role for a wallet.
     * @dev Should not be used for setting MASTER (use setServiceOwner) or role removal (use removeRole).
     * @param _address The wallet whose role needs to be set.
     * @param _role The role to be set.
     * @return A boolean that indicates if the operation was successful.
     */
    function setRole(
        address _address,
        uint8 _role /*onlyMasterOrIssuer*/
    ) public virtual returns (bool);

    /**
     * @dev Removes the role for a wallet.
     * @dev Should not be used to remove MASTER (use setServiceOwner).
     * @param _address The wallet whose role needs to be removed.
     * @return A boolean that indicates if the operation was successful.
     */
    function removeRole(
        address _address /*onlyMasterOrIssuer*/
    ) public virtual returns (bool);

    /**
     * @dev Gets the role for a wallet.
     * @param _address The wallet whose role needs to be fetched.
     * @return A boolean that indicates if the operation was successful.
     */
    function getRole(address _address) public view virtual returns (uint8);

    function addEntity(
        string memory _name,
        address _owner /*onlyMasterOrIssuer onlyNewEntity onlyNewEntityOwner*/
    ) public virtual;

    function changeEntityOwner(
        string memory _name,
        address _oldOwner,
        address _newOwner /*onlyMasterOrIssuer onlyExistingEntityOwner*/
    ) public virtual;

    function addOperator(
        string memory _name,
        address _operator /*onlyEntityOwnerOrAbove onlyNewOperator*/
    ) public virtual;

    function removeOperator(
        string memory _name,
        address _operator /*onlyEntityOwnerOrAbove onlyExistingOperator*/
    ) public virtual;

    function addResource(
        string memory _name,
        address _resource /*onlyMasterOrIssuer onlyExistingEntity onlyNewResource*/
    ) public virtual;

    function removeResource(
        string memory _name,
        address _resource /*onlyMasterOrIssuer onlyExistingResource*/
    ) public virtual;

    function getEntityByOwner(address _owner) public view virtual returns (string memory);

    function getEntityByOperator(address _operator) public view virtual returns (string memory);

    function getEntityByResource(address _resource) public view virtual returns (string memory);

    function isResourceOwner(address _resource, address _owner) public view virtual returns (bool);

    function isResourceOperator(address _resource, address _operator) public view virtual returns (bool);
}


// File: contracts/utils/CommonUtils.sol
pragma solidity ^0.8.13;

//SPDX-License-Identifier: UNLICENSED
library CommonUtils {
  enum IncDec { Increase, Decrease }

  function encodeString(string memory _str) internal pure returns (bytes32) {
    return keccak256(abi.encodePacked(_str));
  }

  function isEqualString(string memory _str1, string memory _str2) internal pure returns (bool) {
    return encodeString(_str1) == encodeString(_str2);
  }

  function isEmptyString(string memory _str) internal pure returns (bool) {
    return isEqualString(_str, "");
  }
}


// File: contracts/utils/Initializable.sol
pragma solidity ^0.8.13;

//SPDX-License-Identifier: UNLICENSED
contract Initializable {
    bool public initialized = false;

    modifier initializer() {
        require(!initialized, "Contract instance has already been initialized");

        _;

        initialized = true;
    }
}


// File: contracts/utils/Ownable.sol
pragma solidity ^0.8.13;

import "./Initializable.sol";

//SPDX-License-Identifier: UNLICENSED
abstract contract Ownable is Initializable {
    address private _owner;

    event OwnershipTransferred(address indexed previousOwner, address indexed newOwner);

    function initialize() public virtual initializer {
        _owner = msg.sender;
        emit OwnershipTransferred(address(0), _owner);
    }

    //Legacy function
    function owner() public view returns (address) {
        return contractOwner();
    }

    function contractOwner() public view returns (address) {
        return _owner;
    }

    modifier onlyOwner() {
        require(isOwner(), "Ownable: caller is not the owner");
        _;
    }

    function isOwner() public view returns (bool) {
        return msg.sender == _owner;
    }

    function renounceOwnership() public onlyOwner {
        emit OwnershipTransferred(_owner, address(0));
        _owner = address(0);
    }

    /**
     * @dev Transfers ownership of the contract to a new account (`newOwner`).
     * Can only be called by the current owner.
     */
    function transferOwnership(address newOwner) public onlyOwner {
        _transferOwnership(newOwner);
    }

    /**
     * @dev Transfers ownership of the contract to a new account (`newOwner`).
     */
    function _transferOwnership(address newOwner) internal {
        require(newOwner != address(0), "Ownable: new owner is the zero address");
        emit OwnershipTransferred(_owner, newOwner);
        _owner = newOwner;
    }
}


// File: contracts/utils/ProxyTarget.sol
pragma solidity ^0.8.13;

//SPDX-License-Identifier: UNLICENSED
contract ProxyTarget {
    address internal ___t1;
    address internal ___t2;

    modifier forceInitializeFromProxy() {
        require(___t1 != address(0x0), "Must be initialized from proxy");

        _;
    }
}


// File: contracts/utils/VersionedContract.sol
pragma solidity ^0.8.13;

//SPDX-License-Identifier: UNLICENSED
contract VersionedContract {
    uint256[] internal VERSIONS = [1];

    function getVersion() public view returns (uint256[] memory) {
        return VERSIONS;
    }
}
