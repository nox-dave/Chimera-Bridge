"""
Chimera Configuration

Shared settings between contractHunter and walletHunter.
"""

import os
from pathlib import Path


ETHERSCAN_API_KEY = os.environ.get("ETHERSCAN_API_KEY", "")
ALCHEMY_API_KEY = os.environ.get("ALCHEMY_API_KEY", "")
INFURA_API_KEY = os.environ.get("INFURA_API_KEY", "")

CHIMERA_ROOT = Path(__file__).parent
PROJECT_ROOT = CHIMERA_ROOT.parent

CONTRACT_HUNTER_DIR = PROJECT_ROOT / "contractHunter"
WALLET_HUNTER_DIR = PROJECT_ROOT / "walletHunter"

CHIMERA_REPORTS_DIR = CHIMERA_ROOT / "reports"
CHIMERA_REPORTS_DIR.mkdir(exist_ok=True)

CHAINS = {
    "ethereum": {
        "chain_id": 1,
        "rpc": f"https://eth-mainnet.g.alchemy.com/v2/{ALCHEMY_API_KEY}" if ALCHEMY_API_KEY else "https://eth.llamarpc.com",
        "explorer": "https://etherscan.io",
        "explorer_api": "https://api.etherscan.io/v2/api",
    },
    "polygon": {
        "chain_id": 137,
        "rpc": f"https://polygon-mainnet.g.alchemy.com/v2/{ALCHEMY_API_KEY}" if ALCHEMY_API_KEY else "https://polygon.llamarpc.com",
        "explorer": "https://polygonscan.com",
        "explorer_api": "https://api.etherscan.io/v2/api",
    },
    "arbitrum": {
        "chain_id": 42161,
        "rpc": f"https://arb-mainnet.g.alchemy.com/v2/{ALCHEMY_API_KEY}" if ALCHEMY_API_KEY else "https://arbitrum.llamarpc.com",
        "explorer": "https://arbiscan.io",
        "explorer_api": "https://api.etherscan.io/v2/api",
    },
    "optimism": {
        "chain_id": 10,
        "rpc": f"https://opt-mainnet.g.alchemy.com/v2/{ALCHEMY_API_KEY}" if ALCHEMY_API_KEY else "https://optimism.llamarpc.com",
        "explorer": "https://optimistic.etherscan.io",
        "explorer_api": "https://api.etherscan.io/v2/api",
    },
    "base": {
        "chain_id": 8453,
        "rpc": f"https://base-mainnet.g.alchemy.com/v2/{ALCHEMY_API_KEY}" if ALCHEMY_API_KEY else "https://base.llamarpc.com",
        "explorer": "https://basescan.org",
        "explorer_api": "https://api.etherscan.io/v2/api",
    },
}

MIN_EXPOSURE_USD = 1000
HIGH_VALUE_THRESHOLD = 100_000
WHALE_THRESHOLD = 1_000_000

ETHERSCAN_RATE_LIMIT = 5
RPC_RATE_LIMIT = 10
