import requests
import os
import time
from typing import Dict, List, Any, Optional
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()

class EtherscanClient:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('ETHERSCAN_API_KEY', '')
        self.base_url = 'https://api.etherscan.io/v2/api'
    
    def _request(self, params: Dict) -> Any:
        params['apikey'] = self.api_key
        params['chainid'] = 1
        try:
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data.get('status') == '1':
                return data.get('result', [])
            elif data.get('status') == '0':
                message = data.get('message', '')
                if 'deprecated' in message.lower() or 'v2' in message.lower():
                    return []
                return []
            return []
        except Exception as e:
            return []
    
    def get_block_by_number(self, block_num: int) -> Optional[Dict]:
        params = {
            'chainid': 1,
            'module': 'proxy',
            'action': 'eth_getBlockByNumber',
            'tag': hex(block_num),
            'boolean': 'true',
            'apikey': self.api_key
        }
        try:
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data.get('status') == '0':
                message = data.get('message', '')
                if 'deprecated' in message.lower():
                    return None
            if data.get('result'):
                return data.get('result')
            return None
        except:
            return None
    
    def get_latest_block_number(self) -> int:
        params = {
            'chainid': 1,
            'module': 'proxy',
            'action': 'eth_blockNumber',
            'apikey': self.api_key
        }
        try:
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data.get('status') == '0':
                return 0
            result = data.get('result')
            if result:
                return int(result, 16)
            return 0
        except:
            return 0
    
    def get_transactions(self, address: str, limit: int = 1000) -> List[Dict]:
        params = {
            'module': 'account',
            'action': 'txlist',
            'address': address,
            'startblock': 0,
            'endblock': 99999999,
            'page': 1,
            'offset': limit,
            'sort': 'desc'
        }
        txs = self._request(params)
        return txs if isinstance(txs, list) else []
    
    def get_internal_transactions(self, address: str, limit: int = 1000) -> List[Dict]:
        params = {
            'module': 'account',
            'action': 'txlistinternal',
            'address': address,
            'startblock': 0,
            'endblock': 99999999,
            'page': 1,
            'offset': limit,
            'sort': 'desc'
        }
        txs = self._request(params)
        return txs if isinstance(txs, list) else []
    
    def get_token_transfers(self, address: str, limit: int = 1000) -> List[Dict]:
        params = {
            'module': 'account',
            'action': 'tokentx',
            'address': address,
            'startblock': 0,
            'endblock': 99999999,
            'page': 1,
            'offset': limit,
            'sort': 'desc'
        }
        txs = self._request(params)
        return txs if isinstance(txs, list) else []
    
    def get_nft_transfers(self, address: str, limit: int = 1000) -> List[Dict]:
        params = {
            'module': 'account',
            'action': 'tokennfttx',
            'address': address,
            'startblock': 0,
            'endblock': 99999999,
            'page': 1,
            'offset': limit,
            'sort': 'desc'
        }
        txs = self._request(params)
        return txs if isinstance(txs, list) else []
    
    def get_token_balances(self, address: str) -> List[Dict]:
        params = {
            'module': 'account',
            'action': 'tokenlist',
            'address': address
        }
        tokens = self._request(params)
        return tokens if isinstance(tokens, list) else []
    
    def get_token_balance(self, address: str, token_address: str) -> float:
        params = {
            'module': 'account',
            'action': 'tokenbalance',
            'contractaddress': token_address,
            'address': address,
            'tag': 'latest'
        }
        result = self._request(params)
        if result and isinstance(result, str):
            try:
                return float(result)
            except ValueError:
                return 0.0
        return 0.0
    
    def get_large_token_transfers(self, token_address: str, min_value_usd: float, decimals: int, price: float, limit: int = 1000) -> List[Dict]:
        params = {
            'module': 'account',
            'action': 'tokentx',
            'contractaddress': token_address,
            'startblock': 0,
            'endblock': 99999999,
            'page': 1,
            'offset': limit,
            'sort': 'desc'
        }
        txs = self._request(params)
        if not isinstance(txs, list) or len(txs) == 0:
            return []
        
        min_value_raw = int((min_value_usd / price) * (10 ** decimals))
        large_transfers = []
        
        for tx in txs:
            value_raw = tx.get('value', '0')
            if value_raw:
                try:
                    value = int(value_raw)
                    if value >= min_value_raw:
                        large_transfers.append(tx)
                except:
                    pass
        
        return large_transfers
    
    def is_contract(self, address: str) -> bool:
        params = {
            'chainid': 1,
            'module': 'proxy',
            'action': 'eth_getCode',
            'address': address,
            'tag': 'latest',
            'apikey': self.api_key
        }
        try:
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            code = data.get('result', '0x')
            return code != '0x' and len(code) > 2
        except:
            return False


class AlchemyClient:
    def __init__(self):
        self.alchemy_base = 'https://eth-mainnet.g.alchemy.com/v2'
        self.alchemy_key = os.getenv('ALCHEMY_API_KEY', '')
    
    def request(self, method: str, params: List) -> Any:
        if not self.alchemy_key:
            return None
        url = f"{self.alchemy_base}/{self.alchemy_key}"
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params
        }
        try:
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            return response.json().get('result')
        except:
            return None


class RPCClient:
    def __init__(self):
        alchemy_key = os.getenv('ALCHEMY_API_KEY', '')
        if alchemy_key:
            rpc_url = f'https://eth-mainnet.g.alchemy.com/v2/{alchemy_key}'
        else:
            rpc_url = os.getenv('RPC_URL', 'https://eth.llamarpc.com')
        
        try:
            self.w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={'timeout': 10}))
            if not self.w3.is_connected():
                if alchemy_key:
                    self.w3 = Web3(Web3.HTTPProvider('https://eth.llamarpc.com', request_kwargs={'timeout': 10}))
                else:
                    self.w3 = Web3(Web3.HTTPProvider('https://eth.llamarpc.com', request_kwargs={'timeout': 10}))
        except:
            self.w3 = Web3(Web3.HTTPProvider('https://eth.llamarpc.com', request_kwargs={'timeout': 10}))
    
    def get_balance(self, address: str) -> Dict:
        try:
            balance_wei = self.w3.eth.get_balance(Web3.to_checksum_address(address))
            balance_eth = balance_wei / 1e18
            return {'eth': balance_eth, 'wei': balance_wei}
        except:
            return {'eth': 0, 'wei': 0}
    
    def get_token_balance(self, address: str, token_address: str, decimals: int = 18) -> float:
        try:
            checksum_address = Web3.to_checksum_address(address)
            checksum_token = Web3.to_checksum_address(token_address)
            
            erc20_abi = [
                {
                    "constant": True,
                    "inputs": [{"name": "_owner", "type": "address"}],
                    "name": "balanceOf",
                    "outputs": [{"name": "balance", "type": "uint256"}],
                    "type": "function"
                },
                {
                    "constant": True,
                    "inputs": [],
                    "name": "decimals",
                    "outputs": [{"name": "", "type": "uint8"}],
                    "type": "function"
                }
            ]
            
            contract = self.w3.eth.contract(address=checksum_token, abi=erc20_abi)
            balance = contract.functions.balanceOf(checksum_address).call()
            
            try:
                actual_decimals = contract.functions.decimals().call()
                decimals = actual_decimals
            except:
                pass
            
            return float(balance) / (10 ** decimals)
        except:
            return 0.0
    
    def is_contract(self, address: str) -> bool:
        try:
            code = self.w3.eth.get_code(Web3.to_checksum_address(address))
            return code and code != b''
        except:
            return False
    
    def get_latest_block(self) -> int:
        try:
            return self.w3.eth.block_number
        except:
            return 0
    
    def get_block_transactions(self, block_num: int) -> List:
        try:
            block = self.w3.eth.get_block(block_num, full_transactions=True, timeout=10)
            return block.transactions if block else []
        except Exception as e:
            return []

