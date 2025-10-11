"""
Tests for Extended Body System

Tests realistic physiology features:
- Realistic bleeding by vessel type
- Blood clotting over time
- Shock mechanics
- Instant death checks
- Consciousness calculation with pain
"""

import pytest
from combat.body_system_extended import BodySystem, BodyPart, VesselType, PHYSIOLOGY_DEFAULTS
from combat.wounds import Wound, WoundType


def test_realistic_bleeding():
    """Test realistic bleeding with clotting"""
    body = BodySystem(species="human")

    # Wound with arterial bleeding
    wound = Wound(
        location="neck",
        type=WoundType.LACERATION,
        depth_cm=4.0,
        bleeding_rate_ml_per_sec=120.0,  # Carotid artery
        tissues_damaged=["skin", "muscle", "artery"],
        created_at_turn=0
    )

    body.add_wound("neck", wound, current_turn=0)

    # After 10 turns
    body.tick(delta_turns=10)

    # Blood loss: 120 ml/sec * 10 sec = 1200 ml
    expected_blood = 5000 - 1200
    assert abs(body.blood_volume - expected_blood) < 100  # Allow clotting reduction


def test_clotting():
    """Test blood clotting over time"""
    body = BodySystem(species="human")

    wound = Wound(
        location="left_arm",
        type=WoundType.LACERATION,
        depth_cm=2.0,
        bleeding_rate_ml_per_sec=10.0,
        tissues_damaged=["skin", "muscle"],
        created_at_turn=0
    )

    body.add_wound("left_arm", wound, current_turn=0)

    # Initial bleeding
    initial_bleeding = body.parts["left_arm"].get_total_bleeding()
    assert initial_bleeding == 10.0

    # After 20 turns, clotting should reduce bleeding
    body.tick(delta_turns=20)

    final_bleeding = body.parts["left_arm"].get_total_bleeding()
    assert final_bleeding < initial_bleeding


def test_instant_death_severed_artery():
    """Test instant death from severed carotid artery"""
    body = BodySystem(species="human")

    # Deep neck wound with carotid artery damage
    wound = Wound(
        location="neck",
        type=WoundType.LACERATION,
        depth_cm=5.0,
        bleeding_rate_ml_per_sec=150.0,
        tissues_damaged=["skin", "muscle", "artery"],
        created_at_turn=0
    )

    body.add_wound("neck", wound, current_turn=0)

    # Should be instant death
    assert body.instant_death == True
    assert body.instant_death_reason == "severed_carotid_artery"


def test_instant_death_head_destruction():
    """Test instant death from head destruction"""
    body = BodySystem(species="human")

    # Massive head wound
    wound = Wound(
        location="head",
        type=WoundType.CRUSH,
        depth_cm=10.0,
        bleeding_rate_ml_per_sec=100.0,
        tissues_damaged=["skin", "skull", "brain"],
        created_at_turn=0
    )

    body.add_wound("head", wound, current_turn=0)

    # Should be instant death
    assert body.instant_death == True
    assert body.instant_death_reason == "destruction_of_head"


def test_consciousness_from_blood_loss():
    """Test consciousness decrease from blood loss"""
    body = BodySystem(species="human")

    # Initial consciousness
    assert body.consciousness == 1.0

    # Simulate moderate blood loss
    body.blood_volume = 3000  # 60% remaining

    body.tick(delta_turns=1)

    # Consciousness should be reduced
    assert body.consciousness < 1.0
    assert body.consciousness > 0.5


def test_unconscious_from_severe_blood_loss():
    """Test unconsciousness from severe blood loss"""
    body = BodySystem(species="human")

    # Severe blood loss
    body.blood_volume = 1500  # 30% remaining

    body.tick(delta_turns=1)

    assert body.is_unconscious() == True


def test_death_from_exsanguination():
    """Test death from critical blood loss"""
    body = BodySystem(species="human")

    # Critical blood loss
    body.blood_volume = 500  # Below death threshold

    body.tick(delta_turns=1)

    assert body.is_dead() == True
    assert body.instant_death_reason == "exsanguination"


def test_pain_affects_consciousness():
    """Test that pain reduces consciousness"""
    body = BodySystem(species="human")

    # Add multiple painful wounds (depth causes pain)
    for i in range(3):
        wound = Wound(
            location="torso",
            type=WoundType.LACERATION,
            depth_cm=6.0,  # Deep wound = high pain
            bleeding_rate_ml_per_sec=5.0,
            tissues_damaged=["skin", "muscle"],
            created_at_turn=0
        )
        body.add_wound("torso", wound, current_turn=0)

    body.tick(delta_turns=1)

    # Consciousness should be reduced by pain
    assert body.consciousness < 1.0


def test_shock_from_pain_and_blood_loss():
    """Test shock status effect from pain + blood loss"""
    body = BodySystem(species="human")

    # Moderate blood loss
    body.blood_volume = 2800  # Below shock threshold

    # Add painful wound (depth creates pain)
    wound = Wound(
        location="leg",
        type=WoundType.PUNCTURE,
        depth_cm=5.0,  # Deep enough for high pain
        bleeding_rate_ml_per_sec=15.0,
        tissues_damaged=["skin", "muscle", "bone"],
        created_at_turn=0
    )

    body.add_wound("left_leg", wound, current_turn=0)

    body.tick(delta_turns=1)

    # Should have shock effect
    assert body.has_status("shock")


def test_species_differences():
    """Test that different species have different physiology"""
    human = BodySystem(species="human")
    goblin = BodySystem(species="goblin")
    orc = BodySystem(species="orc")

    # Different blood volumes
    assert human.max_blood_volume == 5000.0
    assert goblin.max_blood_volume == 3000.0
    assert orc.max_blood_volume == 7000.0

    # Different clotting factors
    assert human.physiology["clotting_factor"] == 1.0
    assert goblin.physiology["clotting_factor"] == 0.8
    assert orc.physiology["clotting_factor"] == 1.2


def test_body_part_integrity_loss():
    """Test integrity loss calculation"""
    part = BodyPart(name="arm")

    wound = Wound(
        location="arm",
        type=WoundType.LACERATION,
        depth_cm=5.0,
        bleeding_rate_ml_per_sec=10.0,
        tissues_damaged=["skin", "muscle", "bone"],
        created_at_turn=0
    )

    part.add_wound(wound, current_turn=0)

    # Integrity should be reduced
    assert part.integrity < 1.0

    # Laceration is worse than puncture (type modifier 1.2)
    # 3 tissues damaged gives tissue modifier
    # Expected loss > base depth_cm / 10


def test_body_part_becomes_nonfunctional():
    """Test that severe damage makes body part nonfunctional"""
    part = BodyPart(name="arm")

    # Multiple severe wounds
    for i in range(5):
        wound = Wound(
            location="arm",
            type=WoundType.CRUSH,
            depth_cm=5.0,
            bleeding_rate_ml_per_sec=10.0,
            tissues_damaged=["skin", "muscle", "bone"],
            created_at_turn=0
        )
        part.add_wound(wound, current_turn=0)

    # Should be nonfunctional
    assert part.functional == False
    assert part.integrity < 0.3


def test_serialization():
    """Test that body system can be saved and loaded"""
    body = BodySystem(species="human")

    wound = Wound(
        location="arm",
        type=WoundType.LACERATION,
        depth_cm=2.0,
        bleeding_rate_ml_per_sec=5.0,
        tissues_damaged=["skin", "muscle"],
        created_at_turn=0
    )

    body.add_wound("left_arm", wound, current_turn=0)
    body.tick(delta_turns=5)

    # Serialize
    data = body.to_dict()

    # Deserialize
    restored = BodySystem.from_dict(data)

    assert restored.species == body.species
    assert restored.blood_volume == body.blood_volume
    assert restored.consciousness == body.consciousness


# ===================================
# INTEGRATION TESTS
# ===================================

def test_full_combat_scenario():
    """
    End-to-end combat scenario with realistic physiology
    """
    # Create combatants
    attacker_body = BodySystem(species="human")
    defender_body = BodySystem(species="goblin")

    # Simulate strike to neck
    from combat.wounds import create_laceration

    wound = create_laceration(
        location="neck",
        depth_cm=3.0,
        turn=1
    )

    defender_body.add_wound("neck", wound, current_turn=1)

    # Simulate several turns
    for turn in range(5):
        defender_body.tick(delta_turns=1)

    # Check results
    assert defender_body.blood_volume < defender_body.max_blood_volume
    print(f"Defender blood: {defender_body.blood_volume}/{defender_body.max_blood_volume}")

    # Defender should be in bad condition
    if defender_body.blood_volume < 1500:
        assert defender_body.is_unconscious()


# ===================================
# EDGE CASES
# ===================================

def test_no_wounds_no_bleeding():
    """Test that body without wounds doesn't bleed"""
    body = BodySystem(species="human")

    initial_blood = body.blood_volume

    body.tick(delta_turns=10)

    assert body.blood_volume == initial_blood


def test_fully_clotted_wound_no_bleeding():
    """Test that fully clotted wound stops bleeding"""
    body = BodySystem(species="human")

    wound = Wound(
        location="arm",
        type=WoundType.PUNCTURE,  # Puncture clots faster
        depth_cm=1.0,
        bleeding_rate_ml_per_sec=2.0,
        tissues_damaged=["skin"],
        created_at_turn=0
    )

    body.add_wound("left_arm", wound, current_turn=0)

    # Simulate many turns for full clotting
    body.tick(delta_turns=50)

    # Bleeding should be nearly zero
    bleeding = body.parts["left_arm"].get_total_bleeding()
    assert bleeding < 0.5  # Nearly stopped


def test_multiple_wounds_additive_bleeding():
    """Test that multiple wounds add up bleeding"""
    body = BodySystem(species="human")

    # Add 3 wounds with 10 ml/sec each
    for i in range(3):
        wound = Wound(
            location="torso",
            type=WoundType.LACERATION,
            depth_cm=2.0,
            bleeding_rate_ml_per_sec=10.0,
            tissues_damaged=["skin", "muscle"],
            created_at_turn=0
        )
        body.add_wound("torso", wound, current_turn=0)

    # Total bleeding should be ~30 ml/sec
    total_bleeding = body.parts["torso"].get_total_bleeding()
    assert 25 < total_bleeding <= 30


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
