// SPDX-License-Identifier: MIT
pragma solidity 0.8.30;

interface IAccessControl {
    function grantRole(bytes32 role, address account) external;

    function revokeRole(bytes32 role, address account) external;
}

contract Challenge2Exploit {
    IAccessControl public accessControl;

    constructor(address _accessControl) {
        accessControl = IAccessControl(_accessControl);
    }

    function pwn() external {}
}

contract AccessControl {
    event GrantRole(bytes32 indexed role, address indexed account);
    event RevokeRole(bytes32 indexed role, address indexed account);

    mapping(bytes32 => mapping(address => bool)) public roles;

    bytes32 public constant ADMIN = keccak256(abi.encodePacked("ADMIN"));
    bytes32 public constant USER = keccak256(abi.encodePacked("USER"));

    modifier onlyRole(bytes32 role) {
        require(roles[role][msg.sender], "not authorized");
        _;
    }

    constructor() {
        _grantRole(ADMIN, msg.sender);
    }

    function _grantRole(bytes32 role, address account) internal {
        roles[role][account] = true;
        emit GrantRole(role, account);
    }

    function grantRole(bytes32 role, address account) external onlyRole(ADMIN) {
        _grantRole(role, account);
    }

    function revokeRole(
        bytes32 role,
        address account
    ) external onlyRole(ADMIN) {
        roles[role][account] = false;
        emit RevokeRole(role, account);
    }
}
