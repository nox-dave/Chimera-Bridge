#!/usr/bin/env python3

from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from collections import defaultdict

@dataclass
class Signal:
    name: str
    value: Any
    matched: bool = False

@dataclass
class PatternMatch:
    pattern_name: str
    matched_signals: List[str]
    total_signals: int
    confidence: float
    verdict: Dict
    overrides: List[str]

class SignalExtractor:
    @staticmethod
    def extract(profile_data: dict) -> Dict[str, Any]:
        behavior = profile_data.get('behavior', {})
        if not behavior:
            behavior = {}
        
        balance_usd = profile_data.get('balance_usd', profile_data.get('total_value_usd', 0)) or 0
        wallet_age_days = profile_data.get('wallet_age_days', profile_data.get('age_days', 0)) or 0
        tx_count = profile_data.get('tx_count', 0) or 0
        
        confidence = behavior.get('confidence_score', profile_data.get('risk_score', 50)) or 50
        
        exchange_interactions = behavior.get('exchange_interactions', [])
        defi_protocols = behavior.get('defi_protocols', [])
        nft_platforms = behavior.get('nft_platforms', [])
        bridges_used = behavior.get('bridges_used', [])
        
        if not defi_protocols and profile_data.get('defi_activity'):
            defi_protocols = ['Unknown']
        if not nft_platforms and profile_data.get('nft_activity'):
            nft_platforms = ['Unknown']
        if not bridges_used and profile_data.get('bridge_activity'):
            bridges_used = ['Unknown']
        
        transaction_analysis = profile_data.get('transaction_analysis', {})
        top_recipients = transaction_analysis.get('top_recipients', []) if transaction_analysis else []
        top_senders = transaction_analysis.get('top_senders', []) if transaction_analysis else []
        
        counterparty_set = set()
        if top_recipients:
            counterparty_set.update([addr for addr, _ in top_recipients if isinstance(addr, str)])
        if top_senders:
            counterparty_set.update([addr for addr, _ in top_senders if isinstance(addr, str)])
        if behavior.get('frequent_counterparties'):
            counterparty_set.update(behavior.get('frequent_counterparties', []))
        
        unique_counterparties = len(counterparty_set) if counterparty_set else 0
        
        if unique_counterparties == 0 and tx_count > 10000:
            unique_counterparties = min(tx_count // 10, 10000)
        elif unique_counterparties == 0 and tx_count > 1000:
            unique_counterparties = min(tx_count // 5, 1000)
        
        if wallet_age_days > 0:
            tx_frequency = tx_count / wallet_age_days
        else:
            tx_frequency = 0
        
        round_number_transfers = behavior.get('round_number_transfers', 0)
        
        token_activity = profile_data.get('token_activity', {})
        unique_tokens = token_activity.get('unique_tokens', 0) if token_activity else 0
        
        total_value_eth = transaction_analysis.get('total_value_eth', 0) if transaction_analysis else 0
        
        if tx_count > 0 and total_value_eth > 0:
            avg_tx_value_eth = total_value_eth / tx_count
        else:
            avg_tx_value_eth = 0
        
        round_number_ratio = round_number_transfers / tx_count if tx_count > 0 else 0
        
        sophistication = behavior.get('sophistication', 'Unknown')
        if sophistication == 'Unknown' and tx_count > 0:
            if tx_count > 50000:
                sophistication = 'Expert'
            elif tx_count > 10000:
                sophistication = 'Advanced'
            elif tx_count > 1000:
                sophistication = 'Intermediate'
            else:
                sophistication = 'Novice'
        
        signals = {
            'wallet_age_days': wallet_age_days,
            'balance_usd': balance_usd,
            'tx_count': tx_count,
            'tx_frequency': tx_frequency,
            'unique_counterparties': unique_counterparties,
            'round_number_transfers': round_number_transfers,
            'round_number_ratio': round_number_ratio,
            'token_diversity': unique_tokens,
            'meme_exposure': behavior.get('meme_exposure', False),
            'dust_attack_target': behavior.get('dust_attack_target', False),
            'exchange_interactions': len(exchange_interactions),
            'defi_protocols_count': len(defi_protocols),
            'nft_platforms_count': len(nft_platforms),
            'bridges_count': len(bridges_used),
            'sophistication': sophistication,
            'confidence_score': confidence,
            'contract_interactions': behavior.get('contract_interactions', 0),
            'avg_tx_value_eth': avg_tx_value_eth,
            'stablecoin_heavy': behavior.get('stablecoin_heavy', False),
            'political_tokens': behavior.get('political_tokens', False),
            'gaming_tokens': behavior.get('gaming_tokens', False),
        }
        
        return signals

class PatternMatcher:
    def __init__(self, patterns: Dict[str, Dict]):
        self.patterns = patterns
    
    def evaluate_signal(self, signal_name: str, operator: str, threshold: Any, signal_value: Any) -> bool:
        if signal_value is None:
            return False
        
        if operator == ">":
            return signal_value > threshold
        elif operator == ">=":
            return signal_value >= threshold
        elif operator == "<":
            return signal_value < threshold
        elif operator == "<=":
            return signal_value <= threshold
        elif operator == "==":
            return signal_value == threshold
        elif operator == "!=":
            return signal_value != threshold
        elif operator == "in":
            return signal_value in threshold if isinstance(threshold, (list, set, tuple)) else False
        elif operator == "not_in":
            return signal_value not in threshold if isinstance(threshold, (list, set, tuple)) else False
        else:
            return False
    
    def match_pattern(self, pattern_name: str, pattern: Dict, signals: Dict[str, Any]) -> Optional[PatternMatch]:
        pattern_signals = pattern.get('signals', [])
        confidence_threshold = pattern.get('confidence_threshold', len(pattern_signals))
        
        matched_signals = []
        
        for signal_def in pattern_signals:
            if len(signal_def) != 3:
                continue
            
            signal_name, operator, threshold = signal_def
            signal_value = signals.get(signal_name)
            
            if self.evaluate_signal(signal_name, operator, threshold, signal_value):
                matched_signals.append(signal_name)
        
        if len(matched_signals) >= confidence_threshold:
            confidence = len(matched_signals) / len(pattern_signals) if pattern_signals else 0
            
            return PatternMatch(
                pattern_name=pattern_name,
                matched_signals=matched_signals,
                total_signals=len(pattern_signals),
                confidence=confidence,
                verdict=pattern.get('verdict', {}),
                overrides=pattern.get('overrides', [])
            )
        
        return None
    
    def match_all(self, signals: Dict[str, Any]) -> List[PatternMatch]:
        matches = []
        
        for pattern_name, pattern in self.patterns.items():
            match = self.match_pattern(pattern_name, pattern, signals)
            if match:
                matches.append(match)
        
        return matches

PATTERN_TEMPLATES = {
    "exchange_hot_wallet": {
        "signals": [
            ("tx_count", ">", 10000),
            ("unique_counterparties", ">", 500),
            ("tx_frequency", ">", 100),
            ("round_number_ratio", "<", 0.1),
            ("token_diversity", ">", 50),
        ],
        "confidence_threshold": 4,
        "verdict": {
            "title": "LIKELY EXCHANGE HOT WALLET",
            "severity": "INFO",
            "category": "FILTER",
            "description": "Pattern matches exchange hot wallet characteristics. High transaction volume, many counterparties, low round number usage.",
            "action": "Filter out - not a target"
        },
        "overrides": ["NEWCOMER", "EASY_TARGET", "FRESH_WHALE", "NO EXCHANGE TRAIL", "NEWCOMER WITH SIGNIFICANT FUNDS"]
    },
    
    "bot_mev": {
        "signals": [
            ("tx_count", ">", 50000),
            ("tx_frequency", ">", 200),
            ("contract_interactions", ">", 1000),
            ("round_number_ratio", "<", 0.05),
            ("defi_protocols_count", ">", 5),
        ],
        "confidence_threshold": 4,
        "verdict": {
            "title": "LIKELY BOT OR MEV OPERATOR",
            "severity": "INFO",
            "category": "FILTER",
            "description": "Extremely high transaction frequency and contract interactions suggest automated trading or MEV operations.",
            "action": "Filter out - automated system"
        },
        "overrides": ["NEWCOMER", "EASY_TARGET", "NO EXCHANGE TRAIL", "NEWCOMER WITH SIGNIFICANT FUNDS"]
    },
    
    "fresh_whale_real": {
        "signals": [
            ("wallet_age_days", "<", 30),
            ("balance_usd", ">", 100000),
            ("tx_count", "<", 500),
            ("round_number_transfers", ">", 3),
            ("meme_exposure", "==", True),
        ],
        "confidence_threshold": 4,
        "verdict": {
            "title": "NEWCOMER WITH SIGNIFICANT FUNDS",
            "severity": "HIGH",
            "category": "VULNERABILITY",
            "description": "Fresh wallet with large balance and human-like transaction patterns. High-value target for scams.",
            "action": "Prime target - likely inexperienced with large funds"
        },
        "overrides": []
    },
    
    "scam_nft_victim": {
        "signals": [
            ("dust_attack_target", "==", True),
            ("nft_platforms_count", ">", 0),
            ("balance_usd", ">", 50000),
        ],
        "confidence_threshold": 3,
        "verdict": {
            "title": "ACTIVE PHISHING TARGET",
            "severity": "HIGH",
            "category": "THREAT",
            "description": "Wallet is being actively targeted by scammers via address poisoning attacks. Attackers are monitoring this wallet.",
            "action": "High-value target for social engineering"
        },
        "overrides": []
    },
    
    "nft_collector": {
        "signals": [
            ("nft_platforms_count", ">", 1),
            ("balance_usd", ">", 100000),
            ("tx_frequency", "<", 5),
            ("defi_protocols_count", "<", 3),
        ],
        "confidence_threshold": 3,
        "verdict": {
            "title": "NFT COLLECTOR PROFILE",
            "severity": "MEDIUM",
            "category": "PROFILE",
            "description": "Wallet shows strong NFT activity with significant holdings. Potential social identity vector through NFT metadata.",
            "action": "Investigate NFT metadata for OSINT"
        },
        "overrides": []
    },
    
    "defi_power_user": {
        "signals": [
            ("defi_protocols_count", ">", 5),
            ("bridges_count", ">", 1),
            ("sophistication", "in", ["Expert", "Advanced"]),
            ("tx_count", ">", 500),
        ],
        "confidence_threshold": 3,
        "verdict": {
            "title": "DEFI POWER USER",
            "severity": "MEDIUM",
            "category": "PROFILE",
            "description": "Advanced DeFi user with multi-protocol exposure and cross-chain activity. High sophistication level.",
            "action": "Target with advanced DeFi scams, fake protocol exploits"
        },
        "overrides": []
    },
    
    "dormant_whale": {
        "signals": [
            ("wallet_age_days", ">", 365),
            ("balance_usd", ">", 500000),
            ("tx_frequency", "<", 0.1),
            ("tx_count", "<", 100),
        ],
        "confidence_threshold": 3,
        "verdict": {
            "title": "DORMANT WHALE",
            "severity": "LOW",
            "category": "PROFILE",
            "description": "Old wallet with large balance but minimal recent activity. May be cold storage or abandoned.",
            "action": "Low priority - minimal activity"
        },
        "overrides": []
    },
    
    "money_mule": {
        "signals": [
            ("tx_count", ">", 1000),
            ("unique_counterparties", ">", 100),
            ("round_number_ratio", ">", 0.5),
            ("wallet_age_days", "<", 90),
            ("balance_usd", "<", 10000),
        ],
        "confidence_threshold": 4,
        "verdict": {
            "title": "SUSPICIOUS FLOW PATTERN",
            "severity": "MEDIUM",
            "category": "THREAT",
            "description": "High transaction volume with many counterparties and round numbers. Possible money mule or laundering pattern.",
            "action": "Investigate transaction flow patterns"
        },
        "overrides": []
    },
    
    "low_sophistication_target": {
        "signals": [
            ("sophistication", "in", ["Novice", "Unknown"]),
            ("balance_usd", ">", 50000),
            ("defi_protocols_count", "<", 2),
            ("exchange_interactions", ">", 0),
        ],
        "confidence_threshold": 3,
        "verdict": {
            "title": "LOW SOPHISTICATION TARGET",
            "severity": "MEDIUM",
            "category": "VULNERABILITY",
            "description": "Wallet shows limited DeFi knowledge but holds significant value. Basic phishing likely to succeed.",
            "action": "Standard phishing attacks likely effective"
        },
        "overrides": []
    },
    
    "confirmed_individual": {
        "signals": [
            ("confidence_score", ">=", 80),
            ("round_number_transfers", ">=", 3),
            ("tx_count", ">", 100),
            ("tx_count", "<", 5000),
        ],
        "confidence_threshold": 3,
        "verdict": {
            "title": "CONFIRMED INDIVIDUAL",
            "severity": "INFO",
            "category": "PROFILE",
            "description": "High confidence this is a real individual, not a bot or institution. Human transaction patterns detected.",
            "action": "Suitable for targeted social engineering"
        },
        "overrides": []
    },
    
    "high_risk_trader": {
        "signals": [
            ("meme_exposure", "==", True),
            ("tx_count", ">", 200),
            ("balance_usd", ">", 50000),
        ],
        "confidence_threshold": 3,
        "verdict": {
            "title": "HIGH-RISK TRADER PROFILE",
            "severity": "MEDIUM",
            "category": "PROFILE",
            "description": "Wallet shows impulsive trading behavior with meme coin exposure. Likely susceptible to FOMO-based attacks.",
            "action": "Target with urgency-based scams, fake alpha"
        },
        "overrides": []
    },
    
    "no_exchange_trail": {
        "signals": [
            ("exchange_interactions", "==", 0),
            ("balance_usd", ">", 500000),
            ("tx_count", ">", 50),
        ],
        "confidence_threshold": 3,
        "verdict": {
            "title": "NO EXCHANGE TRAIL",
            "severity": "MEDIUM",
            "category": "INTEL",
            "description": "Large holder with no detected CEX interactions. Funds origin harder to trace. May be privacy-conscious or using DEX only.",
            "action": "Trace funding source through on-chain analysis"
        },
        "overrides": []
    },
}

class PatternEngine:
    def __init__(self, patterns: Optional[Dict[str, Dict]] = None):
        self.patterns = patterns or PATTERN_TEMPLATES
        self.matcher = PatternMatcher(self.patterns)
        self.extractor = SignalExtractor()
    
    def analyze(self, profile_data: dict) -> List[PatternMatch]:
        signals = self.extractor.extract(profile_data)
        matches = self.matcher.match_all(signals)
        
        override_map = {}
        for match in matches:
            for override in match.overrides:
                override_map[override] = match.pattern_name
        
        filtered_matches = []
        for match in matches:
            verdict_title = match.verdict.get('title', '')
            should_skip = False
            
            for override_pattern_name in override_map.values():
                override_match = next((m for m in matches if m.pattern_name == override_pattern_name), None)
                if override_match and verdict_title in override_match.overrides:
                    should_skip = True
                    break
            
            if not should_skip:
                filtered_matches.append(match)
        
        return filtered_matches
    
    def get_verdicts(self, profile_data: dict) -> List[Dict]:
        from .osint_verdicts import Verdict
        
        matches = self.analyze(profile_data)
        verdicts = []
        
        for match in matches:
            verdict_data = match.verdict.copy()
            verdict_data['evidence'] = [
                f"Matched {len(match.matched_signals)}/{match.total_signals} signals",
                f"Pattern: {match.pattern_name}",
                f"Confidence: {match.confidence:.0%}",
            ] + [f"Signal: {sig}" for sig in match.matched_signals[:5]]
            
            verdicts.append(Verdict(**verdict_data))
        
        return verdicts

