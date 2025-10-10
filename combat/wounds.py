"""
Wound System - Physical Injuries

This module defines the wound system for realistic combat simulation.
Wounds track physical damage to body parts including:
- Type of wound (laceration, puncture, crush, etc.)
- Depth and severity
- Blood loss rate
- Affected tissues

STATUS: Skeleton implementation with stubs
TODO: Implement full wound mechanics in Phase 3
"""

from enum import Enum
from typing import Optional, List
from dataclasses import dataclass, field


class WoundType(Enum):
    """Types of physical wounds"""
    LACERATION = "laceration"    # Рваная рана (slash, cut)
    PUNCTURE = "puncture"        # Колотая рана (stab, pierce)
    CRUSH = "crush"              # Раздробленная (blunt trauma)
    BURN = "burn"                # Ожог
    FROSTBITE = "frostbite"      # Обморожение


@dataclass
class Wound:
    """
    Represents a physical wound on a body part.
    
    Attributes:
        location: Body part location (e.g., "neck", "torso", "left_arm")
        type: Type of wound (WoundType enum)
        depth_cm: Depth of wound in centimeters
        bleeding_rate_ml_per_sec: Blood loss rate in ml/second
        tissues_damaged: List of damaged tissues (e.g., ["skin", "muscle", "artery"])
        created_at_turn: Game turn when wound was created
        bone_damage: Optional description of bone damage
        infection_risk: Risk of infection (0.0-1.0)
    
    Example:
        >>> wound = Wound(
        ...     location="neck",
        ...     type=WoundType.LACERATION,
        ...     depth_cm=3.0,
        ...     bleeding_rate_ml_per_sec=15.0,
        ...     tissues_damaged=["skin", "muscle", "artery"],
        ...     created_at_turn=5
        ... )
        >>> wound.is_critical()
        True
    """
    
    location: str
    type: WoundType
    depth_cm: float
    bleeding_rate_ml_per_sec: float
    tissues_damaged: List[str]
    created_at_turn: int
    bone_damage: Optional[str] = None
    infection_risk: float = 0.0
    
    def is_critical(self) -> bool:
        """
        Determines if wound is life-threatening.
        
        Critical wounds:
        - Heavy bleeding (>10 ml/sec)
        - Arterial damage
        - Deep wounds (>5 cm)
        
        Returns:
            bool: True if wound is critical
        
        TODO: Implement full criticality logic
        """
        # STUB: Simple implementation
        return (
            self.bleeding_rate_ml_per_sec > 10 or
            "artery" in self.tissues_damaged or
            self.depth_cm > 5.0
        )
    
    def tick(self, delta_turns: int = 1) -> float:
        """
        Update wound state over time.
        
        Simulates:
        - Natural blood clotting (bleeding slows down)
        - Wound worsening (infection, etc.)
        
        Args:
            delta_turns: Number of turns passed
        
        Returns:
            float: Total blood lost during this tick (ml)
        
        TODO: Implement realistic clotting mechanics
        TODO: Add infection progression
        TODO: Add pain escalation
        """
        # STUB: Simple implementation
        blood_lost = self.bleeding_rate_ml_per_sec * delta_turns
        
        # Natural clotting (5% reduction per turn)
        self.bleeding_rate_ml_per_sec *= 0.95
        
        return blood_lost
    
    def to_dict(self) -> dict:
        """Serialize wound to dictionary for saving"""
        return {
            "location": self.location,
            "type": self.type.value,
            "depth_cm": self.depth_cm,
            "bleeding_rate_ml_per_sec": self.bleeding_rate_ml_per_sec,
            "tissues_damaged": self.tissues_damaged,
            "created_at_turn": self.created_at_turn,
            "bone_damage": self.bone_damage,
            "infection_risk": self.infection_risk
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Wound':
        """Deserialize wound from dictionary"""
        return cls(
            location=data["location"],
            type=WoundType(data["type"]),
            depth_cm=data["depth_cm"],
            bleeding_rate_ml_per_sec=data["bleeding_rate_ml_per_sec"],
            tissues_damaged=data["tissues_damaged"],
            created_at_turn=data["created_at_turn"],
            bone_damage=data.get("bone_damage"),
            infection_risk=data.get("infection_risk", 0.0)
        )


# ===================================
# HELPER FUNCTIONS (STUBS)
# ===================================

def create_laceration(
    location: str,
    depth_cm: float,
    turn: int
) -> Wound:
    """
    Factory function for creating laceration wounds.
    
    TODO: Implement realistic tissue damage calculation
    TODO: Calculate bleeding rate based on location and depth
    """
    # STUB: Simple calculation
    bleeding_rate = depth_cm * 2.0  # Simplified
    
    return Wound(
        location=location,
        type=WoundType.LACERATION,
        depth_cm=depth_cm,
        bleeding_rate_ml_per_sec=bleeding_rate,
        tissues_damaged=["skin", "muscle"],  # Simplified
        created_at_turn=turn
    )


def create_puncture(
    location: str,
    depth_cm: float,
    turn: int
) -> Wound:
    """
    Factory function for creating puncture wounds.
    
    TODO: Implement organ damage logic
    TODO: Calculate internal bleeding
    """
    # STUB: Simple calculation
    bleeding_rate = depth_cm * 1.5  # Punctures bleed less than lacerations
    
    return Wound(
        location=location,
        type=WoundType.PUNCTURE,
        depth_cm=depth_cm,
        bleeding_rate_ml_per_sec=bleeding_rate,
        tissues_damaged=["skin", "muscle"],  # Simplified
        created_at_turn=turn
    )