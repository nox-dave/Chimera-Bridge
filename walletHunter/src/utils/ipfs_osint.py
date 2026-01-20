#!/usr/bin/env python3

import re
import json
import requests
from typing import Dict, List, Optional, Set
from datetime import datetime
from collections import defaultdict
from urllib.parse import urlparse, urlunparse

IPFS_GATEWAYS = [
    "https://ipfs.io/ipfs/",
    "https://gateway.pinata.cloud/ipfs/",
    "https://cloudflare-ipfs.com/ipfs/",
    "https://dweb.link/ipfs/",
    "https://w3s.link/ipfs/",
    "https://nftstorage.link/ipfs/",
    "https://gateway.ipfs.io/ipfs/",
    "https://ipfs.filebase.io/ipfs/",
    "https://ipfs.eth.aragon.network/ipfs/",
]

IPFS_HASH_PATTERN = re.compile(r'Qm[1-9A-HJ-NP-Za-km-z]{44}|baf[a-z0-9]{56,}')

def extract_ipfs_hash(text: str) -> Optional[str]:
    if not text:
        return None
    
    if text.startswith('ipfs://'):
        return text.replace('ipfs://', '').split('/')[0]
    
    if '/ipfs/' in text:
        parts = text.split('/ipfs/')
        if len(parts) > 1:
            hash_part = parts[1].split('/')[0].split('?')[0]
            if IPFS_HASH_PATTERN.match(hash_part):
                return hash_part
    
    match = IPFS_HASH_PATTERN.search(text)
    if match:
        return match.group(0)
    
    return None

def extract_gateway_from_uri(uri: str) -> Optional[str]:
    if not uri:
        return None
    
    if '/ipfs/' in uri:
        parts = uri.split('/ipfs/')
        if len(parts) > 0:
            gateway_part = parts[0]
            if gateway_part.startswith('http'):
                if not gateway_part.endswith('/'):
                    gateway_part += '/'
                return gateway_part + 'ipfs/'
    
    if uri.startswith('ipfs://'):
        return None
    
    return None

def extract_domain_from_url(url: str) -> Optional[str]:
    if not url:
        return None
    
    try:
        parsed = urlparse(url)
        domain = parsed.netloc or parsed.path.split('/')[0]
        if domain and '.' in domain:
            return domain.lower()
    except:
        pass
    return None

def analyze_domain(domain: str) -> Dict:
    analysis = {
        'domain': domain,
        'is_ipfs': False,
        'is_centralized': True,
        'scam_indicators': [],
        'reputation': 'unknown',
        'whois_info': None
    }
    
    if not domain:
        return analysis
    
    domain_lower = domain.lower()
    
    scam_keywords = ['lucky', 'free', 'claim', 'airdrop', 'reward', 'prize', 'winner', 'congratulations']
    suspicious_tlds = ['.xyz', '.top', '.click', '.online', '.site']
    
    for keyword in scam_keywords:
        if keyword in domain_lower:
            analysis['scam_indicators'].append(f"Contains suspicious keyword: '{keyword}'")
    
    for tld in suspicious_tlds:
        if domain_lower.endswith(tld):
            analysis['scam_indicators'].append(f"Suspicious TLD: {tld}")
    
    if len(analysis['scam_indicators']) > 0:
        analysis['reputation'] = 'suspicious'
    elif any(trusted in domain_lower for trusted in ['opensea.io', 'rarible.com', 'foundation.app', 'superrare.com', 'niftygateway.com']):
        analysis['reputation'] = 'trusted'
    else:
        analysis['reputation'] = 'unknown'
    
    return analysis

def fetch_https_metadata(url: str, timeout: int = 10) -> Optional[Dict]:
    try:
        response = requests.get(url, timeout=timeout, allow_redirects=True, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        if response.status_code == 200:
            content_type = response.headers.get('content-type', '')
            
            if 'application/json' in content_type or response.text.strip().startswith('{'):
                try:
                    return {
                        'type': 'json',
                        'content': response.json(),
                        'url': url,
                        'domain': extract_domain_from_url(url)
                    }
                except:
                    pass
            
            if 'text' in content_type:
                return {
                    'type': 'text',
                    'content': response.text[:10000],
                    'url': url,
                    'domain': extract_domain_from_url(url)
                }
    except:
        pass
    
    return None

def fetch_ipfs_content(ipfs_hash: str, timeout: int = 30, preferred_gateway: Optional[str] = None) -> Optional[Dict]:
    gateways_to_try = []
    
    if preferred_gateway:
        gateways_to_try.append(preferred_gateway)
    
    gateways_to_try.extend(IPFS_GATEWAYS)
    
    for gateway in gateways_to_try:
        try:
            if not gateway.endswith('/'):
                gateway = gateway + '/'
            if not gateway.endswith('ipfs/'):
                gateway = gateway.rstrip('/') + '/ipfs/'
            
            url = f"{gateway}{ipfs_hash}"
            response = requests.get(
                url, 
                timeout=timeout, 
                allow_redirects=True,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
            )
            
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '').lower()
                
                if 'application/json' in content_type or response.text.strip().startswith('{'):
                    try:
                        json_content = response.json()
                        return {
                            'type': 'json',
                            'content': json_content,
                            'gateway': gateway,
                            'hash': ipfs_hash
                        }
                    except json.JSONDecodeError:
                        if response.text.strip().startswith('{'):
                            try:
                                json_content = json.loads(response.text.strip())
                                return {
                                    'type': 'json',
                                    'content': json_content,
                                    'gateway': gateway,
                                    'hash': ipfs_hash
                                }
                            except:
                                pass
                
                if 'image' in content_type:
                    return {
                        'type': 'image',
                        'content_type': content_type,
                        'size': len(response.content),
                        'gateway': gateway,
                        'hash': ipfs_hash
                    }
                
                if 'text' in content_type or 'html' in content_type:
                    text_content = response.text[:10000]
                    if text_content.strip().startswith('{'):
                        try:
                            json_content = json.loads(text_content.strip())
                            return {
                                'type': 'json',
                                'content': json_content,
                                'gateway': gateway,
                                'hash': ipfs_hash
                            }
                        except:
                            pass
                    
                    return {
                        'type': 'text',
                        'content': text_content,
                        'gateway': gateway,
                        'hash': ipfs_hash
                    }
                
                return {
                    'type': 'unknown',
                    'content_type': content_type,
                    'size': len(response.content),
                    'gateway': gateway,
                    'hash': ipfs_hash
                }
        except requests.exceptions.Timeout:
            continue
        except requests.exceptions.RequestException:
            continue
        except Exception:
            continue
    
    return None

def get_nft_metadata_uri(contract_address: str, token_id: str, rpc_client=None) -> Optional[str]:
    if not rpc_client:
        return None
    
    try:
        from web3 import Web3
        
        erc721_abi = [
            {
                "constant": True,
                "inputs": [{"name": "_tokenId", "type": "uint256"}],
                "name": "tokenURI",
                "outputs": [{"name": "", "type": "string"}],
                "type": "function"
            },
            {
                "constant": True,
                "inputs": [{"name": "_tokenId", "type": "uint256"}],
                "name": "uri",
                "outputs": [{"name": "", "type": "string"}],
                "type": "function"
            }
        ]
        
        contract = rpc_client.w3.eth.contract(
            address=Web3.to_checksum_address(contract_address),
            abi=erc721_abi
        )
        
        try:
            uri = contract.functions.tokenURI(int(token_id)).call()
            if uri:
                return uri
        except:
            pass
        
        try:
            uri = contract.functions.uri(int(token_id)).call()
            if uri:
                return uri.replace('{id}', str(token_id).zfill(64))
        except:
            pass
        
        return None
    except Exception as e:
        return None

def get_current_nft_holdings(address: str, contract_address: str, rpc_client=None) -> List[str]:
    if not rpc_client:
        return []
    
    try:
        from web3 import Web3
        
        erc721_abi = [
            {
                "constant": True,
                "inputs": [{"name": "_owner", "type": "address"}],
                "name": "balanceOf",
                "outputs": [{"name": "", "type": "uint256"}],
                "type": "function"
            },
            {
                "constant": True,
                "inputs": [{"name": "_owner", "type": "address"}, {"name": "_index", "type": "uint256"}],
                "name": "tokenOfOwnerByIndex",
                "outputs": [{"name": "", "type": "uint256"}],
                "type": "function"
            }
        ]
        
        contract = rpc_client.w3.eth.contract(
            address=Web3.to_checksum_address(contract_address),
            abi=erc721_abi
        )
        
        balance = contract.functions.balanceOf(Web3.to_checksum_address(address)).call()
        
        if balance == 0:
            return []
        
        token_ids = []
        for i in range(min(balance, 10)):
            try:
                token_id = contract.functions.tokenOfOwnerByIndex(
                    Web3.to_checksum_address(address), i
                ).call()
                token_ids.append(str(token_id))
            except:
                break
        
        return token_ids
    except:
        return []

def analyze_ipfs_metadata(metadata: Dict) -> Dict:
    findings = {
        'name': metadata.get('name', ''),
        'description': metadata.get('description', ''),
        'image': metadata.get('image', ''),
        'external_url': metadata.get('external_url', ''),
        'attributes': metadata.get('attributes', []),
        'properties': metadata.get('properties', {}),
        'creator': metadata.get('creator', {}),
        'artist': metadata.get('artist', ''),
        'collection': metadata.get('collection', {}),
        'ipfs_hashes': [],
        'linked_urls': [],
        'timestamps': [],
        'usernames': [],
        'emails': [],
        'social_links': []
    }
    
    text_content = json.dumps(metadata, default=str).lower()
    
    ipfs_hash = extract_ipfs_hash(findings['image'])
    if ipfs_hash:
        findings['ipfs_hashes'].append(ipfs_hash)
    
    ipfs_hash = extract_ipfs_hash(findings['external_url'])
    if ipfs_hash:
        findings['ipfs_hashes'].append(ipfs_hash)
    
    url_pattern = re.compile(r'https?://[^\s<>"{}|\\^`\[\]]+')
    urls = url_pattern.findall(text_content)
    findings['linked_urls'] = list(set(urls))
    
    email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
    emails = email_pattern.findall(text_content)
    findings['emails'] = list(set(emails))
    
    username_pattern = re.compile(r'@[A-Za-z0-9_]+|twitter\.com/([A-Za-z0-9_]+)|discord\.gg/([A-Za-z0-9]+)')
    usernames = username_pattern.findall(text_content)
    findings['usernames'] = [u for u in usernames if u]
    
    social_pattern = re.compile(r'(twitter|instagram|discord|telegram|github)\.(com|gg|io|org)/[^\s]+')
    social = social_pattern.findall(text_content)
    findings['social_links'] = list(set([f"{s[0]}.{s[1]}" for s in social]))
    
    timestamp_pattern = re.compile(r'\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}')
    timestamps = timestamp_pattern.findall(text_content)
    findings['timestamps'] = timestamps
    
    return findings

def scan_wallet_ipfs(address: str, nft_transfers: List[Dict] = None, rpc_client=None, limit: int = 20, debug: bool = False) -> Dict:
    results = {
        'address': address,
        'ipfs_hashes_found': [],
        'metadata_analyzed': [],
        'debug_info': {
            'nft_transfers_count': 0,
            'contracts_found': 0,
            'tokens_checked': 0,
            'uris_found': 0,
            'ipfs_hashes_extracted': 0,
            'metadata_fetched': 0
        },
        'findings': {
            'total_hashes': 0,
            'unique_hashes': set(),
            'linked_urls': set(),
            'usernames': set(),
            'emails': set(),
            'social_links': set(),
            'timestamps': [],
            'creators': set(),
            'collections': set(),
            'domains': set(),
            'domain_analysis': {},
            'metadata_urls': []
        }
    }
    
    if not rpc_client:
        if debug:
            print("  ⚠️ No RPC client provided")
        return results
    
    nft_contracts = defaultdict(set)
    
    if nft_transfers:
        results['debug_info']['nft_transfers_count'] = len(nft_transfers)
        for tx in nft_transfers[:limit * 2]:
            contract = tx.get('contractAddress', '').lower()
            token_id = tx.get('tokenID', tx.get('tokenId', tx.get('token_id', '')))
            if contract and token_id:
                nft_contracts[contract].add(str(token_id))
                if debug:
                    print(f"  Found NFT: {contract[:10]}... token {token_id}")
    
    if not nft_contracts and rpc_client:
        if debug:
            print("  No NFT transfers provided, fetching from Etherscan...")
        try:
            from ..core.api_clients import EtherscanClient
            import os
            etherscan_api_key = os.getenv('ETHERSCAN_API_KEY')
            etherscan = EtherscanClient(etherscan_api_key)
            nft_transfers = etherscan.get_nft_transfers(address, limit=50)
            results['debug_info']['nft_transfers_count'] = len(nft_transfers) if nft_transfers else 0
            
            if nft_transfers:
                for tx in nft_transfers:
                    contract = tx.get('contractAddress', '').lower()
                    token_id = tx.get('tokenID', tx.get('tokenId', ''))
                    if contract and token_id:
                        nft_contracts[contract].add(str(token_id))
                        if debug:
                            print(f"  Found NFT: {contract[:10]}... token {token_id}")
        except Exception as e:
            if debug:
                print(f"  ⚠️ Error fetching NFT transfers: {e}")
    
    results['debug_info']['contracts_found'] = len(nft_contracts)
    
    if not nft_contracts:
        if debug:
            print("  No NFT contracts found")
        return results
    
    for contract, token_ids in list(nft_contracts.items())[:10]:
        if debug:
            print(f"  Checking contract {contract[:10]}... ({len(token_ids)} tokens from transfers)")
        
        current_holdings = get_current_nft_holdings(address, contract, rpc_client)
        if current_holdings:
            if debug:
                print(f"    Found {len(current_holdings)} current holdings")
            token_ids.update(current_holdings)
        
        for token_id in list(token_ids)[:5]:
            results['debug_info']['tokens_checked'] += 1
            try:
                uri = get_nft_metadata_uri(contract, token_id, rpc_client)
                if not uri:
                    if debug:
                        print(f"    Token {token_id}: No URI found")
                    continue
                
                results['debug_info']['uris_found'] += 1
                if debug:
                    print(f"    Token {token_id}: URI = {uri[:60]}...")
                
                results['findings']['metadata_urls'].append({
                    'contract': contract,
                    'token_id': token_id,
                    'uri': uri
                })
                
                domain = extract_domain_from_url(uri)
                if domain:
                    results['findings']['domains'].add(domain)
                    if domain not in results['findings']['domain_analysis']:
                        results['findings']['domain_analysis'][domain] = analyze_domain(domain)
                
                ipfs_hash = extract_ipfs_hash(uri)
                if ipfs_hash:
                    results['debug_info']['ipfs_hashes_extracted'] += 1
                    results['findings']['unique_hashes'].add(ipfs_hash)
                    results['ipfs_hashes_found'].append({
                        'contract': contract,
                        'token_id': token_id,
                        'uri': uri,
                        'ipfs_hash': ipfs_hash
                    })
                    
                    if debug:
                        print(f"    Extracted IPFS hash: {ipfs_hash}")
                    
                    preferred_gateway = extract_gateway_from_uri(uri)
                    if preferred_gateway and debug:
                        print(f"    Using preferred gateway: {preferred_gateway[:50]}...")
                    
                    content = fetch_ipfs_content(ipfs_hash, timeout=30, preferred_gateway=preferred_gateway)
                    if content:
                        if content.get('type') == 'json':
                            results['debug_info']['metadata_fetched'] += 1
                            metadata = content.get('content', {})
                            analysis = analyze_ipfs_metadata(metadata)
                            
                            results['metadata_analyzed'].append({
                                'contract': contract,
                                'token_id': token_id,
                                'analysis': analysis
                            })
                            
                            results['findings']['linked_urls'].update(analysis['linked_urls'])
                            results['findings']['usernames'].update(analysis['usernames'])
                            results['findings']['emails'].update(analysis['emails'])
                            results['findings']['social_links'].update(analysis['social_links'])
                            results['findings']['timestamps'].extend(analysis['timestamps'])
                            
                            if analysis.get('creator'):
                                creator = analysis['creator']
                                if isinstance(creator, dict):
                                    results['findings']['creators'].add(creator.get('address', ''))
                                else:
                                    results['findings']['creators'].add(str(creator))
                            
                            if analysis.get('collection'):
                                collection = analysis['collection']
                                if isinstance(collection, dict):
                                    results['findings']['collections'].add(collection.get('name', ''))
                                else:
                                    results['findings']['collections'].add(str(collection))
                            
                            if debug:
                                gateway_used = content.get('gateway', 'unknown')
                                print(f"    ✅ Fetched JSON metadata via {gateway_used[:45]}...")
                        elif debug:
                            content_type = content.get('type', 'unknown')
                            print(f"    ⚠️  Fetched {content_type} content (not JSON metadata)")
                    elif debug:
                        print(f"    ❌ Failed to fetch IPFS content (timeout or unavailable)")
                elif uri.startswith('http://') or uri.startswith('https://'):
                    if debug:
                        print(f"    Fetching HTTPS metadata from {domain}...")
                    
                    content = fetch_https_metadata(uri)
                    if content and content.get('type') == 'json':
                        results['debug_info']['metadata_fetched'] += 1
                        metadata = content.get('content', {})
                        analysis = analyze_ipfs_metadata(metadata)
                        
                        results['metadata_analyzed'].append({
                            'contract': contract,
                            'token_id': token_id,
                            'analysis': analysis,
                            'source': 'https',
                            'domain': domain
                        })
                        
                        results['findings']['linked_urls'].update(analysis['linked_urls'])
                        results['findings']['usernames'].update(analysis['usernames'])
                        results['findings']['emails'].update(analysis['emails'])
                        results['findings']['social_links'].update(analysis['social_links'])
                        results['findings']['timestamps'].extend(analysis['timestamps'])
                        
                        if analysis.get('creator'):
                            creator = analysis['creator']
                            if isinstance(creator, dict):
                                results['findings']['creators'].add(creator.get('address', ''))
                            else:
                                results['findings']['creators'].add(str(creator))
                        
                        if analysis.get('collection'):
                            collection = analysis['collection']
                            if isinstance(collection, dict):
                                results['findings']['collections'].add(collection.get('name', ''))
                            else:
                                results['findings']['collections'].add(str(collection))
                    elif debug:
                        print(f"    Failed to fetch HTTPS metadata")
                elif debug:
                    print(f"    Failed to fetch IPFS content or not JSON")
            except Exception as e:
                if debug:
                    print(f"    Error processing token {token_id}: {e}")
                continue
    
    results['findings']['total_hashes'] = len(results['findings']['unique_hashes'])
    results['findings']['unique_hashes'] = list(results['findings']['unique_hashes'])
    results['findings']['linked_urls'] = list(results['findings']['linked_urls'])
    results['findings']['usernames'] = list(results['findings']['usernames'])
    results['findings']['emails'] = list(results['findings']['emails'])
    results['findings']['social_links'] = list(results['findings']['social_links'])
    results['findings']['creators'] = list(results['findings']['creators'])
    results['findings']['collections'] = list(results['findings']['collections'])
    results['findings']['domains'] = list(results['findings']['domains'])
    
    return results

def generate_ipfs_report(ipfs_data: Dict, profile_data: Dict = None, rpc_client=None) -> str:
    lines = []
    lines.append("━" * 80)
    lines.append("🌐 IPFS & DOMAIN OSINT ANALYSIS")
    lines.append("━" * 80)
    lines.append("")
    
    findings = ipfs_data.get('findings', {})
    debug_info = ipfs_data.get('debug_info', {})
    address = ipfs_data.get('address', '')
    
    ens_data = None
    if address and rpc_client:
        try:
            from .ens_resolver import scan_wallet_ens
            ens_data = scan_wallet_ens(address, rpc_client)
        except Exception:
            pass
    
    lines.append(f"NFT Transfers Analyzed: {debug_info.get('nft_transfers_count', 0)}")
    lines.append(f"Contracts Checked: {debug_info.get('contracts_found', 0)}")
    lines.append(f"Tokens Scanned: {debug_info.get('tokens_checked', 0)}")
    lines.append(f"Metadata Files Fetched: {debug_info.get('metadata_fetched', 0)}")
    lines.append("")
    
    total_hashes = findings.get('total_hashes', 0)
    lines.append(f"IPFS Hashes Found: {total_hashes}")
    if total_hashes > 0:
        lines.append("")
        unique_hashes = findings.get('unique_hashes', [])
        if unique_hashes:
            lines.append("Unique IPFS Hashes:")
            for hash_val in unique_hashes[:15]:
                lines.append(f"  • {hash_val}")
            if len(unique_hashes) > 15:
                lines.append(f"  ... and {len(unique_hashes) - 15} more")
        lines.append("")
    else:
        lines.append("  (No IPFS hashes found - metadata may be on centralized servers)")
        lines.append("")
    
    if findings.get('domains'):
        lines.append("━" * 80)
        lines.append("🌍 DOMAIN INTELLIGENCE")
        lines.append("━" * 80)
        lines.append("")
        
        for domain in findings['domains']:
            analysis = findings.get('domain_analysis', {}).get(domain, {})
            reputation = analysis.get('reputation', 'unknown')
            scam_indicators = analysis.get('scam_indicators', [])
            
            lines.append(f"Domain: {domain}")
            lines.append(f"  Reputation: {reputation.upper()}")
            
            if scam_indicators:
                lines.append("  ⚠️  SCAM INDICATORS:")
                for indicator in scam_indicators:
                    lines.append(f"    • {indicator}")
            
            metadata_urls = findings.get('metadata_urls', [])
            if metadata_urls:
                metadata_count = sum(1 for m in metadata_urls if extract_domain_from_url(m.get('uri', '')) == domain)
                if metadata_count > 0:
                    lines.append(f"  Metadata URLs: {metadata_count}")
            
            lines.append("")
    
    if findings.get('metadata_urls'):
        lines.append("━" * 80)
        lines.append("📋 METADATA SOURCES")
        lines.append("━" * 80)
        lines.append("")
        for meta in findings['metadata_urls'][:10]:
            contract_short = meta.get('contract', '')[:10] + '...' if len(meta.get('contract', '')) > 10 else meta.get('contract', '')
            lines.append(f"  Contract: {contract_short} | Token: {meta.get('token_id', 'N/A')}")
            lines.append(f"    URI: {meta.get('uri', 'N/A')[:70]}...")
        lines.append("")
    
    if findings.get('linked_urls'):
        lines.append("━" * 80)
        lines.append("🔗 LINKED URLs")
        lines.append("━" * 80)
        lines.append("")
        for url in findings['linked_urls'][:15]:
            lines.append(f"  • {url}")
        lines.append("")
    
    if findings.get('usernames'):
        lines.append("━" * 80)
        lines.append("👤 USERNAMES/HANDLES")
        lines.append("━" * 80)
        lines.append("")
        for username in findings['usernames'][:10]:
            lines.append(f"  • {username}")
        lines.append("")
    
    if findings.get('emails'):
        lines.append("━" * 80)
        lines.append("📧 EMAIL ADDRESSES")
        lines.append("━" * 80)
        lines.append("")
        for email in findings['emails']:
            lines.append(f"  • {email}")
        lines.append("")
    
    if findings.get('social_links'):
        lines.append("━" * 80)
        lines.append("📱 SOCIAL MEDIA LINKS")
        lines.append("━" * 80)
        lines.append("")
        for link in findings['social_links'][:10]:
            lines.append(f"  • {link}")
        lines.append("")
    
    if findings.get('creators'):
        lines.append("━" * 80)
        lines.append("🎨 CREATOR ADDRESSES")
        lines.append("━" * 80)
        lines.append("")
        for creator in findings['creators']:
            if creator:
                lines.append(f"  • {creator}")
        lines.append("")
    
    if findings.get('collections'):
        lines.append("━" * 80)
        lines.append("🖼️  NFT COLLECTIONS")
        lines.append("━" * 80)
        lines.append("")
        for collection in findings['collections']:
            if collection:
                lines.append(f"  • {collection}")
        lines.append("")
    
    if findings.get('timestamps'):
        lines.append("━" * 80)
        lines.append("⏰ TIMESTAMPS FOUND")
        lines.append("━" * 80)
        lines.append("")
        for ts in findings['timestamps'][:5]:
            lines.append(f"  • {ts}")
        lines.append("")
    
    if ens_data is not None:
        lines.append("━" * 80)
        lines.append("🔗 ENS & SOCIAL IDENTITY")
        lines.append("━" * 80)
        lines.append("")
        
        if ens_data.get('has_ens'):
            lines.append(f"ENS Name: {ens_data.get('ens_name', 'N/A')}")
            lines.append("")
            
            text_records = ens_data.get('text_records', {})
            if text_records:
                lines.append("ENS Text Records:")
                for key, value in text_records.items():
                    lines.append(f"  • {key}: {value}")
                lines.append("")
            
            social_links = ens_data.get('social_links', {})
            if social_links:
                lines.append("Verified Social Links:")
                if social_links.get('twitter'):
                    lines.append(f"  • Twitter: {social_links['twitter']}")
                if social_links.get('discord'):
                    lines.append(f"  • Discord: {social_links['discord']}")
                if social_links.get('github'):
                    lines.append(f"  • GitHub: {social_links['github']}")
                if social_links.get('website'):
                    lines.append(f"  • Website: {social_links['website']}")
                if social_links.get('email'):
                    lines.append(f"  • Email: {social_links['email']}")
                lines.append("")
                
                ipfs_usernames = findings.get('usernames', [])
                ipfs_social = findings.get('social_links', [])
                if ipfs_usernames or ipfs_social:
                    lines.append("Cross-References:")
                    if social_links.get('twitter'):
                        twitter_handle = social_links['twitter'].split('/')[-1]
                        for username in ipfs_usernames:
                            if twitter_handle.lower() in str(username).lower() or str(username).lower() in twitter_handle.lower():
                                lines.append(f"  ✅ IPFS username '{username}' matches ENS Twitter")
                    for ipfs_link in ipfs_social:
                        if 'twitter.com' in ipfs_link.lower() and social_links.get('twitter'):
                            lines.append(f"  ✅ IPFS Twitter link matches ENS record")
                    lines.append("")
        else:
            lines.append("ENS Name: None (wallet does not have an ENS name)")
            lines.append("")
    
    if ipfs_data.get('metadata_analyzed'):
        lines.append("━" * 80)
        lines.append("📊 METADATA ANALYSIS SUMMARY")
        lines.append("━" * 80)
        lines.append("")
        lines.append(f"  Total metadata files analyzed: {len(ipfs_data['metadata_analyzed'])}")
        lines.append("")
    
    try:
        from .osint_verdicts import generate_all_verdicts, format_verdicts_for_report
        
        domains = findings.get('domains', [])
        profile_for_verdicts = profile_data or {}
        
        verdicts = generate_all_verdicts(profile_for_verdicts, ipfs_data, domains, ens_data)
        if verdicts:
            verdict_text = format_verdicts_for_report(verdicts)
            lines.append(verdict_text)
    except ImportError as e:
        import sys
        print(f"Warning: Could not import verdict system: {e}", file=sys.stderr)
    except Exception as e:
        import sys
        print(f"Warning: Error generating verdicts: {e}", file=sys.stderr)
    
    return "\n".join(lines)

