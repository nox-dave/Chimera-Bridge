#!/usr/bin/env python3

import os
import asyncio
import aiohttp
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from enum import Enum


ETHERSCAN_API_KEY = os.getenv('ETHERSCAN_API_KEY', '')
ETHERSCAN_BASE_URL = 'https://api.etherscan.io/api'

MAX_HOPS = 3

MIN_FUNDING_ETH = 0.01

KNOWN_EXCHANGES = {
    '0x71660c4005ba85c37ccec55d0c4493e66fe775d3': 'Coinbase',
    '0x503828976d22510aad0201ac7ec88293211d23da': 'Coinbase',
    '0xddfabcdc4d8ffc6d5beaf154f18b778f892a0740': 'Coinbase',
    '0x3cd751e6b0078be393132286c442345e5dc49699': 'Coinbase',
    '0xb5d85cbf7cb3ee0d56b3bb207d5fc4b82f43f511': 'Coinbase',
    '0xeb2629a2734e272bcc07bda959863f316f4bd4cf': 'Coinbase',
    '0xa9d1e08c7793af67e9d92fe308d5697fb81d3e43': 'Coinbase',
    '0x77696bb39917c91a0c3908d577d5e322095425ca': 'Coinbase',
    '0x7c195d981abfdc3ddecd2ca0fed0958430488e34': 'Coinbase',
    '0x28c6c06298d514db089934071355e5743bf21d60': 'Binance',
    '0x21a31ee1afc51d94c2efccaa2092ad1028285549': 'Binance',
    '0xdfd5293d8e347dfe59e90efd55b2956a1343963d': 'Binance',
    '0x56eddb7aa87536c09ccc2793473599fd21a8b17f': 'Binance',
    '0x9696f59e4d72e237be84ffd425dcad154bf96976': 'Binance',
    '0x4e9ce36e442e55ecd9025b9a6e0d88485d628a67': 'Binance',
    '0xbe0eb53f46cd790cd13851d5eff43d12404d33e8': 'Binance',
    '0xf977814e90da44bfa03b6295a0616a897441acec': 'Binance',
    '0x001866ae5b3de6caa5a51543fd9fb64f524f5478': 'Binance',
    '0x2910543af39aba0cd09dbb2d50200b3e800a63d2': 'Kraken',
    '0x0a869d79a7052c7f1b55a8ebabbea3420f0d1e13': 'Kraken',
    '0xe853c56864a2ebe4576a807d26fdc4a0ada51919': 'Kraken',
    '0x267be1c1d684f78cb4f6a176c4911b741e4ffdc0': 'Kraken',
    '0x6cc5f688a315f3dc28a7781717a9a798a59fda7b': 'OKX',
    '0x236f9f97e0e62388479bf9e5ba4889e46b0273c3': 'OKX',
    '0xa7efae728d2936e78bda97dc267687568dd593f3': 'OKX',
    '0x2b5634c42055806a59e9107ed44d43c426e58258': 'KuCoin',
    '0x689c56aef474df92d44a1b70850f808488f9769c': 'KuCoin',
    '0xa1d8d972560c2f8144af871db508f0b0b10a3fbf': 'KuCoin',
    '0xd24400ae8bfebb18ca49be86258a3c749cf46853': 'Gemini',
    '0x6fc82a5fe25a5cdb58bc74600a40a69c065263f8': 'Gemini',
    '0x61edcdf5bb737adffe5043706e7c5bb1f1a56eea': 'Gemini',
    '0x876eabf441b2ee5b5b0554fd502a8e0600950cfa': 'Bitfinex',
    '0x742d35cc6634c0532925a3b844bc454e4438f44e': 'Bitfinex',
    '0x1151314c646ce4e0efd76d1af4760ae66a9fe30f': 'Bitfinex',
    '0xab5c66752a9e8167967685f1450532fb96d5d24f': 'Huobi',
    '0x6748f50f686bfbca6fe8ad62b22228b87f31ff2b': 'Huobi',
    '0xfdb16996831753d5331ff813c29a93c76834a0ad': 'Huobi',
    '0x0d0707963952f2fba59dd06f2b425ace40b492fe': 'Gate.io',
    '0x7793cd85c11a924478d358d49b05b37e91b5810f': 'Gate.io',
    '0xf89d7b9c864f589bbf53a82105107622b35eaa40': 'Bybit',
    '0x1db92e2eebc8e0c075a02bea49a2935bcd2dfcf4': 'Bybit',
    '0x6262998ced04146fa42253a5c0af90ca02dfd2a3': 'Crypto.com',
    '0x46340b20830761efd32832a74d7169b29feb9758': 'Crypto.com',
}

KNOWN_MIXERS = {
    '0xd90e2f925da726b50c4ed8d0fb90ad053324f31b': 'Tornado Cash Router',
    '0x722122df12d4e14e13ac3b6895a86e84145b6967': 'Tornado Cash 0.1 ETH',
    '0xdd4c48c0b24039969fc16d1cdf626eab821d3384': 'Tornado Cash 1 ETH',
    '0x910cbd523d972eb0a6f4cae4618ad62622b39dbf': 'Tornado Cash 10 ETH',
    '0xa160cdab225685da1d56aa342ad8841c3b53f291': 'Tornado Cash 100 ETH',
    '0xd4b88df4d29f5cedd6857912842cff3b20c8cfa3': 'Tornado Cash DAI',
    '0xfd8610d20aa15b7b2e3be39b396a1bc3516c7144': 'Tornado Cash cDAI',
    '0x07687e702b410fa43f4cb4af7fa097918ffd2730': 'Tornado Cash USDC',
    '0x94a1b5cdb22c43faab4abeb5c74999895464ddaf': 'Tornado Cash USDT',
    '0xba214c1c1928a32bffe790263e38b4af9bfcd659': 'Tornado Cash WBTC',
}

KNOWN_BRIDGES = {
    '0x99c9fc46f92e8a1c0dec1b1747d010903e884be1': 'Optimism Bridge',
    '0x3154cf16ccdb4c6d922629664174b904d80f2c35': 'Base Bridge',
    '0x4dbd4fc535ac27206064b68ffcf827b0a60bab3f': 'Arbitrum Bridge',
    '0x8315177ab297ba92a06054ce80a67ed4dbd7ed3a': 'Arbitrum Bridge 2',
    '0x2796317b0ff8538f253012862c06787adfb8ceb6': 'Synapse Bridge',
    '0x5427fefa711eff984124bfbb1ab6fbf5e3da1820': 'Celer Bridge',
    '0x88ad09518695c6c3712ac10a214be5109a655671': 'Gnosis Bridge',
}

KNOWN_DISTRIBUTORS = {
    '0x090d4613473dee047c3f2706764f49e0821d256e': 'Uniswap Merkle Distributor',
    '0x111111125421ca6dc452d289314280a0f8842a65': '1inch Airdrop',
    '0xd216153c06e857cd7f72665e0af1d7d82172f494': 'ENS Airdrop',
    '0x19cec5a628d8f205fba8ac0a8d284c71be6dd4ae': 'Blur Airdrop',
}

KNOWN_PROTOCOLS = {
    '0x7a250d5630b4cf539739df2c5dacb4c659f2488d': 'Uniswap V2 Router',
    '0xe592427a0aece92de3edee1f18e0157c05861564': 'Uniswap V3 Router',
    '0x68b3465833fb72a70ecdf485e0e4c7bd8665fc45': 'Uniswap V3 Router 2',
    '0xdef1c0ded9bec7f1a1670819833240f027b25eff': '0x Exchange',
    '0x1111111254eeb25477b68fb85ed929f73a960582': '1inch V5',
}

class FundingSourceType(Enum):
    EXCHANGE = 'exchange'
    MIXER = 'mixer'
    BRIDGE = 'bridge'
    DISTRIBUTOR = 'distributor'
    PROTOCOL = 'protocol'
    CONTRACT = 'contract'
    EOA = 'eoa'
    COINBASE = 'coinbase'
    UNKNOWN = 'unknown'


@dataclass
class FundingHop:
    address: str
    label: Optional[str]
    source_type: FundingSourceType
    tx_hash: str
    value_eth: float
    timestamp: datetime
    block_number: int


@dataclass
class FundingChain:
    target: str
    hops: List[FundingHop] = field(default_factory=list)
    origin_found: bool = False
    origin_type: Optional[FundingSourceType] = None
    origin_label: Optional[str] = None
    total_hops: int = 0
    trace_complete: bool = False
    trace_stopped_reason: Optional[str] = None


@dataclass
class FundingVerdict:
    severity: str
    title: str
    description: str
    funding_chain: List[str]
    origin: Optional[str]
    evidence: List[str]
    action: str


class FundingTracer:
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or ETHERSCAN_API_KEY
        self.session: Optional[aiohttp.ClientSession] = None
        self.rate_limit_delay = 0.25
        self._cache: Dict[str, List[Dict]] = {}
        
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
            return data
    
    def identify_address(self, address: str) -> Tuple[FundingSourceType, Optional[str]]:
        address = address.lower()
        
        if address in KNOWN_EXCHANGES:
            return FundingSourceType.EXCHANGE, KNOWN_EXCHANGES[address]
        
        if address in KNOWN_MIXERS:
            return FundingSourceType.MIXER, KNOWN_MIXERS[address]
        
        if address in KNOWN_BRIDGES:
            return FundingSourceType.BRIDGE, KNOWN_BRIDGES[address]
        
        if address in KNOWN_DISTRIBUTORS:
            return FundingSourceType.DISTRIBUTOR, KNOWN_DISTRIBUTORS[address]
        
        if address in KNOWN_PROTOCOLS:
            return FundingSourceType.PROTOCOL, KNOWN_PROTOCOLS[address]
        
        return FundingSourceType.UNKNOWN, None
    
    async def is_contract(self, address: str) -> bool:
        params = {
            'module': 'proxy',
            'action': 'eth_getCode',
            'address': address,
            'tag': 'latest',
        }
        
        data = await self._etherscan_request(params)
        code = data.get('result', '0x')
        
        return code not in ['0x', '', None] and len(code) > 2
    
    async def get_first_funding_tx(self, address: str) -> Optional[Dict]:
        address = address.lower()
        
        if address in self._cache:
            txs = self._cache[address]
        else:
            params = {
                'module': 'account',
                'action': 'txlist',
                'address': address,
                'startblock': 0,
                'endblock': 99999999,
                'sort': 'asc',
            }
            
            data = await self._etherscan_request(params)
            txs = data.get('result', []) if data.get('status') == '1' else []
            self._cache[address] = txs
        
        for tx in txs:
            if tx.get('to', '').lower() != address:
                continue
            
            if tx.get('isError') == '1':
                continue
            
            value_wei = int(tx.get('value', 0))
            value_eth = value_wei / 1e18
            
            if value_eth >= MIN_FUNDING_ETH:
                return {
                    'from': tx.get('from', '').lower(),
                    'to': address,
                    'value_eth': value_eth,
                    'tx_hash': tx.get('hash', ''),
                    'block_number': int(tx.get('blockNumber', 0)),
                    'timestamp': int(tx.get('timeStamp', 0)),
                }
        
        params = {
            'module': 'account',
            'action': 'txlistinternal',
            'address': address,
            'startblock': 0,
            'endblock': 99999999,
            'sort': 'asc',
        }
        
        data = await self._etherscan_request(params)
        internal_txs = data.get('result', []) if data.get('status') == '1' else []
        
        for tx in internal_txs:
            if tx.get('to', '').lower() != address:
                continue
            
            if tx.get('isError') == '1':
                continue
            
            value_wei = int(tx.get('value', 0))
            value_eth = value_wei / 1e18
            
            if value_eth >= MIN_FUNDING_ETH:
                return {
                    'from': tx.get('from', '').lower(),
                    'to': address,
                    'value_eth': value_eth,
                    'tx_hash': tx.get('hash', ''),
                    'block_number': int(tx.get('blockNumber', 0)),
                    'timestamp': int(tx.get('timeStamp', 0)),
                }
        
        return None
    
    async def trace_funding(self, address: str, max_hops: int = MAX_HOPS, 
                           verbose: bool = True) -> FundingChain:
        address = address.lower()
        
        if verbose:
            print(f"\n🔍 Tracing funding source for {address[:16]}...")
        
        chain = FundingChain(target=address)
        visited = {address}
        current_address = address
        
        for hop_num in range(max_hops):
            if verbose:
                print(f"  [Hop {hop_num + 1}/{max_hops}] Checking {current_address[:16]}...")
            
            source_type, label = self.identify_address(current_address)
            
            if source_type != FundingSourceType.UNKNOWN:
                if verbose:
                    print(f"    ✅ Found: {label} ({source_type.value})")
                
                chain.origin_found = True
                chain.origin_type = source_type
                chain.origin_label = label
                chain.trace_complete = True
                break
            
            funding_tx = await self.get_first_funding_tx(current_address)
            
            if not funding_tx:
                if verbose:
                    print(f"    ⚠️  No funding transaction found")
                chain.trace_stopped_reason = "No funding transaction found"
                break
            
            funder = funding_tx['from']
            
            if funder in visited:
                if verbose:
                    print(f"    ⚠️  Circular reference detected")
                chain.trace_stopped_reason = "Circular reference"
                break
            
            visited.add(funder)
            
            funder_type, funder_label = self.identify_address(funder)
            
            if funder_type == FundingSourceType.UNKNOWN:
                is_contract = await self.is_contract(funder)
                if is_contract:
                    funder_type = FundingSourceType.CONTRACT
            
            hop = FundingHop(
                address=funder,
                label=funder_label,
                source_type=funder_type,
                tx_hash=funding_tx['tx_hash'],
                value_eth=funding_tx['value_eth'],
                timestamp=datetime.fromtimestamp(funding_tx['timestamp'], timezone.utc),
                block_number=funding_tx['block_number'],
            )
            
            chain.hops.append(hop)
            chain.total_hops += 1
            
            if verbose:
                if funder_label:
                    print(f"    → Funded by: {funder_label} ({funding_tx['value_eth']:.4f} ETH)")
                else:
                    print(f"    → Funded by: {funder[:16]}... ({funding_tx['value_eth']:.4f} ETH)")
            
            if funder_type in [FundingSourceType.EXCHANGE, FundingSourceType.MIXER, 
                              FundingSourceType.BRIDGE, FundingSourceType.DISTRIBUTOR]:
                chain.origin_found = True
                chain.origin_type = funder_type
                chain.origin_label = funder_label
                chain.trace_complete = True
                break
            
            current_address = funder
        
        if not chain.trace_complete:
            chain.trace_stopped_reason = chain.trace_stopped_reason or f"Max hops ({max_hops}) reached"
        
        if verbose:
            print(f"\n  📋 Trace complete:")
            print(f"     Hops traced: {chain.total_hops}")
            print(f"     Origin found: {chain.origin_found}")
            if chain.origin_label:
                print(f"     Origin: {chain.origin_label}")
        
        return chain
    
    def generate_verdict(self, chain: FundingChain) -> Optional[FundingVerdict]:
        if not chain.hops:
            return None
        
        chain_display = [chain.target[:12] + '...']
        for hop in chain.hops:
            if hop.label:
                chain_display.append(hop.label)
            else:
                chain_display.append(hop.address[:12] + '...')
        
        if chain.origin_type == FundingSourceType.MIXER:
            return FundingVerdict(
                severity='CRITICAL',
                title='FUNDED VIA MIXER (TORNADO CASH)',
                description=f'Wallet funding traced back to {chain.origin_label}. Privacy-focused or potentially illicit funds.',
                funding_chain=chain_display,
                origin=chain.origin_label,
                evidence=[
                    f'Funding traced through {chain.total_hops} hops',
                    f'Origin: {chain.origin_label}',
                    'Tornado Cash is sanctioned by OFAC',
                    'Funds origin cannot be determined',
                ],
                action='HIGH RISK - Mixer-sourced funds may be illicit or sanctions-violating',
            )
        
        if chain.origin_type == FundingSourceType.EXCHANGE:
            return FundingVerdict(
                severity='HIGH',
                title=f'FUNDING TRACED TO {chain.origin_label.upper()}',
                description=f'Wallet funding traced back to {chain.origin_label} in {chain.total_hops} hops. KYC identity likely exists.',
                funding_chain=chain_display,
                origin=chain.origin_label,
                evidence=[
                    f'Funding chain: {" → ".join(chain_display)}',
                    f'{chain.origin_label} requires KYC for withdrawals',
                    'User likely has verified identity on file',
                    f'Trace depth: {chain.total_hops} hops',
                ],
                action=f'KYC VECTOR - User likely has identity verified with {chain.origin_label}',
            )
        
        if chain.origin_type == FundingSourceType.BRIDGE:
            return FundingVerdict(
                severity='MEDIUM',
                title=f'FUNDED VIA BRIDGE ({chain.origin_label.upper()})',
                description=f'Funds bridged from another chain via {chain.origin_label}.',
                funding_chain=chain_display,
                origin=chain.origin_label,
                evidence=[
                    f'Funding chain: {" → ".join(chain_display)}',
                    'Funds originated on another blockchain',
                    'Consider tracing on source chain',
                ],
                action='CROSS-CHAIN - Trace funding on source chain for complete picture',
            )
        
        if chain.origin_type == FundingSourceType.DISTRIBUTOR:
            return FundingVerdict(
                severity='LOW',
                title=f'FUNDED VIA AIRDROP ({chain.origin_label.upper()})',
                description=f'Initial funding from protocol airdrop/distribution.',
                funding_chain=chain_display,
                origin=chain.origin_label,
                evidence=[
                    f'Funding chain: {" → ".join(chain_display)}',
                    'Funds from protocol distribution',
                    'User was eligible for airdrop',
                ],
                action='AIRDROP - User was early participant in protocol',
            )
        
        if chain.total_hops > 0 and not chain.origin_found:
            last_hop = chain.hops[-1]
            return FundingVerdict(
                severity='INFO',
                title='FUNDING PARTIALLY TRACED',
                description=f'Traced {chain.total_hops} hops but origin not identified. Stopped at {last_hop.address[:16]}...',
                funding_chain=chain_display,
                origin=None,
                evidence=[
                    f'Traced {chain.total_hops} hops backwards',
                    f'Stopped: {chain.trace_stopped_reason}',
                    f'Last known: {last_hop.label or last_hop.address[:20]}...',
                ],
                action='MANUAL REVIEW - Continue tracing manually if needed',
            )
        
        return None


def generate_funding_report(chain: FundingChain) -> str:
    lines = [
        "",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "🔍 FUNDING SOURCE TRACE",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "",
        f"  Target: {chain.target}",
        f"  Hops Traced: {chain.total_hops}",
        f"  Origin Found: {'Yes' if chain.origin_found else 'No'}",
    ]
    
    if chain.origin_label:
        lines.append(f"  Origin: {chain.origin_label} ({chain.origin_type.value})")
    
    lines.append("")
    
    if chain.hops:
        lines.append("  Funding Chain:")
        lines.append(f"    📍 {chain.target[:20]}... (TARGET)")
        
        for i, hop in enumerate(chain.hops):
            connector = "└──" if i == len(chain.hops) - 1 else "├──"
            label = hop.label or f"{hop.address[:20]}..."
            
            icon = {
                FundingSourceType.EXCHANGE: "🏦",
                FundingSourceType.MIXER: "🌀",
                FundingSourceType.BRIDGE: "🌉",
                FundingSourceType.DISTRIBUTOR: "🎁",
                FundingSourceType.CONTRACT: "📜",
            }.get(hop.source_type, "👤")
            
            lines.append(f"    {connector} {icon} {label}")
            lines.append(f"        └─ {hop.value_eth:.4f} ETH | {hop.timestamp.strftime('%Y-%m-%d')}")
    
    lines.append("")
    
    return "\n".join(lines)


def generate_funding_report_from_dict(funding_data: Dict) -> str:
    if not funding_data or funding_data.get('error'):
        return ""
    
    lines = [
        "",
        "🔍 FUNDING SOURCE TRACE",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━",
    ]
    
    hops_traced = funding_data.get('total_hops', 0)
    lines.append(f"  Hops Traced: {hops_traced}")
    
    if funding_data.get('origin_label'):
        origin_type = funding_data.get('origin_type', 'unknown')
        lines.append(f"  Origin: {funding_data.get('origin_label')} ({origin_type})")
    
    lines.append("")
    
    funding_chain = funding_data.get('funding_chain', [])
    if funding_chain:
        lines.append("  Funding Chain:")
        
        target = funding_data.get('target', 'unknown')
        if not target:
            target = 'unknown'
        lines.append(f"    📍 {target[:16]}... (TARGET)")
        
        for i, hop in enumerate(funding_chain):
            connector = "└──" if i == len(funding_chain) - 1 else "├──"
            label = hop.get('label') or f"{hop.get('address', '')[:16]}..."
            
            hop_type = hop.get('type', 'unknown')
            icon = {
                'exchange': "🏦",
                'mixer': "🌀",
                'bridge': "🌉",
                'distributor': "🎁",
                'contract': "📜",
            }.get(hop_type, "👤")
            
            lines.append(f"    {connector} {icon} {label}")
            value_eth = hop.get('value_eth', 0)
            lines.append(f"        └─ {value_eth:.4f} ETH")
    
    lines.append("")
    
    return "\n".join(lines)


async def trace_funding_for_profile(address: str) -> Dict:
    async with FundingTracer() as tracer:
        chain = await tracer.trace_funding(address, verbose=False)
        verdict = tracer.generate_verdict(chain)
    
    result = {
        'target': address,
        'trace_timestamp': datetime.now(timezone.utc).isoformat(),
        'total_hops': chain.total_hops,
        'origin_found': chain.origin_found,
        'origin_type': chain.origin_type.value if chain.origin_type else None,
        'origin_label': chain.origin_label,
        'trace_complete': chain.trace_complete,
        'trace_stopped_reason': chain.trace_stopped_reason,
        'funding_chain': [
            {
                'address': hop.address,
                'label': hop.label,
                'type': hop.source_type.value,
                'value_eth': hop.value_eth,
                'tx_hash': hop.tx_hash,
            }
            for hop in chain.hops
        ],
    }
    
    if verdict:
        result['verdict'] = asdict(verdict)
    
    return result


async def main():
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python funding_tracer.py <address>")
        print("       python funding_tracer.py 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb")
        return
    
    address = sys.argv[1]
    
    if not address.startswith('0x') or len(address) != 42:
        print(f"Invalid address: {address}")
        return
    
    async with FundingTracer() as tracer:
        chain = await tracer.trace_funding(address)
        report = generate_funding_report(chain)
        print(report)
        
        verdict = tracer.generate_verdict(chain)
        if verdict:
            print(f"\n  ⚠️  [{verdict.severity}] {verdict.title}")
            print(f"     {verdict.description}")
            print(f"     → {verdict.action}")


if __name__ == "__main__":
    asyncio.run(main())
