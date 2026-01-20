#!/usr/bin/env python3

from typing import Dict
from datetime import datetime

class ReportGenerator:
    @staticmethod
    def format_value(value: float, decimals: int = 4) -> str:
        if value == 0:
            return "0"
        if value < 0.0001:
            return f"{value:.8f}"
        return f"{value:.{decimals}f}"
    
    @staticmethod
    def generate_text_report(profile: Dict) -> str:
        lines = []
        lines.append("=" * 80)
        lines.append(f"WALLET PROFILE REPORT - {profile['address']}")
        lines.append("=" * 80)
        lines.append(f"Generated: {profile.get('analysis_timestamp', 'Unknown')}")
        lines.append("")
        
        lines.append("─" * 80)
        lines.append("BALANCE & OVERVIEW")
        lines.append("─" * 80)
        lines.append(f"ETH Balance: {ReportGenerator.format_value(profile['balance_eth'])} ETH")
        lines.append("")
        
        tx_analysis = profile.get('transaction_analysis', {})
        if tx_analysis:
            lines.append("─" * 80)
            lines.append("TRANSACTION ANALYSIS")
            lines.append("─" * 80)
            lines.append(f"Total Transactions: {tx_analysis.get('total_transactions', 0):,}")
            lines.append(f"Total Value Transacted: {ReportGenerator.format_value(tx_analysis.get('total_value_eth', 0))} ETH")
            
            if tx_analysis.get('first_transaction'):
                lines.append(f"First Transaction: {tx_analysis['first_transaction']}")
            if tx_analysis.get('last_transaction'):
                lines.append(f"Last Transaction: {tx_analysis['last_transaction']}")
            
            lines.append(f"Most Active Hour: {tx_analysis.get('most_active_hour', 'N/A')}:00 UTC")
            lines.append(f"Most Active Day: {tx_analysis.get('most_active_day', 'N/A')}")
            
            top_recipients = tx_analysis.get('top_recipients', [])[:5]
            if top_recipients:
                lines.append("")
                lines.append("Top 5 Recipients:")
                for addr, count in top_recipients:
                    lines.append(f"  {addr} ({count} txs)")
            
            top_senders = tx_analysis.get('top_senders', [])[:5]
            if top_senders:
                lines.append("")
                lines.append("Top 5 Senders:")
                for addr, count in top_senders:
                    lines.append(f"  {addr} ({count} txs)")
            lines.append("")
        
        token_activity = profile.get('token_activity', {})
        if token_activity:
            lines.append("─" * 80)
            lines.append("TOKEN ACTIVITY")
            lines.append("─" * 80)
            lines.append(f"Unique Tokens Interacted: {token_activity.get('unique_tokens', 0)}")
            
            top_tokens = token_activity.get('top_tokens', [])[:10]
            if top_tokens:
                lines.append("")
                lines.append("Top 10 Most Active Tokens:")
                for token, count in top_tokens:
                    lines.append(f"  {token}: {count} transfers")
            lines.append("")
        
        nft_activity = profile.get('nft_activity', {})
        if nft_activity:
            lines.append("─" * 80)
            lines.append("NFT ACTIVITY")
            lines.append("─" * 80)
            lines.append(f"Unique NFT Collections: {nft_activity.get('unique_collections', 0)}")
            
            top_collections = nft_activity.get('top_collections', [])[:10]
            if top_collections:
                lines.append("")
                lines.append("Top Collections:")
                for collection, count in top_collections:
                    lines.append(f"  {collection}: {count} transfers")
            lines.append("")
        
        token_balances = profile.get('token_balances', [])
        if token_balances:
            lines.append("─" * 80)
            lines.append("CURRENT TOKEN HOLDINGS")
            lines.append("─" * 80)
            for token in token_balances[:15]:
                symbol = token.get('symbol', 'UNKNOWN')
                balance = float(token.get('balance', 0)) / (10 ** int(token.get('decimals', 18)))
                if balance > 0:
                    lines.append(f"  {symbol}: {ReportGenerator.format_value(balance)}")
            lines.append("")
        
        contracts = profile.get('top_contracts', [])
        if contracts:
            lines.append("─" * 80)
            lines.append("TOP INTERACTED CONTRACTS")
            lines.append("─" * 80)
            for contract in contracts[:10]:
                lines.append(f"  {contract['address']}")
            lines.append("")
        
        if profile.get('total_internal_txs', 0) > 0:
            lines.append("─" * 80)
            lines.append("ADDITIONAL METRICS")
            lines.append("─" * 80)
            lines.append(f"Internal Transactions: {profile['total_internal_txs']:,}")
            lines.append("")
        
        lines.append("=" * 80)
        lines.append("END OF REPORT")
        lines.append("=" * 80)
        
        return "\n".join(lines)
    
    @staticmethod
    def generate_json_report(profile: Dict) -> str:
        import json
        return json.dumps(profile, indent=2, default=str)

