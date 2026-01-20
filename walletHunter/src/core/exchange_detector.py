from typing import Optional, Set, List
from ..config import KNOWN_EXCHANGE_ADDRESSES, EXCHANGE_TX_COUNT_THRESHOLD, BURN_ADDRESSES
from .api_clients import EtherscanClient


class ExchangeDetector:
    def __init__(self, etherscan_client: EtherscanClient):
        self.etherscan = etherscan_client
        self._known_exchanges_lower = {k.lower(): v for k, v in KNOWN_EXCHANGE_ADDRESSES.items()}
        self._burn_addresses_lower = {addr.lower() for addr in BURN_ADDRESSES}
        self._cache = {}
    
    def get_transaction_count(self, address: str) -> int:
        if address.lower() in self._cache:
            return self._cache[address.lower()].get('tx_count', 0)
        
        txs = self.etherscan.get_transactions(address, limit=1000)
        if isinstance(txs, list):
            count = 100001 if len(txs) >= 1000 else len(txs)
            if address.lower() not in self._cache:
                self._cache[address.lower()] = {}
            self._cache[address.lower()]['tx_count'] = count
            return count
        return 0
    
    def get_transactions(self, address: str, limit: int = 100) -> List[dict]:
        if address.lower() in self._cache and 'transactions' in self._cache[address.lower()]:
            return self._cache[address.lower()]['transactions']
        
        txs = self.etherscan.get_transactions(address, limit=limit)
        if address.lower() not in self._cache:
            self._cache[address.lower()] = {}
        self._cache[address.lower()]['transactions'] = txs
        return txs
    
    def get_funding_source(self, address: str, transactions: List[dict]) -> Optional[str]:
        if not transactions:
            return None
        
        first_tx = transactions[-1]
        if first_tx.get('from'):
            return first_tx['from'].lower()
        return None
    
    def get_counterparties(self, transactions: List[dict]) -> Set[str]:
        counterparties = set()
        for tx in transactions:
            from_addr = tx.get('from', '').lower()
            to_addr = tx.get('to', '').lower()
            if from_addr and len(from_addr) == 42:
                counterparties.add(from_addr)
            if to_addr and len(to_addr) == 42:
                counterparties.add(to_addr)
        return counterparties
    
    def is_burn_address(self, address: str) -> bool:
        return address.lower() in self._burn_addresses_lower
    
    def is_known_exchange(self, address: str) -> bool:
        return address.lower() in self._known_exchanges_lower
    
    def is_institutional_wallet(self, address: str, transactions: Optional[List[dict]] = None) -> bool:
        address_lower = address.lower()
        
        if address_lower in self._burn_addresses_lower:
            return True
        
        if address_lower in self._known_exchanges_lower:
            return True
        
        if transactions is None:
            transactions = self.get_transactions(address, limit=100)
        
        if not transactions:
            return False
        
        tx_count = len(transactions)
        if tx_count >= 1000:
            tx_count = self.get_transaction_count(address)
        
        if tx_count > EXCHANGE_TX_COUNT_THRESHOLD:
            return True
        
        funder = self.get_funding_source(address, transactions)
        if funder and self.is_known_exchange(funder):
            return True
        
        counterparties = self.get_counterparties(transactions)
        if len(counterparties) > 0:
            exchange_counterparties = sum(1 for c in counterparties if self.is_known_exchange(c))
            exchange_ratio = exchange_counterparties / len(counterparties)
            if exchange_ratio > 0.8:
                return True
        
        return False
    
    def is_likely_exchange(self, address: str, tx_count: Optional[int] = None) -> bool:
        return self.is_institutional_wallet(address)

