from datetime import datetime
from collections import defaultdict, Counter
from typing import Dict, List


class TransactionAnalyzer:
    @staticmethod
    def analyze_patterns(txs: List[Dict]) -> Dict:
        if not txs:
            return {}
        
        total_txs = len(txs)
        total_value = sum(int(tx.get('value', 0)) for tx in txs) / 1e18
        
        time_patterns = []
        hour_distribution = Counter()
        day_distribution = Counter()
        
        addresses_sent_to = Counter()
        addresses_received_from = Counter()
        
        gas_used_total = 0
        gas_price_avg = 0
        
        for tx in txs:
            timestamp = int(tx.get('timeStamp', 0))
            if timestamp:
                dt = datetime.fromtimestamp(timestamp)
                hour_distribution[dt.hour] += 1
                day_distribution[dt.strftime('%A')] += 1
                time_patterns.append(dt)
            
            to_addr = tx.get('to', '').lower()
            from_addr = tx.get('from', '').lower()
            
            if to_addr:
                addresses_sent_to[to_addr] += 1
            if from_addr:
                addresses_received_from[from_addr] += 1
            
            gas_used = int(tx.get('gasUsed', 0))
            gas_price = int(tx.get('gasPrice', 0))
            if gas_used:
                gas_used_total += gas_used
            if gas_price:
                gas_price_avg = (gas_price_avg + gas_price) / 2
        
        most_active_hour = hour_distribution.most_common(1)[0] if hour_distribution else (0, 0)
        most_active_day = day_distribution.most_common(1)[0] if day_distribution else ('Unknown', 0)
        
        top_recipients = addresses_sent_to.most_common(10)
        top_senders = addresses_received_from.most_common(10)
        
        first_tx = min(time_patterns) if time_patterns else None
        last_tx = max(time_patterns) if time_patterns else None
        
        return {
            'total_transactions': total_txs,
            'total_value_eth': total_value,
            'most_active_hour': most_active_hour[0],
            'most_active_day': most_active_day[0],
            'top_recipients': top_recipients,
            'top_senders': top_senders,
            'first_transaction': first_tx.isoformat() if first_tx else None,
            'last_transaction': last_tx.isoformat() if last_tx else None,
            'avg_gas_used': gas_used_total / total_txs if total_txs > 0 else 0,
            'avg_gas_price': gas_price_avg
        }
    
    @staticmethod
    def analyze_token_activity(token_txs: List[Dict]) -> Dict:
        if not token_txs:
            return {}
        
        tokens = Counter()
        token_values = defaultdict(float)
        token_types = defaultdict(set)
        
        for tx in token_txs:
            token_symbol = tx.get('tokenSymbol', 'UNKNOWN')
            token_name = tx.get('tokenName', 'Unknown')
            token_address = tx.get('contractAddress', '').lower()
            
            tokens[token_symbol] += 1
            token_types[token_symbol].add(token_name)
            
            value = float(tx.get('value', 0))
            decimals = int(tx.get('tokenDecimal', 18))
            adjusted_value = value / (10 ** decimals)
            token_values[token_symbol] += abs(adjusted_value)
        
        top_tokens = tokens.most_common(20)
        
        return {
            'unique_tokens': len(tokens),
            'top_tokens': top_tokens,
            'token_values': dict(token_values),
            'token_details': {k: list(v) for k, v in token_types.items()}
        }
    
    @staticmethod
    def analyze_nft_activity(nft_txs: List[Dict]) -> Dict:
        if not nft_txs:
            return {}
        
        collections = Counter()
        nft_addresses = Counter()
        
        for tx in nft_txs:
            token_name = tx.get('tokenName', 'Unknown')
            contract_address = tx.get('contractAddress', '').lower()
            
            collections[token_name] += 1
            nft_addresses[contract_address] += 1
        
        return {
            'unique_collections': len(collections),
            'top_collections': collections.most_common(10),
            'collection_addresses': dict(nft_addresses)
        }
    
    @staticmethod
    def identify_contracts(txs: List[Dict]) -> List[Dict]:
        contracts = []
        contract_addresses = set()
        
        for tx in txs:
            to_addr = tx.get('to', '').lower()
            if to_addr and to_addr not in contract_addresses:
                contract_addresses.add(to_addr)
                contracts.append({
                    'address': to_addr,
                    'tx_count': 1,
                    'first_seen': datetime.fromtimestamp(int(tx.get('timeStamp', 0))).isoformat() if tx.get('timeStamp') else None
                })
        
        return sorted(contracts, key=lambda x: x['tx_count'], reverse=True)[:20]

