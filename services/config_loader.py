# services/config_loader.py
"""
Загрузчик конфигурации с валидацией и fallback на дефолтные значения.
"""

from pathlib import Path
from typing import Any, Dict
import yaml
from dataclasses import dataclass, field


@dataclass
class WorldGenerationConfig:
    """
    Централизованная конфигурация генерации мира.
    Все параметры с дефолтными значениями.
    """
    
    # Континенты
    default_continent_radius: int = 3
    
    # Регионы
    min_biomes_per_region: int = 4
    max_biomes_per_region: int = 7
    max_biomes_of_same_type: int = 2
    
    # Биомы
    biome_distance_from_center: float = 70.0
    biome_angle_variance: float = 15.0
    max_attempts_per_biome: int = 10
    guarantee_settlement: bool = True
    
    # Локации
    min_locations_per_biome: int = 1
    max_locations_per_biome: int = 3
    location_min_distance: float = 15.0
    location_max_distance: float = 35.0
    location_angle_variance: float = 20.0
    
    # Гекс-сетка
    hex_size: float = 100.0
    
    # Исследование
    exploration_probability: float = 0.3
    reveal_neighbor_regions: bool = True
    
    # Производительность
    cache_compatibility_checks: bool = True
    max_cached_compatibility_pairs: int = 1000
    
    # Отладка
    log_generation: bool = True
    log_compatibility_checks: bool = False
    verbose_biome_creation: bool = True
    
    @classmethod
    def from_yaml(cls, filepath: str = "config/world_generation.yaml") -> 'WorldGenerationConfig':
        """
        Загружает конфигурацию из YAML файла.
        Если файл не найден или содержит ошибки, использует дефолтные значения.
        """
        config_path = Path(filepath)
        
        if not config_path.exists():
            print(f"⚠️ Конфиг не найден: {filepath}. Используются дефолтные значения.")
            return cls()
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}
            
            print(f"✅ Конфиг загружен из {filepath}")
            
            # Извлекаем вложенные параметры
            return cls(
                # Континенты
                default_continent_radius=data.get('continents', {}).get('default_radius', 3),
                
                # Регионы
                min_biomes_per_region=data.get('regions', {}).get('biomes_per_region', {}).get('min', 4),
                max_biomes_per_region=data.get('regions', {}).get('biomes_per_region', {}).get('max', 7),
                max_biomes_of_same_type=data.get('regions', {}).get('max_biomes_of_same_type', 2),
                
                # Биомы
                biome_distance_from_center=data.get('biomes', {}).get('positioning', {}).get('distance_from_center', 70.0),
                biome_angle_variance=data.get('biomes', {}).get('positioning', {}).get('angle_variance', 15.0),
                max_attempts_per_biome=data.get('biomes', {}).get('generation', {}).get('max_attempts_per_biome', 10),
                guarantee_settlement=data.get('biomes', {}).get('generation', {}).get('guarantee_settlement', True),
                
                # Локации
                min_locations_per_biome=data.get('locations', {}).get('per_biome', {}).get('min', 1),
                max_locations_per_biome=data.get('locations', {}).get('per_biome', {}).get('max', 3),
                location_min_distance=data.get('locations', {}).get('positioning', {}).get('distance_from_biome_center', {}).get('min', 15.0),
                location_max_distance=data.get('locations', {}).get('positioning', {}).get('distance_from_biome_center', {}).get('max', 35.0),
                location_angle_variance=data.get('locations', {}).get('positioning', {}).get('angle_variance', 20.0),
                
                # Гекс-сетка
                hex_size=data.get('hex_grid', {}).get('size', 100.0),
                
                # Исследование
                exploration_probability=data.get('exploration', {}).get('probability_of_new_discoveries', 0.3),
                reveal_neighbor_regions=data.get('exploration', {}).get('reveal_neighbor_regions', True),
                
                # Производительность
                cache_compatibility_checks=data.get('performance', {}).get('cache_compatibility_checks', True),
                max_cached_compatibility_pairs=data.get('performance', {}).get('max_cached_compatibility_pairs', 1000),
                
                # Отладка
                log_generation=data.get('debug', {}).get('log_generation', True),
                log_compatibility_checks=data.get('debug', {}).get('log_compatibility_checks', False),
                verbose_biome_creation=data.get('debug', {}).get('verbose_biome_creation', True),
            )
            
        except yaml.YAMLError as e:
            print(f"❌ Ошибка парсинга YAML: {e}")
            print("⚠️ Используются дефолтные значения.")
            return cls()
        except Exception as e:
            print(f"❌ Неожиданная ошибка при загрузке конфига: {e}")
            print("⚠️ Используются дефолтные значения.")
            return cls()
    
    def validate(self) -> bool:
        """
        Проверяет корректность значений конфигурации.
        
        Returns:
            True если все значения валидны
        """
        errors = []
        
        # Валидация радиуса континента
        if self.default_continent_radius < 1 or self.default_continent_radius > 10:
            errors.append(f"default_continent_radius должен быть от 1 до 10, получено: {self.default_continent_radius}")
        
        # Валидация количества биомов
        if self.min_biomes_per_region < 1:
            errors.append(f"min_biomes_per_region должен быть >= 1, получено: {self.min_biomes_per_region}")
        
        if self.max_biomes_per_region < self.min_biomes_per_region:
            errors.append(f"max_biomes_per_region ({self.max_biomes_per_region}) < min_biomes_per_region ({self.min_biomes_per_region})")
        
        # Валидация размеров
        if self.hex_size <= 0:
            errors.append(f"hex_size должен быть > 0, получено: {self.hex_size}")
        
        if self.biome_distance_from_center <= 0:
            errors.append(f"biome_distance_from_center должен быть > 0, получено: {self.biome_distance_from_center}")
        
        # Валидация вероятностей
        if not (0 <= self.exploration_probability <= 1):
            errors.append(f"exploration_probability должен быть от 0 до 1, получено: {self.exploration_probability}")
        
        if errors:
            print("❌ Ошибки валидации конфигурации:")
            for error in errors:
                print(f"   - {error}")
            return False
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Экспортирует конфигурацию в словарь"""
        from dataclasses import asdict
        return asdict(self)
    
    def save_to_yaml(self, filepath: str = "config/world_generation.yaml"):
        """Сохраняет текущую конфигурацию в YAML файл"""
        config_path = Path(filepath)
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Формируем структурированный словарь для красивого YAML
        structured_data = {
            "continents": {
                "default_radius": self.default_continent_radius
            },
            "regions": {
                "biomes_per_region": {
                    "min": self.min_biomes_per_region,
                    "max": self.max_biomes_per_region
                },
                "max_biomes_of_same_type": self.max_biomes_of_same_type
            },
            "biomes": {
                "positioning": {
                    "distance_from_center": self.biome_distance_from_center,
                    "angle_variance": self.biome_angle_variance
                },
                "generation": {
                    "max_attempts_per_biome": self.max_attempts_per_biome,
                    "guarantee_settlement": self.guarantee_settlement
                }
            },
            "locations": {
                "per_biome": {
                    "min": self.min_locations_per_biome,
                    "max": self.max_locations_per_biome
                },
                "positioning": {
                    "distance_from_biome_center": {
                        "min": self.location_min_distance,
                        "max": self.location_max_distance
                    },
                    "angle_variance": self.location_angle_variance
                }
            },
            "hex_grid": {
                "size": self.hex_size
            },
            "exploration": {
                "reveal_neighbor_regions": self.reveal_neighbor_regions,
                "probability_of_new_discoveries": self.exploration_probability
            },
            "performance": {
                "cache_compatibility_checks": self.cache_compatibility_checks,
                "max_cached_compatibility_pairs": self.max_cached_compatibility_pairs
            },
            "debug": {
                "log_generation": self.log_generation,
                "log_compatibility_checks": self.log_compatibility_checks,
                "verbose_biome_creation": self.verbose_biome_creation
            }
        }
        
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(structured_data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
            print(f"✅ Конфигурация сохранена в {filepath}")
        except Exception as e:
            print(f"❌ Ошибка сохранения конфига: {e}")


# ========== ПРИМЕР ИСПОЛЬЗОВАНИЯ ==========

if __name__ == "__main__":
    # Создаём дефолтный конфиг и сохраняем его
    config = WorldGenerationConfig()
    config.save_to_yaml("config/world_generation.yaml")
    
    # Загружаем конфиг из файла
    loaded_config = WorldGenerationConfig.from_yaml("config/world_generation.yaml")
    
    # Валидируем
    if loaded_config.validate():
        print("\n✅ Конфигурация валидна")
        print(f"Радиус континента: {loaded_config.default_continent_radius}")
        print(f"Биомов на регион: {loaded_config.min_biomes_per_region}-{loaded_config.max_biomes_per_region}")
    else:
        print("\n❌ Конфигурация содержит ошибки")