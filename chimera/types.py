"""
Chimera Shared Types

Data structures shared between contractHunter and walletHunter.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum
from datetime import datetime


class Severity(Enum):
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"
    INFO = "Informational"


class RiskLevel(Enum):
    EXTREME = "Extreme"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"
    SAFE = "Safe"


@dataclass
class VulnerableContract:
    address: str
    chain: str
    protocol_name: str
    tvl: float
    category: str
    
    vulnerability_count: int = 0
    critical_count: int = 0
    high_count: int = 0
    vulnerability_types: List[str] = field(default_factory=list)
    
    priority_score: int = 0
    is_audited: bool = False
    source_available: bool = False


@dataclass
class TrackedWallet:
    address: str
    chain: str = "ethereum"
    
    total_value_usd: float = 0
    eth_balance: float = 0
    token_count: int = 0
    
    tx_count: int = 0
    first_seen: Optional[str] = None
    last_active: Optional[str] = None
    
    is_whale: bool = False
    is_contract: bool = False
    labels: List[str] = field(default_factory=list)
    
    risk_score: int = 0
    risk_factors: List[str] = field(default_factory=list)


@dataclass
class Exposure:
    wallet: TrackedWallet
    contract: VulnerableContract
    
    exposure_amount_usd: float = 0
    exposure_token: str = ""
    exposure_type: str = ""
    
    position_opened: Optional[str] = None
    last_interaction: Optional[str] = None
    can_withdraw: bool = True
    
    risk_level: RiskLevel = RiskLevel.MEDIUM
    
    def calculate_risk(self) -> RiskLevel:
        if self.contract.critical_count > 0 and self.exposure_amount_usd > 100_000:
            return RiskLevel.EXTREME
        elif self.contract.critical_count > 0 or self.exposure_amount_usd > 100_000:
            return RiskLevel.HIGH
        elif self.contract.high_count > 0 or self.exposure_amount_usd > 10_000:
            return RiskLevel.MEDIUM
        elif self.contract.vulnerability_count > 0:
            return RiskLevel.LOW
        return RiskLevel.SAFE


@dataclass
class BridgeResult:
    contract: VulnerableContract
    
    exposures: List[Exposure] = field(default_factory=list)
    
    total_value_at_risk: float = 0
    wallet_count: int = 0
    extreme_risk_count: int = 0
    high_risk_count: int = 0
    
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def summarize(self) -> Dict:
        return {
            "contract": self.contract.address,
            "protocol": self.contract.protocol_name,
            "tvl": self.contract.tvl,
            "vulnerabilities": self.contract.vulnerability_count,
            "total_value_at_risk": self.total_value_at_risk,
            "wallets_exposed": self.wallet_count,
            "extreme_risk_wallets": self.extreme_risk_count,
            "high_risk_wallets": self.high_risk_count,
        }
