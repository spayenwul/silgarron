 # 🌍 SPRINT 3.6: Континент и Органы — Глобальные Скелеты (Этап 0, Слои 0-1)

**Проект:** Silgarron RPG — Композиционная генерация от органов  
**Даты:** 25 октября - 1 ноября 2025 (1 неделя)  
**Приоритет:** 🔴 КРИТИЧЕСКИЙ #1  
**Статус:** В работе  
**Время (оценка):** 32-40 часов (~1 неделя)  
**Версия:** 1.0

---

## 📋 Содержание

1. [Цели спринта](#цели-спринта)
2. [Архитектурное видение](#архитектурное-видение)
3. [Детальный план задач](#детальный-план-задач)
4. [Технические спецификации](#технические-спецификации)
5. [Definition of Done](#definition-of-done)
6. [Риски и митигация](#риски-и-митигация)

---

## 🎯 Цели спринта

### Главная цель
Реализовать **ЭТАП 0 (Слои 0-1)** новой архитектуры генерации: создание "континента-холста" и размещение анатомических органов на нём.

### Что мы НЕ делаем в этом спринте
- ❌ Артерии (Слой 2) — Sprint 3.7
- ❌ Геология (Слой 3) — Sprint 3.7
- ❌ Гидрология (Слой 4) — Sprint 3.8
- ❌ Детализация чанков (Этап 1) — Sprint 3.9
- ❌ Параллелизм — Sprint 3.9
- ❌ Кэширование — Sprint 4.0

### Критерии успеха
✅ Генератор создаёт **органичную форму континента** (не квадрат)  
✅ **Органы размещаются на континенте** детерминированно  
✅ **Региональные маски** определяются анатомией + формой континента  
✅ Все структуры данных (`Organ`, `Region`) реализованы  
✅ Unit-тесты покрывают >85% кода  
✅ Визуализация показывает континент + органы + регионы

---

## 🏗️ Архитектурное видение

### Что мы строим

```
ЭТАП 0: ГЛОБАЛЬНАЯ ГЕНЕРАЦИЯ (512×512, однопоточно)
├─ СЛОЙ 0:   Seed & Meta-параметры ✅ (простой)
├─ СЛОЙ 0.5: Континент (макро-рельеф) 🔴 ГЛАВНОЕ
└─ СЛОЙ 1:   Анатомия (органы + регионы) 🔴 ГЛАВНОЕ
```

### Философия

> **"Мир-организм растёт на континенте, а не заполняет квадрат."**
>
> Сначала создаётся **континент** (форма суши), затем на нём **размещаются органы** (желудок, ганглии, лимфоузлы), которые определяют **регионы** (торакс, органоид, конечность).

---

## 📐 Детальный план задач

### ФАЗА 1: Подготовка инфраструктуры (4-6 часов)

#### Задача 1.1: Обновление моделей данных (2-3 часа)

**Цель:** Добавить новые структуры данных для органов и регионов

**Файл:** `src/models/world.py`

**Что добавить:**

```python
from dataclasses import dataclass, field
from typing import Tuple, Dict, Optional, List
import numpy as np

@dataclass
class Organ:
    """Анатомический орган мира-организма"""
    id: str
    type: str  # 'metabolic_organ', 'digestive', 'neural_cluster', 'immune_node'
    position: Tuple[int, int]  # Координаты на карте 512×512
    radius: float  # Радиус влияния
    
    # Специфичные параметры
    temperature: Optional[float] = None  # Для метаболических органов
    nutrient_output: Optional[float] = None
    acid_level: Optional[float] = None  # Для желудка
    control_strength: Optional[float] = None  # Для ганглиев
    cell_production: Optional[float] = None  # Для лимфоузлов
    
    def __post_init__(self):
        """Валидация после создания"""
        if self.radius <= 0:
            raise ValueError(f"Organ {self.id}: radius must be positive")
        if not (0 <= self.position[0] < 512 and 0 <= self.position[1] < 512):
            raise ValueError(f"Organ {self.id}: position out of bounds")

@dataclass
class Region:
    """Анатомический регион (торакс, органоид, и т.д.)"""
    id: str
    name: str  # 'THORAX', 'DIAPHRAGM', 'ORGANOID', 'GRASPING_LIMB'
    mask: np.ndarray  # (512, 512) boolean mask
    characteristics: Dict[str, float] = field(default_factory=dict)
    # characteristics = {
    #     'elevation_bias': +0.3,
    #     'bone_density': 0.8,
    #     'respiratory_potential': 0.9
    # }
    
    def __post_init__(self):
        """Валидация после создания"""
        if self.mask.shape != (512, 512):
            raise ValueError(f"Region {self.id}: mask must be 512×512")
        if self.mask.dtype != bool:
            raise ValueError(f"Region {self.id}: mask must be boolean")

@dataclass
class ContinentData:
    """Данные континента"""
    mask: np.ndarray  # (512, 512) boolean - где суша
    heightmap: np.ndarray  # (512, 512) float [0, 1] - базовый рельеф
    center: Tuple[int, int]  # Центр масс континента
    major_axis: Tuple[Tuple[int, int], Tuple[int, int]]  # Начало и конец оси
    
    def __post_init__(self):
        """Валидация"""
        if self.mask.shape != (512, 512) or self.heightmap.shape != (512, 512):
            raise ValueError("Continent data must be 512×512")

# Обновляем класс World
@dataclass
class World:
    """Расширенная модель мира с континентом и органами"""
    seed: str
    world_phase: str  # 'EXHALE' или 'INHALE'
    age: str  # 'EARLY_EXHALE', 'LATE_EXHALE', и т.д.
    global_size: Tuple[int, int] = (512, 512)
    
    # НОВОЕ: континент и анатомия
    continent: Optional[ContinentData] = None
    organs: Dict[str, Organ] = field(default_factory=dict)
    regions: Dict[str, Region] = field(default_factory=dict)
    
    # Существующие поля (пока None, заполним в следующих спринтах)
    elevation: Optional[np.ndarray] = None
    temperature: Optional[np.ndarray] = None
    # ... и т.д.
```

**Tests:** `tests/models/test_world.py`

```python
def test_organ_creation():
    organ = Organ(
        id='test_organ',
        type='metabolic_organ',
        position=(256, 256),
        radius=30,
        temperature=0.95
    )
    assert organ.id == 'test_organ'
    assert organ.temperature == 0.95

def test_organ_validation():
    with pytest.raises(ValueError, match="radius must be positive"):
        Organ(id='bad', type='test', position=(100, 100), radius=-5)
    
    with pytest.raises(ValueError, match="position out of bounds"):
        Organ(id='bad', type='test', position=(600, 100), radius=10)

def test_region_creation():
    mask = np.zeros((512, 512), dtype=bool)
    mask[100:200, 100:200] = True
    
    region = Region(
        id='test_region',
        name='TEST',
        mask=mask,
        characteristics={'elevation_bias': 0.3}
    )
    assert region.mask.sum() == 10000  # 100×100

def test_continent_data_validation():
    mask = np.zeros((512, 512), dtype=bool)
    heightmap = np.random.rand(512, 512)
    
    continent = ContinentData(
        mask=mask,
        heightmap=heightmap,
        center=(256, 256),
        major_axis=((100, 256), (400, 256))
    )
    assert continent.center == (256, 256)
```

**Критерии завершения:**
- ✅ Все классы реализованы
- ✅ Валидация работает
- ✅ Тесты проходят (>90% coverage)

---

#### Задача 1.2: Обновление конфигурации (1-2 часа)

**Цель:** Создать структуру конфигурации для нового генератора

**Файл:** `config/world_generation_v2.yaml` (НОВЫЙ)

```yaml
# Конфигурация генерации мира v2.0 (ADR-020)
# Этап 0: Глобальные Скелеты (512×512)

metadata:
  version: "2.0"
  adr: "ADR-020"
  sprint: "3.6"

global_settings:
  # Размер глобальной карты (низкое разрешение)
  global_width: 512
  global_height: 512
  
  # Размер детализации (высокое разрешение) - для Sprint 3.9
  detail_width: 4096
  detail_height: 4096
  scale_factor: 8  # 1 global hex = 8×8 detail hexes
  
  # Текущая фаза мира
  world_phase: "EXHALE"  # EXHALE | INHALE
  world_age: "LATE_EXHALE"

# СЛОЙ 0.5: Континент (макро-рельеф)
continent:
  perlin_noise:
    scale: 150  # Очень низкая частота (плавные контуры)
    octaves: 2
    persistence: 0.6
    lacunarity: 2.0
  
  sea_level: 0.35  # 35% карты будет океаном
  
  # Сглаживание береговой линии
  smoothing:
    binary_opening_iterations: 3
    binary_closing_iterations: 2
    gaussian_sigma: 3.0
    final_threshold: 0.5

# СЛОЙ 1: Анатомия (органы)
organs:
  # Типы органов и их параметры
  metabolic_organ:
    count: 1
    placement_method: "center_of_continent"
    radius: 30
    temperature: 0.95
    nutrient_output: 0.9
  
  digestive:
    count: 1
    placement_method: "suitable_lowland"
    placement_params:
      near: "metabolic_organ"
      direction: "south"
      radius_range: [20, 30]
    radius: 25
    temperature: 0.85
    acid_level: 0.8
  
  neural_cluster:
    count: 2  # thoracic и abdominal
    placement_method: "along_axis"
    placement_params:
      positions: [0.35, 0.65]  # 35% и 65% по оси континента
    radius: 15
    control_strength: 0.7
    control_decay: 0.1  # Каждый следующий на 0.1 слабее
  
  immune_node:
    count: 1
    placement_method: "elevated_point"
    placement_params:
      near: "neural_cluster_0"  # Ближайший ганглий
    radius: 10
    cell_production: 0.9

# Региональные характеристики
regions:
  THORAX:
    detection_method: "skeletal_density"  # Определяется по костям (Sprint 3.7)
    characteristics:
      elevation_bias: 0.3
      bone_density: 0.8
      respiratory_potential: 0.9
  
  DIAPHRAGM:
    detection_method: "muscle_layer"  # Мышечная стенка
    characteristics:
      muscle_density: 0.9
      pulsation_strength: 0.7
      respiratory_potential: 0.4
  
  ORGANOID:
    detection_method: "organ_proximity"  # Вокруг метаболических органов
    characteristics:
      elevation_bias: -0.2
      nutrient_richness: 0.9
      respiratory_potential: 0.1
  
  GRASPING_LIMB:
    detection_method: "extremity"  # Край континента
    characteristics:
      isolation: 0.8
      bone_density: 0.6
      respiratory_potential: 0.2

# Визуализация
visualization:
  # Цвета для органов
  organ_colors:
    metabolic_organ: "#FF4444"  # Красный
    digestive: "#FF8844"        # Оранжевый
    neural_cluster: "#4488FF"   # Синий
    immune_node: "#44FF88"      # Зелёный
  
  # Цвета для регионов (с прозрачностью)
  region_colors:
    THORAX: "#8888FF80"
    DIAPHRAGM: "#FF88FF80"
    ORGANOID: "#FFFF8880"
    GRASPING_LIMB: "#88FF8880"
```

**Tests:** `tests/config/test_config_loading.py`

```python
def test_load_world_generation_config_v2():
    config = load_yaml('config/world_generation_v2.yaml')
    
    assert config['metadata']['version'] == '2.0'
    assert config['global_settings']['global_width'] == 512
    assert config['continent']['sea_level'] == 0.35
    assert len(config['organs']) == 4

def test_organ_config_structure():
    config = load_yaml('config/world_generation_v2.yaml')
    
    # Проверяем, что у каждого типа органа есть обязательные поля
    for organ_type, organ_config in config['organs'].items():
        assert 'count' in organ_config
        assert 'placement_method' in organ_config
        assert 'radius' in organ_config
```

**Критерии завершения:**
- ✅ Конфиг создан и валиден
- ✅ Все параметры задокументированы комментариями
- ✅ Тесты загрузки проходят

---

#### Задача 1.3: Создание структуры нового генератора (1 час)

**Цель:** Создать скелет `WorldGeneratorV2` с чётким разделением слоёв

**Файл:** `src/core/world_generator_v2.py` (НОВЫЙ)

```python
"""
Генератор мира v2.0 (ADR-020)
Композиционная генерация от органов с двухэтапной архитектурой
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

from src.models.world import World, Organ, Region, ContinentData
from src.core.perlin_noise import generate_perlin_noise
from src.utils.config_loader import load_yaml

class WorldGeneratorV2:
    """
    Генератор мира v2.0
    
    Архитектура:
    - ЭТАП 0: Глобальные Скелеты (512×512) - этот класс
    - ЭТАП 1: Детализация Чанков (4096×4096) - Sprint 3.9
    """
    
    def __init__(self, config_path: str = 'config/world_generation_v2.yaml'):
        """Инициализация генератора"""
        self.config = load_yaml(config_path)
        self.global_size = (
            self.config['global_settings']['global_width'],
            self.config['global_settings']['global_height']
        )
    
    def generate(self, seed: str) -> World:
        """
        Главный метод генерации (ЭТАП 0: Глобальные Скелеты)
        
        Args:
            seed: Строка-seed для детерминированной генерации
        
        Returns:
            World объект с континентом и органами
        """
        print(f"🌍 Generating world from seed: {seed}")
        print(f"📐 Global size: {self.global_size}")
        
        # СЛОЙ 0: Seed & Meta
        world = self._initialize_world(seed)
        
        # СЛОЙ 0.5: Континент (макро-рельеф)
        print("  → LAYER 0.5: Generating continent...")
        world.continent = self._generate_continent(seed)
        
        # СЛОЙ 1: Анатомия (органы + регионы)
        print("  → LAYER 1: Placing organs...")
        world.organs = self._place_organs(seed, world.continent)
        
        print("  → LAYER 1: Defining regions...")
        world.regions = self._define_regions(world.continent, world.organs)
        
        print("✅ Global skeletons generated")
        return world
    
    # ========== СЛОЙ 0: SEED & META ==========
    
    def _initialize_world(self, seed: str) -> World:
        """Инициализация мира с meta-параметрами"""
        return World(
            seed=seed,
            world_phase=self.config['global_settings']['world_phase'],
            age=self.config['global_settings']['world_age'],
            global_size=self.global_size
        )
    
    # ========== СЛОЙ 0.5: КОНТИНЕНТ ==========
    
    def _generate_continent(self, seed: str) -> ContinentData:
        """
        Генерация континента (макро-рельеф)
        
        Sprint 3.6 - Задача 2.1
        """
        raise NotImplementedError("To be implemented in Task 2.1")
    
    # ========== СЛОЙ 1: АНАТОМИЯ ==========
    
    def _place_organs(self, seed: str, continent: ContinentData) -> Dict[str, Organ]:
        """
        Размещение органов на континенте
        
        Sprint 3.6 - Задача 3.1
        """
        raise NotImplementedError("To be implemented in Task 3.1")
    
    def _define_regions(self, continent: ContinentData, organs: Dict[str, Organ]) -> Dict[str, Region]:
        """
        Определение региональных масок
        
        Sprint 3.6 - Задача 3.2
        """
        raise NotImplementedError("To be implemented in Task 3.2")
```

**Tests:** `tests/core/test_world_generator_v2.py`

```python
import pytest
from src.core.world_generator_v2 import WorldGeneratorV2

def test_generator_initialization():
    gen = WorldGeneratorV2()
    assert gen.global_size == (512, 512)
    assert gen.config is not None

def test_world_initialization():
    gen = WorldGeneratorV2()
    world = gen._initialize_world("test_seed")
    
    assert world.seed == "test_seed"
    assert world.world_phase == "EXHALE"
    assert world.global_size == (512, 512)

def test_generate_raises_not_implemented():
    """В Sprint 3.6 методы ещё не реализованы"""
    gen = WorldGeneratorV2()
    
    with pytest.raises(NotImplementedError):
        gen.generate("test_seed")
```

**Критерии завершения:**
- ✅ Скелет генератора создан
- ✅ Чёткое разделение по слоям
- ✅ Базовые тесты проходят

---

### ФАЗА 2: Генерация континента (СЛОЙ 0.5) (12-16 часов)

#### Задача 2.1: Генерация макро-рельефа континента (8-10 часов)

**Цель:** Создать органичную форму континента с береговой линией

**Файл:** `src/core/world_generator_v2.py` (метод `_generate_continent`)

**Алгоритм:**

```python
def _generate_continent(self, seed: str) -> ContinentData:
    """
    Генерация континента (макро-рельеф)
    
    Алгоритм:
    1. Низкочастотный Perlin Noise → базовый heightmap
    2. Threshold → continent_mask (суша vs океан)
    3. Морфологические операции → сглаживание береговой линии
    4. Gaussian blur → финальное сглаживание
    5. Расчёт геометрии → center, major_axis
    """
    config = self.config['continent']
    
    # 1. Генерация базового heightmap (Perlin Noise)
    heightmap = generate_perlin_noise(
        seed=hash(seed + "continent") % (2**31),  # Детерминированный hash
        width=self.global_size[0],
        height=self.global_size[1],
        scale=config['perlin_noise']['scale'],
        octaves=config['perlin_noise']['octaves'],
        persistence=config['perlin_noise']['persistence'],
        lacunarity=config['perlin_noise']['lacunarity']
    )
    
    # Нормализация в [0, 1]
    heightmap = (heightmap - heightmap.min()) / (heightmap.max() - heightmap.min())
    
    # 2. Определение суши vs океана
    sea_level = config['sea_level']
    continent_mask = (heightmap > sea_level).astype(bool)
    
    # 3. Морфологические операции для сглаживания
    from scipy import ndimage
    from scipy.ndimage import morphology
    
    # Binary opening (удаляет маленькие острова)
    continent_mask = morphology.binary_opening(
        continent_mask,
        iterations=config['smoothing']['binary_opening_iterations']
    )
    
    # Binary closing (заполняет маленькие заливы)
    continent_mask = morphology.binary_closing(
        continent_mask,
        iterations=config['smoothing']['binary_closing_iterations']
    )
    
    # 4. Gaussian blur для финального сглаживания
    continent_float = ndimage.gaussian_filter(
        continent_mask.astype(float),
        sigma=config['smoothing']['gaussian_sigma']
    )
    
    # Применяем threshold снова после blur
    continent_mask = (continent_float > config['smoothing']['final_threshold']).astype(bool)
    
    # 5. Расчёт геометрии континента
    center = self._calculate_center_of_mass(continent_mask)
    major_axis = self._calculate_major_axis(continent_mask)
    
    return ContinentData(
        mask=continent_mask,
        heightmap=heightmap,
        center=center,
        major_axis=major_axis
    )

def _calculate_center_of_mass(self, mask: np.ndarray) -> Tuple[int, int]:
    """Расчёт центра масс континента"""
    from scipy import ndimage
    cy, cx = ndimage.center_of_mass(mask)
    return (int(cx), int(cy))

def _calculate_major_axis(self, mask: np.ndarray) -> Tuple[Tuple[int, int], Tuple[int, int]]:
    """
    Расчёт главной оси континента (самая длинная ось)
    
    Метод: PCA (Principal Component Analysis) на координатах суши
    """
    # Получаем координаты всех точек суши
    y_coords, x_coords = np.where(mask)
    
    if len(x_coords) == 0:
        # Нет суши - возвращаем центр карты
        center = (self.global_size[0] // 2, self.global_size[1] // 2)
        return (center, center)
    
    coords = np.column_stack([x_coords, y_coords])
    
    # Центрируем данные
    mean = coords.mean(axis=0)
    centered = coords - mean
    
    # PCA: находим главный компонент (направление максимальной дисперсии)
    cov_matrix = np.cov(centered.T)
    eigenvalues, eigenvectors = np.linalg.eig(cov_matrix)
    
    # Главный eigenvector (соответствует максимальному eigenvalue)
    principal_component = eigenvectors[:, eigenvalues.argmax()]
    
    # Проецируем все точки на главный компонент
    projections = centered @ principal_component
    
    # Находим крайние точки (начало и конец оси)
    min_idx = projections.argmin()
    max_idx = projections.argmax()
    
    start_point = coords[min_idx]
    end_point = coords[max_idx]
    
    return (
        (int(start_point[0]), int(start_point[1])),
        (int(end_point[0]), int(end_point[1]))
    )
```

**Tests:** `tests/core/test_continent_generation.py`

```python
def test_continent_generation_deterministic():
    """Континент должен быть детерминированным для одного seed"""
    gen = WorldGeneratorV2()
    
    continent1 = gen._generate_continent("test_seed_123")
    continent2 = gen._generate_continent("test_seed_123")
    
    np.testing.assert_array_equal(continent1.mask, continent2.mask)
    np.testing.assert_array_almost_equal(continent1.heightmap, continent2.heightmap)

def test_continent_has_land():
    """Континент должен содержать сушу"""
    gen = WorldGeneratorV2()
    continent = gen._generate_continent("test_seed")
    
    land_percentage = continent.mask.sum() / (512 * 512)
    
    # Ожидаем 55-75% суши (sea_level = 0.35)
    assert 0.5 < land_percentage < 0.8

def test_continent_has_ocean():
    """Континент должен содержать океан"""
    gen = WorldGeneratorV2()
    continent = gen._generate_continent("test_seed")
    
    ocean_count = (~continent.mask).sum()
    
    assert ocean_count > 0

def test_continent_center_on_land():
    """Центр масс континента должен быть на суше"""
    gen = WorldGeneratorV2()
    continent = gen._generate_continent("test_seed")
    
    cx, cy = continent.center
    
    assert continent.mask[cy, cx], "Center is not on land!"

def test_continent_major_axis():
    """Главная ось континента должна проходить по суше"""
    gen = WorldGeneratorV2()
    continent = gen._generate_continent("test_seed")
    
    (x1, y1), (x2, y2) = continent.major_axis
    
    # Начало и конец оси должны быть на суше
    assert continent.mask[y1, x1], "Axis start not on land"
    assert continent.mask[y2, x2], "Axis end not on land"
    
    # Ось должна быть достаточно длинной
    length = np.sqrt((x2 - x1)**2 + (y2 - y1)**2)
    assert length > 100, f"Axis too short: {length}"

def test_continent_smoothness():
    """Береговая линия должна быть сглаженной (без мелких островков)"""
    gen = WorldGeneratorV2()
    continent = gen._generate_continent("test_seed")
    
    # Подсчёт связных компонент (островов)
    from scipy import ndimage
    labeled, num_islands = ndimage.label(continent.mask)
    
    # Ожидаем 1-3 крупных острова (не десятки мелких)
    assert num_islands <= 5, f"Too many islands: {num_islands}"
```

**Визуализация:** `scripts/visualize_continent.py`

```python
"""
Скрипт для визуализации континента
Usage: python scripts/visualize_continent.py --seed test_seed_123
"""

import matplotlib.pyplot as plt
import numpy as np
from src.core.world_generator_v2 import WorldGeneratorV2

def visualize_continent(seed: str):
    gen = WorldGeneratorV2()
    continent = gen._generate_continent(seed)
    
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    
    # 1. Heightmap
    im1 = axes[0].imshow(continent.heightmap, cmap='terrain', origin='lower')
    axes[0].set_title('Heightmap (Perlin Noise)')
    axes[0].axis('off')
    plt.colorbar(im1, ax=axes[0])
    
    # 2. Continent Mask
    axes[1].imshow(continent.mask, cmap='gray', origin='lower')
    axes[1].set_title(f'Continent Mask (Land: {continent.mask.sum() / (512*512) * 100:.1f}%)')
    axes[1].axis('off')
    
    # 3. Continent + Geometry
    axes[2].imshow(continent.mask, cmap='gray', origin='lower', alpha=0.7)
    
    # Рисуем центр масс
    cx, cy = continent.center
    axes[2].scatter(cx, cy, c='red', s=100, marker='X', label='Center of Mass')
    
    # Рисуем главную ось
    (x1, y1), (x2, y2) = continent.major_axis
    axes[2].plot([x1, x2], [y1, y2], 'b-', linewidth=3, label='Major Axis')
    axes[2].scatter([x1, x2], [y1, y2], c='blue', s=50, marker='o')
    
    axes[2].set_title('Continent Geometry')
    axes[2].legend()
    axes[2].axis('off')
    
    plt.suptitle(f'Continent Generation (seed: {seed})', fontsize=16)
    plt.tight_layout()
    plt.savefig(f'output/continent_{seed}.png', dpi=150, bbox_inches='tight')
    print(f"✅ Saved to output/continent_{seed}.png")
    plt.show()

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--seed', type=str, default='silgarron_alpha_01')
    args = parser.parse_args()
    
    visualize_continent(args.seed)
```

**Критерии завершения:**
- ✅ Континент генерируется детерминированно
- ✅ Береговая линия сглаженная и органичная
- ✅ Центр масс и главная ось рассчитываются правильно
- ✅ Все тесты проходят (>85% coverage)
- ✅ Визуализация показывает красивый континент

---

#### Задача 2.2: Итеративный тюнинг параметров континента (4-6 часов)

**Цель:** Подобрать параметры Perlin Noise и сглаживания для максимальной органичности

**Метод:** Генерация континентов с разными параметрами, визуальная оценка

**Скрипт:** `scripts/tune_continent_parameters.py`

```python
"""
Автоматический тюнинг параметров генерации континента
"""

import itertools
import matplotlib.pyplot as plt
from src.core.world_generator_v2 import WorldGeneratorV2

def tune_parameters():
    # Диапазоны параметров для тестирования
    scales = [100, 150, 200]
    octaves = [1, 2, 3]
    sea_levels = [0.30, 0.35, 0.40]
    
    seed = "tune_test"
    
    fig, axes = plt.subplots(
        len(scales) * len(octaves),
        len(sea_levels),
        figsize=(15, 20)
    )
    
    idx = 0
    best_params = None
    best_score = -1
    
    for scale in scales:
        for octave in octaves:
            for sea_level in sea_levels:
                # Временно обновляем конфиг
                gen = WorldGeneratorV2()
                gen.config['continent']['perlin_noise']['scale'] = scale
                gen.config['continent']['perlin_noise']['octaves'] = octave
                gen.config['continent']['sea_level'] = sea_level
                
                continent = gen._generate_continent(seed)
                
                # Метрика качества
                land_pct = continent.mask.sum() / (512*512)
                
                # Подсчёт островов
                from scipy import ndimage
                labeled, num_islands = ndimage.label(continent.mask)
                
                # Простая метрика: близость к 65% суши + минимум островов
                score = 100 - abs(land_pct - 0.65) * 100 - num_islands * 10
                
                if score > best_score:
                    best_score = score
                    best_params = {
                        'scale': scale,
                        'octaves': octave,
                        'sea_level': sea_level,
                        'land_pct': land_pct,
                        'islands': num_islands
                    }
                
                # Визуализация
                row = idx // len(sea_levels)
                col = idx % len(sea_levels)
                axes[row, col].imshow(continent.mask, cmap='gray')
                axes[row, col].set_title(
                    f"s={scale}, o={octave}, sl={sea_level}\n"
                    f"Land={land_pct*100:.1f}%, Islands={num_islands}",
                    fontsize=8
                )
                axes[row, col].axis('off')
                
                idx += 1
    
    plt.tight_layout()
    plt.savefig('output/continent_tuning.png', dpi=150)
    print(f"✅ Saved tuning results to output/continent_tuning.png")
    
    print("\n🏆 BEST PARAMETERS:")
    for key, value in best_params.items():
        print(f"  {key}: {value}")
    
    return best_params

if __name__ == '__main__':
    tune_parameters()
```

**Процесс тюнинга:**
1. Запустить `tune_continent_parameters.py`
2. Визуально оценить все варианты
3. Выбрать лучший по критериям:
   - Органичная форма (не квадрат)
   - 55-75% суши
   - 1-3 крупных острова (не россыпь мелких)
   - Гладкая береговая линия
4. Обновить `config/world_generation_v2.yaml` с лучшими параметрами

**Ожидаемые результаты:**
```yaml
continent:
  perlin_noise:
    scale: 150  # Может измениться на 100 или 200
    octaves: 2   # Может измениться на 1 или 3
  sea_level: 0.35  # Может измениться на 0.30 или 0.40
```

**Критерии завершения:**
- ✅ Протестированы 3×3×3 = 27 комбинаций параметров
- ✅ Выбраны лучшие параметры
- ✅ Конфиг обновлён
- ✅ Команда одобрила визуал континента

---

### ФАЗА 3: Размещение органов (СЛОЙ 1) (12-16 часов)

#### Задача 3.1: Реализация placement методов для органов (8-10 часов)

**Цель:** Разместить органы на континенте детерминированно

**Файл:** `src/core/organ_placement.py` (НОВЫЙ)

```python
"""
Модуль размещения органов на континенте
"""

import numpy as np
from typing import Dict, Tuple, Optional
from scipy import ndimage

from src.models.world import Organ, ContinentData

class OrganPlacer:
    """Класс для размещения органов на континенте"""
    
    def __init__(self, config: dict):
        self.config = config
    
    def place_all_organs(self, seed: str, continent: ContinentData) -> Dict[str, Organ]:
        """
        Размещение всех органов согласно конфигурации
        
        Args:
            seed: Seed для детерминированности
            continent: Данные континента
        
        Returns:
            Словарь {organ_id: Organ}
        """
        organs = {}
        
        # Размещаем органы в правильном порядке (с учётом зависимостей)
        # 1. Metabolic organ (не зависит от других)
        organs.update(self._place_metabolic_organs(seed, continent))
        
        # 2. Digestive organs (зависят от metabolic)
        organs.update(self._place_digestive_organs(seed, continent, organs))
        
        # 3. Neural clusters (зависят от геометрии континента)
        organs.update(self._place_neural_clusters(seed, continent))
        
        # 4. Immune nodes (зависят от neural clusters)
        organs.update(self._place_immune_nodes(seed, continent, organs))
        
        return organs
    
    # ========== METABOLIC ORGAN ==========
    
    def _place_metabolic_organs(self, seed: str, continent: ContinentData) -> Dict[str, Organ]:
        """Размещение метаболических органов (желудок, сердце)"""
        config = self.config['organs']['metabolic_organ']
        organs = {}
        
        # Метод: center_of_continent
        position = continent.center
        
        organ = Organ(
            id='organ_metabolic_core',
            type='metabolic_organ',
            position=position,
            radius=config['radius'],
            temperature=config['temperature'],
            nutrient_output=config['nutrient_output']
        )
        
        organs[organ.id] = organ
        return organs
    
    # ========== DIGESTIVE ORGAN ==========
    
    def _place_digestive_organs(self, seed: str, continent: ContinentData,
                                 existing_organs: Dict[str, Organ]) -> Dict[str, Organ]:
        """Размещение пищеварительных органов (желудок)"""
        config = self.config['organs']['digestive']
        organs = {}
        
        # Метод: suitable_lowland (ищем низину рядом с metabolic_organ)
        near_organ_id = 'organ_metabolic_core'
        near_organ = existing_organs[near_organ_id]
        
        # Ищем низину южнее metabolic_core
        position = self._find_suitable_lowland(
            continent=continent,
            near_position=near_organ.position,
            direction='south',
            radius_range=config['placement_params']['radius_range'],
            seed=seed
        )
        
        organ = Organ(
            id='organ_stomach',
            type='digestive',
            position=position,
            radius=config['radius'],
            temperature=config['temperature'],
            acid_level=config['acid_level']
        )
        
        organs[organ.id] = organ
        return organs
    
    def _find_suitable_lowland(self, continent: ContinentData,
                               near_position: Tuple[int, int],
                               direction: str,
                               radius_range: list,
                               seed: str) -> Tuple[int, int]:
        """
        Найти подходящую низину
        
        Алгоритм:
        1. Определить зону поиска (южнее near_position)
        2. Найти точки на суше в этой зоне
        3. Выбрать точку с минимальной высотой
        """
        cx, cy = near_position
        min_radius, max_radius = radius_range
        
        # Зона поиска (южнее = выше по Y)
        search_mask = np.zeros_like(continent.mask)
        
        if direction == 'south':
            # Южная полусфера от центра
            y_min = cy + min_radius
            y_max = min(cy + max_radius, continent.heightmap.shape[0])
            x_min = max(0, cx - max_radius)
            x_max = min(cx + max_radius, continent.heightmap.shape[1])
        else:
            raise ValueError(f"Unknown direction: {direction}")
        
        search_mask[y_min:y_max, x_min:x_max] = True
        
        # Пересечение с сушей
        valid_mask = search_mask & continent.mask
        
        if not valid_mask.any():
            # Если не нашли - возвращаем позицию рядом с центром
            return (cx, cy + min_radius)
        
        # Находим точку с минимальной высотой
        heightmap_masked = np.where(valid_mask, continent.heightmap, np.inf)
        min_y, min_x = np.unravel_index(heightmap_masked.argmin(), heightmap_masked.shape)
        
        return (int(min_x), int(min_y))
    
    # ========== NEURAL CLUSTERS ==========
    
    def _place_neural_clusters(self, seed: str, continent: ContinentData) -> Dict[str, Organ]:
        """Размещение нервных узлов (ганглии)"""
        config = self.config['organs']['neural_cluster']
        organs = {}
        
        # Метод: along_axis (вдоль главной оси континента)
        (x1, y1), (x2, y2) = continent.major_axis
        
        for idx, relative_pos in enumerate(config['placement_params']['positions']):
            # Интерполяция по оси
            x = int(x1 + (x2 - x1) * relative_pos)
            y = int(y1 + (y2 - y1) * relative_pos)
            
            # Проверяем, что точка на суше
            if not continent.mask[y, x]:
                # Ищем ближайшую точку на суше
                x, y = self._find_nearest_land(continent.mask, (x, y))
            
            # Сила контроля уменьшается для каждого следующего ганглия
            control_strength = config['control_strength'] - idx * config['control_decay']
            
            organ = Organ(
                id=f'ganglion_{idx}',
                type='neural_cluster',
                position=(x, y),
                radius=config['radius'],
                control_strength=control_strength
            )
            
            organs[organ.id] = organ
        
        return organs
    
    def _find_nearest_land(self, mask: np.ndarray, position: Tuple[int, int]) -> Tuple[int, int]:
        """Найти ближайшую точку на суше"""
        x, y = position
        
        # Distance transform от суши
        from scipy.ndimage import distance_transform_edt
        distances = distance_transform_edt(~mask)
        
        # Ищем в радиусе 50 пикселей
        search_radius = 50
        y_min = max(0, y - search_radius)
        y_max = min(mask.shape[0], y + search_radius)
        x_min = max(0, x - search_radius)
        x_max = min(mask.shape[1], x + search_radius)
        
        # Находим ближайшую сушу
        search_region = distances[y_min:y_max, x_min:x_max]
        min_y, min_x = np.unravel_index(search_region.argmin(), search_region.shape)
        
        return (x_min + int(min_x), y_min + int(min_y))
    
    # ========== IMMUNE NODES ==========
    
    def _place_immune_nodes(self, seed: str, continent: ContinentData,
                           existing_organs: Dict[str, Organ]) -> Dict[str, Organ]:
        """Размещение иммунных узлов (лимфоузлы)"""
        config = self.config['organs']['immune_node']
        organs = {}
        
        # Метод: elevated_point (на возвышении рядом с ганглием)
        near_organ_id = 'ganglion_0'  # Первый ганглий
        near_organ = existing_organs[near_organ_id]
        
        # Ищем возвышенность рядом
        position = self._find_elevated_point(
            continent=continent,
            near_position=near_organ.position,
            search_radius=50,
            seed=seed
        )
        
        organ = Organ(
            id='lymph_node_sclerite',
            type='immune_node',
            position=position,
            radius=config['radius'],
            cell_production=config['cell_production']
        )
        
        organs[organ.id] = organ
        return organs
    
    def _find_elevated_point(self, continent: ContinentData,
                            near_position: Tuple[int, int],
                            search_radius: int,
                            seed: str) -> Tuple[int, int]:
        """Найти возвышенную точку"""
        cx, cy = near_position
        
        # Зона поиска
        y_min = max(0, cy - search_radius)
        y_max = min(continent.heightmap.shape[0], cy + search_radius)
        x_min = max(0, cx - search_radius)
        x_max = min(continent.heightmap.shape[1], cx + search_radius)
        
        # Маска зоны поиска
        search_mask = np.zeros_like(continent.mask)
        search_mask[y_min:y_max, x_min:x_max] = True
        
        # Пересечение с сушей
        valid_mask = search_mask & continent.mask
        
        if not valid_mask.any():
            return near_position  # Fallback
        
        # Находим точку с максимальной высотой
        heightmap_masked = np.where(valid_mask, continent.heightmap, -np.inf)
        max_y, max_x = np.unravel_index(heightmap_masked.argmax(), heightmap_masked.shape)
        
        return (int(max_x), int(max_y))
```

**Tests:** `tests/core/test_organ_placement.py`

```python
def test_metabolic_organ_placement():
    """Метаболический орган должен быть в центре континента"""
    placer = OrganPlacer(config)
    organs = placer._place_metabolic_organs("test", continent)
    
    metabolic = organs['organ_metabolic_core']
    assert metabolic.position == continent.center

def test_digestive_organ_placement():
    """Желудок должен быть южнее метаболического органа"""
    placer = OrganPlacer(config)
    
    metabolic_organs = placer._place_metabolic_organs("test", continent)
    digestive_organs = placer._place_digestive_organs("test", continent, metabolic_organs)
    
    metabolic = metabolic_organs['organ_metabolic_core']
    stomach = digestive_organs['organ_stomach']
    
    # Желудок должен быть ниже (больше Y)
    assert stomach.position[1] > metabolic.position[1]

def test_neural_clusters_on_axis():
    """Ганглии должны быть вдоль главной оси"""
    placer = OrganPlacer(config)
    organs = placer._place_neural_clusters("test", continent)
    
    assert len(organs) == 2
    assert 'ganglion_0' in organs
    assert 'ganglion_1' in organs
    
    # Проверяем, что они на суше
    for organ in organs.values():
        x, y = organ.position
        assert continent.mask[y, x], f"{organ.id} not on land"

def test_immune_node_near_ganglion():
    """Лимфоузел должен быть рядом с ганглием"""
    placer = OrganPlacer(config)
    
    neural = placer._place_neural_clusters("test", continent)
    immune = placer._place_immune_nodes("test", continent, neural)
    
    ganglion = neural['ganglion_0']
    lymph = immune['lymph_node_sclerite']
    
    # Расстояние < 50 пикселей
    distance = np.sqrt(
        (lymph.position[0] - ganglion.position[0])**2 +
        (lymph.position[1] - ganglion.position[1])**2
    )
    
    assert distance < 50

def test_all_organs_on_land():
    """Все органы должны быть на суше"""
    placer = OrganPlacer(config)
    organs = placer.place_all_organs("test", continent)
    
    for organ in organs.values():
        x, y = organ.position
        assert continent.mask[y, x], f"{organ.id} not on land at {organ.position}"

def test_organ_placement_deterministic():
    """Размещение должно быть детерминированным"""
    placer = OrganPlacer(config)
    
    organs1 = placer.place_all_organs("test_seed", continent)
    organs2 = placer.place_all_organs("test_seed", continent)
    
    for organ_id in organs1.keys():
        assert organs1[organ_id].position == organs2[organ_id].position
```

**Интеграция в WorldGeneratorV2:**

```python
# В файле src/core/world_generator_v2.py

from src.core.organ_placement import OrganPlacer

def _place_organs(self, seed: str, continent: ContinentData) -> Dict[str, Organ]:
    """Размещение органов на континенте"""
    placer = OrganPlacer(self.config)
    return placer.place_all_organs(seed, continent)
```

**Критерии завершения:**
- ✅ Все 4 типа органов размещаются правильно
- ✅ Органы детерминированные для одного seed
- ✅ Все органы на суше
- ✅ Тесты проходят (>85% coverage)

---

#### Задача 3.2: Определение региональных масок (4-6 часов)

**Цель:** Создать маски регионов на основе континента и органов

**Файл:** `src/core/region_definition.py` (НОВЫЙ)

```python
"""
Модуль определения региональных масок
"""

import numpy as np
from typing import Dict
from scipy import ndimage

from src.models.world import Region, ContinentData, Organ

class RegionDefiner:
    """Класс для определения региональных масок"""
    
    def __init__(self, config: dict):
        self.config = config
    
    def define_all_regions(self, continent: ContinentData,
                          organs: Dict[str, Organ]) -> Dict[str, Region]:
        """
        Определение всех региональных масок
        
        Примечание: В Sprint 3.6 мы создаём только БАЗОВЫЕ маски.
        Точное определение регионов (особенно THORAX) требует скелета,
        который будет создан в Sprint 3.7.
        
        Пока используем упрощённую логику на основе:
        - Геометрии континента
        - Позиций органов
        """
        regions = {}
        
        # Простейшая логика для Sprint 3.6:
        # Делим континент на 3 зоны по оси Y
        
        (x1, y1), (x2, y2) = continent.major_axis
        
        # THORAX: северная треть (где дыхание)
        regions['THORAX'] = self._define_thorax_region(continent, y1)
        
        # ORGANOID: средняя зона (где органы)
        regions['ORGANOID'] = self._define_organoid_region(continent, organs)
        
        # GRASPING_LIMB: южная оконечность
        regions['GRASPING_LIMB'] = self._define_limb_region(continent, y2)
        
        # DIAPHRAGM: граница между thorax и organoid
        regions['DIAPHRAGM'] = self._define_diaphragm_region(
            continent,
            regions['THORAX'].mask,
            regions['ORGANOID'].mask
        )
        
        return regions
    
    def _define_thorax_region(self, continent: ContinentData, axis_y1: int) -> Region:
        """
        Определение региона THORAX (грудная клетка)
        
        Упрощённая логика для Sprint 3.6:
        Северная треть континента
        """
        config = self.config['regions']['THORAX']
        
        # Маска: северная треть
        mask = np.zeros_like(continent.mask)
        mask[:axis_y1, :] = continent.mask[:axis_y1, :]
        
        return Region(
            id='thorax',
            name='THORAX',
            mask=mask,
            characteristics=config['characteristics']
        )
    
    def _define_organoid_region(self, continent: ContinentData,
                                organs: Dict[str, Organ]) -> Region:
        """
        Определение региона ORGANOID (брюшная полость)
        
        Логика: зона вокруг метаболических органов
        """
        config = self.config['regions']['ORGANOID']
        
        # Находим метаболические органы
        metabolic_positions = [
            org.position for org in organs.values()
            if org.type in ['metabolic_organ', 'digestive']
        ]
        
        # Создаём маску вокруг них
        mask = np.zeros_like(continent.mask)
        
        for (cx, cy) in metabolic_positions:
            # Радиус влияния = 80 пикселей
            y, x = np.ogrid[:mask.shape[0], :mask.shape[1]]
            distance = np.sqrt((x - cx)**2 + (y - cy)**2)
            mask |= (distance < 80)
        
        # Пересечение с сушей
        mask &= continent.mask
        
        return Region(
            id='organoid',
            name='ORGANOID',
            mask=mask,
            characteristics=config['characteristics']
        )
    
    def _define_limb_region(self, continent: ContinentData, axis_y2: int) -> Region:
        """
        Определение региона GRASPING_LIMB (конечность)
        
        Логика: южная оконечность континента
        """
        config = self.config['regions']['GRASPING_LIMB']
        
        # Маска: южная четверть
        mask = np.zeros_like(continent.mask)
        y_threshold = int(axis_y2 + (512 - axis_y2) * 0.5)
        mask[y_threshold:, :] = continent.mask[y_threshold:, :]
        
        return Region(
            id='limb',
            name='GRASPING_LIMB',
            mask=mask,
            characteristics=config['characteristics']
        )
    
    def _define_diaphragm_region(self, continent: ContinentData,
                                 thorax_mask: np.ndarray,
                                 organoid_mask: np.ndarray) -> Region:
        """
        Определение региона DIAPHRAGM (диафрагма)
        
        Логика: граница между thorax и organoid
        """
        config = self.config['regions']['DIAPHRAGM']
        
        # Дилатация масок
        from scipy.ndimage import binary_dilation
        
        thorax_dilated = binary_dilation(thorax_mask, iterations=10)
        organoid_dilated = binary_dilation(organoid_mask, iterations=10)
        
        # Пересечение дилатаций = граница
        mask = thorax_dilated & organoid_dilated & continent.mask
        
        return Region(
            id='diaphragm',
            name='DIAPHRAGM',
            mask=mask,
            characteristics=config['characteristics']
        )
```

**Tests:** `tests/core/test_region_definition.py`

```python
def test_all_regions_defined():
    """Должны быть определены все 4 региона"""
    definer = RegionDefiner(config)
    regions = definer.define_all_regions(continent, organs)
    
    assert len(regions) == 4
    assert 'THORAX' in regions
    assert 'DIAPHRAGM' in regions
    assert 'ORGANOID' in regions
    assert 'GRASPING_LIMB' in regions

def test_regions_on_land():
    """Все регионы должны быть на суше"""
    definer = RegionDefiner(config)
    regions = definer.define_all_regions(continent, organs)
    
    for region in regions.values():
        # Все точки региона должны быть на континенте
        assert np.all(region.mask <= continent.mask)

def test_regions_cover_most_land():
    """Регионы должны покрывать большую часть суши"""
    definer = RegionDefiner(config)
    regions = definer.define_all_regions(continent, organs)
    
    # Объединение всех регионов
    total_mask = np.zeros_like(continent.mask)
    for region in regions.values():
        total_mask |= region.mask
    
    # Покрытие должно быть >60% суши
    coverage = total_mask.sum() / continent.mask.sum()
    assert coverage > 0.6

def test_organoid_contains_metabolic_organ():
    """Органоид должен содержать метаболический орган"""
    definer = RegionDefiner(config)
    regions = definer.define_all_regions(continent, organs)
    
    metabolic = organs['organ_metabolic_core']
    x, y = metabolic.position
    
    assert regions['ORGANOID'].mask[y, x], "Metabolic organ not in ORGANOID"
```

**Интеграция в WorldGeneratorV2:**

```python
# В файле src/core/world_generator_v2.py

from src.core.region_definition import RegionDefiner

def _define_regions(self, continent: ContinentData,
                   organs: Dict[str, Organ]) -> Dict[str, Region]:
    """Определение региональных масок"""
    definer = RegionDefiner(self.config)
    return definer.define_all_regions(continent, organs)
```

**Критерии завершения:**
- ✅ Все 4 региона определены
- ✅ Регионы находятся на суше
- ✅ Органоид содержит метаболический орган
- ✅ Тесты проходят (>85% coverage)

---

### ФАЗА 4: Визуализация и интеграция (4-6 часов)

#### Задача 4.1: Полная визуализация континента + органов + регионов (3-4 часа)

**Цель:** Создать красивую визуализацию результатов Sprint 3.6

**Скрипт:** `scripts/visualize_world_v2.py`

```python
"""
Полная визуализация мира v2.0 (Sprint 3.6)
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
from src.core.world_generator_v2 import WorldGeneratorV2

def visualize_world(seed: str):
    gen = WorldGeneratorV2()
    world = gen.generate(seed)
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 16))
    
    # 1. Континент + геометрия
    ax = axes[0, 0]
    ax.imshow(world.continent.mask, cmap='gray', origin='lower', alpha=0.7)
    
    # Центр масс
    cx, cy = world.continent.center
    ax.scatter(cx, cy, c='red', s=200, marker='X', label='Center', zorder=10)
    
    # Главная ось
    (x1, y1), (x2, y2) = world.continent.major_axis
    ax.plot([x1, x2], [y1, y2], 'b-', linewidth=3, label='Major Axis', zorder=5)
    
    ax.set_title('Continent + Geometry')
    ax.legend()
    ax.axis('off')
    
    # 2. Континент + органы
    ax = axes[0, 1]
    ax.imshow(world.continent.mask, cmap='gray', origin='lower', alpha=0.5)
    
    # Рисуем органы
    colors = gen.config['visualization']['organ_colors']
    
    for organ in world.organs.values():
        x, y = organ.position
        color = colors.get(organ.type, '#FFFFFF')
        
        # Круг радиуса влияния
        circle = patches.Circle(
            (x, y),
            organ.radius,
            fill=True,
            facecolor=color,
            edgecolor='black',
            linewidth=2,
            alpha=0.6,
            label=f"{organ.type}"
        )
        ax.add_patch(circle)
        
        # Метка
        ax.text(x, y, organ.id.split('_')[-1][:3].upper(),
               ha='center', va='center',
               fontsize=8, fontweight='bold', color='white')
    
    ax.set_title(f'Continent + Organs ({len(world.organs)})')
    ax.axis('off')
    
    # Убираем дубликаты в легенде
    handles, labels = ax.get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    ax.legend(by_label.values(), by_label.keys(), loc='upper right')
    
    # 3. Регионы
    ax = axes[1, 0]
    
    # Базовый слой - континент
    base = np.zeros((*world.continent.mask.shape, 3))
    base[world.continent.mask] = [0.3, 0.3, 0.3]  # Серый для суши
    
    # Накладываем регионы
    region_colors_rgb = {
        'THORAX': (0.5, 0.5, 1.0, 0.5),
        'DIAPHRAGM': (1.0, 0.5, 1.0, 0.5),
        'ORGANOID': (1.0, 1.0, 0.5, 0.5),
        'GRASPING_LIMB': (0.5, 1.0, 0.5, 0.5)
    }
    
    for region_name, region in world.regions.items():
        color = region_colors_rgb[region_name]
        mask_rgb = np.zeros((*region.mask.shape, 4))
        mask_rgb[region.mask] = color
        ax.imshow(mask_rgb, origin='lower')
    
    ax.imshow(base, origin='lower', alpha=0.3)
    
    # Легенда
    legend_elements = [
        patches.Patch(facecolor=color[:3], alpha=0.5, label=name)
        for name, color in region_colors_rgb.items()
    ]
    ax.legend(handles=legend_elements, loc='upper right')
    
    ax.set_title('Regions')
    ax.axis('off')
    
    # 4. Комбинированная визуализация
    ax = axes[1, 1]
    
    # Континент
    ax.imshow(world.continent.mask, cmap='gray', origin='lower', alpha=0.3)
    
    # Регионы (полупрозрачные)
    for region_name, region in world.regions.items():
        color = region_colors_rgb[region_name]
        mask_rgb = np.zeros((*region.mask.shape, 4))
        mask_rgb[region.mask] = color
        ax.imshow(mask_rgb, origin='lower', alpha=0.3)
    
    # Органы
    for organ in world.organs.values():
        x, y = organ.position
        color = colors.get(organ.type, '#FFFFFF')
        
        circle = patches.Circle(
            (x, y),
            organ.radius,
            fill=True,
            facecolor=color,
            edgecolor='black',
            linewidth=2,
            alpha=0.8
        )
        ax.add_patch(circle)
    
    ax.set_title('Combined View')
    ax.axis('off')
    
    # Общий заголовок
    plt.suptitle(
        f'World Generation v2.0 - Sprint 3.6\n'
        f'Seed: {seed} | Phase: {world.world_phase}',
        fontsize=16,
        fontweight='bold'
    )
    
    plt.tight_layout()
    plt.savefig(f'output/world_v2_{seed}.png', dpi=200, bbox_inches='tight')
    print(f"✅ Saved to output/world_v2_{seed}.png")
    plt.show()

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--seed', type=str, default='silgarron_alpha_01')
    args = parser.parse_args()
    
    visualize_world(args.seed)
```

**Критерии завершения:**
- ✅ Визуализация показывает континент, органы и регионы
- ✅ Легенда и цвета читаемые
- ✅ Высокое разрешение (200 DPI)

---

#### Задача 4.2: Integration test полного цикла (1-2 часа)

**Цель:** Проверить работу всего пайплайна Sprint 3.6

**Tests:** `tests/integration/test_sprint_3_6_integration.py`

```python
"""
Integration test для Sprint 3.6
"""

def test_full_generation_pipeline():
    """Тест полного цикла генерации Sprint 3.6"""
    gen = WorldGeneratorV2()
    world = gen.generate("integration_test_seed")
    
    # 1. Проверяем континент
    assert world.continent is not None
    assert world.continent.mask.shape == (512, 512)
    assert world.continent.mask.any()  # Есть суша
    
    # 2. Проверяем органы
    assert len(world.organs) >= 4  # Минимум 4 типа
    
    # Все органы на суше
    for organ in world.organs.values():
        x, y = organ.position
        assert world.continent.mask[y, x], f"{organ.id} not on land"
    
    # 3. Проверяем регионы
    assert len(world.regions) == 4
    
    # Все регионы на суше
    for region in world.regions.values():
        assert np.all(region.mask <= world.continent.mask)
    
    # 4. Проверяем консистентность
    # Метаболический орган должен быть в ORGANOID
    metabolic = world.organs['organ_metabolic_core']
    x, y = metabolic.position
    assert world.regions['ORGANOID'].mask[y, x]
    
    print("✅ Full pipeline test passed!")

def test_determinism():
    """Генерация должна быть детерминированной"""
    gen = WorldGeneratorV2()
    
    world1 = gen.generate("determinism_test")
    world2 = gen.generate("determinism_test")
    
    # Континенты идентичны
    np.testing.assert_array_equal(world1.continent.mask, world2.continent.mask)
    
    # Органы в тех же позициях
    for organ_id in world1.organs.keys():
        assert world1.organs[organ_id].position == world2.organs[organ_id].position
    
    print("✅ Determinism test passed!")

def test_performance():
    """Генерация Sprint 3.6 должна быть быстрой (<5 сек)"""
    import time
    
    gen = WorldGeneratorV2()
    
    start = time.time()
    world = gen.generate("performance_test")
    elapsed = time.time() - start
    
    assert elapsed < 5.0, f"Generation took {elapsed:.2f}s (expected <5s)"
    print(f"✅ Performance test passed! ({elapsed:.2f}s)")
```

**Критерии завершения:**
- ✅ Все integration tests проходят
- ✅ Генерация детерминированная
- ✅ Производительность <5 сек

---

## ✅ Definition of Done

Спринт 3.6 считается завершённым, если:

### Функциональность
- [x] Континент генерируется с органичной формой и береговой линией
- [x] Все 4 типа органов размещаются на континенте детерминированно
- [x] 4 региона определены (THORAX, DIAPHRAGM, ORGANOID, GRASPING_LIMB)
- [x] Визуализация показывает красивую карту континента + органов + регионов

### Качество кода
- [x] Unit tests покрывают >85% кода
- [x] Integration tests проходят
- [x] Все компоненты задокументированы (docstrings)
- [x] Конфиг `world_generation_v2.yaml` полный и понятный

### Производительность
- [x] Генерация мира (Sprint 3.6 scope) выполняется за <5 сек
- [x] Нет утечек памяти

### Документация
- [x] Обновлён `MASTER_PLAN.md`
- [x] Создан `SPRINT_3.6_REPORT.md` с результатами
- [x] Все новые компоненты описаны в `Technical_Design_Document.md`

### Визуальная валидация
- [x] Команда одобрила визуал континента
- [x] Органы размещены логично
- [x] Регионы имеют смысл

---

## 🚨 Риски и митигация

### Риск 1: Континент выглядит искусственно
**Вероятность:** Средняя  
**Влияние:** Высокое  
**Митигация:**
- Итеративный тюнинг параметров (Задача 2.2)
- Визуальная валидация с командой
- Fallback: использовать более сложный Perlin (больше octaves)

### Риск 2: Органы размещаются вне суши
**Вероятность:** Низкая  
**Влияние:** Критическое  
**Митигация:**
- Валидация в `Organ.__post_init__`
- Unit tests на проверку `organ.position` на суше
- Метод `_find_nearest_land` как fallback

### Риск 3: Регионы не покрывают сушу
**Вероятность:** Средняя  
**Влияние:** Среднее  
**Митигация:**
- Test `test_regions_cover_most_land` (coverage >60%)
- Упрощённая логика регионов для Sprint 3.6 (точная в 3.7)

### Риск 4: Производительность >5 сек
**Вероятность:** Низкая  
**Влияние:** Низкое  
**Митигация:**
- Perlin Noise уже оптимизирован (Sprint 3.5)
- Размер 512×512 небольшой для современных CPU
- Performance test проверит это

---

## 📚 Технические спецификации

### Data Models

```python
@dataclass
class Organ:
    id: str
    type: str
    position: Tuple[int, int]
    radius: float
    # + специфичные поля

@dataclass
class Region:
    id: str
    name: str
    mask: np.ndarray  # (512, 512) boolean
    characteristics: Dict[str, float]

@dataclass
class ContinentData:
    mask: np.ndarray  # (512, 512) boolean
    heightmap: np.ndarray  # (512, 512) float
    center: Tuple[int, int]
    major_axis: Tuple[Tuple[int, int], Tuple[int, int]]
```

### Компоненты

```
src/
├── core/
│   ├── world_generator_v2.py (НОВЫЙ) - главный генератор
│   ├── organ_placement.py (НОВЫЙ) - размещение органов
│   └── region_definition.py (НОВЫЙ) - определение регионов
├── models/
│   └── world.py (ОБНОВЛЁН) - Organ, Region, ContinentData
config/
└── world_generation_v2.yaml (НОВЫЙ) - конфигурация
scripts/
├── visualize_continent.py (НОВЫЙ)
├── tune_continent_parameters.py (НОВЫЙ)
└── visualize_world_v2.py (НОВЫЙ)
```

### Зависимости от других спринтов

**Переиспользуем из Sprint 3.5:**
- ✅ `src/core/perlin_noise.py` (без изменений)
- ✅ `src/utils/config_loader.py` (без изменений)

**Не зависим от:**
- ❌ Sprint 3.7 (артерии, скелет) - создадим в следующем спринте
- ❌ Sprint 3.8 (гидрология) - создадим позже
- ❌ Sprint 3.9 (детализация) - создадим позже

---

## 🎯 Следующий спринт

**Sprint 3.7: Физиология и Геология (Слои 2-3)**
- Vessel Network (MST + spline)
- Skeleton Generator (хребет, рёбра)
- Structural stress для каверн

---

**Версия:** 1.0  
**Автор:** Claude & Team  
**Дата:** 25 октября 2025
