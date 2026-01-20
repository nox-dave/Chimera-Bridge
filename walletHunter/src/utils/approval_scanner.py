#!/usr/bin/env python3

import os
import asyncio
import aiohttp
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from enum import Enum

ETHERSCAN_API_KEY = os.getenv('ETHERSCAN_API_KEY', '')
ETHERSCAN_BASE_URL = 'https://api.etherscan.io/api'

UINT256_MAX = 2**256 - 1
UINT256_MAX_HEX = '0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff'

UNLIMITED_THRESHOLD = UINT256_MAX // 2
HIGH_VALUE_THRESHOLD_USD = 100_000
NEW_CONTRACT_DAYS = 30
SUSPICIOUS_CONTRACT_DAYS = 7

KNOWN_PROTOCOLS = {
    '0x68b3465833fb72a70ecdf485e0e4c7bd8665fc45': 'Uniswap V3 Router 2',
    '0xe592427a0aece92de3edee1f18e0157c05861564': 'Uniswap V3 Router',
    '0x7a250d5630b4cf539739df2c5dacb4c659f2488d': 'Uniswap V2 Router',
    '0x1111111254eeb25477b68fb85ed929f73a960582': '1inch V5 Router',
    '0x1111111254fb6c44bac0bed2854e76f90643097d': '1inch V4 Router',
    '0x00000000006c3852cbef3e08e8df289169ede581': 'OpenSea Seaport',
    '0x00000000000001ad428e4906ae43d8f9852d0dd6': 'OpenSea Seaport 1.4',
    '0x7d2768de32b0b80b7a3454c06bdac94a69ddc7a9': 'Aave V2 Lending Pool',
    '0x87870bca3f3fd6335c3f4ce8392d69350b4fa4e2': 'Aave V3 Pool',
    '0x3d9819210a31b4961b30ef54be2aed79b9c9cd3b': 'Compound Comptroller',
    '0xbebc44782c7db0a1a60cb6fe97d0b483032ff1c7': 'Curve 3pool',
    '0xae7ab96520de3a18e5e111b5eaab095312d7fe84': 'Lido stETH',
    '0x000000000022d473030f116ddee9f6b43ac78ba3': 'Uniswap Permit2',
}

KNOWN_MALICIOUS = {}

STABLECOINS = {
    '0xdac17f958d2ee523a2206206994597c13d831ec7': ('USDT', 6, 1.0),
    '0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48': ('USDC', 6, 1.0),
    '0x6b175474e89094c44da98b954eedeac495271d0f': ('DAI', 18, 1.0),
    '0x4fabb145d64652a948d72533023f6e7a623c7c53': ('BUSD', 18, 1.0),
}

class RiskLevel(Enum):
    CRITICAL = 'CRITICAL'
    HIGH = 'HIGH'
    MEDIUM = 'MEDIUM'
    LOW = 'LOW'
    INFO = 'INFO'

@dataclass
class TokenApproval:
    token_address: str
    token_symbol: str
    token_decimals: int
    spender_address: str
    spender_name: Optional[str]
    approval_amount: int
    approval_amount_formatted: float
    approval_value_usd: Optional[float]
    is_unlimited: bool
    tx_hash: str
    block_number: int
    timestamp: Optional[datetime]

@dataclass 
class SpenderAnalysis:
    address: str
    name: Optional[str]
    is_verified: bool
    is_known_protocol: bool
    is_known_malicious: bool
    contract_age_days: Optional[int]
    creation_tx: Optional[str]
    risk_level: RiskLevel
    risk_reasons: List[str]

@dataclass
class ApprovalVerdict:
    severity: str
    title: str
    description: str
    token_symbol: str
    token_address: str
    spender_address: str
    spender_name: Optional[str]
    amount_at_risk_usd: Optional[float]
    evidence: List[str]
    action: str

@dataclass
class ApprovalScanResult:
    address: str
    scan_timestamp: str
    total_approvals: int
    unlimited_approvals: int
    high_risk_approvals: int
    total_exposure_usd: float
    approvals: List[TokenApproval]
    spender_analyses: Dict[str, SpenderAnalysis]
    verdicts: List[ApprovalVerdict]

class ApprovalScanner:
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
            data = await resp.json()
            
            if data.get('status') == '0' and 'No transactions found' not in data.get('message', ''):
                if 'rate limit' in data.get('result', '').lower():
                    await asyncio.sleep(1)
                    return await self._etherscan_request(params)
                    
            return data
    
    async def get_approval_events(self, address: str, from_block: int = 0) -> List[Dict]:
        address = address.lower()
        approval_topic = '0x8c5be1e5ebec7d5bd14f71427d1e84f3dd0314c0f7b2291e5b200ac8c7c3b925'
        owner_topic = '0x' + address[2:].zfill(64)
        
        params = {
            'module': 'logs',
            'action': 'getLogs',
            'fromBlock': from_block,
            'toBlock': 'latest',
            'topic0': approval_topic,
            'topic1': owner_topic,
            'topic0_1_opr': 'and',
        }
        
        data = await self._etherscan_request(params)
        
        events = []
        if data.get('status') == '1' and data.get('result'):
            for log in data['result']:
                try:
                    event = self._parse_approval_event(log)
                    if event:
                        events.append(event)
                except Exception:
                    continue
                    
        return events
    
    def _parse_approval_event(self, log: Dict) -> Optional[Dict]:
        topics = log.get('topics', [])
        
        if len(topics) < 3:
            return None
            
        owner = '0x' + topics[1][-40:]
        spender = '0x' + topics[2][-40:]
        
        data = log.get('data', '0x0')
        if data == '0x':
            amount = 0
        else:
            amount = int(data, 16)
        
        return {
            'token_address': log.get('address', '').lower(),
            'owner': owner.lower(),
            'spender': spender.lower(),
            'amount': amount,
            'tx_hash': log.get('transactionHash', ''),
            'block_number': int(log.get('blockNumber', '0'), 16),
            'timestamp': int(log.get('timeStamp', '0'), 16),
        }
    
    async def analyze_spender(self, spender_address: str) -> SpenderAnalysis:
        spender_address = spender_address.lower()
        
        risk_reasons = []
        risk_level = RiskLevel.LOW
        
        if spender_address in KNOWN_PROTOCOLS:
            return SpenderAnalysis(
                address=spender_address,
                name=KNOWN_PROTOCOLS[spender_address],
                is_verified=True,
                is_known_protocol=True,
                is_known_malicious=False,
                contract_age_days=None,
                creation_tx=None,
                risk_level=RiskLevel.INFO,
                risk_reasons=['Known trusted protocol'],
            )
        
        if spender_address in KNOWN_MALICIOUS:
            return SpenderAnalysis(
                address=spender_address,
                name=KNOWN_MALICIOUS[spender_address],
                is_verified=False,
                is_known_protocol=False,
                is_known_malicious=True,
                contract_age_days=None,
                creation_tx=None,
                risk_level=RiskLevel.CRITICAL,
                risk_reasons=['Known malicious contract', KNOWN_MALICIOUS[spender_address]],
            )
        
        is_verified = await self._is_contract_verified(spender_address)
        if not is_verified:
            risk_reasons.append('Contract source code not verified')
            risk_level = RiskLevel.HIGH
        
        creation_info = await self._get_contract_creation(spender_address)
        contract_age_days = None
        creation_tx = None
        
        if creation_info:
            creation_tx = creation_info.get('tx_hash')
            creation_timestamp = creation_info.get('timestamp')
            
            if creation_timestamp:
                age = datetime.now(timezone.utc) - datetime.fromtimestamp(creation_timestamp, timezone.utc)
                contract_age_days = age.days
                
                if contract_age_days < SUSPICIOUS_CONTRACT_DAYS:
                    risk_reasons.append(f'Very new contract ({contract_age_days} days old)')
                    risk_level = RiskLevel.CRITICAL
                elif contract_age_days < NEW_CONTRACT_DAYS:
                    risk_reasons.append(f'New contract ({contract_age_days} days old)')
                    if risk_level.value not in ['CRITICAL']:
                        risk_level = RiskLevel.HIGH
        
        contract_name = await self._get_contract_name(spender_address)
        
        if not risk_reasons:
            risk_reasons.append('Unknown contract - exercise caution')
            risk_level = RiskLevel.MEDIUM
        
        return SpenderAnalysis(
            address=spender_address,
            name=contract_name,
            is_verified=is_verified,
            is_known_protocol=False,
            is_known_malicious=False,
            contract_age_days=contract_age_days,
            creation_tx=creation_tx,
            risk_level=risk_level,
            risk_reasons=risk_reasons,
        )
    
    async def _is_contract_verified(self, address: str) -> bool:
        params = {
            'module': 'contract',
            'action': 'getsourcecode',
            'address': address,
        }
        
        data = await self._etherscan_request(params)
        
        if data.get('status') == '1' and data.get('result'):
            result = data['result'][0]
            return result.get('ABI') != 'Contract source code not verified'
            
        return False
    
    async def _get_contract_creation(self, address: str) -> Optional[Dict]:
        params = {
            'module': 'contract',
            'action': 'getcontractcreation',
            'contractaddresses': address,
        }
        
        data = await self._etherscan_request(params)
        
        if data.get('status') == '1' and data.get('result'):
            result = data['result'][0]
            tx_hash = result.get('txHash')
            
            if tx_hash:
                tx_params = {
                    'module': 'proxy',
                    'action': 'eth_getTransactionByHash',
                    'txhash': tx_hash,
                }
                tx_data = await self._etherscan_request(tx_params)
                
                block_number = None
                if tx_data.get('result'):
                    block_number = int(tx_data['result'].get('blockNumber', '0'), 16)
                
                if block_number:
                    block_params = {
                        'module': 'block',
                        'action': 'getblockreward',
                        'blockno': block_number,
                    }
                    block_data = await self._etherscan_request(block_params)
                    
                    if block_data.get('status') == '1' and block_data.get('result'):
                        timestamp = int(block_data['result'].get('timeStamp', 0))
                        return {
                            'tx_hash': tx_hash,
                            'timestamp': timestamp,
                            'block_number': block_number,
                        }
            
            return {'tx_hash': tx_hash, 'timestamp': None, 'block_number': None}
            
        return None
    
    async def _get_contract_name(self, address: str) -> Optional[str]:
        params = {
            'module': 'contract',
            'action': 'getsourcecode',
            'address': address,
        }
        
        data = await self._etherscan_request(params)
        
        if data.get('status') == '1' and data.get('result'):
            result = data['result'][0]
            name = result.get('ContractName')
            if name and name != '':
                return name
                
        return None
    
    async def get_token_info(self, token_address: str) -> Dict:
        token_address = token_address.lower()
        
        if token_address in STABLECOINS:
            symbol, decimals, price = STABLECOINS[token_address]
            return {
                'symbol': symbol,
                'decimals': decimals,
                'price_usd': price,
            }
        
        params = {
            'module': 'token',
            'action': 'tokeninfo',
            'contractaddress': token_address,
        }
        
        data = await self._etherscan_request(params)
        
        if data.get('status') == '1' and data.get('result'):
            result = data['result'][0] if isinstance(data['result'], list) else data['result']
            return {
                'symbol': result.get('symbol', 'UNKNOWN'),
                'decimals': int(result.get('decimals', 18)),
                'price_usd': None,
            }
        
        return {
            'symbol': 'UNKNOWN',
            'decimals': 18,
            'price_usd': None,
        }
    
    async def scan_wallet(self, address: str, verbose: bool = True) -> ApprovalScanResult:
        address = address.lower()
        
        if verbose:
            print(f"\n🔓 Scanning token approvals for {address[:16]}...")
        
        if verbose:
            print("  [1/4] Fetching approval events...")
        
        approval_events = await self.get_approval_events(address)
        
        if verbose:
            print(f"        Found {len(approval_events)} approval events")
        
        if verbose:
            print("  [2/4] Analyzing approvals...")
        
        approvals = []
        spender_addresses = set()
        
        for event in approval_events:
            if event['amount'] == 0:
                continue
                
            token_info = await self.get_token_info(event['token_address'])
            
            decimals = token_info['decimals']
            formatted_amount = event['amount'] / (10 ** decimals)
            
            is_unlimited = event['amount'] >= UNLIMITED_THRESHOLD
            
            value_usd = None
            if token_info['price_usd']:
                value_usd = formatted_amount * token_info['price_usd']
            
            approval = TokenApproval(
                token_address=event['token_address'],
                token_symbol=token_info['symbol'],
                token_decimals=decimals,
                spender_address=event['spender'],
                spender_name=KNOWN_PROTOCOLS.get(event['spender']),
                approval_amount=event['amount'],
                approval_amount_formatted=formatted_amount,
                approval_value_usd=value_usd,
                is_unlimited=is_unlimited,
                tx_hash=event['tx_hash'],
                block_number=event['block_number'],
                timestamp=datetime.fromtimestamp(event['timestamp'], timezone.utc) if event['timestamp'] else None,
            )
            
            approvals.append(approval)
            spender_addresses.add(event['spender'])
        
        if verbose:
            print(f"  [3/4] Analyzing {len(spender_addresses)} unique spenders...")
        
        spender_analyses = {}
        for spender in spender_addresses:
            analysis = await self.analyze_spender(spender)
            spender_analyses[spender] = analysis
        
        if verbose:
            print("  [4/4] Generating risk verdicts...")
        
        verdicts = self._generate_verdicts(approvals, spender_analyses)
        
        unlimited_count = sum(1 for a in approvals if a.is_unlimited)
        high_risk_count = sum(1 for a in approvals 
                            if spender_analyses.get(a.spender_address, SpenderAnalysis(
                                address='', name=None, is_verified=False, is_known_protocol=False,
                                is_known_malicious=False, contract_age_days=None, creation_tx=None,
                                risk_level=RiskLevel.MEDIUM, risk_reasons=[]
                            )).risk_level in [RiskLevel.CRITICAL, RiskLevel.HIGH])
        
        total_exposure = sum(a.approval_value_usd or 0 for a in approvals if a.is_unlimited)
        
        result = ApprovalScanResult(
            address=address,
            scan_timestamp=datetime.now(timezone.utc).isoformat(),
            total_approvals=len(approvals),
            unlimited_approvals=unlimited_count,
            high_risk_approvals=high_risk_count,
            total_exposure_usd=total_exposure,
            approvals=approvals,
            spender_analyses=spender_analyses,
            verdicts=verdicts,
        )
        
        if verbose:
            print(f"\n  ✅ Scan complete:")
            print(f"     Total approvals: {len(approvals)}")
            print(f"     Unlimited approvals: {unlimited_count}")
            print(f"     High risk approvals: {high_risk_count}")
            print(f"     Verdicts generated: {len(verdicts)}")
        
        return result
    
    def _generate_verdicts(self, approvals: List[TokenApproval], 
                          spender_analyses: Dict[str, SpenderAnalysis]) -> List[ApprovalVerdict]:
        verdicts = []
        
        for approval in approvals:
            spender = spender_analyses.get(approval.spender_address)
            if not spender:
                continue
            
            if spender.is_known_protocol and not approval.is_unlimited:
                continue
            
            if spender.is_known_malicious:
                verdicts.append(ApprovalVerdict(
                    severity='CRITICAL',
                    title='APPROVAL TO KNOWN MALICIOUS CONTRACT',
                    description=f'Active approval to a known drainer/scam contract.',
                    token_symbol=approval.token_symbol,
                    token_address=approval.token_address,
                    spender_address=approval.spender_address,
                    spender_name=spender.name,
                    amount_at_risk_usd=approval.approval_value_usd,
                    evidence=[
                        f'Contract flagged as: {spender.name}',
                        f'Token: {approval.token_symbol}',
                        f'Approval TX: {approval.tx_hash[:16]}...',
                    ],
                    action='REVOKE IMMEDIATELY - This contract can drain your tokens',
                ))
                continue
            
            if approval.is_unlimited and not spender.is_verified:
                verdicts.append(ApprovalVerdict(
                    severity='CRITICAL',
                    title='UNLIMITED APPROVAL TO UNVERIFIED CONTRACT',
                    description=f'Unlimited {approval.token_symbol} approval to an unverified contract.',
                    token_symbol=approval.token_symbol,
                    token_address=approval.token_address,
                    spender_address=approval.spender_address,
                    spender_name=spender.name,
                    amount_at_risk_usd=approval.approval_value_usd,
                    evidence=[
                        'Contract source code not verified on Etherscan',
                        f'Unlimited approval (can drain all {approval.token_symbol})',
                        *spender.risk_reasons,
                    ],
                    action='REVOKE - Unverified contracts with unlimited access are extremely dangerous',
                ))
                continue
            
            if spender.contract_age_days is not None and spender.contract_age_days < SUSPICIOUS_CONTRACT_DAYS:
                severity = 'CRITICAL' if approval.is_unlimited else 'HIGH'
                verdicts.append(ApprovalVerdict(
                    severity=severity,
                    title=f'APPROVAL TO VERY NEW CONTRACT ({spender.contract_age_days} DAYS OLD)',
                    description=f'{"Unlimited " if approval.is_unlimited else ""}{approval.token_symbol} approval to a contract deployed {spender.contract_age_days} days ago.',
                    token_symbol=approval.token_symbol,
                    token_address=approval.token_address,
                    spender_address=approval.spender_address,
                    spender_name=spender.name,
                    amount_at_risk_usd=approval.approval_value_usd,
                    evidence=[
                        f'Contract age: {spender.contract_age_days} days',
                        f'Verified: {spender.is_verified}',
                        'New contracts are high-risk - could be phishing',
                    ],
                    action='INVESTIGATE - Very new contracts require extra scrutiny',
                ))
                continue
            
            if approval.is_unlimited and not spender.is_known_protocol:
                verdicts.append(ApprovalVerdict(
                    severity='HIGH',
                    title='UNLIMITED APPROVAL TO UNKNOWN CONTRACT',
                    description=f'Unlimited {approval.token_symbol} approval to an unknown contract.',
                    token_symbol=approval.token_symbol,
                    token_address=approval.token_address,
                    spender_address=approval.spender_address,
                    spender_name=spender.name,
                    amount_at_risk_usd=approval.approval_value_usd,
                    evidence=[
                        'Contract not in known protocols list',
                        f'Unlimited approval (can drain all {approval.token_symbol})',
                        f'Contract name: {spender.name or "Unknown"}',
                    ],
                    action='REVIEW - Ensure you recognize this contract, consider revoking',
                ))
                continue
            
            if approval.is_unlimited and spender.is_known_protocol:
                verdicts.append(ApprovalVerdict(
                    severity='MEDIUM',
                    title='UNLIMITED APPROVAL TO KNOWN PROTOCOL',
                    description=f'Unlimited {approval.token_symbol} approval to {spender.name}.',
                    token_symbol=approval.token_symbol,
                    token_address=approval.token_address,
                    spender_address=approval.spender_address,
                    spender_name=spender.name,
                    amount_at_risk_usd=approval.approval_value_usd,
                    evidence=[
                        f'Protocol: {spender.name}',
                        'Unlimited approvals carry risk even for trusted protocols',
                        'If protocol is compromised, tokens can be drained',
                    ],
                    action='CONSIDER - Reduce to exact amount needed or revoke if not actively using',
                ))
        
        severity_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3, 'INFO': 4}
        verdicts.sort(key=lambda v: severity_order.get(v.severity, 99))
        
        return verdicts

def generate_approval_report(result: ApprovalScanResult) -> str:
    lines = [
        "",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "🔓 TOKEN APPROVAL RISK ANALYSIS",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "",
        f"  Target: {result.address}",
        f"  Scanned: {result.scan_timestamp}",
        "",
        "  ┌─────────────────────────────────────────────────────────────────────────┐",
        f"  │  Total Approvals:        {result.total_approvals:>6}                                    │",
        f"  │  Unlimited Approvals:    {result.unlimited_approvals:>6}                                    │",
        f"  │  High Risk Approvals:    {result.high_risk_approvals:>6}                                    │",
        f"  │  Total Exposure (USD):   ${result.total_exposure_usd:>14,.2f}                       │",
        "  └─────────────────────────────────────────────────────────────────────────┘",
        "",
    ]
    
    if result.verdicts:
        lines.extend([
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "⚠️  RISK VERDICTS",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "",
        ])
        
        for verdict in result.verdicts:
            icon = {
                'CRITICAL': '🚨',
                'HIGH': '⚠️',
                'MEDIUM': '⚡',
                'LOW': '📌',
                'INFO': 'ℹ️',
            }.get(verdict.severity, '•')
            
            lines.append(f"{icon} [{verdict.severity}] {verdict.title}")
            lines.append(f"   {verdict.description}")
            lines.append(f"   Token: {verdict.token_symbol} ({verdict.token_address[:16]}...)")
            lines.append(f"   Spender: {verdict.spender_name or verdict.spender_address[:16]}...")
            
            if verdict.amount_at_risk_usd:
                lines.append(f"   Value at Risk: ${verdict.amount_at_risk_usd:,.2f}")
            
            for evidence in verdict.evidence[:3]:
                lines.append(f"     • {evidence}")
            
            lines.append(f"   → Action: {verdict.action}")
            lines.append("")
    else:
        lines.extend([
            "  ✅ No high-risk approvals detected",
            "",
        ])
    
    if result.approvals:
        lines.extend([
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "📋 ALL ACTIVE APPROVALS",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "",
            f"  {'Token':<10} {'Spender':<24} {'Amount':<20} {'Risk'}",
            f"  {'-'*10} {'-'*24} {'-'*20} {'-'*10}",
        ])
        
        for approval in result.approvals[:20]:
            spender_display = approval.spender_name or f"{approval.spender_address[:12]}..."
            
            if approval.is_unlimited:
                amount_display = "UNLIMITED ⚠️"
            else:
                amount_display = f"{approval.approval_amount_formatted:,.2f}"
            
            spender_analysis = result.spender_analyses.get(approval.spender_address)
            risk = spender_analysis.risk_level.value if spender_analysis else 'UNKNOWN'
            
            lines.append(f"  {approval.token_symbol:<10} {spender_display:<24} {amount_display:<20} {risk}")
        
        if len(result.approvals) > 20:
            lines.append(f"  ... and {len(result.approvals) - 20} more")
        
        lines.append("")
    
    lines.extend([
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "🔗 REVOKE TOOLS",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "",
        f"  Revoke.cash:  https://revoke.cash/address/{result.address}",
        f"  Etherscan:    https://etherscan.io/tokenapprovalchecker?search={result.address}",
        "",
    ])
    
    return "\n".join(lines)

async def scan_approvals_for_profile(address: str, api_key: str = None) -> Dict:
    async with ApprovalScanner(api_key=api_key) as scanner:
        result = await scanner.scan_wallet(address, verbose=False)
    
    return {
        'scan_timestamp': result.scan_timestamp,
        'total_approvals': result.total_approvals,
        'unlimited_approvals': result.unlimited_approvals,
        'high_risk_approvals': result.high_risk_approvals,
        'total_exposure_usd': result.total_exposure_usd,
        'verdicts': [asdict(v) for v in result.verdicts],
        'has_dangerous_approvals': result.high_risk_approvals > 0,
    }

async def main():
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python approval_scanner.py <address>")
        print("       python approval_scanner.py 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb")
        return
    
    address = sys.argv[1]
    
    if not address.startswith('0x') or len(address) != 42:
        print(f"Invalid address: {address}")
        return
    
    async with ApprovalScanner() as scanner:
        result = await scanner.scan_wallet(address)
        report = generate_approval_report(result)
        print(report)

if __name__ == "__main__":
    asyncio.run(main())
