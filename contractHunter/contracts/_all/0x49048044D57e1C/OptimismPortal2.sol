// File: src/L1/OptimismPortal2.sol
// SPDX-License-Identifier: MIT
pragma solidity 0.8.15;

// Contracts
import { ProxyAdminOwnedBase } from "src/L1/ProxyAdminOwnedBase.sol";
import { Initializable } from "@openzeppelin/contracts/proxy/utils/Initializable.sol";
import { ResourceMetering } from "src/L1/ResourceMetering.sol";
import { ReinitializableBase } from "src/universal/ReinitializableBase.sol";

// Libraries
import { EOA } from "src/libraries/EOA.sol";
import { SafeCall } from "src/libraries/SafeCall.sol";
import { Constants } from "src/libraries/Constants.sol";
import { Types } from "src/libraries/Types.sol";
import { Hashing } from "src/libraries/Hashing.sol";
import { SecureMerkleTrie } from "src/libraries/trie/SecureMerkleTrie.sol";
import { AddressAliasHelper } from "src/vendor/AddressAliasHelper.sol";
import { GameStatus, GameType } from "src/dispute/lib/Types.sol";
import { Features } from "src/libraries/Features.sol";

// Interfaces
import { ISemver } from "interfaces/universal/ISemver.sol";
import { ISystemConfig } from "interfaces/L1/ISystemConfig.sol";
import { IResourceMetering } from "interfaces/L1/IResourceMetering.sol";
import { IDisputeGameFactory } from "interfaces/dispute/IDisputeGameFactory.sol";
import { IDisputeGame } from "interfaces/dispute/IDisputeGame.sol";
import { IAnchorStateRegistry } from "interfaces/dispute/IAnchorStateRegistry.sol";
import { IETHLockbox } from "interfaces/L1/IETHLockbox.sol";
import { ISuperchainConfig } from "interfaces/L1/ISuperchainConfig.sol";

/// @custom:proxied true
/// @title OptimismPortal2
/// @notice The OptimismPortal is a low-level contract responsible for passing messages between L1
///         and L2. Messages sent directly to the OptimismPortal have no form of replayability.
///         Users are encouraged to use the L1CrossDomainMessenger for a higher-level interface.
contract OptimismPortal2 is Initializable, ResourceMetering, ReinitializableBase, ProxyAdminOwnedBase, ISemver {
    /// @notice Represents a proven withdrawal.
    /// @custom:field disputeGameProxy Game that the withdrawal was proven against.
    /// @custom:field timestamp        Timestamp at which the withdrawal was proven.
    struct ProvenWithdrawal {
        IDisputeGame disputeGameProxy;
        uint64 timestamp;
    }

    /// @notice The delay between when a withdrawal is proven and when it may be finalized.
    uint256 internal immutable PROOF_MATURITY_DELAY_SECONDS;

    /// @notice Version of the deposit event.
    uint256 internal constant DEPOSIT_VERSION = 0;

    /// @notice The L2 gas limit set when eth is deposited using the receive() function.
    uint64 internal constant RECEIVE_DEFAULT_GAS_LIMIT = 100_000;

    /// @notice Address of the L2 account which initiated a withdrawal in this transaction.
    ///         If the value of this variable is the default L2 sender address, then we are NOT
    ///         inside of a call to finalizeWithdrawalTransaction.
    address public l2Sender;

    /// @notice A list of withdrawal hashes which have been successfully finalized.
    mapping(bytes32 => bool) public finalizedWithdrawals;

    /// @custom:legacy
    /// @custom:spacer provenWithdrawals
    /// @notice Spacer taking up the legacy `provenWithdrawals` mapping slot.
    bytes32 private spacer_52_0_32;

    /// @custom:legacy
    /// @custom:spacer paused
    /// @notice Spacer for backwards compatibility.
    bool private spacer_53_0_1;

    /// @custom:legacy
    /// @custom:spacer superchainConfig
    /// @notice Spacer for backwards compatibility.
    address private spacer_53_1_20;

    /// @custom:legacy
    /// @custom:spacer l2Oracle
    /// @notice Spacer taking up the legacy `l2Oracle` address slot.
    address private spacer_54_0_20;

    /// @notice Address of the SystemConfig contract.
    /// @custom:network-specific
    ISystemConfig public systemConfig;

    /// @custom:network-specific
    /// @custom:legacy
    /// @custom:spacer disputeGameFactory
    /// @notice Spacer taking up the legacy `disputeGameFactory` address slot.
    address private spacer_56_0_20;

    /// @notice A mapping of withdrawal hashes to proof submitters to ProvenWithdrawal data.
    mapping(bytes32 => mapping(address => ProvenWithdrawal)) public provenWithdrawals;

    /// @custom:legacy
    /// @custom:spacer disputeGameBlacklist
    bytes32 private spacer_58_0_32;

    /// @custom:legacy
    /// @custom:spacer respectedGameType
    GameType private spacer_59_0_4;

    /// @custom:legacy
    /// @custom:spacer respectedGameTypeUpdatedAt
    uint64 private spacer_59_4_8;

    /// @notice Mapping of withdrawal hashes to addresses that have submitted a proof for the
    ///         withdrawal. Original OptimismPortal contract only allowed one proof to be submitted
    ///         for any given withdrawal hash. Fault Proofs version of this contract must allow
    ///         multiple proofs for the same withdrawal hash to prevent a malicious user from
    ///         blocking other withdrawals by proving them against invalid proposals. Submitters
    ///         are tracked in an array to simplify the off-chain process of determining which
    ///         proof submission should be used when finalizing a withdrawal.
    mapping(bytes32 => address[]) public proofSubmitters;

    /// @custom:legacy
    /// @custom:spacer _balance
    uint256 private spacer_61_0_32;

    /// @notice Address of the AnchorStateRegistry contract.
    IAnchorStateRegistry public anchorStateRegistry;

    /// @notice Address of the ETHLockbox contract. NOTE that as of v4.1.0 it is not possible to
    ///         set this value in storage and it is only possible for this value to be set if the
    ///         chain was first upgraded to v4.0.0. Chains that skip v4.0.0 will not have any
    ///         ETHLockbox set here.
    IETHLockbox public ethLockbox;

    /// @custom:legacy
    /// @custom:spacer superRootsActive
    bool private spacer_63_20_1;

    /// @notice Emitted when a transaction is deposited from L1 to L2. The parameters of this event
    ///         are read by the rollup node and used to derive deposit transactions on L2.
    /// @param from       Address that triggered the deposit transaction.
    /// @param to         Address that the deposit transaction is directed to.
    /// @param version    Version of this deposit transaction event.
    /// @param opaqueData ABI encoded deposit data to be parsed off-chain.
    event TransactionDeposited(address indexed from, address indexed to, uint256 indexed version, bytes opaqueData);

    /// @notice Emitted when a withdrawal transaction is proven.
    /// @param withdrawalHash Hash of the withdrawal transaction.
    /// @param from           Address that triggered the withdrawal transaction.
    /// @param to             Address that the withdrawal transaction is directed to.
    event WithdrawalProven(bytes32 indexed withdrawalHash, address indexed from, address indexed to);

    /// @notice Emitted when a withdrawal transaction is proven. Exists as a separate event to
    ///         allow for backwards compatibility for tooling that observes the WithdrawalProven
    ///         event.
    /// @param withdrawalHash Hash of the withdrawal transaction.
    /// @param proofSubmitter Address of the proof submitter.
    event WithdrawalProvenExtension1(bytes32 indexed withdrawalHash, address indexed proofSubmitter);

    /// @notice Emitted when a withdrawal transaction is finalized.
    /// @param withdrawalHash Hash of the withdrawal transaction.
    /// @param success        Whether the withdrawal transaction was successful.
    event WithdrawalFinalized(bytes32 indexed withdrawalHash, bool success);

    /// @notice Thrown when a withdrawal has already been finalized.
    error OptimismPortal_AlreadyFinalized();

    /// @notice Thrown when the target of a withdrawal is unsafe.
    error OptimismPortal_BadTarget();

    /// @notice Thrown when the calldata for a deposit is too large.
    error OptimismPortal_CalldataTooLarge();

    /// @notice Thrown when the portal is paused.
    error OptimismPortal_CallPaused();

    /// @notice Thrown when a gas estimation transaction is being executed.
    error OptimismPortal_GasEstimation();

    /// @notice Thrown when the gas limit for a deposit is too low.
    error OptimismPortal_GasLimitTooLow();

    /// @notice Thrown when the target of a withdrawal is not a proper dispute game.
    error OptimismPortal_ImproperDisputeGame();

    /// @notice Thrown when a withdrawal has not been proven against a valid dispute game.
    error OptimismPortal_InvalidDisputeGame();

    /// @notice Thrown when a withdrawal has not been proven against a valid merkle proof.
    error OptimismPortal_InvalidMerkleProof();

    /// @notice Thrown when a withdrawal has not been proven against a valid output root proof.
    error OptimismPortal_InvalidOutputRootProof();

    /// @notice Thrown when a withdrawal's timestamp is not greater than the dispute game's creation timestamp.
    error OptimismPortal_InvalidProofTimestamp();

    /// @notice Thrown when the root claim of a dispute game is invalid.
    error OptimismPortal_InvalidRootClaim();

    /// @notice Thrown when a withdrawal is being finalized by a reentrant call.
    error OptimismPortal_NoReentrancy();

    /// @notice Thrown when a withdrawal has not been proven for long enough.
    error OptimismPortal_ProofNotOldEnough();

    /// @notice Thrown when a withdrawal has not been proven.
    error OptimismPortal_Unproven();

    /// @notice Thrown when ETHLockbox is set/unset incorrectly depending on the feature flag.
    error OptimismPortal_InvalidLockboxState();

    /// @notice Semantic version.
    /// @custom:semver 5.1.1
    function version() public pure virtual returns (string memory) {
        return "5.1.1";
    }

    /// @param _proofMaturityDelaySeconds The proof maturity delay in seconds.
    constructor(uint256 _proofMaturityDelaySeconds) ReinitializableBase(3) {
        PROOF_MATURITY_DELAY_SECONDS = _proofMaturityDelaySeconds;
        _disableInitializers();
    }

    /// @notice Initializer.
    /// @param _systemConfig Address of the SystemConfig.
    /// @param _anchorStateRegistry Address of the AnchorStateRegistry.
    function initialize(
        ISystemConfig _systemConfig,
        IAnchorStateRegistry _anchorStateRegistry
    )
        external
        reinitializer(initVersion())
    {
        // Initialization transactions must come from the ProxyAdmin or its owner.
        _assertOnlyProxyAdminOrProxyAdminOwner();

        // Now perform initialization logic.
        systemConfig = _systemConfig;
        anchorStateRegistry = _anchorStateRegistry;

        // Assert that the lockbox state is valid.
        _assertValidLockboxState();

        // Set the l2Sender slot, only if it is currently empty. This signals the first
        // initialization of the contract.
        if (l2Sender == address(0)) {
            l2Sender = Constants.DEFAULT_L2_SENDER;
        }

        // Initialize the ResourceMetering contract.
        __ResourceMetering_init();
    }

    /// @notice Getter for the current paused status.
    function paused() public view returns (bool) {
        return systemConfig.paused();
    }

    /// @notice Getter for the proof maturity delay.
    function proofMaturityDelaySeconds() public view returns (uint256) {
        return PROOF_MATURITY_DELAY_SECONDS;
    }

    /// @notice Getter for the address of the DisputeGameFactory contract.
    function disputeGameFactory() public view returns (IDisputeGameFactory) {
        return anchorStateRegistry.disputeGameFactory();
    }

    /// @notice Returns the SuperchainConfig contract.
    /// @return ISuperchainConfig The SuperchainConfig contract.
    function superchainConfig() external view returns (ISuperchainConfig) {
        return systemConfig.superchainConfig();
    }

    /// @custom:legacy
    /// @notice Getter function for the address of the guardian.
    function guardian() external view returns (address) {
        return systemConfig.guardian();
    }

    /// @custom:legacy
    /// @notice Getter for the dispute game finality delay.
    function disputeGameFinalityDelaySeconds() external view returns (uint256) {
        return anchorStateRegistry.disputeGameFinalityDelaySeconds();
    }

    /// @custom:legacy
    /// @notice Getter for the respected game type.
    function respectedGameType() external view returns (GameType) {
        return anchorStateRegistry.respectedGameType();
    }

    /// @custom:legacy
    /// @notice Getter for the retirement timestamp. Note that this value NO LONGER reflects the
    ///         timestamp at which the respected game type was updated. Game retirement and
    ///         respected game type value have been decoupled, this function now only returns the
    ///         retirement timestamp.
    function respectedGameTypeUpdatedAt() external view returns (uint64) {
        return anchorStateRegistry.retirementTimestamp();
    }

    /// @custom:legacy
    /// @notice Getter for the dispute game blacklist.
    /// @param _disputeGame The dispute game to check.
    /// @return Whether the dispute game is blacklisted.
    function disputeGameBlacklist(IDisputeGame _disputeGame) public view returns (bool) {
        return anchorStateRegistry.disputeGameBlacklist(_disputeGame);
    }

    /// @notice Computes the minimum gas limit for a deposit.
    ///         The minimum gas limit linearly increases based on the size of the calldata.
    ///         This is to prevent users from creating L2 resource usage without paying for it.
    ///         This function can be used when interacting with the portal to ensure forwards
    ///         compatibility.
    /// @param _byteCount Number of bytes in the calldata.
    /// @return The minimum gas limit for a deposit.
    function minimumGasLimit(uint64 _byteCount) public pure returns (uint64) {
        return _byteCount * 40 + 21000;
    }

    /// @notice Accepts value so that users can send ETH directly to this contract and have the
    ///         funds be deposited to their address on L2. This is intended as a convenience
    ///         function for EOAs. Contracts should call the depositTransaction() function directly
    ///         otherwise any deposited funds will be lost due to address aliasing.
    receive() external payable {
        depositTransaction(msg.sender, msg.value, RECEIVE_DEFAULT_GAS_LIMIT, false, bytes(""));
    }

    /// @notice Accepts ETH value without triggering a deposit to L2.
    function donateETH() external payable {
        // Intentionally empty.
    }

    /// @notice Proves a withdrawal transaction using an Output Root proof.
    /// @param _tx               Withdrawal transaction to finalize.
    /// @param _disputeGameIndex Index of the dispute game to prove the withdrawal against.
    /// @param _outputRootProof  Inclusion proof of the L2ToL1MessagePasser storage root.
    /// @param _withdrawalProof  Inclusion proof of the withdrawal within the L2ToL1MessagePasser.
    function proveWithdrawalTransaction(
        Types.WithdrawalTransaction memory _tx,
        uint256 _disputeGameIndex,
        Types.OutputRootProof calldata _outputRootProof,
        bytes[] calldata _withdrawalProof
    )
        external
    {
        // Cannot prove withdrawal transactions while the system is paused.
        _assertNotPaused();

        // Fetch the dispute game proxy from the `DisputeGameFactory` contract.
        (,, IDisputeGame disputeGameProxy) = disputeGameFactory().gameAtIndex(_disputeGameIndex);

        // Make sure that the target address is safe.
        if (_isUnsafeTarget(_tx.target)) {
            revert OptimismPortal_BadTarget();
        }

        // Game must be a Proper Game.
        if (!anchorStateRegistry.isGameProper(disputeGameProxy)) {
            revert OptimismPortal_ImproperDisputeGame();
        }

        // Game must have been respected game type when created.
        if (!anchorStateRegistry.isGameRespected(disputeGameProxy)) {
            revert OptimismPortal_InvalidDisputeGame();
        }

        // Game must not have resolved in favor of the Challenger (invalid root claim).
        if (disputeGameProxy.status() == GameStatus.CHALLENGER_WINS) {
            revert OptimismPortal_InvalidDisputeGame();
        }

        // As a sanity check, we make sure that the current timestamp is not less than or equal to
        // the dispute game's creation timestamp. Not strictly necessary but extra layer of
        // safety against weird bugs. Note that this blocks withdrawals from being proven in the
        // same block that a dispute game is created.
        if (block.timestamp <= disputeGameProxy.createdAt().raw()) {
            revert OptimismPortal_InvalidProofTimestamp();
        }

        // Verify that the output root can be generated with the elements in the proof.
        if (disputeGameProxy.rootClaim().raw() != Hashing.hashOutputRootProof(_outputRootProof)) {
            revert OptimismPortal_InvalidOutputRootProof();
        }

        // Load the ProvenWithdrawal into memory, using the withdrawal hash as a unique identifier.
        bytes32 withdrawalHash = Hashing.hashWithdrawal(_tx);

        // Compute the storage slot of the withdrawal hash in the L2ToL1MessagePasser contract.
        // Refer to the Solidity documentation for more information on how storage layouts are
        // computed for mappings.
        bytes32 storageKey = keccak256(
            abi.encode(
                withdrawalHash,
                uint256(0) // The withdrawals mapping is at the first slot in the layout.
            )
        );

        // Verify that the hash of this withdrawal was stored in the L2toL1MessagePasser contract
        // on L2. If this is true, under the assumption that the SecureMerkleTrie does not have
        // bugs, then we know that this withdrawal was actually triggered on L2 and can therefore
        // be relayed on L1.
        if (
            SecureMerkleTrie.verifyInclusionProof({
                _key: abi.encode(storageKey),
                _value: hex"01",
                _proof: _withdrawalProof,
                _root: _outputRootProof.messagePasserStorageRoot
            }) == false
        ) {
            revert OptimismPortal_InvalidMerkleProof();
        }

        // Designate the withdrawalHash as proven by storing the disputeGameProxy and timestamp in
        // the provenWithdrawals mapping. A given user may re-prove a withdrawalHash multiple
        // times, but each proof will reset the proof timer.
        provenWithdrawals[withdrawalHash][msg.sender] =
            ProvenWithdrawal({ disputeGameProxy: disputeGameProxy, timestamp: uint64(block.timestamp) });

        // Add the proof submitter to the list of proof submitters for this withdrawal hash.
        proofSubmitters[withdrawalHash].push(msg.sender);

        // Emit a WithdrawalProven events.
        emit WithdrawalProven(withdrawalHash, _tx.sender, _tx.target);
        emit WithdrawalProvenExtension1(withdrawalHash, msg.sender);
    }

    /// @notice Finalizes a withdrawal transaction.
    /// @param _tx Withdrawal transaction to finalize.
    function finalizeWithdrawalTransaction(Types.WithdrawalTransaction memory _tx) external {
        finalizeWithdrawalTransactionExternalProof(_tx, msg.sender);
    }

    /// @notice Finalizes a withdrawal transaction, using an external proof submitter.
    /// @param _tx Withdrawal transaction to finalize.
    /// @param _proofSubmitter Address of the proof submitter.
    function finalizeWithdrawalTransactionExternalProof(
        Types.WithdrawalTransaction memory _tx,
        address _proofSubmitter
    )
        public
    {
        // Cannot finalize withdrawal transactions while the system is paused.
        _assertNotPaused();

        // Make sure that the l2Sender has not yet been set. The l2Sender is set to a value other
        // than the default value when a withdrawal transaction is being finalized. This check is
        // a defacto reentrancy guard.
        if (l2Sender != Constants.DEFAULT_L2_SENDER) {
            revert OptimismPortal_NoReentrancy();
        }

        // Make sure that the target address is safe.
        if (_isUnsafeTarget(_tx.target)) {
            revert OptimismPortal_BadTarget();
        }

        // Grab the withdrawal.
        bytes32 withdrawalHash = Hashing.hashWithdrawal(_tx);

        // Check that the withdrawal can be finalized.
        checkWithdrawal(withdrawalHash, _proofSubmitter);

        // Mark the withdrawal as finalized so it can't be replayed.
        finalizedWithdrawals[withdrawalHash] = true;

        // If using ETHLockbox, unlock the ETH from the ETHLockbox.
        if (_isUsingLockbox()) {
            if (_tx.value > 0) ethLockbox.unlockETH(_tx.value);
        }

        // Set the l2Sender so contracts know who triggered this withdrawal on L2.
        l2Sender = _tx.sender;

        // Trigger the call to the target contract. We use a custom low level method
        // SafeCall.callWithMinGas to ensure two key properties
        //   1. Target contracts cannot force this call to run out of gas by returning a very large
        //      amount of data (and this is OK because we don't care about the returndata here).
        //   2. The amount of gas provided to the execution context of the target is at least the
        //      gas limit specified by the user. If there is not enough gas in the current context
        //      to accomplish this, `callWithMinGas` will revert.
        bool success = SafeCall.callWithMinGas(_tx.target, _tx.gasLimit, _tx.value, _tx.data);

        // Reset the l2Sender back to the default value.
        l2Sender = Constants.DEFAULT_L2_SENDER;

        // All withdrawals are immediately finalized. Replayability can
        // be achieved through contracts built on top of this contract
        emit WithdrawalFinalized(withdrawalHash, success);

        // If using ETHLockbox, send ETH back to the Lockbox in the case of a failed transaction or
        // it'll get stuck here and would need to be moved back via admin action.
        if (_isUsingLockbox()) {
            if (!success && _tx.value > 0) {
                ethLockbox.lockETH{ value: _tx.value }();
            }
        }

        // Reverting here is useful for determining the exact gas cost to successfully execute the
        // sub call to the target contract if the minimum gas limit specified by the user would not
        // be sufficient to execute the sub call.
        if (!success && tx.origin == Constants.ESTIMATION_ADDRESS) {
            revert OptimismPortal_GasEstimation();
        }
    }

    /// @notice Checks that a withdrawal has been proven and is ready to be finalized.
    /// @param _withdrawalHash Hash of the withdrawal.
    /// @param _proofSubmitter Address of the proof submitter.
    function checkWithdrawal(bytes32 _withdrawalHash, address _proofSubmitter) public view {
        // Grab the withdrawal and dispute game proxy.
        ProvenWithdrawal memory provenWithdrawal = provenWithdrawals[_withdrawalHash][_proofSubmitter];
        IDisputeGame disputeGameProxy = provenWithdrawal.disputeGameProxy;

        // Check that this withdrawal has not already been finalized, this is replay protection.
        if (finalizedWithdrawals[_withdrawalHash]) {
            revert OptimismPortal_AlreadyFinalized();
        }

        // A withdrawal can only be finalized if it has been proven. We know that a withdrawal has
        // been proven at least once when its timestamp is non-zero. Unproven withdrawals will have
        // a timestamp of zero.
        if (provenWithdrawal.timestamp == 0) {
            revert OptimismPortal_Unproven();
        }

        // As a sanity check, we make sure that the proven withdrawal's timestamp is greater than
        // starting timestamp inside the Dispute Game. Not strictly necessary but extra layer of
        // safety against weird bugs in the proving step. Note that this blocks withdrawals that
        // are proven in the same block that a dispute game is created.
        if (provenWithdrawal.timestamp <= disputeGameProxy.createdAt().raw()) {
            revert OptimismPortal_InvalidProofTimestamp();
        }

        // A proven withdrawal must wait at least `PROOF_MATURITY_DELAY_SECONDS` before finalizing.
        if (block.timestamp - provenWithdrawal.timestamp <= PROOF_MATURITY_DELAY_SECONDS) {
            revert OptimismPortal_ProofNotOldEnough();
        }

        // Check that the root claim is valid.
        if (!anchorStateRegistry.isGameClaimValid(disputeGameProxy)) {
            revert OptimismPortal_InvalidRootClaim();
        }
    }

    /// @notice Accepts deposits of ETH and data, and emits a TransactionDeposited event for use in
    ///         deriving deposit transactions. Note that if a deposit is made by a contract, its
    ///         address will be aliased when retrieved using `tx.origin` or `msg.sender`. Consider
    ///         using the CrossDomainMessenger contracts for a simpler developer experience.
    /// @dev    The `msg.value` is locked on the ETHLockbox and minted as ETH when the deposit
    ///         arrives on L2, while `_value` specifies how much ETH to send to the target.
    /// @param _to         Target address on L2.
    /// @param _value      ETH value to send to the recipient.
    /// @param _gasLimit   Amount of L2 gas to purchase by burning gas on L1.
    /// @param _isCreation Whether or not the transaction is a contract creation.
    /// @param _data       Data to trigger the recipient with.
    function depositTransaction(
        address _to,
        uint256 _value,
        uint64 _gasLimit,
        bool _isCreation,
        bytes memory _data
    )
        public
        payable
        metered(_gasLimit)
    {
        // If using ETHLockbox, lock the ETH in the ETHLockbox.
        if (_isUsingLockbox()) {
            if (msg.value > 0) ethLockbox.lockETH{ value: msg.value }();
        }

        // Just to be safe, make sure that people specify address(0) as the target when doing
        // contract creations.
        if (_isCreation && _to != address(0)) {
            revert OptimismPortal_BadTarget();
        }

        // Prevent depositing transactions that have too small of a gas limit. Users should pay
        // more for more resource usage.
        if (_gasLimit < minimumGasLimit(uint64(_data.length))) {
            revert OptimismPortal_GasLimitTooLow();
        }

        // Prevent the creation of deposit transactions that have too much calldata. This gives an
        // upper limit on the size of unsafe blocks over the p2p network. 120kb is chosen to ensure
        // that the transaction can fit into the p2p network policy of 128kb even though deposit
        // transactions are not gossipped over the p2p network.
        if (_data.length > 120_000) {
            revert OptimismPortal_CalldataTooLarge();
        }

        // Transform the from-address to its alias if the caller is a contract.
        address from = msg.sender;
        if (!EOA.isSenderEOA()) {
            from = AddressAliasHelper.applyL1ToL2Alias(msg.sender);
        }

        // Compute the opaque data that will be emitted as part of the TransactionDeposited event.
        // We use opaque data so that we can update the TransactionDeposited event in the future
        // without breaking the current interface.
        bytes memory opaqueData = abi.encodePacked(msg.value, _value, _gasLimit, _isCreation, _data);

        // Emit a TransactionDeposited event so that the rollup node can derive a deposit
        // transaction for this deposit.
        emit TransactionDeposited(from, _to, DEPOSIT_VERSION, opaqueData);
    }

    /// @notice External getter for the number of proof submitters for a withdrawal hash.
    /// @param _withdrawalHash Hash of the withdrawal.
    /// @return The number of proof submitters for the withdrawal hash.
    function numProofSubmitters(bytes32 _withdrawalHash) external view returns (uint256) {
        return proofSubmitters[_withdrawalHash].length;
    }

    /// @notice Checks if the ETHLockbox feature is enabled.
    /// @return bool True if the ETHLockbox feature is enabled.
    function _isUsingLockbox() internal view returns (bool) {
        return systemConfig.isFeatureEnabled(Features.ETH_LOCKBOX) && address(ethLockbox) != address(0);
    }

    /// @notice Asserts that the contract is not paused.
    function _assertNotPaused() internal view {
        if (paused()) {
            revert OptimismPortal_CallPaused();
        }
    }

    /// @notice Asserts that the ETHLockbox is set/unset correctly depending on the feature flag.
    function _assertValidLockboxState() internal view {
        if (
            systemConfig.isFeatureEnabled(Features.ETH_LOCKBOX) && address(ethLockbox) == address(0)
                || !systemConfig.isFeatureEnabled(Features.ETH_LOCKBOX) && address(ethLockbox) != address(0)
        ) {
            revert OptimismPortal_InvalidLockboxState();
        }
    }

    /// @notice Checks if a target address is unsafe.
    function _isUnsafeTarget(address _target) internal view virtual returns (bool) {
        // Prevent users from targeting an unsafe target address on a withdrawal transaction.
        return _target == address(this) || _target == address(ethLockbox);
    }

    /// @notice Getter for the resource config. Used internally by the ResourceMetering contract.
    ///         The SystemConfig is the source of truth for the resource config.
    /// @return config_ ResourceMetering ResourceConfig
    function _resourceConfig() internal view override returns (ResourceMetering.ResourceConfig memory config_) {
        IResourceMetering.ResourceConfig memory config = systemConfig.resourceConfig();
        assembly ("memory-safe") {
            config_ := config
        }
    }
}


// File: src/L1/ProxyAdminOwnedBase.sol
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.15;

// Libraries
import { Storage } from "src/libraries/Storage.sol";
import { Constants } from "src/libraries/Constants.sol";

// Interfaces
import { IProxyAdmin } from "interfaces/universal/IProxyAdmin.sol";
import { IAddressManager } from "interfaces/legacy/IAddressManager.sol";

/// @notice Base contract for ProxyAdmin-owned contracts. This contract is used to introspect
///         compatible Proxy contracts so that their ProxyAdmin and ProxyAdmin owner addresses can
///         be retrieved onchain. Existing Proxy contracts don't have these getters, so we need a
///         base contract instead.
/// @dev WARNING: This contract is ONLY designed to be used with either the Optimism Proxy
///      implementation or the Optimism ResolvedDelegateProxy implementation. It is not safe to use
///      this contract with any other proxy implementation.
///      WARNING: Multiple OP Stack chains may share the same ProxyAdmin owner address.
abstract contract ProxyAdminOwnedBase {
    /// @notice Thrown when the ProxyAdmin owner of the current contract is not the same as the
    ///         ProxyAdmin owner of the other Proxy address provided.
    error ProxyAdminOwnedBase_NotSharedProxyAdminOwner();

    /// @notice Thrown when the caller is not the ProxyAdmin owner.
    error ProxyAdminOwnedBase_NotProxyAdminOwner();

    /// @notice Thrown when the caller is not the ProxyAdmin.
    error ProxyAdminOwnedBase_NotProxyAdmin();

    /// @notice Thrown when the caller is not the ProxyAdmin owner or the ProxyAdmin.
    error ProxyAdminOwnedBase_NotProxyAdminOrProxyAdminOwner();

    /// @notice Thrown when the ProxyAdmin owner of the current contract is not found.
    error ProxyAdminOwnedBase_ProxyAdminNotFound();

    /// @notice Thrown when the current contract is not a ResolvedDelegateProxy.
    error ProxyAdminOwnedBase_NotResolvedDelegateProxy();

    /// @notice Getter for the owner of the ProxyAdmin.
    function proxyAdminOwner() public view returns (address) {
        return proxyAdmin().owner();
    }

    /// @notice Getter for the ProxyAdmin contract that owns this Proxy contract.
    function proxyAdmin() public view returns (IProxyAdmin) {
        // First check for a non-zero address in the reserved slot.
        address proxyAdminAddress = Storage.getAddress(Constants.PROXY_OWNER_ADDRESS);
        if (proxyAdminAddress != address(0)) {
            return IProxyAdmin(proxyAdminAddress);
        }

        // Otherwise, we'll try to read the AddressManager slot.
        // First we make sure this is almost certainly a ResolvedDelegateProxy. We only have a
        // single ResolvedDelegateProxy and it's for the L1CrossDomainMessenger, so we'll check
        // that the storage slot for the mapping at slot 0 returns the string
        // "OVM_L1CrossDomainMessenger". We need to use Solidity's rules for how strings are stored
        // in storage slots to do this.
        if (
            Storage.getBytes32(keccak256(abi.encode(address(this), uint256(0))))
                != bytes32(
                    uint256(bytes32("OVM_L1CrossDomainMessenger")) | uint256(bytes("OVM_L1CrossDomainMessenger").length * 2)
                )
        ) {
            revert ProxyAdminOwnedBase_NotResolvedDelegateProxy();
        }

        // Ok, now we'll try to read the AddressManager slot.
        address addressManagerAddress = Storage.getAddress(keccak256(abi.encode(address(this), uint256(1))));
        if (addressManagerAddress != address(0)) {
            return IProxyAdmin(IAddressManager(addressManagerAddress).owner());
        }

        // We should revert here, we couldn't find a non-zero owner address.
        revert ProxyAdminOwnedBase_ProxyAdminNotFound();
    }

    /// @notice Reverts if the ProxyAdmin owner of the current contract is not the same as the
    ///         ProxyAdmin owner of the other Proxy address provided. Useful asserting that both
    ///         the current contract and the other Proxy share the same security model.+
    function _assertSharedProxyAdminOwner(address _proxy) internal view {
        if (proxyAdminOwner() != ProxyAdminOwnedBase(_proxy).proxyAdminOwner()) {
            revert ProxyAdminOwnedBase_NotSharedProxyAdminOwner();
        }
    }

    /// @notice Reverts if the caller is not the ProxyAdmin owner.
    function _assertOnlyProxyAdminOwner() internal view {
        if (proxyAdminOwner() != msg.sender) {
            revert ProxyAdminOwnedBase_NotProxyAdminOwner();
        }
    }

    /// @notice Reverts if the caller is not the ProxyAdmin.
    function _assertOnlyProxyAdmin() internal view {
        if (address(proxyAdmin()) != msg.sender) {
            revert ProxyAdminOwnedBase_NotProxyAdmin();
        }
    }

    function _assertOnlyProxyAdminOrProxyAdminOwner() internal view {
        if (address(proxyAdmin()) != msg.sender && proxyAdminOwner() != msg.sender) {
            revert ProxyAdminOwnedBase_NotProxyAdminOrProxyAdminOwner();
        }
    }
}


// File: lib/openzeppelin-contracts/contracts/proxy/utils/Initializable.sol
// SPDX-License-Identifier: MIT
// OpenZeppelin Contracts (last updated v4.7.0) (proxy/utils/Initializable.sol)

pragma solidity ^0.8.2;

import "../../utils/Address.sol";

/**
 * @dev This is a base contract to aid in writing upgradeable contracts, or any kind of contract that will be deployed
 * behind a proxy. Since proxied contracts do not make use of a constructor, it's common to move constructor logic to an
 * external initializer function, usually called `initialize`. It then becomes necessary to protect this initializer
 * function so it can only be called once. The {initializer} modifier provided by this contract will have this effect.
 *
 * The initialization functions use a version number. Once a version number is used, it is consumed and cannot be
 * reused. This mechanism prevents re-execution of each "step" but allows the creation of new initialization steps in
 * case an upgrade adds a module that needs to be initialized.
 *
 * For example:
 *
 * [.hljs-theme-light.nopadding]
 * ```
 * contract MyToken is ERC20Upgradeable {
 *     function initialize() initializer public {
 *         __ERC20_init("MyToken", "MTK");
 *     }
 * }
 * contract MyTokenV2 is MyToken, ERC20PermitUpgradeable {
 *     function initializeV2() reinitializer(2) public {
 *         __ERC20Permit_init("MyToken");
 *     }
 * }
 * ```
 *
 * TIP: To avoid leaving the proxy in an uninitialized state, the initializer function should be called as early as
 * possible by providing the encoded function call as the `_data` argument to {ERC1967Proxy-constructor}.
 *
 * CAUTION: When used with inheritance, manual care must be taken to not invoke a parent initializer twice, or to ensure
 * that all initializers are idempotent. This is not verified automatically as constructors are by Solidity.
 *
 * [CAUTION]
 * ====
 * Avoid leaving a contract uninitialized.
 *
 * An uninitialized contract can be taken over by an attacker. This applies to both a proxy and its implementation
 * contract, which may impact the proxy. To prevent the implementation contract from being used, you should invoke
 * the {_disableInitializers} function in the constructor to automatically lock it when it is deployed:
 *
 * [.hljs-theme-light.nopadding]
 * ```
 * /// @custom:oz-upgrades-unsafe-allow constructor
 * constructor() {
 *     _disableInitializers();
 * }
 * ```
 * ====
 */
abstract contract Initializable {
    /**
     * @dev Indicates that the contract has been initialized.
     * @custom:oz-retyped-from bool
     */
    uint8 private _initialized;

    /**
     * @dev Indicates that the contract is in the process of being initialized.
     */
    bool private _initializing;

    /**
     * @dev Triggered when the contract has been initialized or reinitialized.
     */
    event Initialized(uint8 version);

    /**
     * @dev A modifier that defines a protected initializer function that can be invoked at most once. In its scope,
     * `onlyInitializing` functions can be used to initialize parent contracts. Equivalent to `reinitializer(1)`.
     */
    modifier initializer() {
        bool isTopLevelCall = !_initializing;
        require(
            (isTopLevelCall && _initialized < 1) || (!Address.isContract(address(this)) && _initialized == 1),
            "Initializable: contract is already initialized"
        );
        _initialized = 1;
        if (isTopLevelCall) {
            _initializing = true;
        }
        _;
        if (isTopLevelCall) {
            _initializing = false;
            emit Initialized(1);
        }
    }

    /**
     * @dev A modifier that defines a protected reinitializer function that can be invoked at most once, and only if the
     * contract hasn't been initialized to a greater version before. In its scope, `onlyInitializing` functions can be
     * used to initialize parent contracts.
     *
     * `initializer` is equivalent to `reinitializer(1)`, so a reinitializer may be used after the original
     * initialization step. This is essential to configure modules that are added through upgrades and that require
     * initialization.
     *
     * Note that versions can jump in increments greater than 1; this implies that if multiple reinitializers coexist in
     * a contract, executing them in the right order is up to the developer or operator.
     */
    modifier reinitializer(uint8 version) {
        require(!_initializing && _initialized < version, "Initializable: contract is already initialized");
        _initialized = version;
        _initializing = true;
        _;
        _initializing = false;
        emit Initialized(version);
    }

    /**
     * @dev Modifier to protect an initialization function so that it can only be invoked by functions with the
     * {initializer} and {reinitializer} modifiers, directly or indirectly.
     */
    modifier onlyInitializing() {
        require(_initializing, "Initializable: contract is not initializing");
        _;
    }

    /**
     * @dev Locks the contract, preventing any future reinitialization. This cannot be part of an initializer call.
     * Calling this in the constructor of a contract will prevent that contract from being initialized or reinitialized
     * to any version. It is recommended to use this to lock implementation contracts that are designed to be called
     * through proxies.
     */
    function _disableInitializers() internal virtual {
        require(!_initializing, "Initializable: contract is initializing");
        if (_initialized < type(uint8).max) {
            _initialized = type(uint8).max;
            emit Initialized(type(uint8).max);
        }
    }
}


// File: src/L1/ResourceMetering.sol
// SPDX-License-Identifier: MIT
pragma solidity 0.8.15;

// Contracts
import { Initializable } from "@openzeppelin/contracts/proxy/utils/Initializable.sol";

// Libraries
import { Math } from "@openzeppelin/contracts/utils/math/Math.sol";
import { Burn } from "src/libraries/Burn.sol";
import { Arithmetic } from "src/libraries/Arithmetic.sol";

/// @custom:upgradeable
/// @title ResourceMetering
/// @notice ResourceMetering implements an EIP-1559 style resource metering system where pricing
///         updates automatically based on current demand.
abstract contract ResourceMetering is Initializable {
    /// @notice Error returned when too much gas resource is consumed.
    error OutOfGas();

    /// @notice Represents the various parameters that control the way in which resources are
    ///         metered. Corresponds to the EIP-1559 resource metering system.
    /// @custom:field prevBaseFee   Base fee from the previous block(s).
    /// @custom:field prevBoughtGas Amount of gas bought so far in the current block.
    /// @custom:field prevBlockNum  Last block number that the base fee was updated.
    struct ResourceParams {
        uint128 prevBaseFee;
        uint64 prevBoughtGas;
        uint64 prevBlockNum;
    }

    /// @notice Represents the configuration for the EIP-1559 based curve for the deposit gas
    ///         market. These values should be set with care as it is possible to set them in
    ///         a way that breaks the deposit gas market. The target resource limit is defined as
    ///         maxResourceLimit / elasticityMultiplier. This struct was designed to fit within a
    ///         single word. There is additional space for additions in the future.
    /// @custom:field maxResourceLimit             Represents the maximum amount of deposit gas that
    ///                                            can be purchased per block.
    /// @custom:field elasticityMultiplier         Determines the target resource limit along with
    ///                                            the resource limit.
    /// @custom:field baseFeeMaxChangeDenominator  Determines max change on fee per block.
    /// @custom:field minimumBaseFee               The min deposit base fee, it is clamped to this
    ///                                            value.
    /// @custom:field systemTxMaxGas               The amount of gas supplied to the system
    ///                                            transaction. This should be set to the same
    ///                                            number that the op-node sets as the gas limit
    ///                                            for the system transaction.
    /// @custom:field maximumBaseFee               The max deposit base fee, it is clamped to this
    ///                                            value.
    struct ResourceConfig {
        uint32 maxResourceLimit;
        uint8 elasticityMultiplier;
        uint8 baseFeeMaxChangeDenominator;
        uint32 minimumBaseFee;
        uint32 systemTxMaxGas;
        uint128 maximumBaseFee;
    }

    /// @notice EIP-1559 style gas parameters.
    ResourceParams public params;

    /// @notice Reserve extra slots (to a total of 50) in the storage layout for future upgrades.
    uint256[48] private __gap;

    /// @notice Meters access to a function based an amount of a requested resource.
    /// @param _amount Amount of the resource requested.
    modifier metered(uint64 _amount) {
        // Record initial gas amount so we can refund for it later.
        uint256 initialGas = gasleft();

        // Run the underlying function.
        _;

        // Run the metering function.
        _metered(_amount, initialGas);
    }

    /// @notice An internal function that holds all of the logic for metering a resource.
    /// @param _amount     Amount of the resource requested.
    /// @param _initialGas The amount of gas before any modifier execution.
    function _metered(uint64 _amount, uint256 _initialGas) internal {
        // Update block number and base fee if necessary.
        uint256 blockDiff = block.number - params.prevBlockNum;

        ResourceConfig memory config = _resourceConfig();
        int256 targetResourceLimit =
            int256(uint256(config.maxResourceLimit)) / int256(uint256(config.elasticityMultiplier));

        if (blockDiff > 0) {
            // Handle updating EIP-1559 style gas parameters. We use EIP-1559 to restrict the rate
            // at which deposits can be created and therefore limit the potential for deposits to
            // spam the L2 system. Fee scheme is very similar to EIP-1559 with minor changes.
            int256 gasUsedDelta = int256(uint256(params.prevBoughtGas)) - targetResourceLimit;
            int256 baseFeeDelta = (int256(uint256(params.prevBaseFee)) * gasUsedDelta)
                / (targetResourceLimit * int256(uint256(config.baseFeeMaxChangeDenominator)));

            // Update base fee by adding the base fee delta and clamp the resulting value between
            // min and max.
            int256 newBaseFee = Arithmetic.clamp({
                _value: int256(uint256(params.prevBaseFee)) + baseFeeDelta,
                _min: int256(uint256(config.minimumBaseFee)),
                _max: int256(uint256(config.maximumBaseFee))
            });

            // If we skipped more than one block, we also need to account for every empty block.
            // Empty block means there was no demand for deposits in that block, so we should
            // reflect this lack of demand in the fee.
            if (blockDiff > 1) {
                // Update the base fee by repeatedly applying the exponent 1-(1/change_denominator)
                // blockDiff - 1 times. Simulates multiple empty blocks. Clamp the resulting value
                // between min and max.
                newBaseFee = Arithmetic.clamp({
                    _value: Arithmetic.cdexp({
                        _coefficient: newBaseFee,
                        _denominator: int256(uint256(config.baseFeeMaxChangeDenominator)),
                        _exponent: int256(blockDiff - 1)
                    }),
                    _min: int256(uint256(config.minimumBaseFee)),
                    _max: int256(uint256(config.maximumBaseFee))
                });
            }

            // Update new base fee, reset bought gas, and update block number.
            params.prevBaseFee = uint128(uint256(newBaseFee));
            params.prevBoughtGas = 0;
            params.prevBlockNum = uint64(block.number);
        }

        // Make sure we can actually buy the resource amount requested by the user.
        params.prevBoughtGas += _amount;
        if (int256(uint256(params.prevBoughtGas)) > int256(uint256(config.maxResourceLimit))) {
            revert OutOfGas();
        }

        // Determine the amount of ETH to be paid.
        uint256 resourceCost = uint256(_amount) * uint256(params.prevBaseFee);

        // We currently charge for this ETH amount as an L1 gas burn, so we convert the ETH amount
        // into gas by dividing by the L1 base fee. We assume a minimum base fee of 1 gwei to avoid
        // division by zero for L1s that don't support 1559 or to avoid excessive gas burns during
        // periods of extremely low L1 demand. One-day average gas fee hasn't dipped below 1 gwei
        // during any 1 day period in the last 5 years, so should be fine.
        uint256 gasCost = resourceCost / Math.max(block.basefee, 1 gwei);

        // Give the user a refund based on the amount of gas they used to do all of the work up to
        // this point. Since we're at the end of the modifier, this should be pretty accurate. Acts
        // effectively like a dynamic stipend (with a minimum value).
        uint256 usedGas = _initialGas - gasleft();
        if (gasCost > usedGas) {
            Burn.gas(gasCost - usedGas);
        }
    }

    /// @notice Adds an amount of L2 gas consumed to the prev bought gas params. This is meant to be used
    ///         when L2 system transactions are generated from L1.
    /// @param _amount Amount of the L2 gas resource requested.
    function useGas(uint32 _amount) internal {
        params.prevBoughtGas += uint64(_amount);
    }

    /// @notice Virtual function that returns the resource config.
    ///         Contracts that inherit this contract must implement this function.
    /// @return ResourceConfig
    function _resourceConfig() internal virtual returns (ResourceConfig memory);

    /// @notice Sets initial resource parameter values.
    ///         This function must either be called by the initializer function of an upgradeable
    ///         child contract.
    function __ResourceMetering_init() internal onlyInitializing {
        if (params.prevBlockNum == 0) {
            params = ResourceParams({ prevBaseFee: 1 gwei, prevBoughtGas: 0, prevBlockNum: uint64(block.number) });
        }
    }
}


// File: src/universal/ReinitializableBase.sol
// SPDX-License-Identifier: MIT
pragma solidity 0.8.15;

/// @title ReinitializableBase
/// @notice A base contract for reinitializable contracts that exposes a version number.
abstract contract ReinitializableBase {
    /// @notice Thrown when the initialization version is zero.
    error ReinitializableBase_ZeroInitVersion();

    /// @notice Current initialization version.
    uint8 internal immutable INIT_VERSION;

    /// @param _initVersion Current initialization version.
    constructor(uint8 _initVersion) {
        // Sanity check, we should never have a zero init version.
        if (_initVersion == 0) revert ReinitializableBase_ZeroInitVersion();
        INIT_VERSION = _initVersion;
    }

    /// @notice Getter for the current initialization version.
    /// @return The current initialization version.
    function initVersion() public view returns (uint8) {
        return INIT_VERSION;
    }
}


// File: src/libraries/EOA.sol
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/// @title EOA
/// @notice A library for detecting if an address is an EOA.
library EOA {
    /// @notice Returns true if sender address is an EOA.
    /// @return isEOA_ True if the sender address is an EOA.
    function isSenderEOA() internal view returns (bool isEOA_) {
        if (msg.sender == tx.origin) {
            isEOA_ = true;
        } else if (address(msg.sender).code.length == 23) {
            // If the sender is not the origin, check for 7702 delegated EOAs.
            assembly {
                let ptr := mload(0x40)
                mstore(0x40, add(ptr, 0x20))
                extcodecopy(caller(), ptr, 0, 0x20)
                isEOA_ := eq(shr(232, mload(ptr)), 0xEF0100)
            }
        } else {
            // If more or less than 23 bytes of code, not a 7702 delegated EOA.
            isEOA_ = false;
        }
    }
}


// File: src/libraries/SafeCall.sol
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/// @title SafeCall
/// @notice Perform low level safe calls
library SafeCall {
    /// @notice Performs a low level call without copying any returndata.
    /// @dev Passes no calldata to the call context.
    /// @param _target   Address to call
    /// @param _gas      Amount of gas to pass to the call
    /// @param _value    Amount of value to pass to the call
    function send(address _target, uint256 _gas, uint256 _value) internal returns (bool success_) {
        assembly {
            success_ :=
                call(
                    _gas, // gas
                    _target, // recipient
                    _value, // ether value
                    0, // inloc
                    0, // inlen
                    0, // outloc
                    0 // outlen
                )
        }
    }

    /// @notice Perform a low level call with all gas without copying any returndata
    /// @param _target   Address to call
    /// @param _value    Amount of value to pass to the call
    function send(address _target, uint256 _value) internal returns (bool success_) {
        success_ = send(_target, gasleft(), _value);
    }

    /// @notice Perform a low level call without copying any returndata
    /// @param _target   Address to call
    /// @param _gas      Amount of gas to pass to the call
    /// @param _value    Amount of value to pass to the call
    /// @param _calldata Calldata to pass to the call
    function call(
        address _target,
        uint256 _gas,
        uint256 _value,
        bytes memory _calldata
    )
        internal
        returns (bool success_)
    {
        assembly {
            success_ :=
                call(
                    _gas, // gas
                    _target, // recipient
                    _value, // ether value
                    add(_calldata, 32), // inloc
                    mload(_calldata), // inlen
                    0, // outloc
                    0 // outlen
                )
        }
    }

    /// @notice Perform a low level call without copying any returndata
    /// @param _target   Address to call
    /// @param _value    Amount of value to pass to the call
    /// @param _calldata Calldata to pass to the call
    function call(address _target, uint256 _value, bytes memory _calldata) internal returns (bool success_) {
        success_ = call({ _target: _target, _gas: gasleft(), _value: _value, _calldata: _calldata });
    }

    /// @notice Perform a low level call without copying any returndata
    /// @param _target   Address to call
    /// @param _calldata Calldata to pass to the call
    function call(address _target, bytes memory _calldata) internal returns (bool success_) {
        success_ = call({ _target: _target, _gas: gasleft(), _value: 0, _calldata: _calldata });
    }

    /// @notice Helper function to determine if there is sufficient gas remaining within the context
    ///         to guarantee that the minimum gas requirement for a call will be met as well as
    ///         optionally reserving a specified amount of gas for after the call has concluded.
    /// @param _minGas      The minimum amount of gas that may be passed to the target context.
    /// @param _reservedGas Optional amount of gas to reserve for the caller after the execution
    ///                     of the target context.
    /// @return `true` if there is enough gas remaining to safely supply `_minGas` to the target
    ///         context as well as reserve `_reservedGas` for the caller after the execution of
    ///         the target context.
    /// @dev !!!!! FOOTGUN ALERT !!!!!
    ///      1.) The 40_000 base buffer is to account for the worst case of the dynamic cost of the
    ///          `CALL` opcode's `address_access_cost`, `positive_value_cost`, and
    ///          `value_to_empty_account_cost` factors with an added buffer of 5,700 gas. It is
    ///          still possible to self-rekt by initiating a withdrawal with a minimum gas limit
    ///          that does not account for the `memory_expansion_cost` & `code_execution_cost`
    ///          factors of the dynamic cost of the `CALL` opcode.
    ///      2.) This function should *directly* precede the external call if possible. There is an
    ///          added buffer to account for gas consumed between this check and the call, but it
    ///          is only 5,700 gas.
    ///      3.) Because EIP-150 ensures that a maximum of 63/64ths of the remaining gas in the call
    ///          frame may be passed to a subcontext, we need to ensure that the gas will not be
    ///          truncated.
    ///      4.) Use wisely. This function is not a silver bullet.
    function hasMinGas(uint256 _minGas, uint256 _reservedGas) internal view returns (bool) {
        bool _hasMinGas;
        assembly {
            // Equation: gas × 63 ≥ minGas × 64 + 63(40_000 + reservedGas)
            _hasMinGas := iszero(lt(mul(gas(), 63), add(mul(_minGas, 64), mul(add(40000, _reservedGas), 63))))
        }
        return _hasMinGas;
    }

    /// @notice Perform a low level call without copying any returndata. This function
    ///         will revert if the call cannot be performed with the specified minimum
    ///         gas.
    /// @param _target   Address to call
    /// @param _minGas   The minimum amount of gas that may be passed to the call
    /// @param _value    Amount of value to pass to the call
    /// @param _calldata Calldata to pass to the call
    function callWithMinGas(
        address _target,
        uint256 _minGas,
        uint256 _value,
        bytes memory _calldata
    )
        internal
        returns (bool)
    {
        bool _success;
        bool _hasMinGas = hasMinGas(_minGas, 0);
        assembly {
            // Assertion: gasleft() >= (_minGas * 64) / 63 + 40_000
            if iszero(_hasMinGas) {
                // Store the "Error(string)" selector in scratch space.
                mstore(0, 0x08c379a0)
                // Store the pointer to the string length in scratch space.
                mstore(32, 32)
                // Store the string.
                //
                // SAFETY:
                // - We pad the beginning of the string with two zero bytes as well as the
                // length (24) to ensure that we override the free memory pointer at offset
                // 0x40. This is necessary because the free memory pointer is likely to
                // be greater than 1 byte when this function is called, but it is incredibly
                // unlikely that it will be greater than 3 bytes. As for the data within
                // 0x60, it is ensured that it is 0 due to 0x60 being the zero offset.
                // - It's fine to clobber the free memory pointer, we're reverting.
                mstore(88, 0x0000185361666543616c6c3a204e6f7420656e6f75676820676173)

                // Revert with 'Error("SafeCall: Not enough gas")'
                revert(28, 100)
            }

            // The call will be supplied at least ((_minGas * 64) / 63) gas due to the
            // above assertion. This ensures that, in all circumstances (except for when the
            // `_minGas` does not account for the `memory_expansion_cost` and `code_execution_cost`
            // factors of the dynamic cost of the `CALL` opcode), the call will receive at least
            // the minimum amount of gas specified.
            _success :=
                call(
                    gas(), // gas
                    _target, // recipient
                    _value, // ether value
                    add(_calldata, 32), // inloc
                    mload(_calldata), // inlen
                    0x00, // outloc
                    0x00 // outlen
                )
        }
        return _success;
    }
}


// File: src/libraries/Constants.sol
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

// Interfaces
import { IResourceMetering } from "interfaces/L1/IResourceMetering.sol";

/// @title Constants
/// @notice Constants is a library for storing constants. Simple! Don't put everything in here, just
///         the stuff used in multiple contracts. Constants that only apply to a single contract
///         should be defined in that contract instead.
library Constants {
    /// @notice Special address to be used as the tx origin for gas estimation calls in the
    ///         OptimismPortal and CrossDomainMessenger calls. You only need to use this address if
    ///         the minimum gas limit specified by the user is not actually enough to execute the
    ///         given message and you're attempting to estimate the actual necessary gas limit. We
    ///         use address(1) because it's the ecrecover precompile and therefore guaranteed to
    ///         never have any code on any EVM chain.
    address internal constant ESTIMATION_ADDRESS = address(1);

    /// @notice Value used for the L2 sender storage slot in both the OptimismPortal and the
    ///         CrossDomainMessenger contracts before an actual sender is set. This value is
    ///         non-zero to reduce the gas cost of message passing transactions.
    address internal constant DEFAULT_L2_SENDER = 0x000000000000000000000000000000000000dEaD;

    /// @notice The storage slot that holds the address of a proxy implementation.
    /// @dev `bytes32(uint256(keccak256('eip1967.proxy.implementation')) - 1)`
    bytes32 internal constant PROXY_IMPLEMENTATION_ADDRESS =
        0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc;

    /// @notice The storage slot that holds the address of the owner.
    /// @dev `bytes32(uint256(keccak256('eip1967.proxy.admin')) - 1)`
    bytes32 internal constant PROXY_OWNER_ADDRESS = 0xb53127684a568b3173ae13b9f8a6016e243e63b6e8ee1178d6a717850b5d6103;

    /// @notice The address that represents ether when dealing with ERC20 token addresses.
    address internal constant ETHER = 0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE;

    /// @notice The address that represents the system caller responsible for L1 attributes
    ///         transactions.
    address internal constant DEPOSITOR_ACCOUNT = 0xDeaDDEaDDeAdDeAdDEAdDEaddeAddEAdDEAd0001;

    /// @notice Returns the default values for the ResourceConfig. These are the recommended values
    ///         for a production network.
    function DEFAULT_RESOURCE_CONFIG() internal pure returns (IResourceMetering.ResourceConfig memory) {
        IResourceMetering.ResourceConfig memory config = IResourceMetering.ResourceConfig({
            maxResourceLimit: 20_000_000,
            elasticityMultiplier: 10,
            baseFeeMaxChangeDenominator: 8,
            minimumBaseFee: 1 gwei,
            systemTxMaxGas: 1_000_000,
            maximumBaseFee: type(uint128).max
        });
        return config;
    }
}


// File: src/libraries/Types.sol
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/// @title Types
/// @notice Contains various types used throughout the Optimism contract system.
library Types {
    /// @notice OutputProposal represents a commitment to the L2 state. The timestamp is the L1
    ///         timestamp that the output root is posted. This timestamp is used to verify that the
    ///         finalization period has passed since the output root was submitted.
    /// @custom:field outputRoot    Hash of the L2 output.
    /// @custom:field timestamp     Timestamp of the L1 block that the output root was submitted in.
    /// @custom:field l2BlockNumber L2 block number that the output corresponds to.
    struct OutputProposal {
        bytes32 outputRoot;
        uint128 timestamp;
        uint128 l2BlockNumber;
    }

    /// @notice Struct representing the elements that are hashed together to generate an output root
    ///         which itself represents a snapshot of the L2 state.
    /// @custom:field version                  Version of the output root.
    /// @custom:field stateRoot                Root of the state trie at the block of this output.
    /// @custom:field messagePasserStorageRoot Root of the message passer storage trie.
    /// @custom:field latestBlockhash          Hash of the block this output was generated from.
    struct OutputRootProof {
        bytes32 version;
        bytes32 stateRoot;
        bytes32 messagePasserStorageRoot;
        bytes32 latestBlockhash;
    }

    /// @notice Struct representing an output root with a chain id.
    /// @custom:field chainId The chain ID of the L2 chain that the output root commits to.
    /// @custom:field root    The output root.
    struct OutputRootWithChainId {
        uint256 chainId;
        bytes32 root;
    }

    /// @notice Struct representing a super root proof.
    /// @custom:field version     The version of the super root proof.
    /// @custom:field timestamp   The timestamp of the super root proof.
    /// @custom:field outputRoots The output roots that are included in the super root proof.
    struct SuperRootProof {
        bytes1 version;
        uint64 timestamp;
        OutputRootWithChainId[] outputRoots;
    }

    /// @notice Struct representing a deposit transaction (L1 => L2 transaction) created by an end
    ///         user (as opposed to a system deposit transaction generated by the system).
    /// @custom:field from        Address of the sender of the transaction.
    /// @custom:field to          Address of the recipient of the transaction.
    /// @custom:field isCreation  True if the transaction is a contract creation.
    /// @custom:field value       Value to send to the recipient.
    /// @custom:field mint        Amount of ETH to mint.
    /// @custom:field gasLimit    Gas limit of the transaction.
    /// @custom:field data        Data of the transaction.
    /// @custom:field l1BlockHash Hash of the block the transaction was submitted in.
    /// @custom:field logIndex    Index of the log in the block the transaction was submitted in.
    struct UserDepositTransaction {
        address from;
        address to;
        bool isCreation;
        uint256 value;
        uint256 mint;
        uint64 gasLimit;
        bytes data;
        bytes32 l1BlockHash;
        uint256 logIndex;
    }

    /// @notice Struct representing a withdrawal transaction.
    /// @custom:field nonce    Nonce of the withdrawal transaction
    /// @custom:field sender   Address of the sender of the transaction.
    /// @custom:field target   Address of the recipient of the transaction.
    /// @custom:field value    Value to send to the recipient.
    /// @custom:field gasLimit Gas limit of the transaction.
    /// @custom:field data     Data of the transaction.
    struct WithdrawalTransaction {
        uint256 nonce;
        address sender;
        address target;
        uint256 value;
        uint256 gasLimit;
        bytes data;
    }

    /// @notice Enum representing where the FeeVault withdraws funds to.
    /// @custom:value L1 FeeVault withdraws funds to L1.
    /// @custom:value L2 FeeVault withdraws funds to L2.
    enum WithdrawalNetwork {
        L1,
        L2
    }
}


// File: src/libraries/Hashing.sol
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

// Libraries
import { Types } from "src/libraries/Types.sol";
import { Encoding } from "src/libraries/Encoding.sol";

/// @title Hashing
/// @notice Hashing handles Optimism's various different hashing schemes.
library Hashing {
    /// @notice Computes the hash of the RLP encoded L2 transaction that would be generated when a
    ///         given deposit is sent to the L2 system. Useful for searching for a deposit in the L2
    ///         system.
    /// @param _tx User deposit transaction to hash.
    /// @return Hash of the RLP encoded L2 deposit transaction.
    function hashDepositTransaction(Types.UserDepositTransaction memory _tx) internal pure returns (bytes32) {
        return keccak256(Encoding.encodeDepositTransaction(_tx));
    }

    /// @notice Computes the deposit transaction's "source hash", a value that guarantees the hash
    ///         of the L2 transaction that corresponds to a deposit is unique and is
    ///         deterministically generated from L1 transaction data.
    /// @param _l1BlockHash Hash of the L1 block where the deposit was included.
    /// @param _logIndex    The index of the log that created the deposit transaction.
    /// @return Hash of the deposit transaction's "source hash".
    function hashDepositSource(bytes32 _l1BlockHash, uint256 _logIndex) internal pure returns (bytes32) {
        bytes32 depositId = keccak256(abi.encode(_l1BlockHash, _logIndex));
        return keccak256(abi.encode(bytes32(0), depositId));
    }

    /// @notice Hashes the cross domain message based on the version that is encoded into the
    ///         message nonce.
    /// @param _nonce    Message nonce with version encoded into the first two bytes.
    /// @param _sender   Address of the sender of the message.
    /// @param _target   Address of the target of the message.
    /// @param _value    ETH value to send to the target.
    /// @param _gasLimit Gas limit to use for the message.
    /// @param _data     Data to send with the message.
    /// @return Hashed cross domain message.
    function hashCrossDomainMessage(
        uint256 _nonce,
        address _sender,
        address _target,
        uint256 _value,
        uint256 _gasLimit,
        bytes memory _data
    )
        internal
        pure
        returns (bytes32)
    {
        (, uint16 version) = Encoding.decodeVersionedNonce(_nonce);
        if (version == 0) {
            return hashCrossDomainMessageV0(_target, _sender, _data, _nonce);
        } else if (version == 1) {
            return hashCrossDomainMessageV1(_nonce, _sender, _target, _value, _gasLimit, _data);
        } else {
            revert("Hashing: unknown cross domain message version");
        }
    }

    /// @notice Hashes a cross domain message based on the V0 (legacy) encoding.
    /// @param _target Address of the target of the message.
    /// @param _sender Address of the sender of the message.
    /// @param _data   Data to send with the message.
    /// @param _nonce  Message nonce.
    /// @return Hashed cross domain message.
    function hashCrossDomainMessageV0(
        address _target,
        address _sender,
        bytes memory _data,
        uint256 _nonce
    )
        internal
        pure
        returns (bytes32)
    {
        return keccak256(Encoding.encodeCrossDomainMessageV0(_target, _sender, _data, _nonce));
    }

    /// @notice Hashes a cross domain message based on the V1 (current) encoding.
    /// @param _nonce    Message nonce.
    /// @param _sender   Address of the sender of the message.
    /// @param _target   Address of the target of the message.
    /// @param _value    ETH value to send to the target.
    /// @param _gasLimit Gas limit to use for the message.
    /// @param _data     Data to send with the message.
    /// @return Hashed cross domain message.
    function hashCrossDomainMessageV1(
        uint256 _nonce,
        address _sender,
        address _target,
        uint256 _value,
        uint256 _gasLimit,
        bytes memory _data
    )
        internal
        pure
        returns (bytes32)
    {
        return keccak256(Encoding.encodeCrossDomainMessageV1(_nonce, _sender, _target, _value, _gasLimit, _data));
    }

    /// @notice Derives the withdrawal hash according to the encoding in the L2 Withdrawer contract
    /// @param _tx Withdrawal transaction to hash.
    /// @return Hashed withdrawal transaction.
    function hashWithdrawal(Types.WithdrawalTransaction memory _tx) internal pure returns (bytes32) {
        return keccak256(abi.encode(_tx.nonce, _tx.sender, _tx.target, _tx.value, _tx.gasLimit, _tx.data));
    }

    /// @notice Hashes the various elements of an output root proof into an output root hash which
    ///         can be used to check if the proof is valid.
    /// @param _outputRootProof Output root proof which should hash to an output root.
    /// @return Hashed output root proof.
    function hashOutputRootProof(Types.OutputRootProof memory _outputRootProof) internal pure returns (bytes32) {
        return keccak256(
            abi.encode(
                _outputRootProof.version,
                _outputRootProof.stateRoot,
                _outputRootProof.messagePasserStorageRoot,
                _outputRootProof.latestBlockhash
            )
        );
    }

    /// @notice Generates a unique hash for cross l2 messages. This hash is used to identify
    ///         the message and ensure it is not relayed more than once.
    /// @param _destination Chain ID of the destination chain.
    /// @param _source Chain ID of the source chain.
    /// @param _nonce Unique nonce associated with the message to prevent replay attacks.
    /// @param _sender Address of the user who originally sent the message.
    /// @param _target Address of the contract or wallet that the message is targeting on the destination chain.
    /// @param _message The message payload to be relayed to the target on the destination chain.
    /// @return Hash of the encoded message parameters, used to uniquely identify the message.
    function hashL2toL2CrossDomainMessage(
        uint256 _destination,
        uint256 _source,
        uint256 _nonce,
        address _sender,
        address _target,
        bytes memory _message
    )
        internal
        pure
        returns (bytes32)
    {
        return keccak256(abi.encode(_destination, _source, _nonce, _sender, _target, _message));
    }

    /// @notice Hashes a Super Root proof into a Super Root.
    /// @param _superRootProof Super Root proof to hash.
    /// @return Hashed super root proof.
    function hashSuperRootProof(Types.SuperRootProof memory _superRootProof) internal pure returns (bytes32) {
        return keccak256(Encoding.encodeSuperRootProof(_superRootProof));
    }
}


// File: src/libraries/trie/SecureMerkleTrie.sol
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

// Libraries
import { MerkleTrie } from "src/libraries/trie/MerkleTrie.sol";

/// @title SecureMerkleTrie
/// @notice SecureMerkleTrie is a thin wrapper around the MerkleTrie library that hashes the input
///         keys. Ethereum's state trie hashes input keys before storing them.
library SecureMerkleTrie {
    /// @notice Verifies a proof that a given key/value pair is present in the Merkle trie.
    /// @param _key   Key of the node to search for, as a hex string.
    /// @param _value Value of the node to search for, as a hex string.
    /// @param _proof Merkle trie inclusion proof for the desired node. Unlike traditional Merkle
    ///               trees, this proof is executed top-down and consists of a list of RLP-encoded
    ///               nodes that make a path down to the target node.
    /// @param _root  Known root of the Merkle trie. Used to verify that the included proof is
    ///               correctly constructed.
    /// @return valid_ Whether or not the proof is valid.
    function verifyInclusionProof(
        bytes memory _key,
        bytes memory _value,
        bytes[] memory _proof,
        bytes32 _root
    )
        internal
        pure
        returns (bool valid_)
    {
        bytes memory key = _getSecureKey(_key);
        valid_ = MerkleTrie.verifyInclusionProof(key, _value, _proof, _root);
    }

    /// @notice Retrieves the value associated with a given key.
    /// @param _key   Key to search for, as hex bytes.
    /// @param _proof Merkle trie inclusion proof for the key.
    /// @param _root  Known root of the Merkle trie.
    /// @return value_ Value of the key if it exists.
    function get(bytes memory _key, bytes[] memory _proof, bytes32 _root) internal pure returns (bytes memory value_) {
        bytes memory key = _getSecureKey(_key);
        value_ = MerkleTrie.get(key, _proof, _root);
    }

    /// @notice Computes the hashed version of the input key.
    /// @param _key Key to hash.
    /// @return hash_ Hashed version of the key.
    function _getSecureKey(bytes memory _key) private pure returns (bytes memory hash_) {
        hash_ = abi.encodePacked(keccak256(_key));
    }
}


// File: src/vendor/AddressAliasHelper.sol
// SPDX-License-Identifier: Apache-2.0

/*
 * Copyright 2019-2021, Offchain Labs, Inc.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *    http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

pragma solidity ^0.8.0;

library AddressAliasHelper {
    uint160 constant offset = uint160(0x1111000000000000000000000000000000001111);

    /// @notice Utility function that converts the address in the L1 that submitted a tx to
    /// the inbox to the msg.sender viewed in the L2
    /// @param l1Address the address in the L1 that triggered the tx to L2
    /// @return l2Address L2 address as viewed in msg.sender
    function applyL1ToL2Alias(address l1Address) internal pure returns (address l2Address) {
        unchecked {
            l2Address = address(uint160(l1Address) + offset);
        }
    }

    /// @notice Utility function that converts the msg.sender viewed in the L2 to the
    /// address in the L1 that submitted a tx to the inbox
    /// @param l2Address L2 address as viewed in msg.sender
    /// @return l1Address the address in the L1 that triggered the tx to L2
    function undoL1ToL2Alias(address l2Address) internal pure returns (address l1Address) {
        unchecked {
            l1Address = address(uint160(l2Address) - offset);
        }
    }
}


// File: src/dispute/lib/Types.sol
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.15;

// Libraries
import {
    Position,
    Hash,
    GameType,
    VMStatus,
    Timestamp,
    Duration,
    Clock,
    GameId,
    Claim,
    LibGameId,
    LibClock
} from "src/dispute/lib/LibUDT.sol";

/// @notice The current status of the dispute game.
enum GameStatus {
    // The game is currently in progress, and has not been resolved.
    IN_PROGRESS,
    // The game has concluded, and the `rootClaim` was challenged successfully.
    CHALLENGER_WINS,
    // The game has concluded, and the `rootClaim` could not be contested.
    DEFENDER_WINS
}

/// @notice The game's bond distribution type. Games are expected to start in the `UNDECIDED`
///         state, and then choose either `NORMAL` or `REFUND`.
enum BondDistributionMode {
    // Bond distribution strategy has not been chosen.
    UNDECIDED,
    // Bonds should be distributed as normal.
    NORMAL,
    // Bonds should be refunded to claimants.
    REFUND
}

/// @notice Represents an L2 root and the L2 sequence number at which it was generated.
/// @custom:field root The output root.
/// @custom:field l2SequenceNumber The L2 Sequence Number ( e.g. block number / timestamp) at which the root was
/// generated.
struct Proposal {
    Hash root;
    uint256 l2SequenceNumber;
}

/// @title GameTypes
/// @notice A library that defines the IDs of games that can be played.
library GameTypes {
    /// @dev A dispute game type the uses the cannon vm.
    GameType internal constant CANNON = GameType.wrap(0);

    /// @dev A permissioned dispute game type that uses the cannon vm.
    GameType internal constant PERMISSIONED_CANNON = GameType.wrap(1);

    /// @notice A dispute game type that uses the asterisc vm.
    GameType internal constant ASTERISC = GameType.wrap(2);

    /// @notice A dispute game type that uses the asterisc vm with Kona.
    GameType internal constant ASTERISC_KONA = GameType.wrap(3);

    /// @notice A dispute game type that uses the cannon vm (Super Roots).
    GameType internal constant SUPER_CANNON = GameType.wrap(4);

    /// @notice A dispute game type that uses the permissioned cannon vm (Super Roots).
    GameType internal constant SUPER_PERMISSIONED_CANNON = GameType.wrap(5);

    /// @notice A dispute game type that uses OP Succinct
    GameType internal constant OP_SUCCINCT = GameType.wrap(6);

    /// @notice A dispute game type that uses the asterisc vm with Kona (Super Roots).
    GameType internal constant SUPER_ASTERISC_KONA = GameType.wrap(7);

    /// @notice A dispute game type that uses the cannon vm with Kona.
    GameType internal constant CANNON_KONA = GameType.wrap(8);

    /// @notice A dispute game type that uses the cannon vm with Kona (Super Roots).
    GameType internal constant SUPER_CANNON_KONA = GameType.wrap(9);

    /// @notice A dispute game type with short game duration for testing withdrawals.
    ///         Not intended for production use.
    GameType internal constant FAST = GameType.wrap(254);

    /// @notice A dispute game type that uses an alphabet vm.
    ///         Not intended for production use.
    GameType internal constant ALPHABET = GameType.wrap(255);

    /// @notice A dispute game type that uses RISC Zero's Kailua
    GameType internal constant KAILUA = GameType.wrap(1337);
}

/// @title VMStatuses
/// @notice Named type aliases for the various valid VM status bytes.
library VMStatuses {
    /// @notice The VM has executed successfully and the outcome is valid.
    VMStatus internal constant VALID = VMStatus.wrap(0);

    /// @notice The VM has executed successfully and the outcome is invalid.
    VMStatus internal constant INVALID = VMStatus.wrap(1);

    /// @notice The VM has paniced.
    VMStatus internal constant PANIC = VMStatus.wrap(2);

    /// @notice The VM execution is still in progress.
    VMStatus internal constant UNFINISHED = VMStatus.wrap(3);
}

/// @title LocalPreimageKey
/// @notice Named type aliases for local `PreimageOracle` key identifiers.
library LocalPreimageKey {
    /// @notice The identifier for the L1 head hash.
    uint256 internal constant L1_HEAD_HASH = 0x01;

    /// @notice The identifier for the starting output root.
    uint256 internal constant STARTING_OUTPUT_ROOT = 0x02;

    /// @notice The identifier for the disputed output root.
    uint256 internal constant DISPUTED_OUTPUT_ROOT = 0x03;

    /// @notice The identifier for the disputed L2 block number.
    uint256 internal constant DISPUTED_L2_BLOCK_NUMBER = 0x04;

    /// @notice The identifier for the chain ID.
    uint256 internal constant CHAIN_ID = 0x05;
}


// File: src/libraries/Features.sol
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/// @notice Features is a library that stores feature name constants. Can be used alongside the
///         feature flagging functionality in the SystemConfig contract to selectively enable or
///         disable customizable features of the OP Stack.
library Features {
    /// @notice The ETH_LOCKBOX feature determines if the system is configured to use the
    ///         ETHLockbox contract in the OptimismPortal. When the ETH_LOCKBOX feature is active
    ///         and the ETHLockbox contract has been configured, the OptimismPortal will use the
    ///         ETHLockbox to store ETH instead of storing ETH directly in the portal itself.
    bytes32 internal constant ETH_LOCKBOX = "ETH_LOCKBOX";
}


// File: interfaces/universal/ISemver.sol
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/// @title ISemver
/// @notice ISemver is a simple contract for ensuring that contracts are
///         versioned using semantic versioning.
interface ISemver {
    /// @notice Getter for the semantic version of the contract. This is not
    ///         meant to be used onchain but instead meant to be used by offchain
    ///         tooling.
    /// @return Semver contract version as a string.
    function version() external view returns (string memory);
}


// File: interfaces/L1/ISystemConfig.sol
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import { IResourceMetering } from "interfaces/L1/IResourceMetering.sol";
import { ISuperchainConfig } from "interfaces/L1/ISuperchainConfig.sol";
import { IProxyAdminOwnedBase } from "interfaces/L1/IProxyAdminOwnedBase.sol";

interface ISystemConfig is IProxyAdminOwnedBase {
    enum UpdateType {
        BATCHER,
        FEE_SCALARS,
        GAS_LIMIT,
        UNSAFE_BLOCK_SIGNER,
        EIP_1559_PARAMS,
        OPERATOR_FEE_PARAMS,
        MIN_BASE_FEE,
        DA_FOOTPRINT_GAS_SCALAR
    }

    struct Addresses {
        address l1CrossDomainMessenger;
        address l1ERC721Bridge;
        address l1StandardBridge;
        address optimismPortal;
        address optimismMintableERC20Factory;
    }

    error ReinitializableBase_ZeroInitVersion();
    error SystemConfig_InvalidFeatureState();

    event ConfigUpdate(uint256 indexed version, UpdateType indexed updateType, bytes data);
    event FeatureSet(bytes32 indexed feature, bool indexed enabled);
    event Initialized(uint8 version);
    event OwnershipTransferred(address indexed previousOwner, address indexed newOwner);

    function BATCH_INBOX_SLOT() external view returns (bytes32);
    function L1_CROSS_DOMAIN_MESSENGER_SLOT() external view returns (bytes32);
    function L1_ERC_721_BRIDGE_SLOT() external view returns (bytes32);
    function L1_STANDARD_BRIDGE_SLOT() external view returns (bytes32);
    function OPTIMISM_MINTABLE_ERC20_FACTORY_SLOT() external view returns (bytes32);
    function OPTIMISM_PORTAL_SLOT() external view returns (bytes32);
    function START_BLOCK_SLOT() external view returns (bytes32);
    function UNSAFE_BLOCK_SIGNER_SLOT() external view returns (bytes32);
    function VERSION() external view returns (uint256);
    function basefeeScalar() external view returns (uint32);
    function batchInbox() external view returns (address addr_);
    function batcherHash() external view returns (bytes32);
    function blobbasefeeScalar() external view returns (uint32);
    function disputeGameFactory() external view returns (address addr_);
    function gasLimit() external view returns (uint64);
    function eip1559Denominator() external view returns (uint32);
    function eip1559Elasticity() external view returns (uint32);
    function getAddresses() external view returns (Addresses memory);
    function initialize(
        address _owner,
        uint32 _basefeeScalar,
        uint32 _blobbasefeeScalar,
        bytes32 _batcherHash,
        uint64 _gasLimit,
        address _unsafeBlockSigner,
        IResourceMetering.ResourceConfig memory _config,
        address _batchInbox,
        Addresses memory _addresses,
        uint256 _l2ChainId,
        ISuperchainConfig _superchainConfig
    )
        external;
    function initVersion() external view returns (uint8);
    function l1CrossDomainMessenger() external view returns (address addr_);
    function l1ERC721Bridge() external view returns (address addr_);
    function l1StandardBridge() external view returns (address addr_);
    function l2ChainId() external view returns (uint256);
    function maximumGasLimit() external pure returns (uint64);
    function minimumGasLimit() external view returns (uint64);
    function operatorFeeConstant() external view returns (uint64);
    function operatorFeeScalar() external view returns (uint32);
    function minBaseFee() external view returns (uint64);
    function daFootprintGasScalar() external view returns (uint16);
    function optimismMintableERC20Factory() external view returns (address addr_);
    function optimismPortal() external view returns (address addr_);
    function overhead() external view returns (uint256);
    function owner() external view returns (address);
    function renounceOwnership() external;
    function resourceConfig() external view returns (IResourceMetering.ResourceConfig memory);
    function scalar() external view returns (uint256);
    function setBatcherHash(bytes32 _batcherHash) external;
    function setGasConfig(uint256 _overhead, uint256 _scalar) external;
    function setGasConfigEcotone(uint32 _basefeeScalar, uint32 _blobbasefeeScalar) external;
    function setGasLimit(uint64 _gasLimit) external;
    function setOperatorFeeScalars(uint32 _operatorFeeScalar, uint64 _operatorFeeConstant) external;
    function setUnsafeBlockSigner(address _unsafeBlockSigner) external;
    function setEIP1559Params(uint32 _denominator, uint32 _elasticity) external;
    function setMinBaseFee(uint64 _minBaseFee) external;
    function setDAFootprintGasScalar(uint16 _daFootprintGasScalar) external;
    function startBlock() external view returns (uint256 startBlock_);
    function transferOwnership(address newOwner) external; // nosemgrep
    function unsafeBlockSigner() external view returns (address addr_);
    function version() external pure returns (string memory);
    function paused() external view returns (bool);
    function superchainConfig() external view returns (ISuperchainConfig);
    function guardian() external view returns (address);
    function setFeature(bytes32 _feature, bool _enabled) external;
    function isFeatureEnabled(bytes32) external view returns (bool);

    function __constructor__() external;
}


// File: interfaces/L1/IResourceMetering.sol
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

interface IResourceMetering {
    struct ResourceParams {
        uint128 prevBaseFee;
        uint64 prevBoughtGas;
        uint64 prevBlockNum;
    }

    struct ResourceConfig {
        uint32 maxResourceLimit;
        uint8 elasticityMultiplier;
        uint8 baseFeeMaxChangeDenominator;
        uint32 minimumBaseFee;
        uint32 systemTxMaxGas;
        uint128 maximumBaseFee;
    }

    error OutOfGas();

    event Initialized(uint8 version);

    function params() external view returns (uint128 prevBaseFee, uint64 prevBoughtGas, uint64 prevBlockNum); // nosemgrep

    function __constructor__() external;
}


// File: interfaces/dispute/IDisputeGameFactory.sol
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import { IDisputeGame } from "interfaces/dispute/IDisputeGame.sol";
import { GameId, Timestamp, Claim, Hash, GameType } from "src/dispute/lib/Types.sol";
import { IProxyAdminOwnedBase } from "interfaces/L1/IProxyAdminOwnedBase.sol";
import { IReinitializableBase } from "interfaces/universal/IReinitializableBase.sol";

interface IDisputeGameFactory is IProxyAdminOwnedBase, IReinitializableBase {
    struct GameSearchResult {
        uint256 index;
        GameId metadata;
        Timestamp timestamp;
        Claim rootClaim;
        bytes extraData;
    }

    error GameAlreadyExists(Hash uuid);
    error IncorrectBondAmount();
    error NoImplementation(GameType gameType);

    event DisputeGameCreated(address indexed disputeProxy, GameType indexed gameType, Claim indexed rootClaim);
    event ImplementationSet(address indexed impl, GameType indexed gameType);
    event ImplementationArgsSet(GameType indexed gameType, bytes args);
    event InitBondUpdated(GameType indexed gameType, uint256 indexed newBond);
    event Initialized(uint8 version);
    event OwnershipTransferred(address indexed previousOwner, address indexed newOwner);

    function create(
        GameType _gameType,
        Claim _rootClaim,
        bytes memory _extraData
    )
        external
        payable
        returns (IDisputeGame proxy_);
    function findLatestGames(
        GameType _gameType,
        uint256 _start,
        uint256 _n
    )
        external
        view
        returns (GameSearchResult[] memory games_);
    function gameAtIndex(uint256 _index)
        external
        view
        returns (GameType gameType_, Timestamp timestamp_, IDisputeGame proxy_);
    function gameCount() external view returns (uint256 gameCount_);
    function gameArgs(GameType) external view returns (bytes memory);
    function gameImpls(GameType) external view returns (IDisputeGame);
    function games(
        GameType _gameType,
        Claim _rootClaim,
        bytes memory _extraData
    )
        external
        view
        returns (IDisputeGame proxy_, Timestamp timestamp_);
    function getGameUUID(
        GameType _gameType,
        Claim _rootClaim,
        bytes memory _extraData
    )
        external
        pure
        returns (Hash uuid_);
    function initBonds(GameType) external view returns (uint256);
    function initialize(address _owner) external;
    function owner() external view returns (address);
    function renounceOwnership() external;
    function setImplementation(GameType _gameType, IDisputeGame _impl) external;
    function setImplementation(GameType _gameType, IDisputeGame _impl, bytes calldata _args) external;
    function setInitBond(GameType _gameType, uint256 _initBond) external;
    function transferOwnership(address newOwner) external; // nosemgrep
    function version() external view returns (string memory);

    function __constructor__() external;
}


// File: interfaces/dispute/IDisputeGame.sol
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import { IInitializable } from "interfaces/dispute/IInitializable.sol";
import { Timestamp, GameStatus, GameType, Claim, Hash } from "src/dispute/lib/Types.sol";

interface IDisputeGame is IInitializable {
    event Resolved(GameStatus indexed status);

    function createdAt() external view returns (Timestamp);
    function resolvedAt() external view returns (Timestamp);
    function status() external view returns (GameStatus);
    function gameType() external view returns (GameType gameType_);
    function gameCreator() external pure returns (address creator_);
    function rootClaim() external pure returns (Claim rootClaim_);
    function l1Head() external pure returns (Hash l1Head_);
    function l2SequenceNumber() external pure returns (uint256 l2SequenceNumber_);
    function extraData() external pure returns (bytes memory extraData_);
    function resolve() external returns (GameStatus status_);
    function gameData() external view returns (GameType gameType_, Claim rootClaim_, bytes memory extraData_);
    function wasRespectedGameTypeWhenCreated() external view returns (bool);
}


// File: interfaces/dispute/IAnchorStateRegistry.sol
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import { IDisputeGame } from "interfaces/dispute/IDisputeGame.sol";
import { IFaultDisputeGame } from "interfaces/dispute/IFaultDisputeGame.sol";
import { IDisputeGameFactory } from "interfaces/dispute/IDisputeGameFactory.sol";
import { ISystemConfig } from "interfaces/L1/ISystemConfig.sol";
import { GameType, Hash, Proposal } from "src/dispute/lib/Types.sol";
import { ISuperchainConfig } from "interfaces/L1/ISuperchainConfig.sol";
import { IProxyAdminOwnedBase } from "interfaces/L1/IProxyAdminOwnedBase.sol";

interface IAnchorStateRegistry is IProxyAdminOwnedBase {
    error AnchorStateRegistry_InvalidAnchorGame();
    error AnchorStateRegistry_Unauthorized();
    error ReinitializableBase_ZeroInitVersion();

    event AnchorUpdated(IFaultDisputeGame indexed game);
    event DisputeGameBlacklisted(IDisputeGame indexed disputeGame);
    event Initialized(uint8 version);
    event RespectedGameTypeSet(GameType gameType);
    event RetirementTimestampSet(uint256 timestamp);

    function initVersion() external view returns (uint8);
    function anchorGame() external view returns (IFaultDisputeGame);
    function anchors(GameType) external view returns (Hash, uint256);
    function blacklistDisputeGame(IDisputeGame _disputeGame) external;
    function disputeGameBlacklist(IDisputeGame) external view returns (bool);
    function getAnchorRoot() external view returns (Hash, uint256);
    function disputeGameFinalityDelaySeconds() external view returns (uint256);
    function disputeGameFactory() external view returns (IDisputeGameFactory);
    function initialize(
        ISystemConfig _systemConfig,
        IDisputeGameFactory _disputeGameFactory,
        Proposal memory _startingAnchorRoot,
        GameType _startingRespectedGameType
    )
        external;
    function isGameBlacklisted(IDisputeGame _game) external view returns (bool);
    function isGameProper(IDisputeGame _game) external view returns (bool);
    function isGameRegistered(IDisputeGame _game) external view returns (bool);
    function isGameResolved(IDisputeGame _game) external view returns (bool);
    function isGameRespected(IDisputeGame _game) external view returns (bool);
    function isGameRetired(IDisputeGame _game) external view returns (bool);
    function isGameFinalized(IDisputeGame _game) external view returns (bool);
    function isGameClaimValid(IDisputeGame _game) external view returns (bool);
    function paused() external view returns (bool);
    function respectedGameType() external view returns (GameType);
    function retirementTimestamp() external view returns (uint64);
    function setAnchorState(IDisputeGame _game) external;
    function setRespectedGameType(GameType _gameType) external;
    function systemConfig() external view returns (ISystemConfig);
    function updateRetirementTimestamp() external;
    function version() external view returns (string memory);
    function superchainConfig() external view returns (ISuperchainConfig);

    function __constructor__(
        uint256 _disputeGameFinalityDelaySeconds
    ) external;
}


// File: interfaces/L1/IETHLockbox.sol
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import { ISemver } from "interfaces/universal/ISemver.sol";
import { ISystemConfig } from "interfaces/L1/ISystemConfig.sol";
import { IProxyAdminOwnedBase } from "interfaces/L1/IProxyAdminOwnedBase.sol";
import { IOptimismPortal2 } from "interfaces/L1/IOptimismPortal2.sol";
import { ISuperchainConfig } from "interfaces/L1/ISuperchainConfig.sol";
import { IReinitializableBase } from "interfaces/universal/IReinitializableBase.sol";

interface IETHLockbox is IProxyAdminOwnedBase, ISemver, IReinitializableBase {
    error ETHLockbox_Unauthorized();
    error ETHLockbox_Paused();
    error ETHLockbox_InsufficientBalance();
    error ETHLockbox_NoWithdrawalTransactions();
    error ETHLockbox_DifferentSuperchainConfig();

    event Initialized(uint8 version);
    event ETHLocked(IOptimismPortal2 indexed portal, uint256 amount);
    event ETHUnlocked(IOptimismPortal2 indexed portal, uint256 amount);
    event PortalAuthorized(IOptimismPortal2 indexed portal);
    event LockboxAuthorized(IETHLockbox indexed lockbox);
    event LiquidityMigrated(IETHLockbox indexed lockbox, uint256 amount);
    event LiquidityReceived(IETHLockbox indexed lockbox, uint256 amount);

    function initialize(ISystemConfig _systemConfig, IOptimismPortal2[] calldata _portals) external;
    function systemConfig() external view returns (ISystemConfig);
    function paused() external view returns (bool);
    function authorizedPortals(IOptimismPortal2) external view returns (bool);
    function authorizedLockboxes(IETHLockbox) external view returns (bool);
    function receiveLiquidity() external payable;
    function lockETH() external payable;
    function unlockETH(uint256 _value) external;
    function authorizePortal(IOptimismPortal2 _portal) external;
    function authorizeLockbox(IETHLockbox _lockbox) external;
    function migrateLiquidity(IETHLockbox _lockbox) external;
    function superchainConfig() external view returns (ISuperchainConfig);

    function __constructor__() external;
}


// File: interfaces/L1/ISuperchainConfig.sol
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import { IProxyAdminOwnedBase } from "interfaces/L1/IProxyAdminOwnedBase.sol";

interface ISuperchainConfig is IProxyAdminOwnedBase {
    enum UpdateType {
        GUARDIAN
    }

    event ConfigUpdate(UpdateType indexed updateType, bytes data);
    event Initialized(uint8 version);
    event Paused(address identifier);
    event Unpaused(address identifier);

    error SuperchainConfig_OnlyGuardian();
    error SuperchainConfig_AlreadyPaused(address identifier);
    error SuperchainConfig_NotAlreadyPaused(address identifier);
    error ReinitializableBase_ZeroInitVersion();

    function guardian() external view returns (address);
    function initialize(address _guardian) external;
    function pause(address _identifier) external;
    function unpause(address _identifier) external;
    function pausable(address _identifier) external view returns (bool);
    function paused() external view returns (bool);
    function paused(address _identifier) external view returns (bool);
    function expiration(address _identifier) external view returns (uint256);
    function extend(address _identifier) external;
    function version() external view returns (string memory);
    function pauseTimestamps(address) external view returns (uint256);
    function pauseExpiry() external view returns (uint256);
    function initVersion() external view returns (uint8);

    function __constructor__() external;
}


// File: src/libraries/Storage.sol
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/// @title Storage
/// @notice Storage handles reading and writing to arbitary storage locations
library Storage {
    /// @notice Returns an address stored in an arbitrary storage slot.
    ///         These storage slots decouple the storage layout from
    ///         solc's automation.
    /// @param _slot The storage slot to retrieve the address from.
    function getAddress(bytes32 _slot) internal view returns (address addr_) {
        assembly {
            addr_ := sload(_slot)
        }
    }

    /// @notice Stores an address in an arbitrary storage slot, `_slot`.
    /// @param _slot The storage slot to store the address in.
    /// @param _address The protocol version to store
    /// @dev WARNING! This function must be used cautiously, as it allows for overwriting addresses
    ///      in arbitrary storage slots.
    function setAddress(bytes32 _slot, address _address) internal {
        assembly {
            sstore(_slot, _address)
        }
    }

    /// @notice Returns a uint256 stored in an arbitrary storage slot.
    ///         These storage slots decouple the storage layout from
    ///         solc's automation.
    /// @param _slot The storage slot to retrieve the address from.
    function getUint(bytes32 _slot) internal view returns (uint256 value_) {
        assembly {
            value_ := sload(_slot)
        }
    }

    /// @notice Stores a value in an arbitrary storage slot, `_slot`.
    /// @param _slot The storage slot to store the address in.
    /// @param _value The protocol version to store
    /// @dev WARNING! This function must be used cautiously, as it allows for overwriting values
    ///      in arbitrary storage slots.
    function setUint(bytes32 _slot, uint256 _value) internal {
        assembly {
            sstore(_slot, _value)
        }
    }

    /// @notice Returns a bytes32 stored in an arbitrary storage slot.
    ///         These storage slots decouple the storage layout from
    ///         solc's automation.
    /// @param _slot The storage slot to retrieve the address from.
    function getBytes32(bytes32 _slot) internal view returns (bytes32 value_) {
        assembly {
            value_ := sload(_slot)
        }
    }

    /// @notice Stores a bytes32 value in an arbitrary storage slot, `_slot`.
    /// @param _slot The storage slot to store the address in.
    /// @param _value The bytes32 value to store.
    /// @dev WARNING! This function must be used cautiously, as it allows for overwriting values
    ///      in arbitrary storage slots.
    function setBytes32(bytes32 _slot, bytes32 _value) internal {
        assembly {
            sstore(_slot, _value)
        }
    }

    /// @notice Stores a bool value in an arbitrary storage slot, `_slot`.
    /// @param _slot The storage slot to store the bool in.
    /// @param _value The bool value to store
    /// @dev WARNING! This function must be used cautiously, as it allows for overwriting values
    ///      in arbitrary storage slots.
    function setBool(bytes32 _slot, bool _value) internal {
        assembly {
            sstore(_slot, _value)
        }
    }

    /// @notice Returns a bool stored in an arbitrary storage slot.
    /// @param _slot The storage slot to retrieve the bool from.
    function getBool(bytes32 _slot) internal view returns (bool value_) {
        assembly {
            value_ := sload(_slot)
        }
    }
}


// File: interfaces/universal/IProxyAdmin.sol
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import { IAddressManager } from "interfaces/legacy/IAddressManager.sol";

interface IProxyAdmin {
    enum ProxyType {
        ERC1967,
        CHUGSPLASH,
        RESOLVED
    }

    event OwnershipTransferred(address indexed previousOwner, address indexed newOwner);

    function addressManager() external view returns (IAddressManager);
    function changeProxyAdmin(address payable _proxy, address _newAdmin) external;
    function getProxyAdmin(address payable _proxy) external view returns (address);
    function getProxyImplementation(address _proxy) external view returns (address);
    function implementationName(address) external view returns (string memory);
    function isUpgrading() external view returns (bool);
    function owner() external view returns (address);
    function proxyType(address) external view returns (ProxyType);
    function renounceOwnership() external;
    function setAddress(string memory _name, address _address) external;
    function setAddressManager(IAddressManager _address) external;
    function setImplementationName(address _address, string memory _name) external;
    function setProxyType(address _address, ProxyType _type) external;
    function setUpgrading(bool _upgrading) external;
    function transferOwnership(address newOwner) external; // nosemgrep
    function upgrade(address payable _proxy, address _implementation) external;
    function upgradeAndCall(address payable _proxy, address _implementation, bytes memory _data) external payable;

    function __constructor__(address _owner) external;
}


// File: interfaces/legacy/IAddressManager.sol
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import { IOwnable } from "interfaces/universal/IOwnable.sol";

/// @title IAddressManager
/// @notice Interface for the AddressManager contract.
interface IAddressManager is IOwnable {
    event AddressSet(string indexed name, address newAddress, address oldAddress);

    function getAddress(string memory _name) external view returns (address);
    function setAddress(string memory _name, address _address) external;

    function __constructor__() external;
}


// File: lib/openzeppelin-contracts/contracts/utils/Address.sol
// SPDX-License-Identifier: MIT
// OpenZeppelin Contracts (last updated v4.7.0) (utils/Address.sol)

pragma solidity ^0.8.1;

/**
 * @dev Collection of functions related to the address type
 */
library Address {
    /**
     * @dev Returns true if `account` is a contract.
     *
     * [IMPORTANT]
     * ====
     * It is unsafe to assume that an address for which this function returns
     * false is an externally-owned account (EOA) and not a contract.
     *
     * Among others, `isContract` will return false for the following
     * types of addresses:
     *
     *  - an externally-owned account
     *  - a contract in construction
     *  - an address where a contract will be created
     *  - an address where a contract lived, but was destroyed
     * ====
     *
     * [IMPORTANT]
     * ====
     * You shouldn't rely on `isContract` to protect against flash loan attacks!
     *
     * Preventing calls from contracts is highly discouraged. It breaks composability, breaks support for smart wallets
     * like Gnosis Safe, and does not provide security since it can be circumvented by calling from a contract
     * constructor.
     * ====
     */
    function isContract(address account) internal view returns (bool) {
        // This method relies on extcodesize/address.code.length, which returns 0
        // for contracts in construction, since the code is only stored at the end
        // of the constructor execution.

        return account.code.length > 0;
    }

    /**
     * @dev Replacement for Solidity's `transfer`: sends `amount` wei to
     * `recipient`, forwarding all available gas and reverting on errors.
     *
     * https://eips.ethereum.org/EIPS/eip-1884[EIP1884] increases the gas cost
     * of certain opcodes, possibly making contracts go over the 2300 gas limit
     * imposed by `transfer`, making them unable to receive funds via
     * `transfer`. {sendValue} removes this limitation.
     *
     * https://diligence.consensys.net/posts/2019/09/stop-using-soliditys-transfer-now/[Learn more].
     *
     * IMPORTANT: because control is transferred to `recipient`, care must be
     * taken to not create reentrancy vulnerabilities. Consider using
     * {ReentrancyGuard} or the
     * https://solidity.readthedocs.io/en/v0.5.11/security-considerations.html#use-the-checks-effects-interactions-pattern[checks-effects-interactions pattern].
     */
    function sendValue(address payable recipient, uint256 amount) internal {
        require(address(this).balance >= amount, "Address: insufficient balance");

        (bool success, ) = recipient.call{value: amount}("");
        require(success, "Address: unable to send value, recipient may have reverted");
    }

    /**
     * @dev Performs a Solidity function call using a low level `call`. A
     * plain `call` is an unsafe replacement for a function call: use this
     * function instead.
     *
     * If `target` reverts with a revert reason, it is bubbled up by this
     * function (like regular Solidity function calls).
     *
     * Returns the raw returned data. To convert to the expected return value,
     * use https://solidity.readthedocs.io/en/latest/units-and-global-variables.html?highlight=abi.decode#abi-encoding-and-decoding-functions[`abi.decode`].
     *
     * Requirements:
     *
     * - `target` must be a contract.
     * - calling `target` with `data` must not revert.
     *
     * _Available since v3.1._
     */
    function functionCall(address target, bytes memory data) internal returns (bytes memory) {
        return functionCall(target, data, "Address: low-level call failed");
    }

    /**
     * @dev Same as {xref-Address-functionCall-address-bytes-}[`functionCall`], but with
     * `errorMessage` as a fallback revert reason when `target` reverts.
     *
     * _Available since v3.1._
     */
    function functionCall(
        address target,
        bytes memory data,
        string memory errorMessage
    ) internal returns (bytes memory) {
        return functionCallWithValue(target, data, 0, errorMessage);
    }

    /**
     * @dev Same as {xref-Address-functionCall-address-bytes-}[`functionCall`],
     * but also transferring `value` wei to `target`.
     *
     * Requirements:
     *
     * - the calling contract must have an ETH balance of at least `value`.
     * - the called Solidity function must be `payable`.
     *
     * _Available since v3.1._
     */
    function functionCallWithValue(
        address target,
        bytes memory data,
        uint256 value
    ) internal returns (bytes memory) {
        return functionCallWithValue(target, data, value, "Address: low-level call with value failed");
    }

    /**
     * @dev Same as {xref-Address-functionCallWithValue-address-bytes-uint256-}[`functionCallWithValue`], but
     * with `errorMessage` as a fallback revert reason when `target` reverts.
     *
     * _Available since v3.1._
     */
    function functionCallWithValue(
        address target,
        bytes memory data,
        uint256 value,
        string memory errorMessage
    ) internal returns (bytes memory) {
        require(address(this).balance >= value, "Address: insufficient balance for call");
        require(isContract(target), "Address: call to non-contract");

        (bool success, bytes memory returndata) = target.call{value: value}(data);
        return verifyCallResult(success, returndata, errorMessage);
    }

    /**
     * @dev Same as {xref-Address-functionCall-address-bytes-}[`functionCall`],
     * but performing a static call.
     *
     * _Available since v3.3._
     */
    function functionStaticCall(address target, bytes memory data) internal view returns (bytes memory) {
        return functionStaticCall(target, data, "Address: low-level static call failed");
    }

    /**
     * @dev Same as {xref-Address-functionCall-address-bytes-string-}[`functionCall`],
     * but performing a static call.
     *
     * _Available since v3.3._
     */
    function functionStaticCall(
        address target,
        bytes memory data,
        string memory errorMessage
    ) internal view returns (bytes memory) {
        require(isContract(target), "Address: static call to non-contract");

        (bool success, bytes memory returndata) = target.staticcall(data);
        return verifyCallResult(success, returndata, errorMessage);
    }

    /**
     * @dev Same as {xref-Address-functionCall-address-bytes-}[`functionCall`],
     * but performing a delegate call.
     *
     * _Available since v3.4._
     */
    function functionDelegateCall(address target, bytes memory data) internal returns (bytes memory) {
        return functionDelegateCall(target, data, "Address: low-level delegate call failed");
    }

    /**
     * @dev Same as {xref-Address-functionCall-address-bytes-string-}[`functionCall`],
     * but performing a delegate call.
     *
     * _Available since v3.4._
     */
    function functionDelegateCall(
        address target,
        bytes memory data,
        string memory errorMessage
    ) internal returns (bytes memory) {
        require(isContract(target), "Address: delegate call to non-contract");

        (bool success, bytes memory returndata) = target.delegatecall(data);
        return verifyCallResult(success, returndata, errorMessage);
    }

    /**
     * @dev Tool to verifies that a low level call was successful, and revert if it wasn't, either by bubbling the
     * revert reason using the provided one.
     *
     * _Available since v4.3._
     */
    function verifyCallResult(
        bool success,
        bytes memory returndata,
        string memory errorMessage
    ) internal pure returns (bytes memory) {
        if (success) {
            return returndata;
        } else {
            // Look for revert reason and bubble it up if present
            if (returndata.length > 0) {
                // The easiest way to bubble the revert reason is using memory via assembly
                /// @solidity memory-safe-assembly
                assembly {
                    let returndata_size := mload(returndata)
                    revert(add(32, returndata), returndata_size)
                }
            } else {
                revert(errorMessage);
            }
        }
    }
}


// File: lib/openzeppelin-contracts/contracts/utils/math/Math.sol
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


// File: src/libraries/Burn.sol
// SPDX-License-Identifier: MIT
pragma solidity 0.8.15;

/// @title Burn
/// @notice Utilities for burning stuff.
library Burn {
    /// @notice Burns a given amount of ETH.
    /// @param _amount Amount of ETH to burn.
    function eth(uint256 _amount) internal {
        new Burner{ value: _amount }();
    }

    /// @notice Burns a given amount of gas.
    /// @param _amount Amount of gas to burn.
    function gas(uint256 _amount) internal view {
        uint256 i = 0;
        uint256 initialGas = gasleft();
        while (initialGas - gasleft() < _amount) {
            ++i;
        }
    }
}

/// @title Burner
/// @notice Burner self-destructs on creation and sends all ETH to itself, removing all ETH given to
///         the contract from the circulating supply. Self-destructing is the only way to remove ETH
///         from the circulating supply.
contract Burner {
    constructor() payable {
        selfdestruct(payable(address(this)));
    }
}


// File: src/libraries/Arithmetic.sol
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

// Libraries
import { SignedMath } from "@openzeppelin/contracts/utils/math/SignedMath.sol";
import { FixedPointMathLib } from "@rari-capital/solmate/src/utils/FixedPointMathLib.sol";

/// @title Arithmetic
/// @notice Even more math than before.
library Arithmetic {
    /// @notice Clamps a value between a minimum and maximum.
    /// @param _value The value to clamp.
    /// @param _min   The minimum value.
    /// @param _max   The maximum value.
    /// @return The clamped value.
    function clamp(int256 _value, int256 _min, int256 _max) internal pure returns (int256) {
        return SignedMath.min(SignedMath.max(_value, _min), _max);
    }

    /// @notice (c)oefficient (d)enominator (exp)onentiation function.
    ///         Returns the result of: c * (1 - 1/d)^exp.
    /// @param _coefficient Coefficient of the function.
    /// @param _denominator Fractional denominator.
    /// @param _exponent    Power function exponent.
    /// @return Result of c * (1 - 1/d)^exp.
    function cdexp(int256 _coefficient, int256 _denominator, int256 _exponent) internal pure returns (int256) {
        return (_coefficient * (FixedPointMathLib.powWad(1e18 - (1e18 / _denominator), _exponent * 1e18))) / 1e18;
    }

    /// @notice Saturating addition.
    /// @param _x The first value.
    /// @param _y The second value.
    /// @return z_ The sum of the two values, or the maximum value if the sum overflows.
    /// @dev Returns `min(2 ** 256 - 1, x + y)`.
    /// @dev Taken from Solady
    /// https://github.com/Vectorized/solady/blob/63416d60c78aba70a12ca1b3c11125d1061caa12/src/utils/FixedPointMathLib.sol#L673
    function saturatingAdd(uint256 _x, uint256 _y) internal pure returns (uint256 z_) {
        assembly ("memory-safe") {
            z_ := or(sub(0, lt(add(_x, _y), _x)), add(_x, _y))
        }
    }

    /// @notice Saturating multiplication.
    /// @param _x The first value.
    /// @param _y The second value.
    /// @return z_ The product of the two values, or the maximum value if the product overflows.
    /// @dev Returns `min(2 ** 256 - 1, x * y).
    /// @dev Taken from Solady
    /// https://github.com/Vectorized/solady/blob/63416d60c78aba70a12ca1b3c11125d1061caa12/src/utils/FixedPointMathLib.sol#L681
    function saturatingMul(uint256 _x, uint256 _y) internal pure returns (uint256 z_) {
        assembly ("memory-safe") {
            z_ := or(sub(or(iszero(_x), eq(div(mul(_x, _y), _x), _y)), 1), mul(_x, _y))
        }
    }
}


// File: src/libraries/Encoding.sol
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

// Libraries
import { Types } from "src/libraries/Types.sol";
import { Hashing } from "src/libraries/Hashing.sol";
import { RLPWriter } from "src/libraries/rlp/RLPWriter.sol";

/// @title Encoding
/// @notice Encoding handles Optimism's various different encoding schemes.
library Encoding {
    /// @notice Thrown when a provided Super Root proof has an invalid version.
    error Encoding_InvalidSuperRootVersion();

    /// @notice Thrown when a provided Super Root proof has no Output Roots.
    error Encoding_EmptySuperRoot();

    /// @notice RLP encodes the L2 transaction that would be generated when a given deposit is sent
    ///         to the L2 system. Useful for searching for a deposit in the L2 system. The
    ///         transaction is prefixed with 0x7e to identify its EIP-2718 type.
    /// @param _tx User deposit transaction to encode.
    /// @return RLP encoded L2 deposit transaction.
    function encodeDepositTransaction(Types.UserDepositTransaction memory _tx) internal pure returns (bytes memory) {
        bytes32 source = Hashing.hashDepositSource(_tx.l1BlockHash, _tx.logIndex);
        bytes[] memory raw = new bytes[](8);
        raw[0] = RLPWriter.writeBytes(abi.encodePacked(source));
        raw[1] = RLPWriter.writeAddress(_tx.from);
        raw[2] = _tx.isCreation ? RLPWriter.writeBytes("") : RLPWriter.writeAddress(_tx.to);
        raw[3] = RLPWriter.writeUint(_tx.mint);
        raw[4] = RLPWriter.writeUint(_tx.value);
        raw[5] = RLPWriter.writeUint(uint256(_tx.gasLimit));
        raw[6] = RLPWriter.writeBool(false);
        raw[7] = RLPWriter.writeBytes(_tx.data);
        return abi.encodePacked(uint8(0x7e), RLPWriter.writeList(raw));
    }

    /// @notice Encodes the cross domain message based on the version that is encoded into the
    ///         message nonce.
    /// @param _nonce    Message nonce with version encoded into the first two bytes.
    /// @param _sender   Address of the sender of the message.
    /// @param _target   Address of the target of the message.
    /// @param _value    ETH value to send to the target.
    /// @param _gasLimit Gas limit to use for the message.
    /// @param _data     Data to send with the message.
    /// @return Encoded cross domain message.
    function encodeCrossDomainMessage(
        uint256 _nonce,
        address _sender,
        address _target,
        uint256 _value,
        uint256 _gasLimit,
        bytes memory _data
    )
        internal
        pure
        returns (bytes memory)
    {
        (, uint16 version) = decodeVersionedNonce(_nonce);
        if (version == 0) {
            return encodeCrossDomainMessageV0(_target, _sender, _data, _nonce);
        } else if (version == 1) {
            return encodeCrossDomainMessageV1(_nonce, _sender, _target, _value, _gasLimit, _data);
        } else {
            revert("Encoding: unknown cross domain message version");
        }
    }

    /// @notice Encodes a cross domain message based on the V0 (legacy) encoding.
    /// @param _target Address of the target of the message.
    /// @param _sender Address of the sender of the message.
    /// @param _data   Data to send with the message.
    /// @param _nonce  Message nonce.
    /// @return Encoded cross domain message.
    function encodeCrossDomainMessageV0(
        address _target,
        address _sender,
        bytes memory _data,
        uint256 _nonce
    )
        internal
        pure
        returns (bytes memory)
    {
        // nosemgrep: sol-style-use-abi-encodecall
        return abi.encodeWithSignature("relayMessage(address,address,bytes,uint256)", _target, _sender, _data, _nonce);
    }

    /// @notice Encodes a cross domain message based on the V1 (current) encoding.
    /// @param _nonce    Message nonce.
    /// @param _sender   Address of the sender of the message.
    /// @param _target   Address of the target of the message.
    /// @param _value    ETH value to send to the target.
    /// @param _gasLimit Gas limit to use for the message.
    /// @param _data     Data to send with the message.
    /// @return Encoded cross domain message.
    function encodeCrossDomainMessageV1(
        uint256 _nonce,
        address _sender,
        address _target,
        uint256 _value,
        uint256 _gasLimit,
        bytes memory _data
    )
        internal
        pure
        returns (bytes memory)
    {
        // nosemgrep: sol-style-use-abi-encodecall
        return abi.encodeWithSignature(
            "relayMessage(uint256,address,address,uint256,uint256,bytes)",
            _nonce,
            _sender,
            _target,
            _value,
            _gasLimit,
            _data
        );
    }

    /// @notice Adds a version number into the first two bytes of a message nonce.
    /// @param _nonce   Message nonce to encode into.
    /// @param _version Version number to encode into the message nonce.
    /// @return Message nonce with version encoded into the first two bytes.
    function encodeVersionedNonce(uint240 _nonce, uint16 _version) internal pure returns (uint256) {
        uint256 nonce;
        assembly {
            nonce := or(shl(240, _version), _nonce)
        }
        return nonce;
    }

    /// @notice Pulls the version out of a version-encoded nonce.
    /// @param _nonce Message nonce with version encoded into the first two bytes.
    /// @return Nonce without encoded version.
    /// @return Version of the message.
    function decodeVersionedNonce(uint256 _nonce) internal pure returns (uint240, uint16) {
        uint240 nonce;
        uint16 version;
        assembly {
            nonce := and(_nonce, 0x0000ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff)
            version := shr(240, _nonce)
        }
        return (nonce, version);
    }

    /// @notice Returns an appropriately encoded call to L1Block.setL1BlockValuesEcotone
    /// @param _baseFeeScalar       L1 base fee Scalar
    /// @param _blobBaseFeeScalar   L1 blob base fee Scalar
    /// @param _sequenceNumber      Number of L2 blocks since epoch start.
    /// @param _timestamp           L1 timestamp.
    /// @param _number              L1 blocknumber.
    /// @param _baseFee             L1 base fee.
    /// @param _blobBaseFee         L1 blob base fee.
    /// @param _hash                L1 blockhash.
    /// @param _batcherHash         Versioned hash to authenticate batcher by.
    function encodeSetL1BlockValuesEcotone(
        uint32 _baseFeeScalar,
        uint32 _blobBaseFeeScalar,
        uint64 _sequenceNumber,
        uint64 _timestamp,
        uint64 _number,
        uint256 _baseFee,
        uint256 _blobBaseFee,
        bytes32 _hash,
        bytes32 _batcherHash
    )
        internal
        pure
        returns (bytes memory)
    {
        bytes4 functionSignature = bytes4(keccak256("setL1BlockValuesEcotone()"));
        return abi.encodePacked(
            functionSignature,
            _baseFeeScalar,
            _blobBaseFeeScalar,
            _sequenceNumber,
            _timestamp,
            _number,
            _baseFee,
            _blobBaseFee,
            _hash,
            _batcherHash
        );
    }

    /// @notice Returns an appropriately encoded call to L1Block.setL1BlockValuesIsthmus
    /// @param _baseFeeScalar       L1 base fee Scalar
    /// @param _blobBaseFeeScalar   L1 blob base fee Scalar
    /// @param _sequenceNumber      Number of L2 blocks since epoch start.
    /// @param _timestamp           L1 timestamp.
    /// @param _number              L1 blocknumber.
    /// @param _baseFee             L1 base fee.
    /// @param _blobBaseFee         L1 blob base fee.
    /// @param _hash                L1 blockhash.
    /// @param _batcherHash         Versioned hash to authenticate batcher by.
    /// @param _operatorFeeScalar   Operator fee scalar.
    /// @param _operatorFeeConstant Operator fee constant.
    function encodeSetL1BlockValuesIsthmus(
        uint32 _baseFeeScalar,
        uint32 _blobBaseFeeScalar,
        uint64 _sequenceNumber,
        uint64 _timestamp,
        uint64 _number,
        uint256 _baseFee,
        uint256 _blobBaseFee,
        bytes32 _hash,
        bytes32 _batcherHash,
        uint32 _operatorFeeScalar,
        uint64 _operatorFeeConstant
    )
        internal
        pure
        returns (bytes memory)
    {
        bytes4 functionSignature = bytes4(keccak256("setL1BlockValuesIsthmus()"));
        return abi.encodePacked(
            functionSignature,
            _baseFeeScalar,
            _blobBaseFeeScalar,
            _sequenceNumber,
            _timestamp,
            _number,
            _baseFee,
            _blobBaseFee,
            _hash,
            _batcherHash,
            _operatorFeeScalar,
            _operatorFeeConstant
        );
    }

    /// @notice Returns an appropriately encoded call to L1Block.setL1BlockValuesJovian
    /// @param _baseFeeScalar        L1 base fee Scalar
    /// @param _blobBaseFeeScalar    L1 blob base fee Scalar
    /// @param _sequenceNumber       Number of L2 blocks since epoch start.
    /// @param _timestamp            L1 timestamp.
    /// @param _number               L1 blocknumber.
    /// @param _baseFee              L1 base fee.
    /// @param _blobBaseFee          L1 blob base fee.
    /// @param _hash                 L1 blockhash.
    /// @param _batcherHash          Versioned hash to authenticate batcher by.
    /// @param _operatorFeeScalar    Operator fee scalar.
    /// @param _operatorFeeConstant  Operator fee constant.
    /// @param _daFootprintGasScalar DA Footprint scalar.
    function encodeSetL1BlockValuesJovian(
        uint32 _baseFeeScalar,
        uint32 _blobBaseFeeScalar,
        uint64 _sequenceNumber,
        uint64 _timestamp,
        uint64 _number,
        uint256 _baseFee,
        uint256 _blobBaseFee,
        bytes32 _hash,
        bytes32 _batcherHash,
        uint32 _operatorFeeScalar,
        uint64 _operatorFeeConstant,
        uint16 _daFootprintGasScalar
    )
        internal
        pure
        returns (bytes memory)
    {
        bytes4 functionSignature = bytes4(keccak256("setL1BlockValuesJovian()"));

        // Split up the encoding into multiple parts to avoid stack too deep.
        return abi.encodePacked(
            abi.encodePacked(
                functionSignature, _baseFeeScalar, _blobBaseFeeScalar, _sequenceNumber, _timestamp, _number, _baseFee
            ),
            abi.encodePacked(
                _blobBaseFee, _hash, _batcherHash, _operatorFeeScalar, _operatorFeeConstant, _daFootprintGasScalar
            )
        );
    }

    /// @notice Encodes a super root proof into the preimage of a Super Root.
    /// @param _superRootProof Super root proof to encode.
    /// @return Encoded super root proof.
    function encodeSuperRootProof(Types.SuperRootProof memory _superRootProof) internal pure returns (bytes memory) {
        // Version must match the expected version.
        if (_superRootProof.version != 0x01) {
            revert Encoding_InvalidSuperRootVersion();
        }

        // Output roots must not be empty.
        if (_superRootProof.outputRoots.length == 0) {
            revert Encoding_EmptySuperRoot();
        }

        // Start with version byte and timestamp.
        bytes memory encoded = bytes.concat(bytes1(_superRootProof.version), bytes8(_superRootProof.timestamp));

        // Add each output root (chainId + root)
        for (uint256 i = 0; i < _superRootProof.outputRoots.length; i++) {
            Types.OutputRootWithChainId memory outputRoot = _superRootProof.outputRoots[i];
            encoded = bytes.concat(encoded, bytes32(outputRoot.chainId), outputRoot.root);
        }

        return encoded;
    }
}


// File: src/libraries/trie/MerkleTrie.sol
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

// Libraries
import { Bytes } from "src/libraries/Bytes.sol";
import { RLPReader } from "src/libraries/rlp/RLPReader.sol";

/// @title MerkleTrie
/// @notice MerkleTrie is a small library for verifying standard Ethereum Merkle-Patricia trie
///         inclusion proofs. By default, this library assumes a hexary trie. One can change the
///         trie radix constant to support other trie radixes.
library MerkleTrie {
    /// @notice Struct representing a node in the trie.
    /// @custom:field encoded The RLP-encoded node.
    /// @custom:field decoded The RLP-decoded node.
    struct TrieNode {
        bytes encoded;
        RLPReader.RLPItem[] decoded;
    }

    /// @notice Determines the number of elements per branch node.
    uint256 internal constant TREE_RADIX = 16;

    /// @notice Branch nodes have TREE_RADIX elements and one value element.
    uint256 internal constant BRANCH_NODE_LENGTH = TREE_RADIX + 1;

    /// @notice Leaf nodes and extension nodes have two elements, a `path` and a `value`.
    uint256 internal constant LEAF_OR_EXTENSION_NODE_LENGTH = 2;

    /// @notice Prefix for even-nibbled extension node paths.
    uint8 internal constant PREFIX_EXTENSION_EVEN = 0;

    /// @notice Prefix for odd-nibbled extension node paths.
    uint8 internal constant PREFIX_EXTENSION_ODD = 1;

    /// @notice Prefix for even-nibbled leaf node paths.
    uint8 internal constant PREFIX_LEAF_EVEN = 2;

    /// @notice Prefix for odd-nibbled leaf node paths.
    uint8 internal constant PREFIX_LEAF_ODD = 3;

    /// @notice Verifies a proof that a given key/value pair is present in the trie.
    /// @param _key   Key of the node to search for, as a hex string.
    /// @param _value Value of the node to search for, as a hex string.
    /// @param _proof Merkle trie inclusion proof for the desired node. Unlike traditional Merkle
    ///               trees, this proof is executed top-down and consists of a list of RLP-encoded
    ///               nodes that make a path down to the target node.
    /// @param _root  Known root of the Merkle trie. Used to verify that the included proof is
    ///               correctly constructed.
    /// @return valid_ Whether or not the proof is valid.
    function verifyInclusionProof(
        bytes memory _key,
        bytes memory _value,
        bytes[] memory _proof,
        bytes32 _root
    )
        internal
        pure
        returns (bool valid_)
    {
        valid_ = Bytes.equal(_value, get(_key, _proof, _root));
    }

    /// @notice Retrieves the value associated with a given key.
    /// @param _key   Key to search for, as hex bytes.
    /// @param _proof Merkle trie inclusion proof for the key.
    /// @param _root  Known root of the Merkle trie.
    /// @return value_ Value of the key if it exists.
    function get(bytes memory _key, bytes[] memory _proof, bytes32 _root) internal pure returns (bytes memory value_) {
        require(_key.length > 0, "MerkleTrie: empty key");

        TrieNode[] memory proof = _parseProof(_proof);
        bytes memory key = Bytes.toNibbles(_key);
        bytes memory currentNodeID = abi.encodePacked(_root);
        uint256 currentKeyIndex = 0;

        // Proof is top-down, so we start at the first element (root).
        for (uint256 i = 0; i < proof.length; i++) {
            TrieNode memory currentNode = proof[i];

            // Key index should never exceed total key length or we'll be out of bounds.
            require(currentKeyIndex <= key.length, "MerkleTrie: key index exceeds total key length");

            if (currentKeyIndex == 0) {
                // First proof element is always the root node.
                require(
                    Bytes.equal(abi.encodePacked(keccak256(currentNode.encoded)), currentNodeID),
                    "MerkleTrie: invalid root hash"
                );
            } else if (currentNode.encoded.length >= 32) {
                // Nodes 32 bytes or larger are hashed inside branch nodes.
                require(
                    Bytes.equal(abi.encodePacked(keccak256(currentNode.encoded)), currentNodeID),
                    "MerkleTrie: invalid large internal hash"
                );
            } else {
                // Nodes smaller than 32 bytes aren't hashed.
                require(Bytes.equal(currentNode.encoded, currentNodeID), "MerkleTrie: invalid internal node hash");
            }

            if (currentNode.decoded.length == BRANCH_NODE_LENGTH) {
                if (currentKeyIndex == key.length) {
                    // Value is the last element of the decoded list (for branch nodes). There's
                    // some ambiguity in the Merkle trie specification because bytes(0) is a
                    // valid value to place into the trie, but for branch nodes bytes(0) can exist
                    // even when the value wasn't explicitly placed there. Geth treats a value of
                    // bytes(0) as "key does not exist" and so we do the same.
                    value_ = RLPReader.readBytes(currentNode.decoded[TREE_RADIX]);
                    require(value_.length > 0, "MerkleTrie: value length must be greater than zero (branch)");

                    // Extra proof elements are not allowed.
                    require(i == proof.length - 1, "MerkleTrie: value node must be last node in proof (branch)");

                    return value_;
                } else {
                    // We're not at the end of the key yet.
                    // Figure out what the next node ID should be and continue.
                    uint8 branchKey = uint8(key[currentKeyIndex]);
                    RLPReader.RLPItem memory nextNode = currentNode.decoded[branchKey];
                    currentNodeID = _getNodeID(nextNode);
                    currentKeyIndex += 1;
                }
            } else if (currentNode.decoded.length == LEAF_OR_EXTENSION_NODE_LENGTH) {
                bytes memory path = _getNodePath(currentNode);
                uint8 prefix = uint8(path[0]);
                uint8 offset = 2 - (prefix % 2);
                bytes memory pathRemainder = Bytes.slice(path, offset);
                bytes memory keyRemainder = Bytes.slice(key, currentKeyIndex);
                uint256 sharedNibbleLength = _getSharedNibbleLength(pathRemainder, keyRemainder);

                // Whether this is a leaf node or an extension node, the path remainder MUST be a
                // prefix of the key remainder (or be equal to the key remainder) or the proof is
                // considered invalid.
                require(
                    pathRemainder.length == sharedNibbleLength,
                    "MerkleTrie: path remainder must share all nibbles with key"
                );

                if (prefix == PREFIX_LEAF_EVEN || prefix == PREFIX_LEAF_ODD) {
                    // Prefix of 2 or 3 means this is a leaf node. For the leaf node to be valid,
                    // the key remainder must be exactly equal to the path remainder. We already
                    // did the necessary byte comparison, so it's more efficient here to check that
                    // the key remainder length equals the shared nibble length, which implies
                    // equality with the path remainder (since we already did the same check with
                    // the path remainder and the shared nibble length).
                    require(
                        keyRemainder.length == sharedNibbleLength,
                        "MerkleTrie: key remainder must be identical to path remainder"
                    );

                    // Our Merkle Trie is designed specifically for the purposes of the Ethereum
                    // state trie. Empty values are not allowed in the state trie, so we can safely
                    // say that if the value is empty, the key should not exist and the proof is
                    // invalid.
                    value_ = RLPReader.readBytes(currentNode.decoded[1]);
                    require(value_.length > 0, "MerkleTrie: value length must be greater than zero (leaf)");

                    // Extra proof elements are not allowed.
                    require(i == proof.length - 1, "MerkleTrie: value node must be last node in proof (leaf)");

                    return value_;
                } else if (prefix == PREFIX_EXTENSION_EVEN || prefix == PREFIX_EXTENSION_ODD) {
                    // Prefix of 0 or 1 means this is an extension node. We move onto the next node
                    // in the proof and increment the key index by the length of the path remainder
                    // which is equal to the shared nibble length.
                    currentNodeID = _getNodeID(currentNode.decoded[1]);
                    currentKeyIndex += sharedNibbleLength;
                } else {
                    revert("MerkleTrie: received a node with an unknown prefix");
                }
            } else {
                revert("MerkleTrie: received an unparseable node");
            }
        }

        revert("MerkleTrie: ran out of proof elements");
    }

    /// @notice Parses an array of proof elements into a new array that contains both the original
    ///         encoded element and the RLP-decoded element.
    /// @param _proof Array of proof elements to parse.
    /// @return proof_ Proof parsed into easily accessible structs.
    function _parseProof(bytes[] memory _proof) private pure returns (TrieNode[] memory proof_) {
        uint256 length = _proof.length;
        proof_ = new TrieNode[](length);
        for (uint256 i = 0; i < length;) {
            proof_[i] = TrieNode({ encoded: _proof[i], decoded: RLPReader.readList(_proof[i]) });
            unchecked {
                ++i;
            }
        }
    }

    /// @notice Picks out the ID for a node. Node ID is referred to as the "hash" within the
    ///         specification, but nodes < 32 bytes are not actually hashed.
    /// @param _node Node to pull an ID for.
    /// @return id_ ID for the node, depending on the size of its contents.
    function _getNodeID(RLPReader.RLPItem memory _node) private pure returns (bytes memory id_) {
        id_ = _node.length < 32 ? RLPReader.readRawBytes(_node) : RLPReader.readBytes(_node);
    }

    /// @notice Gets the path for a leaf or extension node.
    /// @param _node Node to get a path for.
    /// @return nibbles_ Node path, converted to an array of nibbles.
    function _getNodePath(TrieNode memory _node) private pure returns (bytes memory nibbles_) {
        nibbles_ = Bytes.toNibbles(RLPReader.readBytes(_node.decoded[0]));
    }

    /// @notice Utility; determines the number of nibbles shared between two nibble arrays.
    /// @param _a First nibble array.
    /// @param _b Second nibble array.
    /// @return shared_ Number of shared nibbles.
    function _getSharedNibbleLength(bytes memory _a, bytes memory _b) private pure returns (uint256 shared_) {
        uint256 max = (_a.length < _b.length) ? _a.length : _b.length;
        for (; shared_ < max && _a[shared_] == _b[shared_];) {
            unchecked {
                ++shared_;
            }
        }
    }
}


// File: src/dispute/lib/LibUDT.sol
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.15;

// Libraries
import { Position } from "src/dispute/lib/LibPosition.sol";

using LibClaim for Claim global;
using LibHash for Hash global;
using LibDuration for Duration global;
using LibClock for Clock global;
using LibGameId for GameId global;
using LibTimestamp for Timestamp global;
using LibVMStatus for VMStatus global;
using LibGameType for GameType global;

/// @notice A `Clock` represents a packed `Duration` and `Timestamp`
/// @dev The packed layout of this type is as follows:
/// ┌────────────┬────────────────┐
/// │    Bits    │     Value      │
/// ├────────────┼────────────────┤
/// │ [0, 64)    │ Duration       │
/// │ [64, 128)  │ Timestamp      │
/// └────────────┴────────────────┘
type Clock is uint128;

/// @title LibClock
/// @notice This library contains helper functions for working with the `Clock` type.
library LibClock {
    /// @notice Packs a `Duration` and `Timestamp` into a `Clock` type.
    /// @param _duration The `Duration` to pack into the `Clock` type.
    /// @param _timestamp The `Timestamp` to pack into the `Clock` type.
    /// @return clock_ The `Clock` containing the `_duration` and `_timestamp`.
    function wrap(Duration _duration, Timestamp _timestamp) internal pure returns (Clock clock_) {
        assembly {
            clock_ := or(shl(0x40, _duration), _timestamp)
        }
    }

    /// @notice Pull the `Duration` out of a `Clock` type.
    /// @param _clock The `Clock` type to pull the `Duration` out of.
    /// @return duration_ The `Duration` pulled out of `_clock`.
    function duration(Clock _clock) internal pure returns (Duration duration_) {
        // Shift the high-order 64 bits into the low-order 64 bits, leaving only the `duration`.
        assembly {
            duration_ := shr(0x40, _clock)
        }
    }

    /// @notice Pull the `Timestamp` out of a `Clock` type.
    /// @param _clock The `Clock` type to pull the `Timestamp` out of.
    /// @return timestamp_ The `Timestamp` pulled out of `_clock`.
    function timestamp(Clock _clock) internal pure returns (Timestamp timestamp_) {
        // Clean the high-order 192 bits by shifting the clock left and then right again, leaving
        // only the `timestamp`.
        assembly {
            timestamp_ := shr(0xC0, shl(0xC0, _clock))
        }
    }

    /// @notice Get the value of a `Clock` type in the form of the underlying uint128.
    /// @param _clock The `Clock` type to get the value of.
    /// @return clock_ The value of the `Clock` type as a uint128 type.
    function raw(Clock _clock) internal pure returns (uint128 clock_) {
        assembly {
            clock_ := _clock
        }
    }
}

/// @notice A `GameId` represents a packed 4 byte game ID, a 8 byte timestamp, and a 20 byte address.
/// @dev The packed layout of this type is as follows:
/// ┌───────────┬───────────┐
/// │   Bits    │   Value   │
/// ├───────────┼───────────┤
/// │ [0, 32)   │ Game Type │
/// │ [32, 96)  │ Timestamp │
/// │ [96, 256) │ Address   │
/// └───────────┴───────────┘
type GameId is bytes32;

/// @title LibGameId
/// @notice Utility functions for packing and unpacking GameIds.
library LibGameId {
    /// @notice Packs values into a 32 byte GameId type.
    /// @param _gameType The game type.
    /// @param _timestamp The timestamp of the game's creation.
    /// @param _gameProxy The game proxy address.
    /// @return gameId_ The packed GameId.
    function pack(
        GameType _gameType,
        Timestamp _timestamp,
        address _gameProxy
    )
        internal
        pure
        returns (GameId gameId_)
    {
        assembly {
            gameId_ := or(or(shl(224, _gameType), shl(160, _timestamp)), _gameProxy)
        }
    }

    /// @notice Unpacks values from a 32 byte GameId type.
    /// @param _gameId The packed GameId.
    /// @return gameType_ The game type.
    /// @return timestamp_ The timestamp of the game's creation.
    /// @return gameProxy_ The game proxy address.
    function unpack(GameId _gameId)
        internal
        pure
        returns (GameType gameType_, Timestamp timestamp_, address gameProxy_)
    {
        assembly {
            gameType_ := shr(224, _gameId)
            timestamp_ := and(shr(160, _gameId), 0xFFFFFFFFFFFFFFFF)
            gameProxy_ := and(_gameId, 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)
        }
    }
}

/// @notice A claim represents an MPT root representing the state of the fault proof program.
type Claim is bytes32;

/// @title LibClaim
/// @notice This library contains helper functions for working with the `Claim` type.
library LibClaim {
    /// @notice Get the value of a `Claim` type in the form of the underlying bytes32.
    /// @param _claim The `Claim` type to get the value of.
    /// @return claim_ The value of the `Claim` type as a bytes32 type.
    function raw(Claim _claim) internal pure returns (bytes32 claim_) {
        assembly {
            claim_ := _claim
        }
    }

    /// @notice Hashes a claim and a position together.
    /// @param _claim A Claim type.
    /// @param _position The position of `claim`.
    /// @param _challengeIndex The index of the claim being moved against.
    /// @return claimHash_ A hash of abi.encodePacked(claim, position|challengeIndex);
    function hashClaimPos(
        Claim _claim,
        Position _position,
        uint256 _challengeIndex
    )
        internal
        pure
        returns (Hash claimHash_)
    {
        assembly {
            mstore(0x00, _claim)
            mstore(0x20, or(shl(128, _position), and(0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF, _challengeIndex)))
            claimHash_ := keccak256(0x00, 0x40)
        }
    }
}

/// @notice A dedicated duration type.
/// @dev Unit: seconds
type Duration is uint64;

/// @title LibDuration
/// @notice This library contains helper functions for working with the `Duration` type.
library LibDuration {
    /// @notice Get the value of a `Duration` type in the form of the underlying uint64.
    /// @param _duration The `Duration` type to get the value of.
    /// @return duration_ The value of the `Duration` type as a uint64 type.
    function raw(Duration _duration) internal pure returns (uint64 duration_) {
        assembly {
            duration_ := _duration
        }
    }
}

/// @notice A custom type for a generic hash.
type Hash is bytes32;

/// @title LibHash
/// @notice This library contains helper functions for working with the `Hash` type.
library LibHash {
    /// @notice Get the value of a `Hash` type in the form of the underlying bytes32.
    /// @param _hash The `Hash` type to get the value of.
    /// @return hash_ The value of the `Hash` type as a bytes32 type.
    function raw(Hash _hash) internal pure returns (bytes32 hash_) {
        assembly {
            hash_ := _hash
        }
    }
}

/// @notice A dedicated timestamp type.
type Timestamp is uint64;

/// @title LibTimestamp
/// @notice This library contains helper functions for working with the `Timestamp` type.
library LibTimestamp {
    /// @notice Get the value of a `Timestamp` type in the form of the underlying uint64.
    /// @param _timestamp The `Timestamp` type to get the value of.
    /// @return timestamp_ The value of the `Timestamp` type as a uint64 type.
    function raw(Timestamp _timestamp) internal pure returns (uint64 timestamp_) {
        assembly {
            timestamp_ := _timestamp
        }
    }
}

/// @notice A `VMStatus` represents the status of a VM execution.
type VMStatus is uint8;

/// @title LibVMStatus
/// @notice This library contains helper functions for working with the `VMStatus` type.
library LibVMStatus {
    /// @notice Get the value of a `VMStatus` type in the form of the underlying uint8.
    /// @param _vmstatus The `VMStatus` type to get the value of.
    /// @return vmstatus_ The value of the `VMStatus` type as a uint8 type.
    function raw(VMStatus _vmstatus) internal pure returns (uint8 vmstatus_) {
        assembly {
            vmstatus_ := _vmstatus
        }
    }
}

/// @notice A `GameType` represents the type of game being played.
type GameType is uint32;

/// @title LibGameType
/// @notice This library contains helper functions for working with the `GameType` type.
library LibGameType {
    /// @notice Get the value of a `GameType` type in the form of the underlying uint32.
    /// @param _gametype The `GameType` type to get the value of.
    /// @return gametype_ The value of the `GameType` type as a uint32 type.
    function raw(GameType _gametype) internal pure returns (uint32 gametype_) {
        assembly {
            gametype_ := _gametype
        }
    }
}


// File: interfaces/L1/IProxyAdminOwnedBase.sol
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import { IProxyAdmin } from "interfaces/universal/IProxyAdmin.sol";

interface IProxyAdminOwnedBase {
    error ProxyAdminOwnedBase_NotSharedProxyAdminOwner();
    error ProxyAdminOwnedBase_NotProxyAdminOwner();
    error ProxyAdminOwnedBase_NotProxyAdmin();
    error ProxyAdminOwnedBase_NotProxyAdminOrProxyAdminOwner();
    error ProxyAdminOwnedBase_ProxyAdminNotFound();
    error ProxyAdminOwnedBase_NotResolvedDelegateProxy();

    function proxyAdmin() external view returns (IProxyAdmin);
    function proxyAdminOwner() external view returns (address);
}


// File: interfaces/universal/IReinitializableBase.sol
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

interface IReinitializableBase {
    error ReinitializableBase_ZeroInitVersion();

    function initVersion() external view returns (uint8);

    // ReinitializerBase is abstract, so it has no constructor in its interface.
    function __constructor__() external;
}


// File: interfaces/dispute/IInitializable.sol
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

interface IInitializable {
    function initialize() external payable;
}


// File: interfaces/dispute/IFaultDisputeGame.sol
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import { IDisputeGame } from "interfaces/dispute/IDisputeGame.sol";
import { IDelayedWETH } from "interfaces/dispute/IDelayedWETH.sol";
import { IAnchorStateRegistry } from "interfaces/dispute/IAnchorStateRegistry.sol";
import { IBigStepper } from "interfaces/dispute/IBigStepper.sol";
import { Types } from "src/libraries/Types.sol";
import { GameType, Claim, Position, Clock, Hash, Duration, BondDistributionMode } from "src/dispute/lib/Types.sol";

interface IFaultDisputeGame is IDisputeGame {
    struct ClaimData {
        uint32 parentIndex;
        address counteredBy;
        address claimant;
        uint128 bond;
        Claim claim;
        Position position;
        Clock clock;
    }

    struct ResolutionCheckpoint {
        bool initialCheckpointComplete;
        uint32 subgameIndex;
        Position leftmostPosition;
        address counteredBy;
    }

    struct GameConstructorParams {
        GameType gameType;
        Claim absolutePrestate;
        uint256 maxGameDepth;
        uint256 splitDepth;
        Duration clockExtension;
        Duration maxClockDuration;
        IBigStepper vm;
        IDelayedWETH weth;
        IAnchorStateRegistry anchorStateRegistry;
        uint256 l2ChainId;
    }

    error AlreadyInitialized();
    error AnchorRootNotFound();
    error BadExtraData();
    error BlockNumberMatches();
    error BondTransferFailed();
    error CannotDefendRootClaim();
    error ClaimAboveSplit();
    error ClaimAlreadyExists();
    error ClaimAlreadyResolved();
    error ClockNotExpired();
    error ClockTimeExceeded();
    error ContentLengthMismatch();
    error DuplicateStep();
    error EmptyItem();
    error GameDepthExceeded();
    error GameNotInProgress();
    error IncorrectBondAmount();
    error InvalidChallengePeriod();
    error InvalidClockExtension();
    error InvalidDataRemainder();
    error InvalidDisputedClaimIndex();
    error InvalidHeader();
    error InvalidHeaderRLP();
    error InvalidLocalIdent();
    error InvalidOutputRootProof();
    error InvalidParent();
    error InvalidPrestate();
    error InvalidSplitDepth();
    error L2BlockNumberChallenged();
    error MaxDepthTooLarge();
    error NoCreditToClaim();
    error OutOfOrderResolution();
    error UnexpectedList();
    error UnexpectedRootClaim(Claim rootClaim);
    error UnexpectedString();
    error ValidStep();
    error InvalidBondDistributionMode();
    error GameNotFinalized();
    error GameNotResolved();
    error ReservedGameType();
    error GamePaused();
    event Move(uint256 indexed parentIndex, Claim indexed claim, address indexed claimant);
    event GameClosed(BondDistributionMode bondDistributionMode);

    function absolutePrestate() external view returns (Claim absolutePrestate_);
    function addLocalData(uint256 _ident, uint256 _execLeafIdx, uint256 _partOffset) external;
    function anchorStateRegistry() external view returns (IAnchorStateRegistry registry_);
    function attack(Claim _disputed, uint256 _parentIndex, Claim _claim) external payable;
    function bondDistributionMode() external view returns (BondDistributionMode);
    function challengeRootL2Block(Types.OutputRootProof memory _outputRootProof, bytes memory _headerRLP) external;
    function claimCredit(address _recipient) external;
    function claimData(uint256)
        external
        view // nosemgrep
        returns (
            uint32 parentIndex,
            address counteredBy,
            address claimant,
            uint128 bond,
            Claim claim,
            Position position,
            Clock clock
        );
    function claimDataLen() external view returns (uint256 len_);
    function claims(Hash) external view returns (bool);
    function clockExtension() external view returns (Duration clockExtension_);
    function closeGame() external;
    function credit(address _recipient) external view returns (uint256 credit_);
    function defend(Claim _disputed, uint256 _parentIndex, Claim _claim) external payable;
    function getChallengerDuration(uint256 _claimIndex) external view returns (Duration duration_);
    function getNumToResolve(uint256 _claimIndex) external view returns (uint256 numRemainingChildren_);
    function getRequiredBond(Position _position) external view returns (uint256 requiredBond_);
    function hasUnlockedCredit(address) external view returns (bool);
    function l2BlockNumber() external pure returns (uint256 l2BlockNumber_);
    function l2BlockNumberChallenged() external view returns (bool);
    function l2BlockNumberChallenger() external view returns (address);
    function l2ChainId() external view returns (uint256 l2ChainId_);
    function maxClockDuration() external view returns (Duration maxClockDuration_);
    function maxGameDepth() external view returns (uint256 maxGameDepth_);
    function move(Claim _disputed, uint256 _challengeIndex, Claim _claim, bool _isAttack) external payable;
    function normalModeCredit(address) external view returns (uint256);
    function refundModeCredit(address) external view returns (uint256);
    function resolutionCheckpoints(uint256)
        external
        view
        returns (bool initialCheckpointComplete, uint32 subgameIndex, Position leftmostPosition, address counteredBy); // nosemgrep
    function resolveClaim(uint256 _claimIndex, uint256 _numToResolve) external;
    function resolvedSubgames(uint256) external view returns (bool);
    function splitDepth() external view returns (uint256 splitDepth_);
    function startingBlockNumber() external view returns (uint256 startingBlockNumber_);
    function startingOutputRoot() external view returns (Hash root, uint256 l2SequenceNumber); // nosemgrep
    function startingRootHash() external view returns (Hash startingRootHash_);
    function step(uint256 _claimIndex, bool _isAttack, bytes memory _stateData, bytes memory _proof) external;
    function subgames(uint256, uint256) external view returns (uint256);
    function version() external pure returns (string memory);
    function vm() external view returns (IBigStepper vm_);
    function wasRespectedGameTypeWhenCreated() external view returns (bool);
    function weth() external view returns (IDelayedWETH weth_);

    function __constructor__(GameConstructorParams memory _params) external;
}


// File: interfaces/L1/IOptimismPortal2.sol
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import { Types } from "src/libraries/Types.sol";
import { GameType } from "src/dispute/lib/LibUDT.sol";
import { IDisputeGame } from "interfaces/dispute/IDisputeGame.sol";
import { IDisputeGameFactory } from "interfaces/dispute/IDisputeGameFactory.sol";
import { ISystemConfig } from "interfaces/L1/ISystemConfig.sol";
import { ISuperchainConfig } from "interfaces/L1/ISuperchainConfig.sol";
import { IAnchorStateRegistry } from "interfaces/dispute/IAnchorStateRegistry.sol";
import { IProxyAdminOwnedBase } from "interfaces/L1/IProxyAdminOwnedBase.sol";
import { IETHLockbox } from "interfaces/L1/IETHLockbox.sol";

interface IOptimismPortal2 is IProxyAdminOwnedBase {
    error ContentLengthMismatch();
    error EmptyItem();
    error InvalidDataRemainder();
    error InvalidHeader();
    error ReinitializableBase_ZeroInitVersion();
    error OptimismPortal_AlreadyFinalized();
    error OptimismPortal_BadTarget();
    error OptimismPortal_CallPaused();
    error OptimismPortal_CalldataTooLarge();
    error OptimismPortal_GasEstimation();
    error OptimismPortal_GasLimitTooLow();
    error OptimismPortal_ImproperDisputeGame();
    error OptimismPortal_InvalidDisputeGame();
    error OptimismPortal_InvalidMerkleProof();
    error OptimismPortal_InvalidOutputRootProof();
    error OptimismPortal_InvalidProofTimestamp();
    error OptimismPortal_InvalidRootClaim();
    error OptimismPortal_NoReentrancy();
    error OptimismPortal_ProofNotOldEnough();
    error OptimismPortal_Unproven();
    error OptimismPortal_InvalidLockboxState();
    error OutOfGas();
    error UnexpectedList();
    error UnexpectedString();

    event Initialized(uint8 version);
    event TransactionDeposited(address indexed from, address indexed to, uint256 indexed version, bytes opaqueData);
    event WithdrawalFinalized(bytes32 indexed withdrawalHash, bool success);
    event WithdrawalProven(bytes32 indexed withdrawalHash, address indexed from, address indexed to);
    event WithdrawalProvenExtension1(bytes32 indexed withdrawalHash, address indexed proofSubmitter);

    receive() external payable;

    function anchorStateRegistry() external view returns (IAnchorStateRegistry);
    function ethLockbox() external view returns (IETHLockbox);
    function checkWithdrawal(bytes32 _withdrawalHash, address _proofSubmitter) external view;
    function depositTransaction(
        address _to,
        uint256 _value,
        uint64 _gasLimit,
        bool _isCreation,
        bytes memory _data
    )
        external
        payable;
    function disputeGameBlacklist(IDisputeGame _disputeGame) external view returns (bool);
    function disputeGameFactory() external view returns (IDisputeGameFactory);
    function disputeGameFinalityDelaySeconds() external view returns (uint256);
    function donateETH() external payable;
    function superchainConfig() external view returns (ISuperchainConfig);
    function finalizeWithdrawalTransaction(Types.WithdrawalTransaction memory _tx) external;
    function finalizeWithdrawalTransactionExternalProof(
        Types.WithdrawalTransaction memory _tx,
        address _proofSubmitter
    )
        external;
    function finalizedWithdrawals(bytes32) external view returns (bool);
    function guardian() external view returns (address);
    function initialize(
        ISystemConfig _systemConfig,
        IAnchorStateRegistry _anchorStateRegistry
    )
        external;
    function initVersion() external view returns (uint8);
    function l2Sender() external view returns (address);
    function minimumGasLimit(uint64 _byteCount) external pure returns (uint64);
    function numProofSubmitters(bytes32 _withdrawalHash) external view returns (uint256);
    function params() external view returns (uint128 prevBaseFee, uint64 prevBoughtGas, uint64 prevBlockNum); // nosemgrep
    function paused() external view returns (bool);
    function proofMaturityDelaySeconds() external view returns (uint256);
    function proofSubmitters(bytes32, uint256) external view returns (address);
    function proveWithdrawalTransaction(
        Types.WithdrawalTransaction memory _tx,
        uint256 _disputeGameIndex,
        Types.OutputRootProof memory _outputRootProof,
        bytes[] memory _withdrawalProof
    )
        external;
    function provenWithdrawals(
        bytes32,
        address
    )
        external
        view
        returns (IDisputeGame disputeGameProxy, uint64 timestamp);
    function respectedGameType() external view returns (GameType);
    function respectedGameTypeUpdatedAt() external view returns (uint64);
    function systemConfig() external view returns (ISystemConfig);
    function version() external pure returns (string memory);

    function __constructor__(uint256 _proofMaturityDelaySeconds) external;
}


// File: interfaces/universal/IOwnable.sol
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/// @title IOwnable
/// @notice Interface for Ownable.
interface IOwnable {
    event OwnershipTransferred(address indexed previousOwner, address indexed newOwner);

    function owner() external view returns (address);
    function renounceOwnership() external;
    function transferOwnership(address newOwner) external; // nosemgrep

    function __constructor__() external;
}


// File: lib/openzeppelin-contracts/contracts/utils/math/SignedMath.sol
// SPDX-License-Identifier: MIT
// OpenZeppelin Contracts (last updated v4.5.0) (utils/math/SignedMath.sol)

pragma solidity ^0.8.0;

/**
 * @dev Standard signed math utilities missing in the Solidity language.
 */
library SignedMath {
    /**
     * @dev Returns the largest of two signed numbers.
     */
    function max(int256 a, int256 b) internal pure returns (int256) {
        return a >= b ? a : b;
    }

    /**
     * @dev Returns the smallest of two signed numbers.
     */
    function min(int256 a, int256 b) internal pure returns (int256) {
        return a < b ? a : b;
    }

    /**
     * @dev Returns the average of two signed numbers without overflow.
     * The result is rounded towards zero.
     */
    function average(int256 a, int256 b) internal pure returns (int256) {
        // Formula from the book "Hacker's Delight"
        int256 x = (a & b) + ((a ^ b) >> 1);
        return x + (int256(uint256(x) >> 255) & (a ^ b));
    }

    /**
     * @dev Returns the absolute unsigned value of a signed value.
     */
    function abs(int256 n) internal pure returns (uint256) {
        unchecked {
            // must be unchecked in order to support `n = type(int256).min`
            return uint256(n >= 0 ? n : -n);
        }
    }
}


// File: lib/solmate/src/utils/FixedPointMathLib.sol
// SPDX-License-Identifier: MIT
pragma solidity >=0.8.0;

/// @notice Arithmetic library with operations for fixed-point numbers.
/// @author Solmate (https://github.com/Rari-Capital/solmate/blob/main/src/utils/FixedPointMathLib.sol)
library FixedPointMathLib {
    /*//////////////////////////////////////////////////////////////
                    SIMPLIFIED FIXED POINT OPERATIONS
    //////////////////////////////////////////////////////////////*/

    uint256 internal constant WAD = 1e18; // The scalar of ETH and most ERC20s.

    function mulWadDown(uint256 x, uint256 y) internal pure returns (uint256) {
        return mulDivDown(x, y, WAD); // Equivalent to (x * y) / WAD rounded down.
    }

    function mulWadUp(uint256 x, uint256 y) internal pure returns (uint256) {
        return mulDivUp(x, y, WAD); // Equivalent to (x * y) / WAD rounded up.
    }

    function divWadDown(uint256 x, uint256 y) internal pure returns (uint256) {
        return mulDivDown(x, WAD, y); // Equivalent to (x * WAD) / y rounded down.
    }

    function divWadUp(uint256 x, uint256 y) internal pure returns (uint256) {
        return mulDivUp(x, WAD, y); // Equivalent to (x * WAD) / y rounded up.
    }

    function powWad(int256 x, int256 y) internal pure returns (int256) {
        // Equivalent to x to the power of y because x ** y = (e ** ln(x)) ** y = e ** (ln(x) * y)
        return expWad((lnWad(x) * y) / int256(WAD)); // Using ln(x) means x must be greater than 0.
    }

    function expWad(int256 x) internal pure returns (int256 r) {
        unchecked {
            // When the result is < 0.5 we return zero. This happens when
            // x <= floor(log(0.5e18) * 1e18) ~ -42e18
            if (x <= -42139678854452767551) return 0;

            // When the result is > (2**255 - 1) / 1e18 we can not represent it as an
            // int. This happens when x >= floor(log((2**255 - 1) / 1e18) * 1e18) ~ 135.
            if (x >= 135305999368893231589) revert("EXP_OVERFLOW");

            // x is now in the range (-42, 136) * 1e18. Convert to (-42, 136) * 2**96
            // for more intermediate precision and a binary basis. This base conversion
            // is a multiplication by 1e18 / 2**96 = 5**18 / 2**78.
            x = (x << 78) / 5**18;

            // Reduce range of x to (-½ ln 2, ½ ln 2) * 2**96 by factoring out powers
            // of two such that exp(x) = exp(x') * 2**k, where k is an integer.
            // Solving this gives k = round(x / log(2)) and x' = x - k * log(2).
            int256 k = ((x << 96) / 54916777467707473351141471128 + 2**95) >> 96;
            x = x - k * 54916777467707473351141471128;

            // k is in the range [-61, 195].

            // Evaluate using a (6, 7)-term rational approximation.
            // p is made monic, we'll multiply by a scale factor later.
            int256 y = x + 1346386616545796478920950773328;
            y = ((y * x) >> 96) + 57155421227552351082224309758442;
            int256 p = y + x - 94201549194550492254356042504812;
            p = ((p * y) >> 96) + 28719021644029726153956944680412240;
            p = p * x + (4385272521454847904659076985693276 << 96);

            // We leave p in 2**192 basis so we don't need to scale it back up for the division.
            int256 q = x - 2855989394907223263936484059900;
            q = ((q * x) >> 96) + 50020603652535783019961831881945;
            q = ((q * x) >> 96) - 533845033583426703283633433725380;
            q = ((q * x) >> 96) + 3604857256930695427073651918091429;
            q = ((q * x) >> 96) - 14423608567350463180887372962807573;
            q = ((q * x) >> 96) + 26449188498355588339934803723976023;

            assembly {
                // Div in assembly because solidity adds a zero check despite the unchecked.
                // The q polynomial won't have zeros in the domain as all its roots are complex.
                // No scaling is necessary because p is already 2**96 too large.
                r := sdiv(p, q)
            }

            // r should be in the range (0.09, 0.25) * 2**96.

            // We now need to multiply r by:
            // * the scale factor s = ~6.031367120.
            // * the 2**k factor from the range reduction.
            // * the 1e18 / 2**96 factor for base conversion.
            // We do this all at once, with an intermediate result in 2**213
            // basis, so the final right shift is always by a positive amount.
            r = int256((uint256(r) * 3822833074963236453042738258902158003155416615667) >> uint256(195 - k));
        }
    }

    function lnWad(int256 x) internal pure returns (int256 r) {
        unchecked {
            require(x > 0, "UNDEFINED");

            // We want to convert x from 10**18 fixed point to 2**96 fixed point.
            // We do this by multiplying by 2**96 / 10**18. But since
            // ln(x * C) = ln(x) + ln(C), we can simply do nothing here
            // and add ln(2**96 / 10**18) at the end.

            // Reduce range of x to (1, 2) * 2**96
            // ln(2^k * x) = k * ln(2) + ln(x)
            int256 k = int256(log2(uint256(x))) - 96;
            x <<= uint256(159 - k);
            x = int256(uint256(x) >> 159);

            // Evaluate using a (8, 8)-term rational approximation.
            // p is made monic, we will multiply by a scale factor later.
            int256 p = x + 3273285459638523848632254066296;
            p = ((p * x) >> 96) + 24828157081833163892658089445524;
            p = ((p * x) >> 96) + 43456485725739037958740375743393;
            p = ((p * x) >> 96) - 11111509109440967052023855526967;
            p = ((p * x) >> 96) - 45023709667254063763336534515857;
            p = ((p * x) >> 96) - 14706773417378608786704636184526;
            p = p * x - (795164235651350426258249787498 << 96);

            // We leave p in 2**192 basis so we don't need to scale it back up for the division.
            // q is monic by convention.
            int256 q = x + 5573035233440673466300451813936;
            q = ((q * x) >> 96) + 71694874799317883764090561454958;
            q = ((q * x) >> 96) + 283447036172924575727196451306956;
            q = ((q * x) >> 96) + 401686690394027663651624208769553;
            q = ((q * x) >> 96) + 204048457590392012362485061816622;
            q = ((q * x) >> 96) + 31853899698501571402653359427138;
            q = ((q * x) >> 96) + 909429971244387300277376558375;
            assembly {
                // Div in assembly because solidity adds a zero check despite the unchecked.
                // The q polynomial is known not to have zeros in the domain.
                // No scaling required because p is already 2**96 too large.
                r := sdiv(p, q)
            }

            // r is in the range (0, 0.125) * 2**96

            // Finalization, we need to:
            // * multiply by the scale factor s = 5.549…
            // * add ln(2**96 / 10**18)
            // * add k * ln(2)
            // * multiply by 10**18 / 2**96 = 5**18 >> 78

            // mul s * 5e18 * 2**96, base is now 5**18 * 2**192
            r *= 1677202110996718588342820967067443963516166;
            // add ln(2) * k * 5e18 * 2**192
            r += 16597577552685614221487285958193947469193820559219878177908093499208371 * k;
            // add ln(2**96 / 10**18) * 5e18 * 2**192
            r += 600920179829731861736702779321621459595472258049074101567377883020018308;
            // base conversion: mul 2**18 / 2**192
            r >>= 174;
        }
    }

    /*//////////////////////////////////////////////////////////////
                    LOW LEVEL FIXED POINT OPERATIONS
    //////////////////////////////////////////////////////////////*/

    function mulDivDown(
        uint256 x,
        uint256 y,
        uint256 denominator
    ) internal pure returns (uint256 z) {
        assembly {
            // Store x * y in z for now.
            z := mul(x, y)

            // Equivalent to require(denominator != 0 && (x == 0 || (x * y) / x == y))
            if iszero(and(iszero(iszero(denominator)), or(iszero(x), eq(div(z, x), y)))) {
                revert(0, 0)
            }

            // Divide z by the denominator.
            z := div(z, denominator)
        }
    }

    function mulDivUp(
        uint256 x,
        uint256 y,
        uint256 denominator
    ) internal pure returns (uint256 z) {
        assembly {
            // Store x * y in z for now.
            z := mul(x, y)

            // Equivalent to require(denominator != 0 && (x == 0 || (x * y) / x == y))
            if iszero(and(iszero(iszero(denominator)), or(iszero(x), eq(div(z, x), y)))) {
                revert(0, 0)
            }

            // First, divide z - 1 by the denominator and add 1.
            // We allow z - 1 to underflow if z is 0, because we multiply the
            // end result by 0 if z is zero, ensuring we return 0 if z is zero.
            z := mul(iszero(iszero(z)), add(div(sub(z, 1), denominator), 1))
        }
    }

    function rpow(
        uint256 x,
        uint256 n,
        uint256 scalar
    ) internal pure returns (uint256 z) {
        assembly {
            switch x
            case 0 {
                switch n
                case 0 {
                    // 0 ** 0 = 1
                    z := scalar
                }
                default {
                    // 0 ** n = 0
                    z := 0
                }
            }
            default {
                switch mod(n, 2)
                case 0 {
                    // If n is even, store scalar in z for now.
                    z := scalar
                }
                default {
                    // If n is odd, store x in z for now.
                    z := x
                }

                // Shifting right by 1 is like dividing by 2.
                let half := shr(1, scalar)

                for {
                    // Shift n right by 1 before looping to halve it.
                    n := shr(1, n)
                } n {
                    // Shift n right by 1 each iteration to halve it.
                    n := shr(1, n)
                } {
                    // Revert immediately if x ** 2 would overflow.
                    // Equivalent to iszero(eq(div(xx, x), x)) here.
                    if shr(128, x) {
                        revert(0, 0)
                    }

                    // Store x squared.
                    let xx := mul(x, x)

                    // Round to the nearest number.
                    let xxRound := add(xx, half)

                    // Revert if xx + half overflowed.
                    if lt(xxRound, xx) {
                        revert(0, 0)
                    }

                    // Set x to scaled xxRound.
                    x := div(xxRound, scalar)

                    // If n is even:
                    if mod(n, 2) {
                        // Compute z * x.
                        let zx := mul(z, x)

                        // If z * x overflowed:
                        if iszero(eq(div(zx, x), z)) {
                            // Revert if x is non-zero.
                            if iszero(iszero(x)) {
                                revert(0, 0)
                            }
                        }

                        // Round to the nearest number.
                        let zxRound := add(zx, half)

                        // Revert if zx + half overflowed.
                        if lt(zxRound, zx) {
                            revert(0, 0)
                        }

                        // Return properly scaled zxRound.
                        z := div(zxRound, scalar)
                    }
                }
            }
        }
    }

    /*//////////////////////////////////////////////////////////////
                        GENERAL NUMBER UTILITIES
    //////////////////////////////////////////////////////////////*/

    function sqrt(uint256 x) internal pure returns (uint256 z) {
        assembly {
            let y := x // We start y at x, which will help us make our initial estimate.

            z := 181 // The "correct" value is 1, but this saves a multiplication later.

            // This segment is to get a reasonable initial estimate for the Babylonian method. With a bad
            // start, the correct # of bits increases ~linearly each iteration instead of ~quadratically.

            // We check y >= 2^(k + 8) but shift right by k bits
            // each branch to ensure that if x >= 256, then y >= 256.
            if iszero(lt(y, 0x10000000000000000000000000000000000)) {
                y := shr(128, y)
                z := shl(64, z)
            }
            if iszero(lt(y, 0x1000000000000000000)) {
                y := shr(64, y)
                z := shl(32, z)
            }
            if iszero(lt(y, 0x10000000000)) {
                y := shr(32, y)
                z := shl(16, z)
            }
            if iszero(lt(y, 0x1000000)) {
                y := shr(16, y)
                z := shl(8, z)
            }

            // Goal was to get z*z*y within a small factor of x. More iterations could
            // get y in a tighter range. Currently, we will have y in [256, 256*2^16).
            // We ensured y >= 256 so that the relative difference between y and y+1 is small.
            // That's not possible if x < 256 but we can just verify those cases exhaustively.

            // Now, z*z*y <= x < z*z*(y+1), and y <= 2^(16+8), and either y >= 256, or x < 256.
            // Correctness can be checked exhaustively for x < 256, so we assume y >= 256.
            // Then z*sqrt(y) is within sqrt(257)/sqrt(256) of sqrt(x), or about 20bps.

            // For s in the range [1/256, 256], the estimate f(s) = (181/1024) * (s+1) is in the range
            // (1/2.84 * sqrt(s), 2.84 * sqrt(s)), with largest error when s = 1 and when s = 256 or 1/256.

            // Since y is in [256, 256*2^16), let a = y/65536, so that a is in [1/256, 256). Then we can estimate
            // sqrt(y) using sqrt(65536) * 181/1024 * (a + 1) = 181/4 * (y + 65536)/65536 = 181 * (y + 65536)/2^18.

            // There is no overflow risk here since y < 2^136 after the first branch above.
            z := shr(18, mul(z, add(y, 65536))) // A mul() is saved from starting z at 181.

            // Given the worst case multiplicative error of 2.84 above, 7 iterations should be enough.
            z := shr(1, add(z, div(x, z)))
            z := shr(1, add(z, div(x, z)))
            z := shr(1, add(z, div(x, z)))
            z := shr(1, add(z, div(x, z)))
            z := shr(1, add(z, div(x, z)))
            z := shr(1, add(z, div(x, z)))
            z := shr(1, add(z, div(x, z)))

            // If x+1 is a perfect square, the Babylonian method cycles between
            // floor(sqrt(x)) and ceil(sqrt(x)). This statement ensures we return floor.
            // See: https://en.wikipedia.org/wiki/Integer_square_root#Using_only_integer_division
            // Since the ceil is rare, we save gas on the assignment and repeat division in the rare case.
            // If you don't care whether the floor or ceil square root is returned, you can remove this statement.
            z := sub(z, lt(div(x, z), z))
        }
    }

    function log2(uint256 x) internal pure returns (uint256 r) {
        require(x > 0, "UNDEFINED");

        assembly {
            r := shl(7, lt(0xffffffffffffffffffffffffffffffff, x))
            r := or(r, shl(6, lt(0xffffffffffffffff, shr(r, x))))
            r := or(r, shl(5, lt(0xffffffff, shr(r, x))))
            r := or(r, shl(4, lt(0xffff, shr(r, x))))
            r := or(r, shl(3, lt(0xff, shr(r, x))))
            r := or(r, shl(2, lt(0xf, shr(r, x))))
            r := or(r, shl(1, lt(0x3, shr(r, x))))
            r := or(r, lt(0x1, shr(r, x)))
        }
    }
}


// File: src/libraries/rlp/RLPWriter.sol
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/// @custom:attribution https://github.com/bakaoh/solidity-rlp-encode
/// @title RLPWriter
/// @author RLPWriter is a library for encoding Solidity types to RLP bytes. Adapted from Bakaoh's
///         RLPEncode library (https://github.com/bakaoh/solidity-rlp-encode) with minor
///         modifications to improve legibility.
library RLPWriter {
    /// @notice RLP encodes a byte string.
    /// @param _in The byte string to encode.
    /// @return out_ The RLP encoded string in bytes.
    function writeBytes(bytes memory _in) internal pure returns (bytes memory out_) {
        if (_in.length == 1 && uint8(_in[0]) < 128) {
            out_ = _in;
        } else {
            out_ = abi.encodePacked(_writeLength(_in.length, 128), _in);
        }
    }

    /// @notice RLP encodes a list of RLP encoded byte byte strings.
    /// @param _in The list of RLP encoded byte strings.
    /// @return list_ The RLP encoded list of items in bytes.
    function writeList(bytes[] memory _in) internal pure returns (bytes memory list_) {
        list_ = _flatten(_in);
        list_ = abi.encodePacked(_writeLength(list_.length, 192), list_);
    }

    /// @notice RLP encodes a string.
    /// @param _in The string to encode.
    /// @return out_ The RLP encoded string in bytes.
    function writeString(string memory _in) internal pure returns (bytes memory out_) {
        out_ = writeBytes(bytes(_in));
    }

    /// @notice RLP encodes an address.
    /// @param _in The address to encode.
    /// @return out_ The RLP encoded address in bytes.
    function writeAddress(address _in) internal pure returns (bytes memory out_) {
        out_ = writeBytes(abi.encodePacked(_in));
    }

    /// @notice RLP encodes a uint.
    /// @param _in The uint256 to encode.
    /// @return out_ The RLP encoded uint256 in bytes.
    function writeUint(uint256 _in) internal pure returns (bytes memory out_) {
        out_ = writeBytes(_toBinary(_in));
    }

    /// @notice RLP encodes a bool.
    /// @param _in The bool to encode.
    /// @return out_ The RLP encoded bool in bytes.
    function writeBool(bool _in) internal pure returns (bytes memory out_) {
        out_ = new bytes(1);
        out_[0] = (_in ? bytes1(0x01) : bytes1(0x80));
    }

    /// @notice Encode the first byte and then the `len` in binary form if `length` is more than 55.
    /// @param _len    The length of the string or the payload.
    /// @param _offset 128 if item is string, 192 if item is list.
    /// @return out_ RLP encoded bytes.
    function _writeLength(uint256 _len, uint256 _offset) private pure returns (bytes memory out_) {
        if (_len < 56) {
            out_ = new bytes(1);
            out_[0] = bytes1(uint8(_len) + uint8(_offset));
        } else {
            uint256 lenLen;
            uint256 i = 1;
            while (_len / i != 0) {
                lenLen++;
                i *= 256;
            }

            out_ = new bytes(lenLen + 1);
            out_[0] = bytes1(uint8(lenLen) + uint8(_offset) + 55);
            for (i = 1; i <= lenLen; i++) {
                out_[i] = bytes1(uint8((_len / (256 ** (lenLen - i))) % 256));
            }
        }
    }

    /// @notice Encode integer in big endian binary form with no leading zeroes.
    /// @param _x The integer to encode.
    /// @return out_ RLP encoded bytes.
    function _toBinary(uint256 _x) private pure returns (bytes memory out_) {
        bytes memory b = abi.encodePacked(_x);

        uint256 i = 0;
        for (; i < 32; i++) {
            if (b[i] != 0) {
                break;
            }
        }

        out_ = new bytes(32 - i);
        for (uint256 j = 0; j < out_.length; j++) {
            out_[j] = b[i++];
        }
    }

    /// @custom:attribution https://github.com/Arachnid/solidity-stringutils
    /// @notice Copies a piece of memory to another location.
    /// @param _dest Destination location.
    /// @param _src  Source location.
    /// @param _len  Length of memory to copy.
    function _memcpy(uint256 _dest, uint256 _src, uint256 _len) private pure {
        uint256 dest = _dest;
        uint256 src = _src;
        uint256 len = _len;

        for (; len >= 32; len -= 32) {
            assembly {
                mstore(dest, mload(src))
            }
            dest += 32;
            src += 32;
        }

        uint256 mask;
        unchecked {
            mask = 256 ** (32 - len) - 1;
        }
        assembly {
            let srcpart := and(mload(src), not(mask))
            let destpart := and(mload(dest), mask)
            mstore(dest, or(destpart, srcpart))
        }
    }

    /// @custom:attribution https://github.com/sammayo/solidity-rlp-encoder
    /// @notice Flattens a list of byte strings into one byte string.
    /// @param _list List of byte strings to flatten.
    /// @return out_ The flattened byte string.
    function _flatten(bytes[] memory _list) private pure returns (bytes memory out_) {
        if (_list.length == 0) {
            return new bytes(0);
        }

        uint256 len;
        uint256 i = 0;
        for (; i < _list.length; i++) {
            len += _list[i].length;
        }

        out_ = new bytes(len);
        uint256 flattenedPtr;
        assembly {
            flattenedPtr := add(out_, 0x20)
        }

        for (i = 0; i < _list.length; i++) {
            bytes memory item = _list[i];

            uint256 listPtr;
            assembly {
                listPtr := add(item, 0x20)
            }

            _memcpy(flattenedPtr, listPtr, item.length);
            flattenedPtr += _list[i].length;
        }
    }
}


// File: src/libraries/Bytes.sol
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/// @title Bytes
/// @notice Bytes is a library for manipulating byte arrays.
library Bytes {
    /// @custom:attribution https://github.com/GNSPS/solidity-bytes-utils
    /// @notice Slices a byte array with a given starting index and length. Returns a new byte array
    ///         as opposed to a pointer to the original array. Will throw if trying to slice more
    ///         bytes than exist in the array.
    /// @param _bytes Byte array to slice.
    /// @param _start Starting index of the slice.
    /// @param _length Length of the slice.
    /// @return Slice of the input byte array.
    function slice(bytes memory _bytes, uint256 _start, uint256 _length) internal pure returns (bytes memory) {
        unchecked {
            require(_length + 31 >= _length, "slice_overflow");
            require(_start + _length >= _start, "slice_overflow");
            require(_bytes.length >= _start + _length, "slice_outOfBounds");
        }

        bytes memory tempBytes;

        assembly {
            switch iszero(_length)
            case 0 {
                // Get a location of some free memory and store it in tempBytes as
                // Solidity does for memory variables.
                tempBytes := mload(0x40)

                // The first word of the slice result is potentially a partial
                // word read from the original array. To read it, we calculate
                // the length of that partial word and start copying that many
                // bytes into the array. The first word we copy will start with
                // data we don't care about, but the last `lengthmod` bytes will
                // land at the beginning of the contents of the new array. When
                // we're done copying, we overwrite the full first word with
                // the actual length of the slice.
                let lengthmod := and(_length, 31)

                // The multiplication in the next line is necessary
                // because when slicing multiples of 32 bytes (lengthmod == 0)
                // the following copy loop was copying the origin's length
                // and then ending prematurely not copying everything it should.
                let mc := add(add(tempBytes, lengthmod), mul(0x20, iszero(lengthmod)))
                let end := add(mc, _length)

                for {
                    // The multiplication in the next line has the same exact purpose
                    // as the one above.
                    let cc := add(add(add(_bytes, lengthmod), mul(0x20, iszero(lengthmod))), _start)
                } lt(mc, end) {
                    mc := add(mc, 0x20)
                    cc := add(cc, 0x20)
                } { mstore(mc, mload(cc)) }

                mstore(tempBytes, _length)

                //update free-memory pointer
                //allocating the array padded to 32 bytes like the compiler does now
                mstore(0x40, and(add(mc, 31), not(31)))
            }
            //if we want a zero-length slice let's just return a zero-length array
            default {
                tempBytes := mload(0x40)

                //zero out the 32 bytes slice we are about to return
                //we need to do it because Solidity does not garbage collect
                mstore(tempBytes, 0)

                mstore(0x40, add(tempBytes, 0x20))
            }
        }

        return tempBytes;
    }

    /// @notice Slices a byte array with a given starting index up to the end of the original byte
    ///         array. Returns a new array rathern than a pointer to the original.
    /// @param _bytes Byte array to slice.
    /// @param _start Starting index of the slice.
    /// @return Slice of the input byte array.
    function slice(bytes memory _bytes, uint256 _start) internal pure returns (bytes memory) {
        if (_start >= _bytes.length) {
            return bytes("");
        }
        return slice(_bytes, _start, _bytes.length - _start);
    }

    /// @notice Converts a byte array into a nibble array by splitting each byte into two nibbles.
    ///         Resulting nibble array will be exactly twice as long as the input byte array.
    /// @param _bytes Input byte array to convert.
    /// @return Resulting nibble array.
    function toNibbles(bytes memory _bytes) internal pure returns (bytes memory) {
        bytes memory _nibbles;
        assembly {
            // Grab a free memory offset for the new array
            _nibbles := mload(0x40)

            // Load the length of the passed bytes array from memory
            let bytesLength := mload(_bytes)

            // Calculate the length of the new nibble array
            // This is the length of the input array times 2
            let nibblesLength := shl(0x01, bytesLength)

            // Update the free memory pointer to allocate memory for the new array.
            // To do this, we add the length of the new array + 32 bytes for the array length
            // rounded up to the nearest 32 byte boundary to the current free memory pointer.
            mstore(0x40, add(_nibbles, and(not(0x1F), add(nibblesLength, 0x3F))))

            // Store the length of the new array in memory
            mstore(_nibbles, nibblesLength)

            // Store the memory offset of the _bytes array's contents on the stack
            let bytesStart := add(_bytes, 0x20)

            // Store the memory offset of the nibbles array's contents on the stack
            let nibblesStart := add(_nibbles, 0x20)

            // Loop through each byte in the input array
            for { let i := 0x00 } lt(i, bytesLength) { i := add(i, 0x01) } {
                // Get the starting offset of the next 2 bytes in the nibbles array
                let offset := add(nibblesStart, shl(0x01, i))
                // Load the byte at the current index within the `_bytes` array
                let b := byte(0x00, mload(add(bytesStart, i)))

                // Pull out the first nibble and store it in the new array
                mstore8(offset, shr(0x04, b))
                // Pull out the second nibble and store it in the new array
                mstore8(add(offset, 0x01), and(b, 0x0F))
            }
        }
        return _nibbles;
    }

    /// @notice Compares two byte arrays by comparing their keccak256 hashes.
    /// @param _bytes First byte array to compare.
    /// @param _other Second byte array to compare.
    /// @return True if the two byte arrays are equal, false otherwise.
    function equal(bytes memory _bytes, bytes memory _other) internal pure returns (bool) {
        return keccak256(_bytes) == keccak256(_other);
    }
}


// File: src/libraries/rlp/RLPReader.sol
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.8;

// Libraries
import {
    EmptyItem,
    UnexpectedString,
    InvalidDataRemainder,
    ContentLengthMismatch,
    InvalidHeader,
    UnexpectedList
} from "src/libraries/rlp/RLPErrors.sol";

/// @custom:attribution https://github.com/hamdiallam/Solidity-RLP
/// @title RLPReader
/// @notice RLPReader is a library for parsing RLP-encoded byte arrays into Solidity types. Adapted
///         from Solidity-RLP (https://github.com/hamdiallam/Solidity-RLP) by Hamdi Allam with
///         various tweaks to improve readability.
library RLPReader {
    /// @notice Custom pointer type to avoid confusion between pointers and uint256s.
    type MemoryPointer is uint256;

    /// @notice RLP item types.
    /// @custom:value DATA_ITEM Represents an RLP data item (NOT a list).
    /// @custom:value LIST_ITEM Represents an RLP list item.
    enum RLPItemType {
        DATA_ITEM,
        LIST_ITEM
    }

    /// @notice Struct representing an RLP item.
    /// @custom:field length Length of the RLP item.
    /// @custom:field ptr    Pointer to the RLP item in memory.
    struct RLPItem {
        uint256 length;
        MemoryPointer ptr;
    }

    /// @notice Max list length that this library will accept.
    uint256 internal constant MAX_LIST_LENGTH = 32;

    /// @notice Converts bytes to a reference to memory position and length.
    /// @param _in Input bytes to convert.
    /// @return out_ Output memory reference.
    function toRLPItem(bytes memory _in) internal pure returns (RLPItem memory out_) {
        // Empty arrays are not RLP items.
        if (_in.length == 0) revert EmptyItem();

        MemoryPointer ptr;
        assembly {
            ptr := add(_in, 32)
        }

        out_ = RLPItem({ length: _in.length, ptr: ptr });
    }

    /// @notice Reads an RLP list value into a list of RLP items.
    /// @param _in RLP list value.
    /// @return out_ Decoded RLP list items.
    function readList(RLPItem memory _in) internal pure returns (RLPItem[] memory out_) {
        (uint256 listOffset, uint256 listLength, RLPItemType itemType) = _decodeLength(_in);

        if (itemType != RLPItemType.LIST_ITEM) revert UnexpectedString();

        if (listOffset + listLength != _in.length) revert InvalidDataRemainder();

        // Solidity in-memory arrays can't be increased in size, but *can* be decreased in size by
        // writing to the length. Since we can't know the number of RLP items without looping over
        // the entire input, we'd have to loop twice to accurately size this array. It's easier to
        // simply set a reasonable maximum list length and decrease the size before we finish.
        out_ = new RLPItem[](MAX_LIST_LENGTH);

        uint256 itemCount = 0;
        uint256 offset = listOffset;
        while (offset < _in.length) {
            (uint256 itemOffset, uint256 itemLength,) = _decodeLength(
                RLPItem({ length: _in.length - offset, ptr: MemoryPointer.wrap(MemoryPointer.unwrap(_in.ptr) + offset) })
            );

            // We don't need to check itemCount < out.length explicitly because Solidity already
            // handles this check on our behalf, we'd just be wasting gas.
            out_[itemCount] = RLPItem({
                length: itemLength + itemOffset,
                ptr: MemoryPointer.wrap(MemoryPointer.unwrap(_in.ptr) + offset)
            });

            itemCount += 1;
            offset += itemOffset + itemLength;
        }

        // Decrease the array size to match the actual item count.
        assembly {
            mstore(out_, itemCount)
        }
    }

    /// @notice Reads an RLP list value into a list of RLP items.
    /// @param _in RLP list value.
    /// @return out_ Decoded RLP list items.
    function readList(bytes memory _in) internal pure returns (RLPItem[] memory out_) {
        out_ = readList(toRLPItem(_in));
    }

    /// @notice Reads an RLP bytes value into bytes.
    /// @param _in RLP bytes value.
    /// @return out_ Decoded bytes.
    function readBytes(RLPItem memory _in) internal pure returns (bytes memory out_) {
        (uint256 itemOffset, uint256 itemLength, RLPItemType itemType) = _decodeLength(_in);

        if (itemType != RLPItemType.DATA_ITEM) revert UnexpectedList();

        if (_in.length != itemOffset + itemLength) revert InvalidDataRemainder();

        out_ = _copy(_in.ptr, itemOffset, itemLength);
    }

    /// @notice Reads an RLP bytes value into bytes.
    /// @param _in RLP bytes value.
    /// @return out_ Decoded bytes.
    function readBytes(bytes memory _in) internal pure returns (bytes memory out_) {
        out_ = readBytes(toRLPItem(_in));
    }

    /// @notice Reads the raw bytes of an RLP item.
    /// @param _in RLP item to read.
    /// @return out_ Raw RLP bytes.
    function readRawBytes(RLPItem memory _in) internal pure returns (bytes memory out_) {
        out_ = _copy(_in.ptr, 0, _in.length);
    }

    /// @notice Decodes the length of an RLP item.
    /// @param _in RLP item to decode.
    /// @return offset_ Offset of the encoded data.
    /// @return length_ Length of the encoded data.
    /// @return type_ RLP item type (LIST_ITEM or DATA_ITEM).
    function _decodeLength(RLPItem memory _in)
        private
        pure
        returns (uint256 offset_, uint256 length_, RLPItemType type_)
    {
        // Short-circuit if there's nothing to decode, note that we perform this check when
        // the user creates an RLP item via toRLPItem, but it's always possible for them to bypass
        // that function and create an RLP item directly. So we need to check this anyway.
        if (_in.length == 0) revert EmptyItem();

        MemoryPointer ptr = _in.ptr;
        uint256 prefix;
        assembly {
            prefix := byte(0, mload(ptr))
        }

        if (prefix <= 0x7f) {
            // Single byte.
            return (0, 1, RLPItemType.DATA_ITEM);
        } else if (prefix <= 0xb7) {
            // Short string.

            // slither-disable-next-line variable-scope
            uint256 strLen = prefix - 0x80;

            if (_in.length <= strLen) revert ContentLengthMismatch();

            bytes1 firstByteOfContent;
            assembly {
                firstByteOfContent := and(mload(add(ptr, 1)), shl(248, 0xff))
            }

            if (strLen == 1 && firstByteOfContent < 0x80) revert InvalidHeader();

            return (1, strLen, RLPItemType.DATA_ITEM);
        } else if (prefix <= 0xbf) {
            // Long string.
            uint256 lenOfStrLen = prefix - 0xb7;

            if (_in.length <= lenOfStrLen) revert ContentLengthMismatch();

            bytes1 firstByteOfContent;
            assembly {
                firstByteOfContent := and(mload(add(ptr, 1)), shl(248, 0xff))
            }

            if (firstByteOfContent == 0x00) revert InvalidHeader();

            uint256 strLen;
            assembly {
                strLen := shr(sub(256, mul(8, lenOfStrLen)), mload(add(ptr, 1)))
            }

            if (strLen <= 55) revert InvalidHeader();

            if (_in.length <= lenOfStrLen + strLen) revert ContentLengthMismatch();

            return (1 + lenOfStrLen, strLen, RLPItemType.DATA_ITEM);
        } else if (prefix <= 0xf7) {
            // Short list.
            // slither-disable-next-line variable-scope
            uint256 listLen = prefix - 0xc0;

            if (_in.length <= listLen) revert ContentLengthMismatch();

            return (1, listLen, RLPItemType.LIST_ITEM);
        } else {
            // Long list.
            uint256 lenOfListLen = prefix - 0xf7;

            if (_in.length <= lenOfListLen) revert ContentLengthMismatch();

            bytes1 firstByteOfContent;
            assembly {
                firstByteOfContent := and(mload(add(ptr, 1)), shl(248, 0xff))
            }

            if (firstByteOfContent == 0x00) revert InvalidHeader();

            uint256 listLen;
            assembly {
                listLen := shr(sub(256, mul(8, lenOfListLen)), mload(add(ptr, 1)))
            }

            if (listLen <= 55) revert InvalidHeader();

            if (_in.length <= lenOfListLen + listLen) revert ContentLengthMismatch();

            return (1 + lenOfListLen, listLen, RLPItemType.LIST_ITEM);
        }
    }

    /// @notice Copies the bytes from a memory location.
    /// @param _src    Pointer to the location to read from.
    /// @param _offset Offset to start reading from.
    /// @param _length Number of bytes to read.
    /// @return out_ Copied bytes.
    function _copy(MemoryPointer _src, uint256 _offset, uint256 _length) private pure returns (bytes memory out_) {
        out_ = new bytes(_length);
        if (_length == 0) {
            return out_;
        }

        // Mostly based on Solidity's copy_memory_to_memory:
        // https://github.com/ethereum/solidity/blob/34dd30d71b4da730488be72ff6af7083cf2a91f6/libsolidity/codegen/YulUtilFunctions.cpp#L102-L114
        uint256 src = MemoryPointer.unwrap(_src) + _offset;
        assembly {
            let dest := add(out_, 32)
            let i := 0
            for { } lt(i, _length) { i := add(i, 32) } { mstore(add(dest, i), mload(add(src, i))) }

            if gt(i, _length) { mstore(add(dest, _length), 0) }
        }
    }
}


// File: src/dispute/lib/LibPosition.sol
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.15;

using LibPosition for Position global;

/// @notice A `Position` represents a position of a claim within the game tree.
/// @dev This is represented as a "generalized index" where the high-order bit
/// is the level in the tree and the remaining bits is a unique bit pattern, allowing
/// a unique identifier for each node in the tree. Mathematically, it is calculated
/// as 2^{depth} + indexAtDepth.
type Position is uint128;

/// @title LibPosition
/// @notice This library contains helper functions for working with the `Position` type.
library LibPosition {
    /// @notice the `MAX_POSITION_BITLEN` is the number of bits that the `Position` type, and the implementation of
    ///         its behavior within this library, can safely support.
    uint8 internal constant MAX_POSITION_BITLEN = 126;

    /// @notice Computes a generalized index (2^{depth} + indexAtDepth).
    /// @param _depth The depth of the position.
    /// @param _indexAtDepth The index at the depth of the position.
    /// @return position_ The computed generalized index.
    function wrap(uint8 _depth, uint128 _indexAtDepth) internal pure returns (Position position_) {
        assembly {
            // gindex = 2^{_depth} + _indexAtDepth
            position_ := add(shl(_depth, 1), _indexAtDepth)
        }
    }

    /// @notice Pulls the `depth` out of a `Position` type.
    /// @param _position The generalized index to get the `depth` of.
    /// @return depth_ The `depth` of the `position` gindex.
    /// @custom:attribution Solady <https://github.com/Vectorized/Solady>
    function depth(Position _position) internal pure returns (uint8 depth_) {
        // Return the most significant bit offset, which signifies the depth of the gindex.
        assembly {
            depth_ := or(depth_, shl(6, lt(0xffffffffffffffff, shr(depth_, _position))))
            depth_ := or(depth_, shl(5, lt(0xffffffff, shr(depth_, _position))))

            // For the remaining 32 bits, use a De Bruijn lookup.
            _position := shr(depth_, _position)
            _position := or(_position, shr(1, _position))
            _position := or(_position, shr(2, _position))
            _position := or(_position, shr(4, _position))
            _position := or(_position, shr(8, _position))
            _position := or(_position, shr(16, _position))

            depth_ :=
                or(
                    depth_,
                    byte(
                        shr(251, mul(_position, shl(224, 0x07c4acdd))),
                        0x0009010a0d15021d0b0e10121619031e080c141c0f111807131b17061a05041f
                    )
                )
        }
    }

    /// @notice Pulls the `indexAtDepth` out of a `Position` type.
    ///         The `indexAtDepth` is the left/right index of a position at a specific depth within
    ///         the binary tree, starting from index 0. For example, at gindex 2, the `depth` = 1
    ///         and the `indexAtDepth` = 0.
    /// @param _position The generalized index to get the `indexAtDepth` of.
    /// @return indexAtDepth_ The `indexAtDepth` of the `position` gindex.
    function indexAtDepth(Position _position) internal pure returns (uint128 indexAtDepth_) {
        // Return bits p_{msb-1}...p_{0}. This effectively pulls the 2^{depth} out of the gindex,
        // leaving only the `indexAtDepth`.
        uint256 msb = depth(_position);
        assembly {
            indexAtDepth_ := sub(_position, shl(msb, 1))
        }
    }

    /// @notice Get the left child of `_position`.
    /// @param _position The position to get the left position of.
    /// @return left_ The position to the left of `position`.
    function left(Position _position) internal pure returns (Position left_) {
        assembly {
            left_ := shl(1, _position)
        }
    }

    /// @notice Get the right child of `_position`
    /// @param _position The position to get the right position of.
    /// @return right_ The position to the right of `position`.
    function right(Position _position) internal pure returns (Position right_) {
        assembly {
            right_ := or(1, shl(1, _position))
        }
    }

    /// @notice Get the parent position of `_position`.
    /// @param _position The position to get the parent position of.
    /// @return parent_ The parent position of `position`.
    function parent(Position _position) internal pure returns (Position parent_) {
        assembly {
            parent_ := shr(1, _position)
        }
    }

    /// @notice Get the deepest, right most gindex relative to the `position`. This is equivalent to
    ///         calling `right` on a position until the maximum depth is reached.
    /// @param _position The position to get the relative deepest, right most gindex of.
    /// @param _maxDepth The maximum depth of the game.
    /// @return rightIndex_ The deepest, right most gindex relative to the `position`.
    function rightIndex(Position _position, uint256 _maxDepth) internal pure returns (Position rightIndex_) {
        uint256 msb = depth(_position);
        assembly {
            let remaining := sub(_maxDepth, msb)
            rightIndex_ := or(shl(remaining, _position), sub(shl(remaining, 1), 1))
        }
    }

    /// @notice Get the deepest, right most trace index relative to the `position`. This is
    ///         equivalent to calling `right` on a position until the maximum depth is reached and
    ///         then finding its index at depth.
    /// @param _position The position to get the relative trace index of.
    /// @param _maxDepth The maximum depth of the game.
    /// @return traceIndex_ The trace index relative to the `position`.
    function traceIndex(Position _position, uint256 _maxDepth) internal pure returns (uint256 traceIndex_) {
        uint256 msb = depth(_position);
        assembly {
            let remaining := sub(_maxDepth, msb)
            traceIndex_ := sub(or(shl(remaining, _position), sub(shl(remaining, 1), 1)), shl(_maxDepth, 1))
        }
    }

    /// @notice Gets the position of the highest ancestor of `_position` that commits to the same
    ///         trace index.
    /// @param _position The position to get the highest ancestor of.
    /// @return ancestor_ The highest ancestor of `position` that commits to the same trace index.
    function traceAncestor(Position _position) internal pure returns (Position ancestor_) {
        // Create a field with only the lowest unset bit of `_position` set.
        Position lsb;
        assembly {
            lsb := and(not(_position), add(_position, 1))
        }
        // Find the index of the lowest unset bit within the field.
        uint256 msb = depth(lsb);
        // The highest ancestor that commits to the same trace index is the original position
        // shifted right by the index of the lowest unset bit.
        assembly {
            let a := shr(msb, _position)
            // Bound the ancestor to the minimum gindex, 1.
            ancestor_ := or(a, iszero(a))
        }
    }

    /// @notice Gets the position of the highest ancestor of `_position` that commits to the same
    ///         trace index, while still being below `_upperBoundExclusive`.
    /// @param _position The position to get the highest ancestor of.
    /// @param _upperBoundExclusive The exclusive upper depth bound, used to inform where to stop in order
    ///                             to not escape a sub-tree.
    /// @return ancestor_ The highest ancestor of `position` that commits to the same trace index.
    function traceAncestorBounded(
        Position _position,
        uint256 _upperBoundExclusive
    )
        internal
        pure
        returns (Position ancestor_)
    {
        // This function only works for positions that are below the upper bound.
        if (_position.depth() <= _upperBoundExclusive) {
            assembly {
                // Revert with `ClaimAboveSplit()`
                mstore(0x00, 0xb34b5c22)
                revert(0x1C, 0x04)
            }
        }

        // Grab the global trace ancestor.
        ancestor_ = traceAncestor(_position);

        // If the ancestor is above or at the upper bound, shift it to be below the upper bound.
        // This should be a special case that only covers positions that commit to the final leaf
        // in a sub-tree.
        if (ancestor_.depth() <= _upperBoundExclusive) {
            ancestor_ = ancestor_.rightIndex(_upperBoundExclusive + 1);
        }
    }

    /// @notice Get the move position of `_position`, which is the left child of:
    ///         1. `_position` if `_isAttack` is true.
    ///         2. `_position | 1` if `_isAttack` is false.
    /// @param _position The position to get the relative attack/defense position of.
    /// @param _isAttack Whether or not the move is an attack move.
    /// @return move_ The move position relative to `position`.
    function move(Position _position, bool _isAttack) internal pure returns (Position move_) {
        assembly {
            move_ := shl(1, or(iszero(_isAttack), _position))
        }
    }

    /// @notice Get the value of a `Position` type in the form of the underlying uint128.
    /// @param _position The position to get the value of.
    /// @return raw_ The value of the `position` as a uint128 type.
    function raw(Position _position) internal pure returns (uint128 raw_) {
        assembly {
            raw_ := _position
        }
    }
}


// File: interfaces/dispute/IDelayedWETH.sol
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import { ISystemConfig } from "interfaces/L1/ISystemConfig.sol";
import { ISuperchainConfig } from "interfaces/L1/ISuperchainConfig.sol";
import { IProxyAdminOwnedBase } from "interfaces/L1/IProxyAdminOwnedBase.sol";

interface IDelayedWETH is IProxyAdminOwnedBase {
    error ReinitializableBase_ZeroInitVersion();

    struct WithdrawalRequest {
        uint256 amount;
        uint256 timestamp;
    }

    event Initialized(uint8 version);

    fallback() external payable;
    receive() external payable;

    function initVersion() external view returns (uint8);
    function systemConfig() external view returns (ISystemConfig);
    function delay() external view returns (uint256);
    function hold(address _guy) external;
    function hold(address _guy, uint256 _wad) external;
    function initialize(ISystemConfig _systemConfig) external;
    function recover(uint256 _wad) external;
    function unlock(address _guy, uint256 _wad) external;
    function withdraw(address _guy, uint256 _wad) external;
    function withdrawals(address, address) external view returns (uint256 amount, uint256 timestamp);
    function version() external view returns (string memory);
    function withdraw(uint256 _wad) external;

    event Approval(address indexed src, address indexed guy, uint256 wad);

    event Transfer(address indexed src, address indexed dst, uint256 wad);

    event Deposit(address indexed dst, uint256 wad);

    event Withdrawal(address indexed src, uint256 wad);

    function name() external view returns (string memory);

    function symbol() external view returns (string memory);

    function decimals() external view returns (uint8);

    function balanceOf(address src) external view returns (uint256);

    function allowance(address owner, address spender) external view returns (uint256);

    function deposit() external payable;

    function totalSupply() external view returns (uint256);

    function approve(address guy, uint256 wad) external returns (bool);

    function transfer(address dst, uint256 wad) external returns (bool);

    function transferFrom(address src, address dst, uint256 wad) external returns (bool);

    function config() external view returns (ISuperchainConfig);

    function __constructor__(uint256 _delay) external;
}


// File: interfaces/dispute/IBigStepper.sol
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import { IPreimageOracle } from "interfaces/cannon/IPreimageOracle.sol";

/// @title IBigStepper
/// @notice Describes a state machine that can perform a single instruction step, provided a prestate and an optional
///         proof.
/// ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
/// ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣼⠶⢅⠒⢄⢔⣶⡦⣤⡤⠄⣀⠀⠀⠀⠀⠀⠀⠀
/// ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠨⡏⠀⠀⠈⠢⣙⢯⣄⠀⢨⠯⡺⡘⢄⠀⠀⠀⠀⠀
/// ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⣶⡆⠀⠀⠀⠀⠈⠓⠬⡒⠡⣀⢙⡜⡀⠓⠄⠀⠀⠀
/// ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⡷⠿⣧⣀⡀⠀⠀⠀⠀⠀⠀⠉⠣⣞⠩⠥⠀⠼⢄⠀⠀
/// ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⡇⠀⠀⠀⠉⢹⣶⠒⠒⠂⠈⠉⠁⠘⡆⠀⣿⣿⠫⡄⠀
/// ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣠⢶⣤⣀⡀⠀⠀⢸⡿⠀⠀⠀⠀⠀⢀⠞⠀⠀⢡⢨⢀⡄⠀
/// ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣠⡒⣿⢿⡤⠝⡣⠉⠁⠚⠛⠀⠤⠤⣄⡰⠁⠀⠀⠀⠉⠙⢸⠀⠀
/// ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⡤⢯⡌⡿⡇⠘⡷⠀⠁⠀⠀⢀⣰⠢⠲⠛⣈⣸⠦⠤⠶⠴⢬⣐⣊⡂⠀
/// ⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣤⡪⡗⢫⠞⠀⠆⣀⠻⠤⠴⠐⠚⣉⢀⠦⠂⠋⠁⠀⠁⠀⠀⠀⠀⢋⠉⠇⠀
/// ⠀⠀⠀⠀⣀⡤⠐⠒⠘⡹⠉⢸⠇⠸⠀⠀⠀⠀⣀⣤⠴⠚⠉⠈⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠼⠀⣾⠀
/// ⠀⠀⠀⡰⠀⠉⠉⠀⠁⠀⠀⠈⢇⠈⠒⠒⠘⠈⢀⢡⡂⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢰⠀⢸⡄
/// ⠀⠀⠸⣿⣆⠤⢀⡀⠀⠀⠀⠀⢘⡌⠀⠀⣀⣀⣀⡈⣤⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⠀⢸⡇
/// ⠀⠀⢸⣀⠀⠉⠒⠐⠛⠋⠭⠭⠍⠉⠛⠒⠒⠒⠀⠒⠚⠛⠛⠛⠩⠭⠭⠭⠭⠤⠤⠤⠤⠤⠭⠭⠉⠓⡆
/// ⠀⠀⠘⠿⣷⣶⣤⣤⣀⣀⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣠⣤⣄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡇
/// ⠀⠀⠀⠀⠀⠉⠙⠛⠛⠻⠿⢿⣿⣿⣷⣶⣶⣶⣤⣤⣀⣁⣛⣃⣒⠿⠿⠿⠤⠠⠄⠤⠤⢤⣛⣓⣂⣻⡇
/// ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠉⠉⠉⠙⠛⠻⠿⠿⠿⢿⣿⣿⣿⣷⣶⣶⣾⣿⣿⣿⣿⠿⠟⠁
/// ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠈⠉⠉⠉⠉⠁⠀⠀⠀⠀⠀
interface IBigStepper {
    /// @notice Performs the state transition from a given prestate and returns the hash of the post state witness.
    /// @param _stateData The raw opaque prestate data.
    /// @param _proof Opaque proof data, can be used to prove things about the prestate in relation to the state of the
    ///               interface's implementation.
    /// @param _localContext The local key context for the preimage oracle. Optional, can be set as a constant if the
    ///                      implementation only requires one set of local keys.
    /// @return postState_ The hash of the post state witness after the state transition.
    function step(
        bytes calldata _stateData,
        bytes calldata _proof,
        bytes32 _localContext
    )
        external
        returns (bytes32 postState_);

    /// @notice Returns the preimage oracle used by the state machine.
    function oracle() external view returns (IPreimageOracle oracle_);
}


// File: src/libraries/rlp/RLPErrors.sol
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/// @notice The length of an RLP item must be greater than zero to be decodable
error EmptyItem();

/// @notice The decoded item type for list is not a list item
error UnexpectedString();

/// @notice The RLP item has an invalid data remainder
error InvalidDataRemainder();

/// @notice Decoded item type for bytes is not a string item
error UnexpectedList();

/// @notice The length of the content must be greater than the RLP item length
error ContentLengthMismatch();

/// @notice Invalid RLP header for RLP item
error InvalidHeader();


// File: interfaces/cannon/IPreimageOracle.sol
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import { LibKeccak } from "@lib-keccak/LibKeccak.sol";
import { LPPMetaData } from "src/cannon/libraries/CannonTypes.sol";

interface IPreimageOracle {
    struct Leaf {
        bytes input;
        uint256 index;
        bytes32 stateCommitment;
    }

    error ActiveProposal();
    error AlreadyFinalized();
    error AlreadyInitialized();
    error BadProposal();
    error BondTransferFailed();
    error InsufficientBond();
    error InvalidInputSize();
    error InvalidPreimage();
    error InvalidProof();
    error NotEOA();
    error NotInitialized();
    error PartOffsetOOB();
    error PostStateMatches();
    error StatesNotContiguous();
    error TreeSizeOverflow();
    error WrongStartingBlock();

    function KECCAK_TREE_DEPTH() external view returns (uint256);
    function MAX_LEAF_COUNT() external view returns (uint256);
    function MIN_BOND_SIZE() external view returns (uint256);
    function PRECOMPILE_CALL_RESERVED_GAS() external view returns (uint256);
    function addLeavesLPP(
        uint256 _uuid,
        uint256 _inputStartBlock,
        bytes memory _input,
        bytes32[] memory _stateCommitments,
        bool _finalize
    )
        external;
    function challengeFirstLPP(
        address _claimant,
        uint256 _uuid,
        Leaf memory _postState,
        bytes32[] memory _postStateProof
    )
        external;
    function challengeLPP(
        address _claimant,
        uint256 _uuid,
        LibKeccak.StateMatrix memory _stateMatrix,
        Leaf memory _preState,
        bytes32[] memory _preStateProof,
        Leaf memory _postState,
        bytes32[] memory _postStateProof
    )
        external;
    function challengePeriod() external view returns (uint256 challengePeriod_);
    function getTreeRootLPP(address _owner, uint256 _uuid) external view returns (bytes32 treeRoot_);
    function initLPP(uint256 _uuid, uint32 _partOffset, uint32 _claimedSize) external payable;
    function loadBlobPreimagePart(
        uint256 _z,
        uint256 _y,
        bytes memory _commitment,
        bytes memory _proof,
        uint256 _partOffset
    )
        external;
    function loadKeccak256PreimagePart(uint256 _partOffset, bytes memory _preimage) external;
    function loadLocalData(
        uint256 _ident,
        bytes32 _localContext,
        bytes32 _word,
        uint256 _size,
        uint256 _partOffset
    )
        external
        returns (bytes32 key_);
    function loadPrecompilePreimagePart(
        uint256 _partOffset,
        address _precompile,
        uint64 _requiredGas,
        bytes memory _input
    )
        external;
    function loadSha256PreimagePart(uint256 _partOffset, bytes memory _preimage) external;
    function minProposalSize() external view returns (uint256 minProposalSize_);
    function preimageLengths(bytes32) external view returns (uint256);
    function preimagePartOk(bytes32, uint256) external view returns (bool);
    function preimageParts(bytes32, uint256) external view returns (bytes32);
    function proposalBlocks(address, uint256, uint256) external view returns (uint64);
    function proposalBlocksLen(address _claimant, uint256 _uuid) external view returns (uint256 len_);
    function proposalBonds(address, uint256) external view returns (uint256);
    function proposalBranches(address, uint256, uint256) external view returns (bytes32);
    function proposalCount() external view returns (uint256 count_);
    function proposalMetadata(address, uint256) external view returns (LPPMetaData);
    function proposalParts(address, uint256) external view returns (bytes32);
    function proposals(uint256) external view returns (address claimant, uint256 uuid); // nosemgrep:
        // sol-style-return-arg-fmt
    function readPreimage(bytes32 _key, uint256 _offset) external view returns (bytes32 dat_, uint256 datLen_);
    function squeezeLPP(
        address _claimant,
        uint256 _uuid,
        LibKeccak.StateMatrix memory _stateMatrix,
        Leaf memory _preState,
        bytes32[] memory _preStateProof,
        Leaf memory _postState,
        bytes32[] memory _postStateProof
    )
        external;
    function version() external view returns (string memory);
    function zeroHashes(uint256) external view returns (bytes32);

    function __constructor__(uint256 _minProposalSize, uint256 _challengePeriod) external;
}


// File: lib/lib-keccak/contracts/lib/LibKeccak.sol
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/// @title LibKeccak
/// @notice An EVM implementation of the Keccak-f[1600] permutation.
/// @author clabby <https://github.com/clabby>
/// @custom:attribution geohot <https://github.com/geohot>
library LibKeccak {
    /// @notice The block size of the Keccak-f[1600] permutation, 1088 bits (136 bytes).
    uint256 internal constant BLOCK_SIZE_BYTES = 136;

    /// @notice The round constants for the keccak256 hash function. Packed in memory for efficient reading during the
    ///         permutation.
    bytes internal constant ROUND_CONSTANTS = abi.encode(
        0x00000000000000010000000000008082800000000000808a8000000080008000, // r1,r2,r3,r4
        0x000000000000808b000000008000000180000000800080818000000000008009, // r5,r6,r7,r8
        0x000000000000008a00000000000000880000000080008009000000008000000a, // r9,r10,r11,r12
        0x000000008000808b800000000000008b80000000000080898000000000008003, // r13,r14,r15,r16
        0x80000000000080028000000000000080000000000000800a800000008000000a, // r17,r18,r19,r20
        0x8000000080008081800000000000808000000000800000018000000080008008 // r21,r22,r23,r24
    );

    /// @notice A mask for 64-bit values.
    uint64 private constant U64_MASK = 0xFFFFFFFFFFFFFFFF;

    /// @notice The 5x5 state matrix for the keccak-f[1600] permutation.
    struct StateMatrix {
        uint64[25] state;
    }

    /// @notice Performs the Keccak-f[1600] permutation on the given 5x5 state matrix.
    function permutation(StateMatrix memory _stateMatrix) internal pure {
        // Pull the round constants into memory to avoid reallocation in the unrolled permutation loop.
        bytes memory roundConstants = ROUND_CONSTANTS;

        assembly {
            // Add 32 to the state matrix pointer to skip the data location field.
            let stateMatrixPtr := add(_stateMatrix, 0x20)
            let rcPtr := add(roundConstants, 0x20)

            // set a state element in the passed `StateMatrix` struct memory ptr.
            function setStateElem(ptr, idx, data) {
                mstore(add(ptr, shl(0x05, idx)), and(data, U64_MASK))
            }

            // fetch a state element from the passed `StateMatrix` struct memory ptr.
            function stateElem(ptr, idx) -> elem {
                elem := mload(add(ptr, shl(0x05, idx)))
            }

            // 64 bit logical shift
            function shl64(a, b) -> val {
                val := and(shl(a, b), U64_MASK)
            }

            // Performs an indivudual rho + pi computation, to be used in the full `thetaRhoPi` chain.
            function rhoPi(ptr, destIdx, srcIdx, fact, dt) {
                let xs1 := xor(stateElem(ptr, srcIdx), dt)
                let res := xor(shl(fact, xs1), shr(sub(64, fact), xs1))
                setStateElem(ptr, destIdx, res)
            }

            // xor a column in the state matrix
            function xorColumn(ptr, col) -> val {
                val :=
                    xor(
                        xor(xor(stateElem(ptr, col), stateElem(ptr, add(col, 5))), stateElem(ptr, add(col, 10))),
                        xor(stateElem(ptr, add(col, 15)), stateElem(ptr, add(col, 20)))
                    )
            }

            // Performs the `theta`, `rho`, and `pi` steps of the Keccak-f[1600] permutation on
            // the passed `StateMatrix` struct memory ptr.
            function thetaRhoPi(ptr) {
                // Theta
                let C0 := xorColumn(ptr, 0)
                let C1 := xorColumn(ptr, 1)
                let C2 := xorColumn(ptr, 2)
                let C3 := xorColumn(ptr, 3)
                let C4 := xorColumn(ptr, 4)
                let D0 := xor(xor(shl64(1, C1), shr(63, C1)), C4)
                let D1 := xor(xor(shl64(1, C2), shr(63, C2)), C0)
                let D2 := xor(xor(shl64(1, C3), shr(63, C3)), C1)
                let D3 := xor(xor(shl64(1, C4), shr(63, C4)), C2)
                let D4 := xor(xor(shl64(1, C0), shr(63, C0)), C3)

                let xs1 := xor(stateElem(ptr, 1), D1)
                let A1 := xor(shl(1, xs1), shr(63, xs1))

                let _ptr := ptr
                setStateElem(_ptr, 0, xor(stateElem(_ptr, 0), D0))
                rhoPi(_ptr, 1, 6, 44, D1)
                rhoPi(_ptr, 6, 9, 20, D4)
                rhoPi(_ptr, 9, 22, 61, D2)
                rhoPi(_ptr, 22, 14, 39, D4)
                rhoPi(_ptr, 14, 20, 18, D0)
                rhoPi(_ptr, 20, 2, 62, D2)
                rhoPi(_ptr, 2, 12, 43, D2)
                rhoPi(_ptr, 12, 13, 25, D3)
                rhoPi(_ptr, 13, 19, 8, D4)
                rhoPi(_ptr, 19, 23, 56, D3)
                rhoPi(_ptr, 23, 15, 41, D0)
                rhoPi(_ptr, 15, 4, 27, D4)
                rhoPi(_ptr, 4, 24, 14, D4)
                rhoPi(_ptr, 24, 21, 2, D1)
                rhoPi(_ptr, 21, 8, 55, D3)
                rhoPi(_ptr, 8, 16, 45, D1)
                rhoPi(_ptr, 16, 5, 36, D0)
                rhoPi(_ptr, 5, 3, 28, D3)
                rhoPi(_ptr, 3, 18, 21, D3)
                rhoPi(_ptr, 18, 17, 15, D2)
                rhoPi(_ptr, 17, 11, 10, D1)
                rhoPi(_ptr, 11, 7, 6, D2)
                rhoPi(_ptr, 7, 10, 3, D0)
                setStateElem(_ptr, 10, A1)
            }

            // Inner `chi` function, unrolled in `chi` for performance.
            function innerChi(ptr, start) {
                let A0 := stateElem(ptr, start)
                let A1 := stateElem(ptr, add(start, 1))
                let A2 := stateElem(ptr, add(start, 2))
                let A3 := stateElem(ptr, add(start, 3))
                let A4 := stateElem(ptr, add(start, 4))

                setStateElem(ptr, start, xor(A0, and(not(A1), A2)))
                setStateElem(ptr, add(start, 1), xor(A1, and(not(A2), A3)))
                setStateElem(ptr, add(start, 2), xor(A2, and(not(A3), A4)))
                setStateElem(ptr, add(start, 3), xor(A3, and(not(A4), A0)))
                setStateElem(ptr, add(start, 4), xor(A4, and(not(A0), A1)))
            }

            // Performs the `chi` step of the Keccak-f[1600] permutation on the passed `StateMatrix` struct memory ptr
            function chi(ptr) {
                innerChi(ptr, 0)
                innerChi(ptr, 5)
                innerChi(ptr, 10)
                innerChi(ptr, 15)
                innerChi(ptr, 20)
            }

            // Perform the full Keccak-f[1600] permutation on a `StateMatrix` struct memory ptr for a given round.
            function permute(ptr, roundsPtr, round) {
                // Theta, Rho, Pi, Chi
                thetaRhoPi(ptr)
                chi(ptr)
                // Iota
                let roundConst := shr(192, mload(add(roundsPtr, shl(0x03, round))))
                setStateElem(ptr, 0, xor(stateElem(ptr, 0), roundConst))
            }

            // Unroll the permutation loop.
            permute(stateMatrixPtr, rcPtr, 0)
            permute(stateMatrixPtr, rcPtr, 1)
            permute(stateMatrixPtr, rcPtr, 2)
            permute(stateMatrixPtr, rcPtr, 3)
            permute(stateMatrixPtr, rcPtr, 4)
            permute(stateMatrixPtr, rcPtr, 5)
            permute(stateMatrixPtr, rcPtr, 6)
            permute(stateMatrixPtr, rcPtr, 7)
            permute(stateMatrixPtr, rcPtr, 8)
            permute(stateMatrixPtr, rcPtr, 9)
            permute(stateMatrixPtr, rcPtr, 10)
            permute(stateMatrixPtr, rcPtr, 11)
            permute(stateMatrixPtr, rcPtr, 12)
            permute(stateMatrixPtr, rcPtr, 13)
            permute(stateMatrixPtr, rcPtr, 14)
            permute(stateMatrixPtr, rcPtr, 15)
            permute(stateMatrixPtr, rcPtr, 16)
            permute(stateMatrixPtr, rcPtr, 17)
            permute(stateMatrixPtr, rcPtr, 18)
            permute(stateMatrixPtr, rcPtr, 19)
            permute(stateMatrixPtr, rcPtr, 20)
            permute(stateMatrixPtr, rcPtr, 21)
            permute(stateMatrixPtr, rcPtr, 22)
            permute(stateMatrixPtr, rcPtr, 23)
        }
    }

    /// @notice Absorb a fixed-sized block into the sponge.
    function absorb(StateMatrix memory _stateMatrix, bytes memory _input) internal pure {
        assembly {
            // The input must be 1088 bits long.
            if iszero(eq(mload(_input), BLOCK_SIZE_BYTES)) { revert(0, 0) }

            let dataPtr := add(_input, 0x20)
            let statePtr := add(_stateMatrix, 0x20)

            // set a state element in the passed `StateMatrix` struct memory ptr.
            function setStateElem(ptr, idx, data) {
                mstore(add(ptr, shl(0x05, idx)), and(data, U64_MASK))
            }

            // fetch a state element from the passed `StateMatrix` struct memory ptr.
            function stateElem(ptr, idx) -> elem {
                elem := mload(add(ptr, shl(0x05, idx)))
            }

            // Inner sha3 absorb XOR function
            function absorbInner(stateMatrixPtr, inputPtr, idx) {
                let boWord := mload(add(inputPtr, shl(3, idx)))

                let res :=
                    or(
                        or(
                            or(shl(56, byte(7, boWord)), shl(48, byte(6, boWord))),
                            or(shl(40, byte(5, boWord)), shl(32, byte(4, boWord)))
                        ),
                        or(
                            or(shl(24, byte(3, boWord)), shl(16, byte(2, boWord))),
                            or(shl(8, byte(1, boWord)), byte(0, boWord))
                        )
                    )
                setStateElem(stateMatrixPtr, idx, xor(stateElem(stateMatrixPtr, idx), res))
            }

            // Unroll the input XOR loop.
            absorbInner(statePtr, dataPtr, 0)
            absorbInner(statePtr, dataPtr, 1)
            absorbInner(statePtr, dataPtr, 2)
            absorbInner(statePtr, dataPtr, 3)
            absorbInner(statePtr, dataPtr, 4)
            absorbInner(statePtr, dataPtr, 5)
            absorbInner(statePtr, dataPtr, 6)
            absorbInner(statePtr, dataPtr, 7)
            absorbInner(statePtr, dataPtr, 8)
            absorbInner(statePtr, dataPtr, 9)
            absorbInner(statePtr, dataPtr, 10)
            absorbInner(statePtr, dataPtr, 11)
            absorbInner(statePtr, dataPtr, 12)
            absorbInner(statePtr, dataPtr, 13)
            absorbInner(statePtr, dataPtr, 14)
            absorbInner(statePtr, dataPtr, 15)
            absorbInner(statePtr, dataPtr, 16)
        }
    }

    /// @notice Squeezes the final keccak256 digest from the passed `StateMatrix`.
    function squeeze(StateMatrix memory _stateMatrix) internal pure returns (bytes32 hash_) {
        assembly {
            // 64 bit logical shift
            function shl64(a, b) -> val {
                val := and(shl(a, b), U64_MASK)
            }

            // convert a big endian 64-bit value to a little endian 64-bit value.
            function toLE(beVal) -> leVal {
                beVal := or(and(shl64(8, beVal), 0xFF00FF00FF00FF00), and(shr(8, beVal), 0x00FF00FF00FF00FF))
                beVal := or(and(shl64(16, beVal), 0xFFFF0000FFFF0000), and(shr(16, beVal), 0x0000FFFF0000FFFF))
                leVal := or(shl64(32, beVal), shr(32, beVal))
            }

            // fetch a state element from the passed `StateMatrix` struct memory ptr.
            function stateElem(ptr, idx) -> elem {
                elem := mload(add(ptr, shl(0x05, idx)))
            }

            let stateMatrixPtr := add(_stateMatrix, 0x20)
            hash_ :=
                or(
                    or(shl(192, toLE(stateElem(stateMatrixPtr, 0))), shl(128, toLE(stateElem(stateMatrixPtr, 1)))),
                    or(shl(64, toLE(stateElem(stateMatrixPtr, 2))), toLE(stateElem(stateMatrixPtr, 3)))
                )
        }
    }

    /// @notice Pads input data to an even multiple of the Keccak-f[1600] permutation block size, 1088 bits (136 bytes).
    function pad(bytes calldata _data) internal pure returns (bytes memory padded_) {
        assembly {
            padded_ := mload(0x40)

            // Grab the original length of `_data`
            let len := _data.length

            let dataPtr := add(padded_, 0x20)
            let endPtr := add(dataPtr, len)

            // Copy the data into memory.
            calldatacopy(dataPtr, _data.offset, len)

            let modBlockSize := mod(len, BLOCK_SIZE_BYTES)
            switch modBlockSize
            case false {
                // Clean the full padding block. It is possible that this memory is dirty, since solidity sometimes does
                // not update the free memory pointer when allocating memory, for example with external calls. To do
                // this, we read out-of-bounds from the calldata, which will always return 0 bytes.
                calldatacopy(endPtr, calldatasize(), BLOCK_SIZE_BYTES)

                // If the input is a perfect multiple of the block size, then we add a full extra block of padding.
                mstore8(endPtr, 0x01)
                mstore8(sub(add(endPtr, BLOCK_SIZE_BYTES), 0x01), 0x80)

                // Update the length of the data to include the padding.
                mstore(padded_, add(len, BLOCK_SIZE_BYTES))
            }
            default {
                // If the input is not a perfect multiple of the block size, then we add a partial block of padding.
                // This should entail a set bit after the input, followed by as many zero bits as necessary to fill
                // the block, followed by a single 1 bit in the lowest-order bit of the final block.

                let remaining := sub(BLOCK_SIZE_BYTES, modBlockSize)
                let newLen := add(len, remaining)
                let paddedEndPtr := add(dataPtr, newLen)

                // Clean the remainder to ensure that the intermediate data between the padding bits is 0. It is
                // possible that this memory is dirty, since solidity sometimes does not update the free memory pointer
                // when allocating memory, for example with external calls. To do this, we read out-of-bounds from the
                // calldata, which will always return 0 bytes.
                let partialRemainder := sub(paddedEndPtr, endPtr)
                calldatacopy(endPtr, calldatasize(), partialRemainder)

                // Store the padding bits.
                mstore8(sub(paddedEndPtr, 0x01), 0x80)
                mstore8(endPtr, or(byte(0x00, mload(endPtr)), 0x01))

                // Update the length of the data to include the padding. The length should be a multiple of the
                // block size after this.
                mstore(padded_, newLen)
            }

            // Update the free memory pointer.
            mstore(0x40, add(padded_, and(add(mload(padded_), 0x3F), not(0x1F))))
        }
    }

    /// @notice Pads input data to an even multiple of the Keccak-f[1600] permutation block size, 1088 bits (136 bytes).
    function padMemory(bytes memory _data) internal pure returns (bytes memory padded_) {
        assembly {
            padded_ := mload(0x40)

            // Grab the original length of `_data`
            let len := mload(_data)

            let dataPtr := add(padded_, 0x20)
            let endPtr := add(dataPtr, len)

            // Copy the data.
            let originalDataPtr := add(_data, 0x20)
            for { let i := 0x00 } lt(i, len) { i := add(i, 0x20) } {
                mstore(add(dataPtr, i), mload(add(originalDataPtr, i)))
            }

            let modBlockSize := mod(len, BLOCK_SIZE_BYTES)
            switch modBlockSize
            case false {
                // Clean the full padding block. It is possible that this memory is dirty, since solidity sometimes does
                // not update the free memory pointer when allocating memory, for example with external calls. To do
                // this, we read out-of-bounds from the calldata, which will always return 0 bytes.
                calldatacopy(endPtr, calldatasize(), BLOCK_SIZE_BYTES)

                // If the input is a perfect multiple of the block size, then we add a full extra block of padding.
                mstore8(sub(add(endPtr, BLOCK_SIZE_BYTES), 0x01), 0x80)
                mstore8(endPtr, 0x01)

                // Update the length of the data to include the padding.
                mstore(padded_, add(len, BLOCK_SIZE_BYTES))
            }
            default {
                // If the input is not a perfect multiple of the block size, then we add a partial block of padding.
                // This should entail a set bit after the input, followed by as many zero bits as necessary to fill
                // the block, followed by a single 1 bit in the lowest-order bit of the final block.

                let remaining := sub(BLOCK_SIZE_BYTES, modBlockSize)
                let newLen := add(len, remaining)
                let paddedEndPtr := add(dataPtr, newLen)

                // Clean the remainder to ensure that the intermediate data between the padding bits is 0. It is
                // possible that this memory is dirty, since solidity sometimes does not update the free memory pointer
                // when allocating memory, for example with external calls. To do this, we read out-of-bounds from the
                // calldata, which will always return 0 bytes.
                let partialRemainder := sub(paddedEndPtr, endPtr)
                calldatacopy(endPtr, calldatasize(), partialRemainder)

                // Store the padding bits.
                mstore8(sub(paddedEndPtr, 0x01), 0x80)
                mstore8(endPtr, or(byte(0x00, mload(endPtr)), 0x01))

                // Update the length of the data to include the padding. The length should be a multiple of the
                // block size after this.
                mstore(padded_, newLen)
            }

            // Update the free memory pointer.
            mstore(0x40, add(padded_, and(add(mload(padded_), 0x3F), not(0x1F))))
        }
    }
}


// File: src/cannon/libraries/CannonTypes.sol
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

using LPPMetadataLib for LPPMetaData global;

/// @notice Packed LPP metadata.
/// ┌─────────────┬────────────────────────────────────────────┐
/// │ Bit Offsets │                Description                 │
/// ├─────────────┼────────────────────────────────────────────┤
/// │ [0, 64)     │ Timestamp (Finalized - All data available) │
/// │ [64, 96)    │ Part Offset                                │
/// │ [96, 128)   │ Claimed Size                               │
/// │ [128, 160)  │ Blocks Processed (Inclusive of Padding)    │
/// │ [160, 192)  │ Bytes Processed (Non-inclusive of Padding) │
/// │ [192, 256)  │ Countered                                  │
/// └─────────────┴────────────────────────────────────────────┘
type LPPMetaData is bytes32;

/// @notice LPP metadata UDT extension functions.
library LPPMetadataLib {
    uint256 private constant U64_MASK = 0xFFFFFFFFFFFFFFFF;
    uint256 private constant U32_MASK = 0xFFFFFFFF;

    function setTimestamp(LPPMetaData _self, uint64 _timestamp) internal pure returns (LPPMetaData self_) {
        assembly {
            self_ := or(shl(192, _timestamp), and(_self, not(shl(192, U64_MASK))))
        }
    }

    function setPartOffset(LPPMetaData _self, uint32 _partOffset) internal pure returns (LPPMetaData self_) {
        assembly {
            self_ := or(shl(160, _partOffset), and(_self, not(shl(160, U32_MASK))))
        }
    }

    function setClaimedSize(LPPMetaData _self, uint32 _claimedSize) internal pure returns (LPPMetaData self_) {
        assembly {
            self_ := or(shl(128, _claimedSize), and(_self, not(shl(128, U32_MASK))))
        }
    }

    function setBlocksProcessed(LPPMetaData _self, uint32 _blocksProcessed) internal pure returns (LPPMetaData self_) {
        assembly {
            self_ := or(shl(96, _blocksProcessed), and(_self, not(shl(96, U32_MASK))))
        }
    }

    function setBytesProcessed(LPPMetaData _self, uint32 _bytesProcessed) internal pure returns (LPPMetaData self_) {
        assembly {
            self_ := or(shl(64, _bytesProcessed), and(_self, not(shl(64, U32_MASK))))
        }
    }

    function setCountered(LPPMetaData _self, bool _countered) internal pure returns (LPPMetaData self_) {
        assembly {
            self_ := or(_countered, and(_self, not(U64_MASK)))
        }
    }

    function timestamp(LPPMetaData _self) internal pure returns (uint64 timestamp_) {
        assembly {
            timestamp_ := shr(192, _self)
        }
    }

    function partOffset(LPPMetaData _self) internal pure returns (uint64 partOffset_) {
        assembly {
            partOffset_ := and(shr(160, _self), U32_MASK)
        }
    }

    function claimedSize(LPPMetaData _self) internal pure returns (uint32 claimedSize_) {
        assembly {
            claimedSize_ := and(shr(128, _self), U32_MASK)
        }
    }

    function blocksProcessed(LPPMetaData _self) internal pure returns (uint32 blocksProcessed_) {
        assembly {
            blocksProcessed_ := and(shr(96, _self), U32_MASK)
        }
    }

    function bytesProcessed(LPPMetaData _self) internal pure returns (uint32 bytesProcessed_) {
        assembly {
            bytesProcessed_ := and(shr(64, _self), U32_MASK)
        }
    }

    function countered(LPPMetaData _self) internal pure returns (bool countered_) {
        assembly {
            countered_ := and(_self, U64_MASK)
        }
    }
}
