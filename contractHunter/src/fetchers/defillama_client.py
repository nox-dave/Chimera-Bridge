"""
DeFiLlama API Client for Basilisk Contract Hunter

Mirrors Gargophias's data collection layer but for protocols/contracts.
Free API - no authentication required.

API Base: https://api.llama.fi
Docs: https://defillama.com/docs/api
"""

import httpx
import asyncio
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import json


@dataclass
class Protocol:
    """Protocol data from DeFiLlama"""
    id: str
    name: str
    slug: str
    tvl: Optional[float]
    chain: str
    chains: List[str]
    category: str
    symbol: Optional[str] = None
    url: Optional[str] = None
    twitter: Optional[str] = None
    description: Optional[str] = None
    logo: Optional[str] = None
    audits: Optional[str] = None
    audit_links: List[str] = field(default_factory=list)
    gecko_id: Optional[str] = None
    change_1h: Optional[float] = None
    change_1d: Optional[float] = None
    change_7d: Optional[float] = None
    mcap: Optional[float] = None
    
    is_audited: bool = False
    age_days: Optional[int] = None
    
    def __post_init__(self):
        if self.tvl is None:
            self.tvl = 0.0
        self.is_audited = self.audits in ["1", "2"] or len(self.audit_links) > 0
        if self.chains is None:
            self.chains = []


@dataclass 
class ProtocolDetail:
    """Detailed protocol data including contracts"""
    protocol: Protocol
    contracts: Dict[str, str] = field(default_factory=dict)
    tvl_history: List[Dict] = field(default_factory=list)
    raises: List[Dict] = field(default_factory=list)


class DeFiLlamaClient:
    """
    DeFiLlama API client for contract discovery
    
    Usage:
        client = DeFiLlamaClient()
        
        # Get all protocols
        protocols = await client.get_protocols()
        
        # Filter by criteria
        targets = await client.find_targets(
            min_tvl=100_000,
            max_tvl=10_000_000,
            categories=["Lending", "DEX"],
            chains=["Ethereum"],
            exclude_audited=True
        )
    """
    
    BASE_URL = "https://api.llama.fi"
    
    CATEGORIES = [
        "Lending", "DEX", "Derivatives", "Bridge", "Yield", "Yield Aggregator",
        "CDP", "Liquid Staking", "RWA", "Leveraged Farming", "Insurance",
        "Options", "Indexes", "Staking", "Algo-Stables", "NFT Lending",
        "Prediction Market", "Gaming", "Launchpad", "Synthetics", "Farm",
        "Reserve Currency", "NFT Marketplace", "Cross Chain", "Liquidity Manager"
    ]
    
    NON_DEFI_CATEGORIES = ["CEX", "Chain"]
    
    HIGH_RISK_CATEGORIES = [
        "Lending", "DEX", "Bridge", "Yield", "Yield Aggregator", 
        "Leveraged Farming", "CDP", "Cross Chain", "Liquid Staking",
        "Liquid Restaking", "Derivatives", "Options"
    ]
    
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self._cache: Dict[str, Any] = {}
        self._cache_time: Dict[str, datetime] = {}
        self._cache_ttl = timedelta(minutes=15)
    
    def _is_cache_valid(self, key: str) -> bool:
        """Check if cached data is still valid"""
        if key not in self._cache_time:
            return False
        return datetime.now() - self._cache_time[key] < self._cache_ttl
    
    async def _get(self, endpoint: str, use_cache: bool = True) -> Optional[Dict]:
        """Make GET request to DeFiLlama API"""
        cache_key = endpoint
        
        if use_cache and self._is_cache_valid(cache_key):
            return self._cache[cache_key]
        
        url = f"{self.BASE_URL}{endpoint}"
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()
                
                self._cache[cache_key] = data
                self._cache_time[cache_key] = datetime.now()
                
                return data
                
        except httpx.HTTPStatusError as e:
            print(f"[!] HTTP error fetching {url}: {e.response.status_code}")
            return None
        except httpx.RequestError as e:
            print(f"[!] Request error fetching {url}: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"[!] JSON decode error: {e}")
            return None
    
    async def get_protocols(self) -> List[Protocol]:
        """
        Fetch all protocols from DeFiLlama
        
        Returns list of Protocol objects with TVL, category, chains, etc.
        """
        data = await self._get("/protocols")
        
        if not data:
            print("[!] No data returned from DeFiLlama API")
            return []
        
        protocols = []
        for p in data:
            try:
                raw_tvl = p.get("tvl")
                tvl = 0.0
                if raw_tvl is not None:
                    try:
                        tvl = float(raw_tvl)
                    except (ValueError, TypeError):
                        tvl = 0.0
                
                chains = p.get("chains") or []
                if not isinstance(chains, list):
                    chains = []
                
                audit_links = p.get("audit_links") or []
                if not isinstance(audit_links, list):
                    audit_links = []
                
                protocol = Protocol(
                    id=str(p.get("id", "")),
                    name=p.get("name") or "Unknown",
                    slug=p.get("slug") or "",
                    tvl=tvl,
                    chain=p.get("chain") or "",
                    chains=chains,
                    category=p.get("category") or "",
                    symbol=p.get("symbol"),
                    url=p.get("url"),
                    twitter=p.get("twitter"),
                    description=p.get("description"),
                    logo=p.get("logo"),
                    audits=p.get("audits"),
                    audit_links=audit_links,
                    gecko_id=p.get("gecko_id"),
                    change_1h=p.get("change_1h"),
                    change_1d=p.get("change_1d"),
                    change_7d=p.get("change_7d"),
                    mcap=p.get("mcap")
                )
                protocols.append(protocol)
            except Exception as e:
                print(f"[!] Skipping malformed protocol entry: {e}")
                continue
        
        print(f"[+] Loaded {len(protocols)} protocols from DeFiLlama")
        return protocols
    
    async def get_protocol_detail(self, slug: str) -> Optional[ProtocolDetail]:
        """
        Fetch detailed protocol data including contract addresses
        
        Args:
            slug: Protocol slug (e.g., "aave", "uniswap")
        """
        data = await self._get(f"/protocol/{slug}")
        
        if not data:
            return None
        
        contracts = {}
        
        if data.get("address"):
            addr = data["address"]
            if isinstance(addr, str) and addr.startswith("0x"):
                contracts["main"] = addr
        
        if data.get("treasury"):
            addr = data["treasury"]
            if isinstance(addr, str) and addr.startswith("0x"):
                contracts["treasury"] = addr
        
        if data.get("governanceID"):
            for gov in data["governanceID"]:
                if isinstance(gov, str) and ":" in gov:
                    parts = gov.split(":")
                    if len(parts) >= 2 and parts[1].startswith("0x"):
                        contracts[f"governance_{parts[0]}"] = parts[1]
        
        if data.get("oracles"):
            for oracle in data.get("oracles", []):
                if isinstance(oracle, str) and oracle.startswith("0x"):
                    contracts["oracle"] = oracle
                    break
        
        raw_str = str(data)
        import re
        addr_matches = re.findall(r'0x[a-fA-F0-9]{40}', raw_str)
        if addr_matches and "main" not in contracts:
            contracts["main"] = addr_matches[0]
        
        protocol = Protocol(
            id=str(data.get("id", "")),
            name=data.get("name", "Unknown"),
            slug=slug,
            tvl=float(data.get("tvl", 0) or 0),
            chain=data.get("chain", ""),
            chains=data.get("chains", []) or [],
            category=data.get("category", ""),
            symbol=data.get("symbol"),
            url=data.get("url"),
            twitter=data.get("twitter"),
            description=data.get("description"),
            logo=data.get("logo"),
            audits=data.get("audits"),
            audit_links=data.get("audit_links", []) or [],
            gecko_id=data.get("gecko_id")
        )
        
        return ProtocolDetail(
            protocol=protocol,
            contracts=contracts,
            tvl_history=data.get("tvl", []),
            raises=data.get("raises", [])
        )
    
    async def get_tvl(self, slug: str) -> Optional[float]:
        """Get current TVL for a protocol"""
        data = await self._get(f"/tvl/{slug}")
        if data is not None:
            return float(data)
        return None
    
    async def find_targets(
        self,
        min_tvl: float = 100_000,
        max_tvl: Optional[float] = None,
        categories: Optional[List[str]] = None,
        chains: Optional[List[str]] = None,
        exclude_audited: bool = False,
        high_risk_only: bool = False,
        exclude_non_defi: bool = True,
        limit: int = 100
    ) -> List[Protocol]:
        """
        Find protocols matching criteria
        
        Args:
            min_tvl: Minimum TVL in USD (default: $100k)
            max_tvl: Maximum TVL in USD (optional)
            categories: Filter by categories (e.g., ["Lending", "DEX"])
            chains: Filter by chains (e.g., ["Ethereum", "Arbitrum"])
            exclude_audited: Only return unaudited protocols
            high_risk_only: Only return high-risk categories
            exclude_non_defi: Exclude CEX and other non-DeFi (default: True)
            limit: Maximum number of results
            
        Returns:
            List of Protocol objects matching criteria
        """
        protocols = await self.get_protocols()
        
        if not protocols:
            return []
        
        filtered = []
        
        for p in protocols:
            if p.tvl is None:
                continue
                
            if p.tvl < min_tvl:
                continue
            if max_tvl is not None and p.tvl > max_tvl:
                continue
            
            if exclude_non_defi and p.category in self.NON_DEFI_CATEGORIES:
                continue
            
            if categories and p.category not in categories:
                continue
            
            if high_risk_only and p.category not in self.HIGH_RISK_CATEGORIES:
                continue
            
            if chains:
                if not p.chains or not any(chain in p.chains for chain in chains):
                    continue
            
            if exclude_audited and p.is_audited:
                continue
            
            filtered.append(p)
        
        filtered.sort(key=lambda x: x.tvl or 0, reverse=True)
        
        return filtered[:limit]
    
    async def find_fresh_protocols(
        self,
        min_tvl: float = 50_000,
        growth_threshold: float = 10.0,
        limit: int = 50
    ) -> List[Protocol]:
        """
        Find protocols with rapid TVL growth (potential new targets)
        
        Args:
            min_tvl: Minimum TVL
            growth_threshold: Minimum 7-day growth percentage
            limit: Maximum results
        """
        protocols = await self.get_protocols()
        
        growing = []
        for p in protocols:
            if p.tvl is None or p.tvl < min_tvl:
                continue
            if p.change_7d is not None and p.change_7d >= growth_threshold:
                growing.append(p)
        
        growing.sort(key=lambda x: x.change_7d if x.change_7d is not None else 0, reverse=True)
        
        return growing[:limit]
    
    async def get_chains(self) -> List[Dict]:
        """Get all supported chains with their TVL"""
        return await self._get("/chains") or []
    
    def format_protocol_summary(self, protocol: Protocol) -> str:
        """Format protocol info for display"""
        audit_status = "✅ Audited" if protocol.is_audited else "❌ Unaudited"
        tvl_formatted = f"${protocol.tvl:,.0f}" if protocol.tvl else "Unknown"
        
        lines = [
            f"📊 {protocol.name} ({protocol.slug})",
            f"   Category: {protocol.category}",
            f"   TVL: {tvl_formatted}",
            f"   Chains: {', '.join(protocol.chains[:5])}{'...' if len(protocol.chains) > 5 else ''}",
            f"   Audit: {audit_status}",
        ]
        
        if protocol.change_7d:
            direction = "📈" if protocol.change_7d > 0 else "📉"
            lines.append(f"   7d Change: {direction} {protocol.change_7d:.1f}%")
        
        if protocol.url:
            lines.append(f"   URL: {protocol.url}")
        
        return "\n".join(lines)
    
    async def close(self):
        """Clean up resources"""
        pass


async def main():
    """CLI interface for testing"""
    import argparse
    
    parser = argparse.ArgumentParser(description="DeFiLlama Contract Hunter")
    parser.add_argument("--min-tvl", type=float, default=100_000, help="Minimum TVL in USD")
    parser.add_argument("--max-tvl", type=float, help="Maximum TVL in USD")
    parser.add_argument("--category", type=str, help="Filter by category")
    parser.add_argument("--chain", type=str, help="Filter by chain")
    parser.add_argument("--unaudited", action="store_true", help="Only unaudited protocols")
    parser.add_argument("--high-risk", action="store_true", help="Only high-risk categories")
    parser.add_argument("--growing", action="store_true", help="Find fast-growing protocols")
    parser.add_argument("--limit", type=int, default=20, help="Maximum results")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    
    args = parser.parse_args()
    
    client = DeFiLlamaClient()
    
    print("🔱 Chimera contract analysis — DeFiLlama discovery")
    print("=" * 50)
    
    if args.growing:
        print(f"\n🚀 Finding fast-growing protocols (min TVL: ${args.min_tvl:,.0f})...\n")
        protocols = await client.find_fresh_protocols(
            min_tvl=args.min_tvl,
            limit=args.limit
        )
    else:
        categories = [args.category] if args.category else None
        chains = [args.chain] if args.chain else None
        
        print(f"\n🎯 Hunting targets...")
        print(f"   Min TVL: ${args.min_tvl:,.0f}")
        if args.max_tvl:
            print(f"   Max TVL: ${args.max_tvl:,.0f}")
        if categories:
            print(f"   Categories: {categories}")
        if chains:
            print(f"   Chains: {chains}")
        if args.unaudited:
            print(f"   Filter: Unaudited only")
        if args.high_risk:
            print(f"   Filter: High-risk categories only")
        print()
        
        protocols = await client.find_targets(
            min_tvl=args.min_tvl,
            max_tvl=args.max_tvl,
            categories=categories,
            chains=chains,
            exclude_audited=args.unaudited,
            high_risk_only=args.high_risk,
            limit=args.limit
        )
    
    if args.json:
        import json
        output = [{
            "name": p.name,
            "slug": p.slug,
            "tvl": p.tvl,
            "category": p.category,
            "chains": p.chains,
            "audited": p.is_audited,
            "change_7d": p.change_7d,
            "url": p.url
        } for p in protocols]
        print(json.dumps(output, indent=2))
    else:
        print(f"Found {len(protocols)} targets:\n")
        for i, p in enumerate(protocols, 1):
            print(f"[{i}] {client.format_protocol_summary(p)}")
            print()
    
    if not args.json:
        total_tvl = sum(p.tvl for p in protocols)
        unaudited = sum(1 for p in protocols if not p.is_audited)
        print("=" * 50)
        print(f"📊 Summary:")
        print(f"   Total protocols: {len(protocols)}")
        print(f"   Combined TVL: ${total_tvl:,.0f}")
        print(f"   Unaudited: {unaudited} ({unaudited/len(protocols)*100:.0f}%)" if protocols else "")


if __name__ == "__main__":
    asyncio.run(main())
