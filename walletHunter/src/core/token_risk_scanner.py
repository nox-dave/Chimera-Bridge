#!/usr/bin/env python3

import os
import asyncio
import aiohttp
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from enum import Enum


ETHERSCAN_API_KEY = os.getenv('ETHERSCAN_API_KEY', '')
ETHERSCAN_BASE_URL = 'https://api.etherscan.io/api'

MIN_TOKEN_VALUE_USD = 10

LEGITIMATE_TOKENS = {
    '0xdac17f958d2ee523a2206206994597c13d831ec7': 'USDT',
    '0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48': 'USDC',
    '0x6b175474e89094c44da98b954eedeac495271d0f': 'DAI',
    '0x4fabb145d64652a948d72533023f6e7a623c7c53': 'BUSD',
    '0x1f9840a85d5af5bf1d1762f925bdaddc4201f984': 'UNI',
    '0x7fc66500c84a76ad7e9c93437bfc5ac33e2ddae9': 'AAVE',
    '0xc00e94cb662c3520282e6f5717214004a7f26888': 'COMP',
    '0x9f8f72aa9304c8b593d555f12ef6589cc3a579a2': 'MKR',
    '0xc011a73ee8576fb46f5e1c5751ca3b9fe0af2a6f': 'SNX',
    '0x514910771af9ca656af840dff83e8264ecf986ca': 'LINK',
    '0x4d224452801aced8b2f0aebe155379bb5d594381': 'APE',
    '0x95ad61b0a150d79219dcf64e1e6cc01f0b64c4ce': 'SHIB',
    '0x6982508145454ce325ddbe47a25d4ec3d2311933': 'PEPE',
    '0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2': 'WETH',
    '0x2260fac5e5542a773aa44fbcfedf7c193bc2c599': 'WBTC',
}

KNOWN_SCAM_TOKENS = {}

IMPERSONATOR_PATTERNS = {
    'usdt': '0xdac17f958d2ee523a2206206994597c13d831ec7',
    'usdc': '0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48',
    'dai': '0x6b175474e89094c44da98b954eedeac495271d0f',
    'weth': '0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2',
    'wbtc': '0x2260fac5e5542a773aa44fbcfedf7c193bc2c599',
    'uni': '0x1f9840a85d5af5bf1d1762f925bdaddc4201f984',
    'aave': '0x7fc66500c84a76ad7e9c93437bfc5ac33e2ddae9',
    'link': '0x514910771af9ca656af840dff83e8264ecf986ca',
    'pepe': '0x6982508145454ce325ddbe47a25d4ec3d2311933',
    'shib': '0x95ad61b0a150d79219dcf64e1e6cc01f0b64c4ce',
}

HONEYPOT_SIGNATURES = [
    'c9567bf9',
    '8f70ccf7',
    'af465a27',
    'a9059cbb',
]

class TokenRiskLevel(Enum):
    SAFE = 'safe'
    LOW = 'low'
    MEDIUM = 'medium'
    HIGH = 'high'
    CRITICAL = 'critical'


@dataclass
class TokenRiskAnalysis:
    token_address: str
    token_symbol: str
    token_name: str
    balance: float
    balance_usd: Optional[float]
    risk_level: TokenRiskLevel
    risk_score: int
    risk_reasons: List[str] = field(default_factory=list)
    is_verified: bool = False
    contract_age_days: Optional[int] = None
    has_proxy: bool = False
    owner_renounced: Optional[bool] = None
    is_honeypot: bool = False
    honeypot_reason: Optional[str] = None
    sell_tax: Optional[float] = None
    buy_tax: Optional[float] = None
    is_impersonator: bool = False
    impersonates: Optional[str] = None
    has_liquidity: bool = True
    liquidity_locked: Optional[bool] = None


@dataclass
class TokenRiskVerdict:
    severity: str
    title: str
    description: str
    token_symbol: str
    token_address: str
    balance_at_risk: Optional[float]
    evidence: List[str]
    action: str


@dataclass
class TokenRiskScanResult:
    address: str
    scan_timestamp: str
    tokens_analyzed: int
    risky_tokens: int
    total_value_at_risk_usd: float
    token_analyses: List[TokenRiskAnalysis]
    verdicts: List[TokenRiskVerdict]


class TokenRiskScanner:
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or ETHERSCAN_API_KEY
        self.session: Optional[aiohttp.ClientSession] = None
        self.rate_limit_delay = 0.25
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
            
    async def _ensure_session(self):
        if self.session is None:
            self.session = aiohttp.ClientSession()
    
    async def _etherscan_request(self, params: Dict) -> Dict:
        await self._ensure_session()
        params['apikey'] = self.api_key
        await asyncio.sleep(self.rate_limit_delay)
        
        async with self.session.get(ETHERSCAN_BASE_URL, params=params) as resp:
            return await resp.json()
    
    async def get_token_holdings(self, address: str) -> List[Dict]:
        address = address.lower()
        
        params = {
            'module': 'account',
            'action': 'tokentx',
            'address': address,
            'startblock': 0,
            'endblock': 99999999,
            'sort': 'desc',
        }
        
        data = await self._etherscan_request(params)
        
        if data.get('status') != '1' or not data.get('result'):
            return []
        
        tokens_seen = {}
        for tx in data['result']:
            token_addr = tx.get('contractAddress', '').lower()
            if token_addr and token_addr not in tokens_seen:
                tokens_seen[token_addr] = {
                    'address': token_addr,
                    'symbol': tx.get('tokenSymbol', 'UNKNOWN'),
                    'name': tx.get('tokenName', 'Unknown Token'),
                    'decimals': int(tx.get('tokenDecimal', 18)),
                }
        
        return list(tokens_seen.values())
    
    async def get_token_balance(self, wallet: str, token: str) -> int:
        params = {
            'module': 'account',
            'action': 'tokenbalance',
            'contractaddress': token,
            'address': wallet,
            'tag': 'latest',
        }
        
        data = await self._etherscan_request(params)
        
        if data.get('status') == '1':
            return int(data.get('result', 0))
        return 0
    
    async def analyze_token_contract(self, token_address: str) -> Dict:
        token_address = token_address.lower()
        
        analysis = {
            'is_verified': False,
            'contract_age_days': None,
            'has_proxy': False,
            'source_code': None,
            'compiler_version': None,
        }
        
        params = {
            'module': 'contract',
            'action': 'getsourcecode',
            'address': token_address,
        }
        
        data = await self._etherscan_request(params)
        
        if data.get('status') == '1' and data.get('result'):
            result = data['result'][0]
            analysis['is_verified'] = result.get('ABI') != 'Contract source code not verified'
            analysis['source_code'] = result.get('SourceCode', '')
            analysis['compiler_version'] = result.get('CompilerVersion', '')
            
            if result.get('Proxy') == '1' or 'proxy' in result.get('ContractName', '').lower():
                analysis['has_proxy'] = True
        
        params = {
            'module': 'contract',
            'action': 'getcontractcreation',
            'contractaddresses': token_address,
        }
        
        data = await self._etherscan_request(params)
        
        if data.get('status') == '1' and data.get('result'):
            tx_hash = data['result'][0].get('txHash')
            if tx_hash:
                tx_params = {
                    'module': 'proxy',
                    'action': 'eth_getTransactionByHash',
                    'txhash': tx_hash,
                }
                tx_data = await self._etherscan_request(tx_params)
                
                if tx_data.get('result'):
                    block_number = int(tx_data['result'].get('blockNumber', '0'), 16)
                    
                    block_params = {
                        'module': 'block',
                        'action': 'getblockreward',
                        'blockno': block_number,
                    }
                    block_data = await self._etherscan_request(block_params)
                    
                    if block_data.get('status') == '1' and block_data.get('result'):
                        timestamp = int(block_data['result'].get('timeStamp', 0))
                        if timestamp:
                            creation_date = datetime.fromtimestamp(timestamp, timezone.utc)
                            age = datetime.now(timezone.utc) - creation_date
                            analysis['contract_age_days'] = age.days
        
        return analysis
    
    async def check_honeypot_indicators(self, token_address: str, source_code: str = None) -> Dict:
        indicators = {
            'is_honeypot': False,
            'honeypot_reason': None,
            'red_flags': [],
        }
        
        if not source_code:
            return indicators
        
        source_lower = source_code.lower()
        
        honeypot_patterns = [
            ('blacklist', 'Contains blacklist functionality'),
            ('whitelist', 'Contains whitelist restriction'),
            ('_isblacklisted', 'Has blacklist mapping'),
            ('canttrade', 'Has trading restriction'),
            ('tradingopen', 'Trading can be disabled'),
            ('antibotdelay', 'Has anti-bot that may block sells'),
            ('maxwalletamount', 'Has max wallet restriction'),
            ('cooldownenabled', 'Has cooldown that may prevent selling'),
            ('onlyowner', 'Owner-only functions that may affect transfers'),
        ]
        
        for pattern, reason in honeypot_patterns:
            if pattern in source_lower:
                indicators['red_flags'].append(reason)
        
        fee_patterns = [
            ('_taxfee', 'Has tax fee variable'),
            ('_liquidityfee', 'Has liquidity fee'),
            ('totfees', 'Has total fees calculation'),
            ('selltax', 'Has sell tax'),
            ('buytax', 'Has buy tax'),
        ]
        
        for pattern, reason in fee_patterns:
            if pattern in source_lower:
                indicators['red_flags'].append(reason)
        
        if 'function mint(' in source_lower or 'function _mint(' in source_lower:
            if 'onlyowner' in source_lower and 'mint' in source_lower:
                indicators['red_flags'].append('Owner can mint new tokens (rug risk)')
        
        critical_flags = [
            'Contains blacklist functionality',
            'Has blacklist mapping',
            'Trading can be disabled',
        ]
        
        for flag in indicators['red_flags']:
            if flag in critical_flags:
                indicators['is_honeypot'] = True
                indicators['honeypot_reason'] = flag
                break
        
        return indicators
    
    def check_impersonation(self, token_address: str, symbol: str, name: str) -> Dict:
        token_address = token_address.lower()
        symbol_lower = symbol.lower()
        name_lower = name.lower()
        
        result = {
            'is_impersonator': False,
            'impersonates': None,
            'reason': None,
        }
        
        if token_address in LEGITIMATE_TOKENS:
            return result
        
        for legit_symbol, legit_address in IMPERSONATOR_PATTERNS.items():
            if symbol_lower == legit_symbol and token_address != legit_address:
                result['is_impersonator'] = True
                result['impersonates'] = legit_symbol.upper()
                result['reason'] = f'Symbol matches {legit_symbol.upper()} but wrong contract address'
                return result
        
        suspicious_name_patterns = [
            ('tether', 'USDT'),
            ('usd coin', 'USDC'),
            ('wrapped ether', 'WETH'),
            ('wrapped bitcoin', 'WBTC'),
            ('uniswap', 'UNI'),
            ('chainlink', 'LINK'),
        ]
        
        for pattern, token in suspicious_name_patterns:
            if pattern in name_lower:
                legit_addr = IMPERSONATOR_PATTERNS.get(token.lower())
                if legit_addr and token_address != legit_addr:
                    result['is_impersonator'] = True
                    result['impersonates'] = token
                    result['reason'] = f'Name suggests {token} but wrong contract address'
                    return result
        
        return result
    
    async def scan_wallet(self, address: str, verbose: bool = True) -> TokenRiskScanResult:
        address = address.lower()
        
        if verbose:
            print(f"\n🪤 Scanning token risks for {address[:16]}...")
        
        if verbose:
            print("  [1/3] Fetching token holdings...")
        
        tokens = await self.get_token_holdings(address)
        
        if verbose:
            print(f"        Found {len(tokens)} unique tokens")
        
        if verbose:
            print("  [2/3] Analyzing token risks...")
        
        analyses = []
        
        for i, token in enumerate(tokens[:20]):
            token_addr = token['address']
            
            if token_addr in LEGITIMATE_TOKENS:
                continue
            
            if token['symbol'] in ['WETH', 'USDT', 'USDC', 'DAI', 'WBTC']:
                if token_addr in LEGITIMATE_TOKENS.values():
                    continue
            
            balance_raw = await self.get_token_balance(address, token_addr)
            if balance_raw == 0:
                continue
            
            decimals = token.get('decimals', 18)
            balance = balance_raw / (10 ** decimals)
            
            if balance < 0.0001:
                continue
            
            contract_analysis = await self.analyze_token_contract(token_addr)
            
            honeypot_check = await self.check_honeypot_indicators(
                token_addr, 
                contract_analysis.get('source_code')
            )
            
            impersonation_check = self.check_impersonation(
                token_addr,
                token['symbol'],
                token['name']
            )
            
            risk_score = 0
            risk_reasons = []
            
            if not contract_analysis['is_verified']:
                risk_score += 30
                risk_reasons.append('Contract not verified on Etherscan')
            
            age = contract_analysis.get('contract_age_days')
            if age is not None:
                if age < 7:
                    risk_score += 25
                    risk_reasons.append(f'Very new contract ({age} days old)')
                elif age < 30:
                    risk_score += 15
                    risk_reasons.append(f'New contract ({age} days old)')
            
            if honeypot_check['is_honeypot']:
                risk_score += 40
                risk_reasons.append(f'Honeypot detected: {honeypot_check["honeypot_reason"]}')
            elif honeypot_check['red_flags']:
                risk_score += len(honeypot_check['red_flags']) * 5
                for flag in honeypot_check['red_flags'][:3]:
                    risk_reasons.append(flag)
            
            if impersonation_check['is_impersonator']:
                risk_score += 35
                risk_reasons.append(f'Impersonating {impersonation_check["impersonates"]}')
            
            if contract_analysis['has_proxy']:
                risk_score += 10
                risk_reasons.append('Upgradeable proxy contract')
            
            if token_addr in KNOWN_SCAM_TOKENS:
                risk_score = 100
                risk_reasons = [f'Known scam token: {KNOWN_SCAM_TOKENS[token_addr]}']
            
            if risk_score >= 70:
                risk_level = TokenRiskLevel.CRITICAL
            elif risk_score >= 50:
                risk_level = TokenRiskLevel.HIGH
            elif risk_score >= 30:
                risk_level = TokenRiskLevel.MEDIUM
            elif risk_score >= 10:
                risk_level = TokenRiskLevel.LOW
            else:
                risk_level = TokenRiskLevel.SAFE
            
            if risk_score > 0:
                analysis = TokenRiskAnalysis(
                    token_address=token_addr,
                    token_symbol=token['symbol'],
                    token_name=token['name'],
                    balance=balance,
                    balance_usd=None,
                    risk_level=risk_level,
                    risk_score=risk_score,
                    risk_reasons=risk_reasons,
                    is_verified=contract_analysis['is_verified'],
                    contract_age_days=age,
                    has_proxy=contract_analysis['has_proxy'],
                    is_honeypot=honeypot_check['is_honeypot'],
                    honeypot_reason=honeypot_check.get('honeypot_reason'),
                    is_impersonator=impersonation_check['is_impersonator'],
                    impersonates=impersonation_check.get('impersonates'),
                )
                analyses.append(analysis)
        
        if verbose:
            print("  [3/3] Generating verdicts...")
        
        verdicts = self._generate_verdicts(analyses)
        
        risky_count = sum(1 for a in analyses if a.risk_level in [TokenRiskLevel.HIGH, TokenRiskLevel.CRITICAL])
        
        result = TokenRiskScanResult(
            address=address,
            scan_timestamp=datetime.now(timezone.utc).isoformat(),
            tokens_analyzed=len(tokens),
            risky_tokens=risky_count,
            total_value_at_risk_usd=0,
            token_analyses=analyses,
            verdicts=verdicts,
        )
        
        if verbose:
            print(f"\n  ✅ Scan complete:")
            print(f"     Tokens analyzed: {len(tokens)}")
            print(f"     Risky tokens found: {risky_count}")
            print(f"     Verdicts generated: {len(verdicts)}")
        
        return result
    
    def _generate_verdicts(self, analyses: List[TokenRiskAnalysis]) -> List[TokenRiskVerdict]:
        verdicts = []
        
        for analysis in analyses:
            if analysis.risk_level == TokenRiskLevel.SAFE:
                continue
            
            if analysis.risk_score >= 70 or analysis.is_honeypot:
                severity = 'CRITICAL'
                if analysis.is_honeypot:
                    title = f'HOLDING HONEYPOT TOKEN: {analysis.token_symbol}'
                    description = f'Wallet holds {analysis.balance:,.2f} {analysis.token_symbol} which appears to be a honeypot. Likely cannot sell.'
                    action = 'DO NOT INTERACT - Token is likely unsellable and may drain wallet on interaction'
                elif analysis.is_impersonator:
                    title = f'HOLDING FAKE TOKEN: {analysis.token_symbol}'
                    description = f'Wallet holds fake {analysis.impersonates} token. This is an impersonator contract.'
                    action = 'WORTHLESS - This is not the real token, do not attempt to use'
                else:
                    title = f'HIGH-RISK TOKEN: {analysis.token_symbol}'
                    description = f'Multiple critical risk indicators detected for {analysis.token_symbol}'
                    action = 'EXTREME CAUTION - Token has multiple red flags'
            
            elif analysis.risk_level == TokenRiskLevel.HIGH:
                severity = 'HIGH'
                if analysis.is_impersonator:
                    title = f'POSSIBLE FAKE TOKEN: {analysis.token_symbol}'
                    description = f'Token may be impersonating {analysis.impersonates}. Verify contract address.'
                    action = 'VERIFY - Check if this is the legitimate token contract'
                else:
                    title = f'RISKY TOKEN HOLDING: {analysis.token_symbol}'
                    description = f'Token has significant risk indicators: {", ".join(analysis.risk_reasons[:2])}'
                    action = 'INVESTIGATE - Research token before any interaction'
            
            elif analysis.risk_level == TokenRiskLevel.MEDIUM:
                severity = 'MEDIUM'
                title = f'TOKEN WITH CONCERNS: {analysis.token_symbol}'
                description = f'Some risk indicators: {", ".join(analysis.risk_reasons[:2])}'
                action = 'REVIEW - Understand token risks before transacting'
            
            else:
                severity = 'LOW'
                title = f'MINOR TOKEN CONCERNS: {analysis.token_symbol}'
                description = f'Minor risk indicators detected'
                action = 'AWARENESS - Minor concerns, proceed with normal caution'
            
            verdict = TokenRiskVerdict(
                severity=severity,
                title=title,
                description=description,
                token_symbol=analysis.token_symbol,
                token_address=analysis.token_address,
                balance_at_risk=analysis.balance_usd,
                evidence=analysis.risk_reasons[:5],
                action=action,
            )
            verdicts.append(verdict)
        
        severity_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}
        verdicts.sort(key=lambda v: severity_order.get(v.severity, 99))
        
        return verdicts


def generate_token_risk_report(result: TokenRiskScanResult) -> str:
    lines = [
        "",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "🪤 TOKEN RISK ANALYSIS",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "",
        f"  Target: {result.address}",
        f"  Scanned: {result.scan_timestamp}",
        "",
        f"  Tokens Analyzed:     {result.tokens_analyzed}",
        f"  Risky Tokens Found:  {result.risky_tokens}",
        "",
    ]
    
    if result.verdicts:
        lines.append("  Risk Verdicts:")
        lines.append("")
        
        for verdict in result.verdicts:
            icon = {
                'CRITICAL': '🚨',
                'HIGH': '⚠️',
                'MEDIUM': '⚡',
                'LOW': '📌',
            }.get(verdict.severity, '•')
            
            lines.append(f"  {icon} [{verdict.severity}] {verdict.title}")
            lines.append(f"     {verdict.description}")
            lines.append(f"     Token: {verdict.token_address[:20]}...")
            for evidence in verdict.evidence[:3]:
                lines.append(f"       • {evidence}")
            lines.append(f"     → {verdict.action}")
            lines.append("")
    else:
        lines.append("  ✅ No high-risk tokens detected")
        lines.append("")
    
    return "\n".join(lines)


def generate_token_risk_report_from_dict(token_risk_data: Dict) -> str:
    if not token_risk_data or token_risk_data.get('error'):
        return ""
    
    risky_tokens = token_risk_data.get('risky_tokens', 0)
    if risky_tokens == 0:
        return ""
    
    lines = [
        "",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "🪤 TOKEN RISK ANALYSIS",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "",
        f"  Tokens Analyzed:     {token_risk_data.get('tokens_analyzed', 0)}",
        f"  Risky Tokens Found:  {risky_tokens}",
        f"  Honeypots Detected:  {token_risk_data.get('honeypots_detected', 0)}",
        f"  Fake Tokens:         {token_risk_data.get('impersonators_detected', 0)}",
        "",
    ]
    
    verdicts = token_risk_data.get('verdicts', [])
    if verdicts:
        lines.append("  Risk Verdicts:")
        lines.append("")
        
        for verdict_dict in verdicts:
            severity = verdict_dict.get('severity', 'INFO')
            icon = {
                'CRITICAL': '🚨',
                'HIGH': '⚠️',
                'MEDIUM': '⚡',
                'LOW': '📌',
            }.get(severity, '•')
            
            lines.append(f"  {icon} [{severity}] {verdict_dict.get('title', '')}")
            lines.append(f"     {verdict_dict.get('description', '')}")
            token_addr = verdict_dict.get('token_address', '')
            if token_addr:
                lines.append(f"     Token: {token_addr[:20]}...")
            evidence = verdict_dict.get('evidence', [])
            for ev in evidence[:3]:
                lines.append(f"       • {ev}")
            action = verdict_dict.get('action', '')
            if action:
                lines.append(f"     → {action}")
            lines.append("")
    
    return "\n".join(lines)


async def scan_token_risks_for_profile(address: str) -> Dict:
    async with TokenRiskScanner() as scanner:
        result = await scanner.scan_wallet(address, verbose=False)
    
    return {
        'scan_timestamp': result.scan_timestamp,
        'tokens_analyzed': result.tokens_analyzed,
        'risky_tokens': result.risky_tokens,
        'total_value_at_risk_usd': result.total_value_at_risk_usd,
        'has_risky_tokens': result.risky_tokens > 0,
        'verdicts': [asdict(v) for v in result.verdicts],
        'honeypots_detected': sum(1 for a in result.token_analyses if a.is_honeypot),
        'impersonators_detected': sum(1 for a in result.token_analyses if a.is_impersonator),
    }


async def main():
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python token_risk_scanner.py <address>")
        return
    
    address = sys.argv[1]
    
    async with TokenRiskScanner() as scanner:
        result = await scanner.scan_wallet(address)
        report = generate_token_risk_report(result)
        print(report)


if __name__ == "__main__":
    asyncio.run(main())
