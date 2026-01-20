import os
import json
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Dict, List, Tuple

from .config import (
    AUTO_TRASH_CATEGORIES,
    MIN_BALANCE_USD,
    MIN_CONFIDENCE
)


@dataclass
class PriorityScore:
    address: str
    total_score: int
    value_score: int
    vulnerability_score: int
    confidence_score: int
    freshness_score: int
    balance_usd: float
    categories: List[str]
    confidence_pct: int
    last_updated: str
    disqualified: bool = False
    disqualify_reason: str = ""


def calculate_value_score(balance_usd: float) -> int:
    if balance_usd >= 5_000_000:
        return 40
    elif balance_usd >= 1_000_000:
        return 30
    elif balance_usd >= 500_000:
        return 20
    elif balance_usd >= 100_000:
        return 10
    elif balance_usd >= 50_000:
        return 5
    else:
        return 0


def calculate_vulnerability_score(categories: List[str], profile_data: dict) -> int:
    score = 0
    
    category_scores = {
        "🎯_prime_targets": 30,
        "🆕_newcomers": 15,
        "🐟_easy_targets": 15,
        "🎰_gamblers": 12,
        "🏆_status_seekers": 10,
        "💤_dormant_whales": 8,
        "🌉_cross_chain_users": 5,
        "🧠_defi_natives": 3,
        "🦊_cautious_holders": 0,
    }
    
    for cat in categories:
        if cat in category_scores:
            score = max(score, category_scores[cat])
    
    if "🆕_newcomers" in categories and "🐟_easy_targets" in categories:
        score = min(30, score + 10)
    
    behavior = profile_data.get('behavior', {})
    if behavior.get('dust_attack_target'):
        score = min(30, score + 5)
    
    return score


def calculate_confidence_score(confidence_pct: int) -> int:
    if confidence_pct >= 80:
        return 20
    elif confidence_pct >= 60:
        return 15
    elif confidence_pct >= 40:
        return 10
    elif confidence_pct >= 30:
        return 5
    else:
        return 0


def calculate_freshness_score(last_updated: str) -> int:
    try:
        if not last_updated:
            return 0
        
        updated = datetime.fromisoformat(last_updated.replace('Z', '+00:00'))
        now = datetime.now(updated.tzinfo) if updated.tzinfo else datetime.now()
        age = now - updated
        
        if age.days < 1:
            return 10
        elif age.days < 7:
            return 7
        elif age.days < 30:
            return 3
        else:
            return 0
    except:
        return 0


def check_disqualifiers(profile_data: dict, categories: List[str]) -> Tuple[bool, str]:
    for cat in categories:
        if cat in AUTO_TRASH_CATEGORIES:
            return True, f"Category: {cat}"
    
    balance = profile_data.get('balance_usd', profile_data.get('total_value_usd', 0))
    if balance < MIN_BALANCE_USD:
        return True, f"Balance too low: ${balance:,.0f}"
    
    behavior = profile_data.get('behavior', {})
    confidence = behavior.get('confidence_score', profile_data.get('risk_score', 50))
    if confidence < MIN_CONFIDENCE:
        return True, f"Confidence too low: {confidence}%"
    
    address = profile_data.get('address', '').lower()
    if address == '0x000000000000000000000000000000000000dead':
        return True, "Burn address"
    
    return False, ""


def score_profile(profile_data: dict) -> PriorityScore:
    address = profile_data.get('address', 'unknown')
    balance = profile_data.get('balance_usd', profile_data.get('total_value_usd', 0))
    categories = profile_data.get('osint_categories', [])
    behavior = profile_data.get('behavior', {})
    confidence = behavior.get('confidence_score', profile_data.get('risk_score', 50))
    last_updated = profile_data.get('last_updated', profile_data.get('generated', ''))
    
    disqualified, reason = check_disqualifiers(profile_data, categories)
    
    if disqualified:
        return PriorityScore(
            address=address,
            total_score=0,
            value_score=0,
            vulnerability_score=0,
            confidence_score=0,
            freshness_score=0,
            balance_usd=balance,
            categories=categories,
            confidence_pct=confidence,
            last_updated=last_updated,
            disqualified=True,
            disqualify_reason=reason
        )
    
    value_score = calculate_value_score(balance)
    vuln_score = calculate_vulnerability_score(categories, profile_data)
    conf_score = calculate_confidence_score(confidence)
    fresh_score = calculate_freshness_score(last_updated)
    
    total = value_score + vuln_score + conf_score + fresh_score
    
    return PriorityScore(
        address=address,
        total_score=total,
        value_score=value_score,
        vulnerability_score=vuln_score,
        confidence_score=conf_score,
        freshness_score=fresh_score,
        balance_usd=balance,
        categories=categories,
        confidence_pct=confidence,
        last_updated=last_updated
    )

