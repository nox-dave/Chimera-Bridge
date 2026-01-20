"""
Etherscan API Client for Basilisk

Fetches verified contract source code for vulnerability scanning.

Supports:
- Ethereum Mainnet
- Polygon
- Arbitrum
- Optimism
- BSC
- Base
- And more...

Usage:
    client = EtherscanClient(api_key="YOUR_KEY")
    
    # Fetch contract source
    source = await client.get_contract_source("0x1234...")
    
    # Fetch with specific network
    source = await client.get_contract_source("0x1234...", network="polygon")
"""

import httpx
import asyncio
from dataclasses import dataclass
from typing import Optional, Dict, List, Any
import os
import json


@dataclass
class ContractSource:
    """Contract source code data"""
    address: str
    name: str
    source_code: str
    compiler_version: str
    optimization_used: bool
    runs: int
    constructor_arguments: str
    abi: str
    implementation: Optional[str] = None
    is_proxy: bool = False
    network: str = "ethereum"


class EtherscanClient:
    """
    Etherscan API client for fetching contract source code
    
    Supports multiple networks via their respective block explorers.
    """
    
    NETWORKS = {
        "ethereum": {
            "url": "https://api.etherscan.io/v2/api",
            "env_key": "ETHERSCAN_API_KEY",
            "chainid": "1"
        },
        "polygon": {
            "url": "https://api.etherscan.io/v2/api",
            "env_key": "ETHERSCAN_API_KEY",
            "chainid": "137"
        },
        "arbitrum": {
            "url": "https://api.etherscan.io/v2/api",
            "env_key": "ETHERSCAN_API_KEY",
            "chainid": "42161"
        },
        "optimism": {
            "url": "https://api.etherscan.io/v2/api",
            "env_key": "ETHERSCAN_API_KEY",
            "chainid": "10"
        },
        "bsc": {
            "url": "https://api.etherscan.io/v2/api",
            "env_key": "ETHERSCAN_API_KEY",
            "chainid": "56"
        },
        "base": {
            "url": "https://api.etherscan.io/v2/api",
            "env_key": "ETHERSCAN_API_KEY",
            "chainid": "8453"
        },
        "avalanche": {
            "url": "https://api.etherscan.io/v2/api",
            "env_key": "ETHERSCAN_API_KEY",
            "chainid": "43114"
        },
        "fantom": {
            "url": "https://api.etherscan.io/v2/api",
            "env_key": "ETHERSCAN_API_KEY",
            "chainid": "250"
        },
    }
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        default_network: str = "ethereum",
        timeout: int = 30
    ):
        self.api_key = api_key
        self.default_network = default_network
        self.timeout = timeout
        self._api_keys: Dict[str, str] = {}
        
        self._load_api_keys()
    
    def _load_api_keys(self):
        """Load API keys from environment variables"""
        for network, config in self.NETWORKS.items():
            env_key = config["env_key"]
            key = os.environ.get(env_key)
            if key:
                self._api_keys[network] = key
        
        if self.api_key:
            self._api_keys[self.default_network] = self.api_key
    
    def _get_api_key(self, network: str) -> Optional[str]:
        """Get API key for network"""
        if network in self._api_keys:
            return self._api_keys[network]
        if self.api_key:
            return self.api_key
        return os.environ.get("ETHERSCAN_API_KEY")
    
    def _get_base_url(self, network: str) -> str:
        """Get API base URL for network"""
        if network in self.NETWORKS:
            return self.NETWORKS[network]["url"]
        return self.NETWORKS["ethereum"]["url"]
    
    async def get_contract_source(
        self,
        address: str,
        network: Optional[str] = None
    ) -> Optional[ContractSource]:
        """
        Fetch verified contract source code
        
        Args:
            address: Contract address
            network: Network name (default: ethereum)
            
        Returns:
            ContractSource object or None if not verified
        """
        network = network or self.default_network
        network = network.lower()
        api_key = self._get_api_key(network)
        base_url = self._get_base_url(network)
        
        chainid = self.NETWORKS.get(network, {}).get("chainid", "1")
        
        if not api_key:
            print(f"[!] No API key for {network}. Set ETHERSCAN_API_KEY")
            return None
        
        params = {
            "chainid": chainid,
            "module": "contract",
            "action": "getsourcecode",
            "address": address,
            "apikey": api_key
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(base_url, params=params)
                response.raise_for_status()
                data = response.json()
                
                if data.get("status") != "1":
                    message = data.get("message", "Unknown error")
                    result_msg = data.get("result", "")
                    if message == "NOTOK" and result_msg:
                        error_msg = result_msg
                    else:
                        error_msg = message
                    print(f"[!] Etherscan API error: {error_msg}")
                    return None
                
                result = data.get("result", [])
                if not result or not result[0].get("SourceCode"):
                    print(f"[!] Contract not verified: {address}")
                    return None
                
                contract_data = result[0]
                
                implementation = contract_data.get("Implementation")
                is_proxy = bool(implementation)
                
                source_code = contract_data.get("SourceCode", "")
                
                if source_code.startswith("{{"):
                    source_code = source_code[1:-1]
                    try:
                        source_json = json.loads(source_code)
                        sources = source_json.get("sources", {})
                        combined_source = []
                        for filename, content in sources.items():
                            file_content = content.get("content", "")
                            combined_source.append(f"// File: {filename}\n{file_content}")
                        source_code = "\n\n".join(combined_source)
                    except json.JSONDecodeError:
                        pass
                elif source_code.startswith("{"):
                    try:
                        source_json = json.loads(source_code)
                        sources = source_json.get("sources", {})
                        combined_source = []
                        for filename, content in sources.items():
                            file_content = content.get("content", "")
                            combined_source.append(f"// File: {filename}\n{file_content}")
                        source_code = "\n\n".join(combined_source)
                    except json.JSONDecodeError:
                        pass
                
                return ContractSource(
                    address=address,
                    name=contract_data.get("ContractName", "Unknown"),
                    source_code=source_code,
                    compiler_version=contract_data.get("CompilerVersion", ""),
                    optimization_used=contract_data.get("OptimizationUsed") == "1",
                    runs=int(contract_data.get("Runs", 0)),
                    constructor_arguments=contract_data.get("ConstructorArguments", ""),
                    abi=contract_data.get("ABI", ""),
                    implementation=implementation,
                    is_proxy=is_proxy,
                    network=network
                )
                
        except httpx.HTTPStatusError as e:
            print(f"[!] HTTP error: {e.response.status_code}")
            return None
        except httpx.RequestError as e:
            print(f"[!] Request error: {e}")
            return None
        except Exception as e:
            print(f"[!] Error fetching contract: {e}")
            return None
    
    async def get_implementation_source(
        self,
        proxy_address: str,
        network: Optional[str] = None
    ) -> Optional[ContractSource]:
        """
        Fetch implementation contract source for a proxy
        
        Args:
            proxy_address: Proxy contract address
            network: Network name
            
        Returns:
            ContractSource of implementation or None
        """
        proxy = await self.get_contract_source(proxy_address, network)
        
        if not proxy:
            return None
        
        if not proxy.is_proxy or not proxy.implementation:
            print(f"[!] Contract is not a proxy or implementation not found")
            return proxy
        
        return await self.get_contract_source(proxy.implementation, network)
    
    async def is_contract_verified(
        self,
        address: str,
        network: Optional[str] = None
    ) -> bool:
        """Check if contract is verified"""
        source = await self.get_contract_source(address, network)
        return source is not None and bool(source.source_code)
    
    def get_supported_networks(self) -> List[str]:
        """Get list of supported networks"""
        return list(self.NETWORKS.keys())
    
    async def close(self):
        """Clean up resources"""
        pass


EtherscanFetcher = EtherscanClient


CHAIN_MAPPING = {
    "ethereum": "ethereum",
    "eth": "ethereum",
    "multi-chain": "ethereum",
    "multichain": "ethereum",
    "polygon": "polygon",
    "matic": "polygon",
    "arbitrum": "arbitrum",
    "arbitrum one": "arbitrum",
    "optimism": "optimism",
    "op mainnet": "optimism",
    "bsc": "bsc",
    "binance": "bsc",
    "bnb chain": "bsc",
    "base": "base",
    "avalanche": "avalanche",
    "avax": "avalanche",
    "fantom": "fantom",
    "ftm": "fantom",
}


def normalize_chain_name(chain: str) -> str:
    """Convert chain name to Etherscan network name"""
    if not chain:
        return "ethereum"
    
    chain_lower = chain.lower().strip()
    return CHAIN_MAPPING.get(chain_lower, "ethereum")


async def main():
    """CLI for testing"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Etherscan Contract Fetcher")
    parser.add_argument("address", help="Contract address")
    parser.add_argument("--network", "-n", default="ethereum", help="Network name")
    parser.add_argument("--output", "-o", help="Output file for source code")
    parser.add_argument("--proxy", "-p", action="store_true", help="Fetch implementation for proxy")
    
    args = parser.parse_args()
    
    client = EtherscanClient()
    
    print(f"\n🔍 Fetching contract: {args.address}")
    print(f"   Network: {args.network}")
    
    if args.proxy:
        source = await client.get_implementation_source(args.address, args.network)
    else:
        source = await client.get_contract_source(args.address, args.network)
    
    if not source:
        print("❌ Failed to fetch contract")
        return
    
    print(f"\n✅ Contract: {source.name}")
    print(f"   Address: {source.address}")
    print(f"   Compiler: {source.compiler_version}")
    print(f"   Optimization: {source.optimization_used} ({source.runs} runs)")
    print(f"   Is Proxy: {source.is_proxy}")
    if source.implementation:
        print(f"   Implementation: {source.implementation}")
    print(f"   Source Size: {len(source.source_code)} bytes")
    
    if args.output:
        with open(args.output, 'w') as f:
            f.write(source.source_code)
        print(f"\n💾 Source saved to: {args.output}")
    else:
        print(f"\n📄 Source Preview (first 500 chars):")
        print("-" * 40)
        print(source.source_code[:500])
        if len(source.source_code) > 500:
            print("...")


if __name__ == "__main__":
    asyncio.run(main())
