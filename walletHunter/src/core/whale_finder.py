import sys
import time
from typing import Dict, List, Set
from concurrent.futures import ThreadPoolExecutor, as_completed
from web3 import Web3
from ..config import (
    MAJOR_TOKENS, KNOWN_MIXERS, SEED_WHALES,
    DEFI_PROTOCOLS, BLUE_CHIP_NFTS, GOVERNANCE_TOKENS, EARLY_BLOCKS
)
from .api_clients import EtherscanClient, RPCClient
from .exchange_detector import ExchangeDetector


class WhaleFinder:
    def __init__(self, etherscan_client: EtherscanClient, rpc_client: RPCClient, exchange_detector: ExchangeDetector):
        self.etherscan = etherscan_client
        self.rpc = rpc_client
        self.exchange_detector = exchange_detector
    
    def is_institutional(self, address: str) -> bool:
        transactions = self.exchange_detector.get_transactions(address, limit=100)
        return self.exchange_detector.is_institutional_wallet(address, transactions)
    
    def get_nft_balance(self, address: str, nft_contract: str) -> int:
        try:
            erc721_abi = [
                {
                    "constant": True,
                    "inputs": [{"name": "_owner", "type": "address"}],
                    "name": "balanceOf",
                    "outputs": [{"name": "", "type": "uint256"}],
                    "type": "function"
                }
            ]
            checksum_address = Web3.to_checksum_address(address)
            checksum_contract = Web3.to_checksum_address(nft_contract)
            contract = self.rpc.w3.eth.contract(address=checksum_contract, abi=erc721_abi)
            balance = contract.functions.balanceOf(checksum_address).call()
            return balance
        except:
            return 0
    
    def find_defi_power_users(self, min_position_usd: float = 100000) -> List[Dict]:
        candidates = []
        
        protocol_count = sum(len(p.get('aTokens', [])) for p in DEFI_PROTOCOLS.values())
        current = 0
        
        for protocol_name, protocol_info in DEFI_PROTOCOLS.items():
            if 'aTokens' in protocol_info:
                for a_token_addr in protocol_info['aTokens']:
                    current += 1
                    if current % 3 == 0:
                        print(f"      Checking DeFi token {current}/{protocol_count}...", file=sys.stderr)
                    
                    try:
                        transfers = self.etherscan.get_large_token_transfers(
                            a_token_addr,
                            min_position_usd * 0.1,
                            18,
                            2000.0,
                            limit=100
                        )
                        seen_addresses = set()
                        for tx in transfers[:30]:
                            to_addr = tx.get('to', '').lower()
                            from_addr = tx.get('from', '').lower()
                            
                            for addr in [to_addr, from_addr]:
                                if addr and len(addr) == 42 and addr not in seen_addresses:
                                    seen_addresses.add(addr)
                                    if self.rpc.is_contract(addr):
                                        continue
                                    
                                    balance = self.rpc.get_token_balance(addr, a_token_addr, 18)
                                    if balance * 2000 >= min_position_usd:
                                        if not self.is_institutional(addr):
                                            candidates.append({
                                                'address': addr,
                                                'protocol': protocol_name,
                                                'position_type': 'lending',
                                                'position_value_usd': balance * 2000
                                            })
                    except:
                        continue
        
        return candidates
    
    def find_nft_whales(self, min_nfts: int = 2) -> List[Dict]:
        candidates = []
        seen_addresses = set()
        
        print(f"    Scanning {len(BLUE_CHIP_NFTS)} NFT collections...", file=sys.stderr)
        
        for idx, (collection_name, contract_addr) in enumerate(BLUE_CHIP_NFTS.items(), 1):
            print(f"      [{idx}/{len(BLUE_CHIP_NFTS)}] Checking {collection_name}...", file=sys.stderr)
            try:
                contract_addr_lower = contract_addr.lower()
                latest_block = self.rpc.get_latest_block()
                start_block = max(latest_block - 500, 0)
                
                potential_addresses = set()
                scanned = 0
                max_blocks = 10
                
                for block_num in range(start_block, latest_block, 100):
                    scanned += 1
                    if scanned > max_blocks:
                        break
                    
                    try:
                        transactions = self.rpc.get_block_transactions(block_num)
                        for tx in transactions:
                            to_addr = None
                            if hasattr(tx, 'to') and tx.to:
                                to_addr = tx.to.lower() if isinstance(tx.to, str) else str(tx.to).lower()
                            elif isinstance(tx, dict):
                                to_addr = tx.get('to', '').lower()
                            
                            if to_addr == contract_addr_lower:
                                from_addr = None
                                if hasattr(tx, 'from_'):
                                    from_addr = tx.from_
                                elif isinstance(tx, dict):
                                    from_addr = tx.get('from')
                                
                                if from_addr:
                                    addr = from_addr.lower() if isinstance(from_addr, str) else str(from_addr).lower()
                                    if addr and len(addr) == 42 and addr != '0x0000000000000000000000000000000000000000':
                                        potential_addresses.add(addr)
                    except:
                        continue
                
                checked = 0
                for addr in list(potential_addresses)[:20]:
                    if addr in seen_addresses:
                        continue
                    seen_addresses.add(addr)
                    checked += 1
                    
                    if self.rpc.is_contract(addr):
                        continue
                    
                    nft_balance = self.get_nft_balance(addr, contract_addr)
                    if nft_balance >= min_nfts:
                        if not self.is_institutional(addr):
                            candidates.append({
                                'address': addr,
                                'collection': collection_name,
                                'nft_count': nft_balance
                            })
            except Exception as e:
                print(f"        Error: {str(e)[:50]}", file=sys.stderr)
                continue
        
        return candidates
    
    def find_dao_participants(self, min_tokens: float = 1000) -> List[Dict]:
        candidates = []
        
        for idx, (token_name, token_info) in enumerate(GOVERNANCE_TOKENS.items(), 1):
            print(f"      [{idx}/{len(GOVERNANCE_TOKENS)}] Checking {token_name} holders...", file=sys.stderr)
            try:
                token_transfers = self.etherscan.get_token_transfers(token_info['address'], limit=200)
                holders = set()
                
                for tx in token_transfers[:100]:
                    to_addr = tx.get('to', '').lower()
                    from_addr = tx.get('from', '').lower()
                    
                    for addr in [to_addr, from_addr]:
                        if addr and len(addr) == 42:
                            holders.add(addr)
                
                checked = 0
                for addr in list(holders)[:30]:
                    checked += 1
                    if self.rpc.is_contract(addr):
                        continue
                    
                    balance = self.rpc.get_token_balance(addr, token_info['address'], token_info['decimals'])
                    if balance >= min_tokens:
                        if not self.is_institutional(addr):
                            txs = self.etherscan.get_transactions(addr, limit=10)
                            has_recent_activity = len(txs) > 0 and int(txs[0].get('timeStamp', 0)) > 0
                            
                            if has_recent_activity:
                                candidates.append({
                                    'address': addr,
                                    'dao': token_name,
                                    'token_balance': balance
                                })
            except:
                continue
        
        return candidates
    
    def find_early_adopters(self) -> List[Dict]:
        candidates = []
        
        print("    Skipping early adopter scan (too slow, use --early-adopters flag to enable)", file=sys.stderr)
        
        return candidates
    
    def _fetch_block_candidates(self, block_num: int, min_eth: float) -> List[str]:
        candidates = []
        try:
            block = self.rpc.w3.eth.get_block(block_num, full_transactions=True)
            if not block or not block.transactions:
                return candidates
            
            for tx in block.transactions:
                try:
                    value_wei = tx['value']
                    value_eth = float(self.rpc.w3.from_wei(value_wei, 'ether'))
                    
                    if value_eth >= min_eth:
                        from_addr = tx['from'].lower() if tx['from'] else None
                        to_addr = tx['to'].lower() if tx['to'] else None
                        
                        for addr in [from_addr, to_addr]:
                            if addr and len(addr) == 42:
                                if addr not in KNOWN_MIXERS:
                                    if not self.exchange_detector.is_known_exchange(addr) and not self.exchange_detector.is_burn_address(addr):
                                        candidates.append(addr)
                except (KeyError, TypeError, AttributeError):
                    continue
        except:
            pass
        return candidates
    
    def find_candidates_from_large_transfers(self, min_balance_usd: float) -> Set[str]:
        candidate_addresses = set()
        
        print("  - Strategy 5: RPC block scanning (parallel)...", file=sys.stderr)
        try:
            latest_block = self.rpc.get_latest_block()
            if latest_block == 0:
                print("      Error: Could not get latest block", file=sys.stderr)
                return candidate_addresses
            
            blocks_to_scan = 50
            start_block = latest_block - blocks_to_scan
            num_blocks = latest_block - start_block
            
            print(f"      Scanning {num_blocks} blocks (>= 10 ETH, parallel)...", file=sys.stderr)
            
            blocks_to_fetch = list(range(start_block, latest_block + 1))
            
            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = {executor.submit(self._fetch_block_candidates, b, 10.0): b for b in blocks_to_fetch}
                
                done = 0
                for future in as_completed(futures):
                    done += 1
                    for addr in future.result():
                        candidate_addresses.add(addr)
                    
                    if done % 10 == 0:
                        print(f"      Scanned {done}/{len(blocks_to_fetch)} blocks, found {len(candidate_addresses)} candidates...", file=sys.stderr)
        except Exception as e:
            print(f"      Block scan error: {str(e)[:50]}", file=sys.stderr)
        
        if len(candidate_addresses) == 0:
            print("    Trying token transfers fallback...", file=sys.stderr)
            for token_name, token_info in MAJOR_TOKENS.items():
                min_transfer = max(min_balance_usd * 0.1, 10000)
                try:
                    transfers = self.etherscan.get_large_token_transfers(
                        token_info['address'],
                        min_transfer,
                        token_info['decimals'],
                        token_info['price'],
                        limit=200
                    )
                    
                    for tx in transfers[:50]:
                        to_addr = tx.get('to', '').lower()
                        from_addr = tx.get('from', '').lower()
                        
                        for addr in [to_addr, from_addr]:
                            if addr and len(addr) == 42 and addr not in KNOWN_MIXERS:
                                if not self.rpc.is_contract(addr):
                                    candidate_addresses.add(addr)
                except Exception as e:
                    continue
        
        return candidate_addresses
    
    def find_high_value_wallets(self, min_balance_usd: float = 100000, limit: int = 10) -> List[Dict]:
        print(f"Searching for interesting individual whales (min ${min_balance_usd:,.0f})...", file=sys.stderr)
        
        all_candidates = {}
        
        print("  - Strategy 1: DeFi power users...", file=sys.stderr)
        defi_users = self.find_defi_power_users(min_position_usd=min_balance_usd * 0.3)
        for user in defi_users:
            addr = user['address']
            if addr not in all_candidates:
                all_candidates[addr] = {'address': addr, 'categories': [], 'metadata': {}}
            all_candidates[addr]['categories'].append('defi')
            all_candidates[addr]['metadata'][f"defi_{user['protocol']}"] = user.get('position_value_usd', 0)
        print(f"    Found {len(defi_users)} DeFi power users", file=sys.stderr)
        
        print("  - Strategy 2: NFT whales...", file=sys.stderr)
        nft_whales = self.find_nft_whales(min_nfts=1)
        for whale in nft_whales:
            addr = whale['address']
            if addr not in all_candidates:
                all_candidates[addr] = {'address': addr, 'categories': [], 'metadata': {}}
            all_candidates[addr]['categories'].append('nft')
            if 'nft_collections' not in all_candidates[addr]['metadata']:
                all_candidates[addr]['metadata']['nft_collections'] = []
            all_candidates[addr]['metadata']['nft_collections'].append({
                'name': whale['collection'],
                'count': whale['nft_count']
            })
        print(f"    Found {len(nft_whales)} NFT whales", file=sys.stderr)
        
        print("  - Strategy 3: DAO participants...", file=sys.stderr)
        dao_participants = self.find_dao_participants(min_tokens=100)
        for participant in dao_participants:
            addr = participant['address']
            if addr not in all_candidates:
                all_candidates[addr] = {'address': addr, 'categories': [], 'metadata': {}}
            all_candidates[addr]['categories'].append('dao')
            all_candidates[addr]['metadata'][f"dao_{participant['dao']}"] = participant.get('token_balance', 0)
        print(f"    Found {len(dao_participants)} DAO participants", file=sys.stderr)
        
        print("  - Strategy 4: Early adopters (2015-2017)...", file=sys.stderr)
        early_adopters = self.find_early_adopters()
        for adopter in early_adopters[:50]:
            addr = adopter['address']
            if addr not in all_candidates:
                all_candidates[addr] = {'address': addr, 'categories': [], 'metadata': {}}
            all_candidates[addr]['categories'].append('early_adopter')
        print(f"    Found {len(early_adopters)} early adopters", file=sys.stderr)
        
        if len(all_candidates) == 0:
            fallback_candidates = self.find_candidates_from_large_transfers(min_balance_usd)
            print(f"    Found {len(fallback_candidates)} addresses from fallback strategy", file=sys.stderr)
            for addr in fallback_candidates:
                if addr not in all_candidates:
                    all_candidates[addr] = {'address': addr, 'categories': ['high_value'], 'metadata': {}}
        
        print(f"  - Found {len(all_candidates)} unique candidate addresses", file=sys.stderr)
        
        if not all_candidates:
            print("  - No candidates found", file=sys.stderr)
            return []
        
        print("  - Validating candidates and checking balances (parallel)...", file=sys.stderr)
        
        candidates_list = list(all_candidates.items())[:100]
        
        def check_candidate(addr_data):
            addr, candidate_data = addr_data
            try:
                if self.rpc.is_contract(addr):
                    return None
                
                balance_data = self.rpc.get_balance(addr)
                eth_balance = balance_data['eth']
                eth_price = 3000
                eth_value_usd = eth_balance * eth_price
                
                if eth_value_usd < min_balance_usd * 0.3:
                    return None
                
                token_holdings = {}
                total_token_value = 0
                
                for token_name, token_info in list(MAJOR_TOKENS.items())[:3]:
                    try:
                        balance = self.rpc.get_token_balance(addr, token_info['address'], token_info['decimals'])
                        if balance > 0:
                            value_usd = balance * token_info['price']
                            if value_usd >= 100:
                                token_holdings[token_name] = {
                                    'balance': balance,
                                    'value_usd': value_usd
                                }
                                total_token_value += value_usd
                    except:
                        pass
                
                total_value = eth_value_usd + total_token_value
                
                if total_value >= min_balance_usd * 0.3:
                    if not self.is_institutional(addr):
                        tx_count = self.exchange_detector.get_transaction_count(addr)
                        
                        return {
                            'address': addr,
                            'total_value_usd': total_value,
                            'eth_balance': eth_balance,
                            'eth_value_usd': eth_value_usd,
                            'token_holdings': token_holdings,
                            'categories': candidate_data['categories'],
                            'metadata': candidate_data['metadata'],
                            'tx_count': tx_count
                        }
            except:
                pass
            return None
        
        high_value_wallets = []
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {executor.submit(check_candidate, item): item[0] for item in candidates_list}
            
            done = 0
            for future in as_completed(futures):
                done += 1
                result = future.result()
                if result:
                    high_value_wallets.append(result)
                
                if done % 20 == 0:
                    print(f"    Checked {done}/{len(candidates_list)} addresses, found {len(high_value_wallets)} whales...", file=sys.stderr)
                
                if len(high_value_wallets) >= limit * 2:
                    break
        
        high_value_wallets.sort(key=lambda x: (
            len(x.get('categories', [])),
            x['total_value_usd']
        ), reverse=True)
        
        return high_value_wallets[:limit]

