import sys
from datetime import datetime
from typing import Dict, Optional
from .api_clients import EtherscanClient, RPCClient
from .exchange_detector import ExchangeDetector
from .transaction_analyzer import TransactionAnalyzer
from .whale_finder import WhaleFinder


class WalletProfiler:
    def __init__(self, api_key: Optional[str] = None):
        self.etherscan = EtherscanClient(api_key)
        self.rpc = RPCClient()
        self.exchange_detector = ExchangeDetector(self.etherscan)
        self.transaction_analyzer = TransactionAnalyzer()
        self.whale_finder = WhaleFinder(self.etherscan, self.rpc, self.exchange_detector)
    
    def get_balance(self, address: str) -> Dict:
        return self.rpc.get_balance(address)
    
    def get_transactions(self, address: str, limit: int = 1000) -> list:
        return self.etherscan.get_transactions(address, limit)
    
    def get_internal_transactions(self, address: str, limit: int = 1000) -> list:
        return self.etherscan.get_internal_transactions(address, limit)
    
    def get_token_transfers(self, address: str, limit: int = 1000) -> list:
        return self.etherscan.get_token_transfers(address, limit)
    
    def get_nft_transfers(self, address: str, limit: int = 1000) -> list:
        return self.etherscan.get_nft_transfers(address, limit)
    
    def get_token_balances(self, address: str) -> list:
        return self.etherscan.get_token_balances(address)
    
    def is_likely_exchange(self, address: str) -> bool:
        return self.exchange_detector.is_likely_exchange(address)
    
    def find_high_value_wallets(self, min_balance_usd: float = 100000, limit: int = 10) -> list:
        return self.whale_finder.find_high_value_wallets(min_balance_usd, limit)
    
    def generate_profile(self, address: str) -> Dict:
        address = address.lower()
        
        print(f"Analyzing wallet: {address}", file=sys.stderr)
        
        balance = self.get_balance(address)
        print("  - Fetching transactions...", file=sys.stderr)
        txs = self.get_transactions(address, limit=1000)
        print("  - Fetching internal transactions...", file=sys.stderr)
        internal_txs = self.get_internal_transactions(address, limit=500)
        print("  - Fetching token transfers...", file=sys.stderr)
        token_txs = self.get_token_transfers(address, limit=1000)
        print("  - Fetching NFT transfers...", file=sys.stderr)
        nft_txs = self.get_nft_transfers(address, limit=500)
        print("  - Fetching token balances...", file=sys.stderr)
        token_balances = self.get_token_balances(address)
        
        print("  - Analyzing patterns...", file=sys.stderr)
        tx_patterns = self.transaction_analyzer.analyze_patterns(txs)
        token_activity = self.transaction_analyzer.analyze_token_activity(token_txs)
        nft_activity = self.transaction_analyzer.analyze_nft_activity(nft_txs)
        contracts = self.transaction_analyzer.identify_contracts(txs)
        
        profile = {
            'address': address,
            'balance_eth': balance['eth'],
            'transaction_analysis': tx_patterns,
            'token_activity': token_activity,
            'nft_activity': nft_activity,
            'token_balances': token_balances[:20],
            'top_contracts': contracts,
            'total_internal_txs': len(internal_txs),
            'analysis_timestamp': datetime.now().isoformat()
        }
        
        return profile
