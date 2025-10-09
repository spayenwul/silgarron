"""
Status Effects System - Physical Conditions

This module defines status effects that result from physical trauma:
- Bleeding
- Shock
- Pain
- Unconsciousness
- Fatigue
- Broken bones
- Paralysis

STATUS: Skeleton implementation with stubs
TODO: Implement full effect mechanics and interactions in Phase 3
"""

from enum import Enum
from typing import Optional
from dataclasses import dataclass


class EffectType(Enum):
    """Types of physical status effects"""
    BLEEDING = "bleeding"           # Active blood loss
    SHOCK = "shock"                 # Traumatic shock (low blood pressure)
    UNCONSCIOUS = "unconscious"     # Loss of consciousness
    PAIN = "pain"                   # Pain (reduces effectiveness)
    FATIGUE = "fatigue"             # Physical exhaustion
    BROKEN_BONE = "broken_bone"     # Fractured bone (mobility loss)
    PARALYSIS = "paralysis"         # Nerve damage (immobilization)


@dataclass
class StatusEffect:
    """
    Represents a physical status effect on a character.
    
    Attributes:
        type: Type of effect (EffectType enum)
        severity: Severity level (0.0-1.0)
        duration_remaining: Turns remaining (999 = permanent until treated)
        source: What caused this effect (e.g., "neck_wound", "blood_loss")
        applied_at_turn: When effect was applied
    
    Example:
        >>> effect = StatusEffect(
        ...     type=EffectType.BLEEDING,
        ...     severity=0.8,
        ...     duration_remaining=999,
        ...     source="sword_laceration",
        ...     applied_at_turn=5
        ... )
        >>> effect.tick(1)
        >>> effect.duration_remaining
        998
    """
    
    type: EffectType
    severity: float              # 0.0-1.0
    duration_remaining: int      # Turns (999 = until treated)
    source: str                  # What caused this effect
    applied_at_turn: int
    
    def __post_init__(self):
        """Validate severity"""
        if not 0.0 <= self.severity <= 1.0:
            raise ValueError(f"Severity must be 0.0-1.0, got {self.severity}")
    
    def tick(self, delta_turns: int = 1):
        """
        Update effect state over time.
        
        Some effects:
        - Fade naturally (pain)
        - Worsen over time (bleeding, infection)
        - Remain constant (broken bone)
        
        Args:
            delta_turns: Number of turns passed
        
        TODO: Implement effect-specific progression logic
        TODO: Add effect interactions (e.g., shock increases from bleeding)
        """
        # STUB: Simple implementation
        self.duration_remaining -= delta_turns
        
        # Some effects worsen
        if self.type == EffectType.BLEEDING:
            self.severity = min(1.0, self.severity * 1.05)
        
        # Some effects fade
        elif self.type == EffectType.PAIN:
            self.severity = max(0.0, self.severity * 0.95)
    
    def is_expired(self) -> bool:
        """Check if effect duration has ended"""
        return self.duration_remaining <= 0
    
    def get_modifier(self) -> float:
        """
        Get numerical modifier for game mechanics.
        
        Returns:
            float: Modifier value (0.0-1.0, where 1.0 = full penalty)
        
        TODO: Implement effect-specific modifiers
        TODO: Add diminishing returns for stacking effects
        """
        # STUB: Simple linear scaling
        return self.severity
    
    def to_dict(self) -> dict:
        """Serialize effect to dictionary"""
        return {
            "type": self.type.value,
            "severity": self.severity,
            "duration_remaining": self.duration_remaining,
            "source": self.source,
            "applied_at_turn": self.applied_at_turn
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'StatusEffect':
        """Deserialize effect from dictionary"""
        return cls(
            type=EffectType(data["type"]),
            severity=data["severity"],
            duration_remaining=data["duration_remaining"],
            source=data["source"],
            applied_at_turn=data["applied_at_turn"]
        )


# ===================================
# HELPER FUNCTIONS (STUBS)
# ===================================

def create_bleeding_effect(
    severity: float,
    source: str,
    turn: int
) -> StatusEffect:
    """
    Factory function for bleeding effects.
    
    TODO: Calculate severity from wound properties
    TODO: Add blood loss tracking
    """
    return StatusEffect(
        type=EffectType.BLEEDING,
        severity=severity,
        duration_remaining=999,  # Until treated
        source=source,
        applied_at_turn=turn
    )


def create_shock_effect(
    severity: float,
    duration: int,
    turn: int
) -> StatusEffect:
    """
    Factory function for shock effects.
    
    TODO: Calculate from blood loss and trauma
    TODO: Add organ failure risk
    """
    return StatusEffect(
        type=EffectType.SHOCK,
        severity=severity,
        duration_remaining=duration,
        source="traumatic_shock",
        applied_at_turn=turn
    )


def calculate_effect_stack(effects: list[StatusEffect], effect_type: EffectType) -> float:
    """
    Calculate combined severity of stacked effects.
    
    TODO: Implement diminishing returns
    TODO: Add synergy effects (e.g., pain + shock)
    
    Returns:
        float: Combined severity (0.0-1.0)
    """
    # STUB: Simple sum with cap
    total = sum(e.severity for e in effects if e.type == effect_type)
    return min(1.0, total)