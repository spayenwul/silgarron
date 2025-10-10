# models/character.py
from .inventory import Inventory

try:
    from combat.body_system import BodySystem
    BODY_SYSTEM_AVAILABLE = True
except ImportError:
    BODY_SYSTEM_AVAILABLE = False
    # Combat system not yet fully implemented

class Character:
    def __init__(self, name: str, species: str = "human"):
        self.name = name
        self.species = species
        
        # ===== LEGACY SYSTEM (TEMPORARY) =====
        # TODO: Remove after Phase 3 when combat system is complete
        self.max_hp = 20
        self.hp = self.max_hp
        
        # ===== NEW BODY SYSTEM (PHASE 1+) =====
        # TODO: Make this the primary system in Phase 3
        if BODY_SYSTEM_AVAILABLE:
            self.body = BodySystem(species=species)
        else:
            self.body = None  # Fallback
        
        # Physical characteristics (NEW)
        self.physical_stats = {
            "strength_kg": 50.0,      # Сила в кг (может поднять)
            "endurance_sec": 120.0,   # Выносливость в секундах
            "agility": 1.0,           # Множитель скорости
        }
        
        # Старые абстрактные статы (LEGACY, TODO: remove)
        self.stats = {
            "сила": 10,
            "ловкость": 10,
            "интеллект": 10,
        }
        
        self.inventory = Inventory()
        
        # Навыки (NEW)
        self.skills = {
            "sword": 0.5,
            "bow": 0.3,
            "dodge": 0.4,
        }

    def take_damage(self, amount: int):
        """
        LEGACY METHOD - For backward compatibility only.
        
        TODO: Remove after Phase 3
        TODO: Replace with body.add_wound() calls
        """
        self.hp -= amount
        if self.hp < 0:
            self.hp = 0
        print(f"DEBUG: {self.name} получил {amount} урона. Осталось HP: {self.hp}")

    def is_dead(self) -> bool:
        """
        Check if character is dead.

        Uses new body system if available, falls back to HP.
        Checks BOTH systems to ensure backward compatibility.
        """
        if BODY_SYSTEM_AVAILABLE and self.body:
            # Проверяем обе системы: новую body system И legacy HP
            # Персонаж мёртв если любая из систем показывает смерть
            return self.body.is_dead() or self.hp <= 0
        else:
            # LEGACY: HP-based death
            return self.hp <= 0
    
    def tick_body(self, delta_turns: int = 1):
        """
        Update physical state over time.
        
        TODO: Make this automatic in game loop
        """
        if BODY_SYSTEM_AVAILABLE and self.body:
            self.body.tick(delta_turns)

    def __str__(self):
        # Display both systems for now
        status_parts = [f"=== Персонаж: {self.name} ==="]
        
        # LEGACY HP display
        status_parts.append(f"HP: {self.hp}/{self.max_hp}")
        
        # NEW BODY SYSTEM display (if available)
        if BODY_SYSTEM_AVAILABLE and self.body:
            blood_pct = (self.body.blood_volume / self.body.max_blood_volume) * 100
            status_parts.append(f"Кровь: {blood_pct:.0f}% ({self.body.blood_volume:.0f}/{self.body.max_blood_volume:.0f} мл)")
            status_parts.append(f"Сознание: {self.body.consciousness*100:.0f}%")
            
            if self.body.is_unconscious():
                status_parts.append("⚠️ БЕЗ СОЗНАНИЯ")
            
            if self.body.status_effects:
                effects_str = ", ".join(e.type.value for e in self.body.status_effects)
                status_parts.append(f"Эффекты: {effects_str}")
        
        # Stats
        stats_str = ", ".join(f"{key}: {value}" for key, value in self.stats.items())
        status_parts.append(f"Статы: {stats_str}")
        
        # Inventory
        status_parts.append(str(self.inventory))
        
        return "\n".join(status_parts)

    def to_dict(self) -> dict:
        state = {
            "name": self.name,
            "species": self.species,
            "max_hp": self.max_hp,  # LEGACY
            "hp": self.hp,          # LEGACY
            "physical_stats": self.physical_stats,
            "stats": self.stats,     # LEGACY
            "skills": self.skills,
            "inventory": self.inventory.to_dict()
        }
        
        # NEW: Add body system if available
        if BODY_SYSTEM_AVAILABLE and self.body:
            state["body"] = self.body.to_dict()
        
        return state

    @classmethod
    def from_dict(cls, data: dict):
        obj = cls.__new__(cls)
        obj.name = data["name"]
        obj.species = data.get("species", "human")
        
        # LEGACY system
        obj.max_hp = data.get("max_hp", 20)
        obj.hp = data.get("hp", 20)
        obj.stats = data.get("stats", {"сила": 10, "ловкость": 10, "интеллект": 10})
        
        # NEW systems
        obj.physical_stats = data.get("physical_stats", {
            "strength_kg": 50.0,
            "endurance_sec": 120.0,
            "agility": 1.0
        })
        obj.skills = data.get("skills", {"sword": 0.5, "bow": 0.3, "dodge": 0.4})
        obj.inventory = Inventory.from_dict(data["inventory"])
        
        # Restore body system if available
        if BODY_SYSTEM_AVAILABLE and "body" in data:
            obj.body = BodySystem.from_dict(data["body"])
        else:
            obj.body = None
        
        return obj