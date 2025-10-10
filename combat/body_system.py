"""
Body System - Anatomical Simulation

This module provides the core anatomical system for characters:
- Body parts with integrity tracking
- Blood volume and consciousness
- Wound management
- Status effect tracking

STATUS: Skeleton implementation with stubs
TODO: Implement full physiological simulation in Phase 3
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from .wounds import Wound
from .status_effects import StatusEffect, EffectType


@dataclass
class BodyPart:
    """
    Represents a single body part.
    
    Attributes:
        name: Body part name (e.g., "head", "torso", "left_arm")
        integrity: Structural integrity (0.0 = destroyed, 1.0 = perfect)
        wounds: List of active wounds on this part
        armor: Optional armor protection
        functional: Whether part is still functional
    
    TODO: Add hit boxes for precise targeting
    TODO: Add vital organ tracking
    TODO: Add articulation/mobility tracking
    """
    
    name: str
    integrity: float = 1.0           # 0.0-1.0
    wounds: List[Wound] = field(default_factory=list)
    armor: Optional[str] = None
    functional: bool = True
    
    def add_wound(self, wound: Wound):
        """
        Add a wound to this body part.
        
        TODO: Calculate integrity loss based on wound type
        TODO: Check for functional impairment
        TODO: Add wound interactions (compound injuries)
        """
        # STUB: Simple implementation
        self.wounds.append(wound)
        
        # Reduce integrity (simplified)
        integrity_loss = wound.depth_cm / 10.0
        self.integrity = max(0.0, self.integrity - integrity_loss)
        
        # Check functionality
        if self.integrity < 0.3:
            self.functional = False
    
    def get_total_bleeding(self) -> float:
        """
        Calculate total bleeding rate from all wounds.
        
        Returns:
            float: Total bleeding in ml/sec
        """
        return sum(w.bleeding_rate_ml_per_sec for w in self.wounds)
    
    def to_dict(self) -> dict:
        """Serialize body part"""
        return {
            "name": self.name,
            "integrity": self.integrity,
            "wounds": [w.to_dict() for w in self.wounds],
            "armor": self.armor,
            "functional": self.functional
        }


class BodySystem:
    """
    Complete anatomical system for a character.
    
    Manages:
    - Body parts and their state
    - Blood volume and circulation
    - Consciousness level
    - Status effects
    
    TODO: Add organ systems (cardiovascular, respiratory, nervous)
    TODO: Add metabolic simulation (hunger, thirst, temperature)
    TODO: Add healing mechanics
    
    Example:
        >>> body = BodySystem(species="human")
        >>> body.blood_volume
        5000.0
        >>> body.add_wound("neck", wound)
        >>> body.tick(1)
        >>> body.is_unconscious()
        False
    """
    
    def __init__(self, species: str = "human"):
        """
        Initialize body system.
        
        Args:
            species: Species type (determines physiology)
        
        TODO: Load species-specific parameters from data files
        TODO: Add size/weight variations
        """
        self.species = species
        
        # Blood system (STUB values for human)
        self.blood_volume: float = 5000.0      # ml
        self.max_blood_volume: float = 5000.0  # ml
        
        # Consciousness (0.0 = dead, 1.0 = alert)
        self.consciousness: float = 1.0
        
        # Body parts
        self.parts: Dict[str, BodyPart] = self._initialize_body_parts()
        
        # Status effects
        self.status_effects: List[StatusEffect] = []
    
    def _initialize_body_parts(self) -> Dict[str, BodyPart]:
        """
        Create body parts for this species.
        
        TODO: Load from species definition files
        TODO: Add species-specific anatomy (tails, wings, etc.)
        """
        # STUB: Basic human anatomy
        return {
            "head": BodyPart("head"),
            "neck": BodyPart("neck"),
            "torso": BodyPart("torso"),
            "left_arm": BodyPart("left_arm"),
            "right_arm": BodyPart("right_arm"),
            "left_leg": BodyPart("left_leg"),
            "right_leg": BodyPart("right_leg"),
        }
    
    def add_wound(self, body_part: str, wound: Wound):
        """
        Add a wound to specified body part.
        
        Args:
            body_part: Name of body part
            wound: Wound object
        
        Raises:
            ValueError: If body part doesn't exist
        
        TODO: Add wound bleeding to status effects
        TODO: Check for instant death (vital organs)
        """
        if body_part not in self.parts:
            raise ValueError(f"Unknown body part: {body_part}")
        
        # Add wound to body part
        self.parts[body_part].add_wound(wound)
        
        # Add bleeding effect if significant
        if wound.bleeding_rate_ml_per_sec > 1.0:
            from .status_effects import create_bleeding_effect
            effect = create_bleeding_effect(
                severity=min(1.0, wound.bleeding_rate_ml_per_sec / 20.0),
                source=f"{body_part}_wound",
                turn=wound.created_at_turn
            )
            self.add_status_effect(effect)
    
    def add_status_effect(self, effect: StatusEffect):
        """Add a status effect"""
        self.status_effects.append(effect)
    
    def has_status(self, effect_type: str) -> bool:
        """
        Check if character has a specific status effect.
        
        Args:
            effect_type: Effect type name (string)
        
        Returns:
            bool: True if effect is active
        """
        return any(
            e.type.value == effect_type 
            for e in self.status_effects
        )
    
    def tick(self, delta_turns: int = 1):
        """
        Update body state over time.
        
        Simulates:
        - Blood loss from wounds
        - Consciousness changes
        - Status effect progression
        - Natural healing (TODO)
        
        Args:
            delta_turns: Number of turns to simulate
        
        TODO: Add shock calculation
        TODO: Add pain accumulation
        TODO: Add natural healing
        """
        # STUB: Simple implementation
        
        # 1. Blood loss from all wounds
        total_blood_loss = 0.0
        for part in self.parts.values():
            for wound in part.wounds:
                total_blood_loss += wound.tick(delta_turns)
        
        self.blood_volume = max(0.0, self.blood_volume - total_blood_loss)
        
        # 2. Update consciousness based on blood loss
        blood_percentage = self.blood_volume / self.max_blood_volume
        if blood_percentage < 0.6:
            self.consciousness = blood_percentage
        
        # 3. Update status effects
        self.status_effects = [
            e for e in self.status_effects
            if not (e.tick(delta_turns), e.is_expired())[1]
        ]
    
    def is_unconscious(self) -> bool:
        """
        Check if character is unconscious.

        Causes:
        - Low blood volume (<= 30%)
        - UNCONSCIOUS status effect
        - Head trauma (TODO)

        Returns:
            bool: True if unconscious
        """
        return (
            self.consciousness <= 0.3 or  # Исправлено: <= вместо < (граничное значение)
            any(e.type == EffectType.UNCONSCIOUS for e in self.status_effects)
        )
    
    def is_dead(self) -> bool:
        """
        Check if character is dead.
        
        Death conditions:
        - Critical blood loss (< 1000 ml)
        - Head destroyed (< 10% integrity)
        - Torso destroyed (< 20% integrity)
        
        TODO: Add time-based death (bleeding out)
        TODO: Add organ failure
        
        Returns:
            bool: True if dead
        """
        return (
            self.blood_volume < 1000 or
            self.parts["head"].integrity < 0.1 or
            self.parts["torso"].integrity < 0.2
        )
    
    def to_dict(self) -> dict:
        """Serialize body system for saving"""
        return {
            "species": self.species,
            "blood_volume": self.blood_volume,
            "max_blood_volume": self.max_blood_volume,
            "consciousness": self.consciousness,
            "parts": {
                name: part.to_dict() 
                for name, part in self.parts.items()
            },
            "status_effects": [
                e.to_dict() for e in self.status_effects
            ]
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'BodySystem':
        """
        Deserialize body system from dictionary.
        
        TODO: Full reconstruction of wounds and effects
        """
        # STUB: Partial implementation
        body = cls(species=data["species"])
        body.blood_volume = data["blood_volume"]
        body.consciousness = data["consciousness"]
        # TODO: Restore wounds and effects
        return body