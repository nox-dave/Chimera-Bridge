#!/usr/bin/env python3

from typing import Dict, List, Optional
from web3 import Web3

ENS_REGISTRY = "0x00000000000C2E074eC69A0dFb2997BA6C7d2e1e"
PUBLIC_RESOLVER = "0x4976fb03C32e5B8cfe2b6cCB31c09Ba78EBaBa41"
REVERSE_REGISTRAR = "0x084b1c3C81545d370f3634392De611CaaBFf8146"

ENS_REGISTRY_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "node", "type": "bytes32"}],
        "name": "resolver",
        "outputs": [{"name": "", "type": "address"}],
        "type": "function"
    }
]

RESOLVER_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "node", "type": "bytes32"}],
        "name": "addr",
        "outputs": [{"name": "", "type": "address"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [{"name": "node", "type": "bytes32"}, {"name": "key", "type": "string"}],
        "name": "text",
        "outputs": [{"name": "", "type": "string"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [{"name": "node", "type": "bytes32"}],
        "name": "name",
        "outputs": [{"name": "", "type": "string"}],
        "type": "function"
    }
]

REVERSE_RESOLVER_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "addr", "type": "address"}],
        "name": "node",
        "outputs": [{"name": "", "type": "bytes32"}],
        "type": "function"
    }
]

def namehash(name: str) -> bytes:
    if not name:
        return b'\x00' * 32
    
    parts = name.split('.')
    node = b'\x00' * 32
    
    for part in reversed(parts):
        label_hash = Web3.keccak(text=part)
        node = Web3.keccak(node + label_hash)
    
    return node

def normalize_ens_name(name: str) -> str:
    if not name:
        return ""
    
    name = name.strip().lower()
    if not name.endswith('.eth'):
        name = name + '.eth'
    
    return name

def resolve_ens_to_address(ens_name: str, rpc_client) -> Optional[str]:
    if not ens_name or not rpc_client:
        return None
    
    try:
        ens_name = normalize_ens_name(ens_name)
        node = namehash(ens_name)
        
        registry = rpc_client.w3.eth.contract(
            address=Web3.to_checksum_address(ENS_REGISTRY),
            abi=ENS_REGISTRY_ABI
        )
        
        resolver_address = registry.functions.resolver(node).call()
        if not resolver_address or resolver_address == '0x0000000000000000000000000000000000000000':
            return None
        
        resolver = rpc_client.w3.eth.contract(
            address=Web3.to_checksum_address(resolver_address),
            abi=RESOLVER_ABI
        )
        
        address = resolver.functions.addr(node).call()
        if address and address != '0x0000000000000000000000000000000000000000':
            return Web3.to_checksum_address(address)
        
        return None
    except Exception:
        return None

def resolve_address_to_ens(address: str, rpc_client) -> Optional[str]:
    if not address or not rpc_client:
        return None
    
    try:
        address = Web3.to_checksum_address(address)
        reverse_node = namehash(f"{address[2:].lower()}.addr.reverse")
        
        registry = rpc_client.w3.eth.contract(
            address=Web3.to_checksum_address(ENS_REGISTRY),
            abi=ENS_REGISTRY_ABI
        )
        
        resolver_address = registry.functions.resolver(reverse_node).call()
        if not resolver_address or resolver_address == '0x0000000000000000000000000000000000000000':
            return None
        
        resolver = rpc_client.w3.eth.contract(
            address=Web3.to_checksum_address(resolver_address),
            abi=RESOLVER_ABI
        )
        
        ens_name = resolver.functions.name(reverse_node).call()
        if ens_name and ens_name.strip():
            return ens_name.strip()
        
        return None
    except Exception:
        return None

def get_ens_text_record(ens_name: str, key: str, rpc_client) -> Optional[str]:
    if not ens_name or not key or not rpc_client:
        return None
    
    try:
        ens_name = normalize_ens_name(ens_name)
        node = namehash(ens_name)
        
        registry = rpc_client.w3.eth.contract(
            address=Web3.to_checksum_address(ENS_REGISTRY),
            abi=ENS_REGISTRY_ABI
        )
        
        resolver_address = registry.functions.resolver(node).call()
        if not resolver_address or resolver_address == '0x0000000000000000000000000000000000000000':
            return None
        
        resolver = rpc_client.w3.eth.contract(
            address=Web3.to_checksum_address(resolver_address),
            abi=RESOLVER_ABI
        )
        
        text_value = resolver.functions.text(node, key).call()
        if text_value and text_value.strip():
            return text_value.strip()
        
        return None
    except Exception:
        return None

def get_all_ens_text_records(ens_name: str, rpc_client) -> Dict[str, str]:
    if not ens_name or not rpc_client:
        return {}
    
    text_records = {}
    common_keys = [
        'com.twitter',
        'com.discord',
        'com.github',
        'url',
        'email',
        'description',
        'avatar',
        'com.reddit',
        'com.telegram',
        'com.instagram'
    ]
    
    for key in common_keys:
        value = get_ens_text_record(ens_name, key, rpc_client)
        if value:
            text_records[key] = value
    
    return text_records

def check_ens_social_links(ens_name: str, rpc_client) -> Dict[str, str]:
    if not ens_name or not rpc_client:
        return {}
    
    text_records = get_all_ens_text_records(ens_name, rpc_client)
    social_links = {}
    
    twitter = text_records.get('com.twitter', '')
    if twitter:
        if not twitter.startswith('@'):
            twitter = '@' + twitter
        social_links['twitter'] = f"https://twitter.com/{twitter.lstrip('@')}"
    
    discord = text_records.get('com.discord', '')
    if discord:
        social_links['discord'] = discord
    
    github = text_records.get('com.github', '')
    if github:
        if not github.startswith('http'):
            github = f"https://github.com/{github.lstrip('@')}"
        social_links['github'] = github
    
    website = text_records.get('url', '')
    if website:
        if not website.startswith('http'):
            website = f"https://{website}"
        social_links['website'] = website
    
    email = text_records.get('email', '')
    if email:
        social_links['email'] = email
    
    return social_links

def scan_wallet_ens(address: str, rpc_client) -> Dict:
    if not address or not rpc_client:
        return {
            'address': address,
            'ens_name': None,
            'text_records': {},
            'social_links': {},
            'has_ens': False,
            'has_social_links': False
        }
    
    try:
        ens_name = resolve_address_to_ens(address, rpc_client)
        
        if not ens_name:
            return {
                'address': address,
                'ens_name': None,
                'text_records': {},
                'social_links': {},
                'has_ens': False,
                'has_social_links': False
            }
        
        text_records = get_all_ens_text_records(ens_name, rpc_client)
        social_links = check_ens_social_links(ens_name, rpc_client)
        
        return {
            'address': address,
            'ens_name': ens_name,
            'text_records': text_records,
            'social_links': social_links,
            'has_ens': True,
            'has_social_links': len(social_links) > 0
        }
    except Exception:
        return {
            'address': address,
            'ens_name': None,
            'text_records': {},
            'social_links': {},
            'has_ens': False,
            'has_social_links': False
        }

