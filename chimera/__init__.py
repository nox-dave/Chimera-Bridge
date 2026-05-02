"""
Chimera — on-chain fraud analysis toolkit.

Traces cryptocurrency fund flows, identifies addresses linked to contracts under
technical assessment, and generates intelligence profiles to support financial
crime investigations. contractHunter supplies contract assessments; chimera.bridge
correlates them with on-chain counterparties; walletHunter enriches addresses.
"""

from .bridge import ContractWalletBridge, BridgeResult, ExposedWallet

__all__ = [
    "ContractWalletBridge",
    "BridgeResult",
    "ExposedWallet",
]
