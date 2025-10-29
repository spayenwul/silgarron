"""
Schema validation script for WP1: Foundation

Validates that generated world conforms to WP1 data schema:
- World structure
- ContinentData structure
- Organ structure
- Type checking
- Value range checking

Usage:
    python scripts/validate_wp1_schema.py --seed my_seed
    python scripts/validate_wp1_schema.py --seed my_seed --verbose
"""

import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import argparse
import yaml
import numpy as np
from typing import List, Tuple
from dataclasses import fields

from core.world_generator_v3 import WorldGeneratorV3
from core.models.world import World, ContinentData, Organ


class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass


class WP1Validator:
    """Validator for WP1 schema"""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def log(self, message: str):
        """Log message if verbose"""
        if self.verbose:
            print(f"  {message}")

    def error(self, message: str):
        """Record validation error"""
        self.errors.append(message)
        print(f"  [ERROR] ERROR: {message}")

    def warning(self, message: str):
        """Record validation warning"""
        self.warnings.append(message)
        print(f"  [WARN] WARNING: {message}")

    def validate_world(self, world: World) -> bool:
        """
        Validate World structure

        Returns:
            True if valid, False otherwise
        """
        print("\n[1/3] Validating World structure...")

        try:
            # Check type
            if not isinstance(world, World):
                self.error(f"World is not instance of World class, got {type(world)}")
                return False

            # Check required fields
            required_fields = ['seed', 'world_phase', 'age', 'global_size']
            for field in required_fields:
                if not hasattr(world, field):
                    self.error(f"World missing required field: {field}")

            # Seed
            if not isinstance(world.seed, str):
                self.error(f"World.seed should be str, got {type(world.seed)}")
            else:
                self.log(f"[OK] seed: '{world.seed}'")

            # World phase
            valid_phases = ['EXHALE', 'INHALE']
            if world.world_phase not in valid_phases:
                self.error(f"World.world_phase should be in {valid_phases}, got '{world.world_phase}'")
            else:
                self.log(f"[OK] world_phase: '{world.world_phase}'")

            # Age
            if not isinstance(world.age, str):
                self.error(f"World.age should be str, got {type(world.age)}")
            else:
                self.log(f"[OK] age: '{world.age}'")

            # Global size
            if not isinstance(world.global_size, tuple) or len(world.global_size) != 2:
                self.error(f"World.global_size should be tuple(int, int), got {world.global_size}")
            elif world.global_size != (512, 512):
                self.warning(f"World.global_size is {world.global_size}, expected (512, 512)")
            else:
                self.log(f"[OK] global_size: {world.global_size}")

            print(f"[OK] World structure valid" if not self.errors else f"[ERROR] World structure has errors")
            return len(self.errors) == 0

        except Exception as e:
            self.error(f"Exception during World validation: {e}")
            return False

    def validate_continent(self, continent: ContinentData) -> bool:
        """
        Validate ContinentData structure

        Returns:
            True if valid, False otherwise
        """
        print("\n[2/3] Validating ContinentData structure...")

        try:
            # Check type
            if not isinstance(continent, ContinentData):
                self.error(f"Continent is not instance of ContinentData, got {type(continent)}")
                return False

            # === Mask ===
            if not isinstance(continent.mask, np.ndarray):
                self.error(f"continent.mask should be np.ndarray, got {type(continent.mask)}")
            else:
                # Shape
                if continent.mask.shape != (512, 512):
                    self.error(f"continent.mask shape should be (512, 512), got {continent.mask.shape}")
                else:
                    self.log(f"[OK] mask.shape: {continent.mask.shape}")

                # Dtype
                if continent.mask.dtype != bool:
                    self.error(f"continent.mask dtype should be bool, got {continent.mask.dtype}")
                else:
                    self.log(f"[OK] mask.dtype: {continent.mask.dtype}")

                # Range
                land_ratio = continent.mask.sum() / continent.mask.size
                if not (0.55 <= land_ratio <= 0.90):
                    self.warning(f"Land ratio {land_ratio:.2%} outside recommended range [55%, 90%]")
                else:
                    self.log(f"[OK] Land ratio: {land_ratio:.2%}")

            # === Heightmap ===
            if not isinstance(continent.heightmap, np.ndarray):
                self.error(f"continent.heightmap should be np.ndarray, got {type(continent.heightmap)}")
            else:
                # Shape
                if continent.heightmap.shape != (512, 512):
                    self.error(f"continent.heightmap shape should be (512, 512), got {continent.heightmap.shape}")
                else:
                    self.log(f"[OK] heightmap.shape: {continent.heightmap.shape}")

                # Dtype
                if continent.heightmap.dtype != np.float32:
                    self.warning(f"continent.heightmap dtype should be float32, got {continent.heightmap.dtype}")
                else:
                    self.log(f"[OK] heightmap.dtype: {continent.heightmap.dtype}")

                # Range [0, 1]
                if continent.heightmap.min() < 0 or continent.heightmap.max() > 1:
                    self.error(f"continent.heightmap values outside [0, 1]: [{continent.heightmap.min():.3f}, {continent.heightmap.max():.3f}]")
                else:
                    self.log(f"[OK] heightmap range: [{continent.heightmap.min():.3f}, {continent.heightmap.max():.3f}]")

                # NaN/Inf check
                if np.isnan(continent.heightmap).any():
                    self.error("continent.heightmap contains NaN values")
                if np.isinf(continent.heightmap).any():
                    self.error("continent.heightmap contains Inf values")

            # === Center ===
            if not isinstance(continent.center, tuple) or len(continent.center) != 2:
                self.error(f"continent.center should be tuple(int, int), got {continent.center}")
            else:
                cx, cy = continent.center
                if not (0 <= cx < 512 and 0 <= cy < 512):
                    self.error(f"continent.center {continent.center} outside map bounds")
                elif not continent.mask[cy, cx]:
                    self.error(f"continent.center {continent.center} is not on land!")
                else:
                    self.log(f"[OK] center: {continent.center}")

            # === Major Axis ===
            if not isinstance(continent.major_axis, tuple) or len(continent.major_axis) != 2:
                self.error(f"continent.major_axis should be tuple of 2 points, got {continent.major_axis}")
            else:
                (x1, y1), (x2, y2) = continent.major_axis

                # Check bounds
                if not (0 <= x1 < 512 and 0 <= y1 < 512):
                    self.error(f"major_axis point 1 ({x1}, {y1}) outside bounds")
                if not (0 <= x2 < 512 and 0 <= y2 < 512):
                    self.error(f"major_axis point 2 ({x2}, {y2}) outside bounds")

                # Check length
                axis_length = np.sqrt((x2 - x1)**2 + (y2 - y1)**2)
                if axis_length < 400:
                    self.warning(f"major_axis length {axis_length:.1f}px < 400px (too short)")
                else:
                    self.log(f"[OK] major_axis length: {axis_length:.1f}px")

            # === Spine Path ===
            if continent.spine_path is None:
                self.warning("continent.spine_path is None (spine mode disabled)")
            elif not isinstance(continent.spine_path, np.ndarray):
                self.error(f"continent.spine_path should be np.ndarray, got {type(continent.spine_path)}")
            else:
                # Shape
                if continent.spine_path.ndim != 2 or continent.spine_path.shape[1] != 2:
                    self.error(f"continent.spine_path should be (N, 2), got {continent.spine_path.shape}")
                else:
                    self.log(f"[OK] spine_path.shape: {continent.spine_path.shape}")

                # North→South
                if continent.spine_path[0, 1] >= continent.spine_path[-1, 1]:
                    self.warning("spine_path does not run north→south (start Y >= end Y)")
                else:
                    self.log(f"[OK] spine_path: north({continent.spine_path[0, 1]:.0f}) → south({continent.spine_path[-1, 1]:.0f})")

            print(f"[OK] ContinentData structure valid" if not self.errors else f"[ERROR] ContinentData structure has errors")
            return len(self.errors) == 0

        except Exception as e:
            self.error(f"Exception during ContinentData validation: {e}")
            return False

    def validate_organs(self, organs: dict, continent: ContinentData) -> bool:
        """
        Validate organs structure

        Returns:
            True if valid, False otherwise
        """
        print("\n[3/3] Validating Organs structure...")

        try:
            # Check type
            if not isinstance(organs, dict):
                self.error(f"organs should be dict, got {type(organs)}")
                return False

            # Check count
            if len(organs) != 5:
                self.error(f"Should have exactly 5 organs, got {len(organs)}")
            else:
                self.log(f"[OK] Organ count: {len(organs)}")

            # Expected organ IDs
            expected_ids = {
                'organ_metabolic_core',
                'organ_stomach',
                'ganglion_0',
                'ganglion_1',
                'lymph_node_sclerite'
            }

            if set(organs.keys()) != expected_ids:
                missing = expected_ids - set(organs.keys())
                extra = set(organs.keys()) - expected_ids
                if missing:
                    self.error(f"Missing organs: {missing}")
                if extra:
                    self.error(f"Extra organs: {extra}")
            else:
                self.log(f"[OK] Organ IDs correct")

            # Expected organ types
            expected_types = {
                'organ_metabolic_core': 'metabolic_organ',
                'organ_stomach': 'digestive',
                'ganglion_0': 'neural_cluster',
                'ganglion_1': 'neural_cluster',
                'lymph_node_sclerite': 'immune_node'
            }

            # Validate each organ
            for organ_id, expected_type in expected_types.items():
                if organ_id not in organs:
                    continue  # Already reported as missing

                organ = organs[organ_id]

                # Type check
                if not isinstance(organ, Organ):
                    self.error(f"{organ_id}: not instance of Organ class")
                    continue

                # Organ type
                if organ.type != expected_type:
                    self.error(f"{organ_id}: type should be '{expected_type}', got '{organ.type}'")

                # Position
                if not isinstance(organ.position, tuple) or len(organ.position) != 2:
                    self.error(f"{organ_id}: position should be tuple(int, int), got {organ.position}")
                else:
                    x, y = organ.position
                    if not (0 <= x < 512 and 0 <= y < 512):
                        self.error(f"{organ_id}: position {organ.position} outside bounds")
                    elif not continent.mask[y, x]:
                        self.error(f"{organ_id}: position {organ.position} not on land!")
                    else:
                        self.log(f"[OK] {organ_id}: position {organ.position}")

                # Radius
                if not isinstance(organ.radius, (int, float)) or organ.radius <= 0:
                    self.error(f"{organ_id}: radius should be positive number, got {organ.radius}")

            # Specific validations
            # Metabolic core should be near center
            if 'organ_metabolic_core' in organs:
                metabolic = organs['organ_metabolic_core']
                center = continent.center
                distance = np.sqrt(
                    (metabolic.position[0] - center[0])**2 +
                    (metabolic.position[1] - center[1])**2
                )
                if distance > 10:
                    self.warning(f"Metabolic core {distance:.1f}px from center (expected <10px)")

            # Stomach should be in southern half
            if 'organ_stomach' in organs:
                stomach = organs['organ_stomach']
                if stomach.position[1] <= 256:
                    self.warning(f"Stomach at y={stomach.position[1]}, expected southern half (y>256)")

            print(f"[OK] Organs structure valid" if not self.errors else f"[ERROR] Organs structure has errors")
            return len(self.errors) == 0

        except Exception as e:
            self.error(f"Exception during Organs validation: {e}")
            return False

    def validate_all(self, world: World) -> bool:
        """
        Run all validations

        Returns:
            True if all validations pass, False otherwise
        """
        valid_world = self.validate_world(world)
        valid_continent = self.validate_continent(world.continent)
        valid_organs = self.validate_organs(world.organs, world.continent)

        return valid_world and valid_continent and valid_organs

    def print_summary(self):
        """Print validation summary"""
        print(f"\n{'='*60}")
        print("VALIDATION SUMMARY")
        print(f"{'='*60}")

        if not self.errors and not self.warnings:
            print("[OK] ALL CHECKS PASSED - WP1 schema is valid!")
        else:
            if self.errors:
                print(f"[ERROR] ERRORS: {len(self.errors)}")
                for error in self.errors:
                    print(f"  - {error}")

            if self.warnings:
                print(f"\n[WARN] WARNINGS: {len(self.warnings)}")
                for warning in self.warnings:
                    print(f"  - {warning}")

        print(f"{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(description='Validate WP1 schema')
    parser.add_argument('--seed', type=str, default='validation_test',
                       help='World seed (default: validation_test)')
    parser.add_argument('--config', type=str, default='config/world_generation_v3.yaml',
                       help='Config file path')
    parser.add_argument('--verbose', action='store_true',
                       help='Verbose output')

    args = parser.parse_args()

    print(f"\n{'='*60}")
    print(f"WP1 Schema Validation")
    print(f"{'='*60}")
    print(f"Seed: {args.seed}")
    print(f"Config: {args.config}")
    print(f"{'='*60}")

    # Load config
    with open(args.config, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    # Generate world
    print("\nGenerating world...")
    generator = WorldGeneratorV3(config)
    world = generator.generate_wp1(args.seed)
    print("[OK] World generated")

    # Validate
    validator = WP1Validator(verbose=args.verbose)
    is_valid = validator.validate_all(world)

    # Summary
    validator.print_summary()

    # Exit code
    exit(0 if is_valid else 1)


if __name__ == '__main__':
    main()
