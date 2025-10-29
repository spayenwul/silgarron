"""
Визуализатор для Sprint 3.6 - Phase 1: Подготовка инфраструктуры

Демонстрирует:
- Загрузку и валидацию конфигурации
- Создание моделей данных (Organ, Region, ContinentData, World)
- Валидацию моделей
- Визуализацию структур данных

Usage:
    python scripts/visualize_phase1.py
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle
import sys
from pathlib import Path

# Добавляем корень проекта в путь
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.models.world import Organ, Region, ContinentData, World
from services.world_config_v2 import WorldGenerationConfigV2


def demo_config_manager():
    """Демонстрация работы менеджера конфигурации"""
    print("\n" + "="*70)
    print("[CONFIG] ДЕМОНСТРАЦИЯ: Менеджер конфигурации")
    print("="*70)

    # Загрузка конфига
    try:
        config = WorldGenerationConfigV2.from_yaml('config/world_generation_v2.yaml')
    except FileNotFoundError:
        print("[ERROR] Файл config/world_generation_v2.yaml не найден")
        print("   Создайте файл или запустите генератор сначала")
        return None

    # Вывод сводки
    config.print_summary()

    # Валидация
    if not config.validate():
        print("[ERROR] Конфигурация содержит ошибки")
        return None

    # Примеры доступа к параметрам
    print("\n[INFO] Примеры доступа к параметрам:")
    print(f"   Размер карты: {config.get_global_size()}")
    print(f"   Уровень моря: {config.get_sea_level()}")
    print(f"   Perlin параметры: {config.get_perlin_params()}")

    metabolic = config.get_organ_config('metabolic_organ')
    if metabolic:
        print(f"   Метаболический орган: count={metabolic['count']}, radius={metabolic['radius']}")

    return config


def demo_organ_creation():
    """Демонстрация создания и валидации органов"""
    print("\n" + "="*70)
    print("[ORGAN] ДЕМОНСТРАЦИЯ: Создание органов")
    print("="*70)

    # Успешное создание органа
    print("\n[OK] Создание валидного органа:")
    organ = Organ(
        id='heart',
        type='metabolic_organ',
        position=(256, 256),
        radius=30,
        temperature=0.95,
        nutrient_output=0.9
    )
    print(f"   {organ.id}: type={organ.type}, pos={organ.position}, r={organ.radius}")

    # Попытка создать невалидный орган
    print("\n[ERROR] Попытка создать орган с отрицательным радиусом:")
    try:
        bad_organ = Organ(
            id='bad',
            type='test',
            position=(100, 100),
            radius=-5
        )
    except ValueError as e:
        print(f"   Валидация сработала: {e}")

    print("\n[ERROR] Попытка создать орган вне границ карты:")
    try:
        bad_organ = Organ(
            id='bad',
            type='test',
            position=(600, 100),
            radius=10
        )
    except ValueError as e:
        print(f"   Валидация сработала: {e}")

    return organ


def demo_region_creation():
    """Демонстрация создания регионов"""
    print("\n" + "="*70)
    print("[REGION] ДЕМОНСТРАЦИЯ: Создание регионов")
    print("="*70)

    # Создаем маску региона (верхняя половина карты)
    mask = np.zeros((512, 512), dtype=bool)
    mask[:256, :] = True

    print(f"\n[OK] Создание региона THORAX:")
    region = Region(
        id='thorax_1',
        name='THORAX',
        mask=mask,
        characteristics={
            'elevation_bias': 0.3,
            'bone_density': 0.8,
            'respiratory_potential': 0.9
        }
    )
    print(f"   {region.id}: name={region.name}")
    print(f"   Покрытие: {mask.sum()} пикселей ({mask.sum() / (512*512) * 100:.1f}%)")
    print(f"   Характеристики: {region.characteristics}")

    # Попытка создать регион с неправильным размером
    print("\n[ERROR] Попытка создать регион с неправильным размером маски:")
    try:
        bad_mask = np.zeros((256, 256), dtype=bool)
        bad_region = Region(id='bad', name='BAD', mask=bad_mask)
    except ValueError as e:
        print(f"   Валидация сработала: {e}")

    return region


def demo_continent_creation():
    """Демонстрация создания континента"""
    print("\n" + "="*70)
    print("[CONTINENT] ДЕМОНСТРАЦИЯ: Создание континента")
    print("="*70)

    # Создаем простой континент (круг в центре)
    mask = np.zeros((512, 512), dtype=bool)
    Y, X = np.ogrid[:512, :512]
    center = (256, 256)
    radius = 150

    distance = np.sqrt((X - center[0])**2 + (Y - center[1])**2)
    mask = distance <= radius

    # Простой heightmap (градиент от центра)
    heightmap = 1.0 - (distance / 256)
    heightmap = np.clip(heightmap, 0, 1)

    print(f"\n[OK] Создание континента:")
    continent = ContinentData(
        mask=mask,
        heightmap=heightmap,
        center=(256, 256),
        major_axis=((106, 256), (406, 256))  # Горизонтальная ось
    )

    land_pct = mask.sum() / (512 * 512) * 100
    print(f"   Суша: {land_pct:.1f}%")
    print(f"   Центр: {continent.center}")
    print(f"   Главная ось: {continent.major_axis}")

    return continent


def demo_world_creation(organ, region, continent):
    """Демонстрация создания полного мира"""
    print("\n" + "="*70)
    print("[WORLD] ДЕМОНСТРАЦИЯ: Создание мира")
    print("="*70)

    print("\n[OK] Создание World с континентом, органами и регионами:")
    world = World(
        seed="demo_seed_123",
        world_phase="EXHALE",
        age="LATE_EXHALE",
        continent=continent,
        organs={'heart': organ},
        regions={'THORAX': region}
    )

    print(f"   Seed: {world.seed}")
    print(f"   Phase: {world.world_phase}")
    print(f"   Age: {world.age}")
    print(f"   Органов: {len(world.organs)}")
    print(f"   Регионов: {len(world.regions)}")
    print(f"   Континент: {'Да' if world.continent else 'Нет'}")

    return world


def visualize_all(organ, region, continent, world):
    """Создает визуализацию всех компонентов"""
    print("\n" + "="*70)
    print("[INFO] СОЗДАНИЕ ВИЗУАЛИЗАЦИИ")
    print("="*70)

    fig, axes = plt.subplots(2, 2, figsize=(14, 14))

    # 1. Континент (mask)
    axes[0, 0].imshow(continent.mask, cmap='gray', origin='lower')
    axes[0, 0].scatter(*continent.center, c='red', s=200, marker='X', label='Center', zorder=10)
    (x1, y1), (x2, y2) = continent.major_axis
    axes[0, 0].plot([x1, x2], [y1, y2], 'b-', linewidth=3, label='Major Axis')
    axes[0, 0].set_title('Континент (Mask)', fontsize=14, fontweight='bold')
    axes[0, 0].legend()
    axes[0, 0].set_xlim(0, 512)
    axes[0, 0].set_ylim(0, 512)

    # 2. Континент (heightmap)
    im = axes[0, 1].imshow(continent.heightmap, cmap='terrain', origin='lower')
    axes[0, 1].set_title('Континент (Heightmap)', fontsize=14, fontweight='bold')
    plt.colorbar(im, ax=axes[0, 1], label='Elevation')
    axes[0, 1].set_xlim(0, 512)
    axes[0, 1].set_ylim(0, 512)

    # 3. Регион
    axes[1, 0].imshow(region.mask, cmap='Blues', origin='lower', alpha=0.7)
    axes[1, 0].set_title(f'Регион: {region.name}', fontsize=14, fontweight='bold')
    land_pct = region.mask.sum() / (512*512) * 100
    axes[1, 0].text(
        10, 490,
        f'Покрытие: {land_pct:.1f}%\nХарактеристики:\n' +
        '\n'.join(f'  {k}: {v}' for k, v in region.characteristics.items()),
        fontsize=9,
        bbox=dict(boxstyle='round', facecolor='white', alpha=0.8),
        verticalalignment='top'
    )
    axes[1, 0].set_xlim(0, 512)
    axes[1, 0].set_ylim(0, 512)

    # 4. Орган на континенте
    axes[1, 1].imshow(continent.mask, cmap='gray', origin='lower', alpha=0.5)

    # Рисуем орган как круг
    circle = Circle(
        organ.position,
        organ.radius,
        color='red',
        alpha=0.6,
        label=f'{organ.type}'
    )
    axes[1, 1].add_patch(circle)
    axes[1, 1].scatter(*organ.position, c='darkred', s=100, marker='o', zorder=10)

    axes[1, 1].set_title(f'Орган: {organ.id}', fontsize=14, fontweight='bold')
    axes[1, 1].text(
        organ.position[0] + organ.radius + 10,
        organ.position[1],
        f'Type: {organ.type}\nRadius: {organ.radius}\nTemp: {organ.temperature}\nNutrient: {organ.nutrient_output}',
        fontsize=9,
        bbox=dict(boxstyle='round', facecolor='white', alpha=0.8)
    )
    axes[1, 1].legend()
    axes[1, 1].set_xlim(0, 512)
    axes[1, 1].set_ylim(0, 512)

    plt.suptitle(
        f'Sprint 3.6 Phase 1: Модели данных\nSeed: {world.seed} | Phase: {world.world_phase}',
        fontsize=16,
        fontweight='bold'
    )
    plt.tight_layout()

    # Сохранение
    output_dir = project_root / 'output'
    output_dir.mkdir(exist_ok=True)

    output_path = output_dir / 'phase1_visualization.png'
    plt.savefig(output_path, dpi=150, bbox_inches='tight')

    print(f"\n[OK] Визуализация сохранена: {output_path}")

    # Показать
    plt.show()


def main():
    """Главная функция"""
    print("\n" + "="*70)
    print("[VIZ] SPRINT 3.6 - PHASE 1: ВИЗУАЛИЗАЦИЯ ИНФРАСТРУКТУРЫ")
    print("="*70)

    # 1. Демонстрация конфиг-менеджера
    config = demo_config_manager()

    # 2. Демонстрация моделей
    organ = demo_organ_creation()
    region = demo_region_creation()
    continent = demo_continent_creation()
    world = demo_world_creation(organ, region, continent)

    # 3. Визуализация
    visualize_all(organ, region, continent, world)

    print("\n" + "="*70)
    print("[OK] ДЕМОНСТРАЦИЯ ЗАВЕРШЕНА")
    print("="*70)
    print("\nПроверьте файл: output/phase1_visualization.png")
    print("\nСледующий шаг: Запустите Phase 2 для генерации континента")
    print("="*70 + "\n")


if __name__ == '__main__':
    main()
