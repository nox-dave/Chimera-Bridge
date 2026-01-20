"""
Chimera - Bridge between contractHunter and walletHunter

Flow:
    contractHunter (finds vulnerable contracts)
        ↓
    chimera/bridge.py (queries exposed wallets)
        ↓
    walletHunter (profiles those wallets)
        ↓
    Exposure Report (wallets at risk)
"""

from .bridge import ContractWalletBridge, ExposureReport, ExposedWallet

__all__ = [
    "ContractWalletBridge",
    "ExposureReport", 
    "ExposedWallet",
]
