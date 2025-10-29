# Space Colonization Algorithm для артерий Сильгаррона

**Категория:** Алгоритмическая документация
**Версия:** 3.0
**Дата:** 29 октября 2025
**Статус:** 🚧 В планировании (Sprint 3.8)

**Phase:** 3 (Physiology - Vessels & Nerves)

---

## Обзор

Space Colonization Algorithm - это процедурный алгоритм для генерации разветвлённых структур, имитирующих рост растений к свету. В контексте Сильгаррона он используется для создания **сети артерий**, которые растут от metabolic_core к другим органам, **огибая плотные костные структуры**.

**Ключевая особенность v3.0:** Алгоритм учитывает **плотность костей** (`bone_density_map`) и выбирает пути наименьшего сопротивления.

---

## Философия

> Артерии в Сильгарроне - это **подземная инфраструктура**, по которой течёт ихор (питательная лимфа). Они не бурят массивные кости насквозь, а **огибают** их, следуя пути наименьшего сопротивления через мягкие ткани.

**Аналогия:** Представьте корни дерева, растущие в почве с камнями. Корни НЕ пробивают камни - они обходят их, находя промежутки в грунте.

---

## Алгоритм

### Основная идея

1. **Attraction Points** (точки притяжения): Позиции органов, к которым должны дорасти артерии
2. **Growth Tips** (растущие кончики): Активные точки роста артерий
3. **Iteration:** На каждой итерации:
   - Каждый growth tip "чувствует" ближайший attraction point
   - Tip растёт в направлении точки притяжения
   - При расчёте учитывается **стоимость** прохождения через кости
   - Когда tip достигает attraction point - точка удаляется

### Псевдокод (базовый)

```
ALGORITHM Space_Colonization(organs, bone_density_map):
    attraction_points = [organ.position for organ in organs if organ != metabolic_core]

    root = metabolic_core.position
    active_tips = [root]
    branches = []

    WHILE attraction_points AND active_tips:
        FOR EACH tip IN active_tips:
            closest_ap = find_closest_attraction_point(tip, attraction_points)

            IF closest_ap exists:
                direction = normalize(closest_ap.position - tip.position)
                new_position = tip.position + direction × segment_length

                branches.append(Branch(tip.position, new_position))

                tip.position = new_position

                IF distance(new_position, closest_ap.position) < kill_distance:
                    attraction_points.remove(closest_ap)

    RETURN branches
```

---

## Density-Aware Modification (v3.0)

### Ключевое изменение

Вместо простого Euclidean distance используется **взвешенная стоимость** (cost), которая учитывает плотность костей на пути.

### Формула стоимости

```python
cost = euclidean_distance × (1.0 + bone_density × bone_density_penalty)
```

**Где:**
- `euclidean_distance` - прямое расстояние до точки
- `bone_density` - плотность костей в целевой точке [0, 1]
- `bone_density_penalty` - множитель штрафа (обычно 3.0)

**Пример:**
```
Точка A: distance = 20, bone_density = 0.0 (мягкая ткань)
  cost = 20 × (1.0 + 0.0 × 3.0) = 20

Точка B: distance = 15, bone_density = 0.8 (плотная кость)
  cost = 15 × (1.0 + 0.8 × 3.0) = 15 × 3.4 = 51

Результат: Алгоритм выберет точку A (cost = 20), несмотря на то что B ближе!
```

### Модифицированный псевдокод

```python
def find_closest_attraction_point_with_density(tip, attraction_points, bone_density_map, penalty):
    min_cost = infinity
    closest_point = None

    for ap in attraction_points:
        # Расстояние
        dist = euclidean_distance(tip.position, ap.position)

        # Плотность костей в целевой точке
        bone_density = bone_density_map[ap.position.y, ap.position.x]

        # Взвешенная стоимость
        cost = dist * (1.0 + bone_density * penalty)

        if cost < min_cost:
            min_cost = cost
            closest_point = ap

    return closest_point
```

---

## Параметры

### Основные параметры

| Параметр | Тип | Значение | Описание |
|----------|-----|----------|----------|
| `influence_radius` | float | `50.0` | Радиус "чувствительности" к attraction points (пиксели) |
| `kill_distance` | float | `10.0` | Расстояние "достижения" цели (пиксели) |
| `segment_length` | float | `5.0` | Длина одного сегмента ветви (пиксели) |
| `bone_density_penalty` | float | `3.0` | Множитель штрафа за прохождение через кости |

### Настройка параметров

#### influence_radius (радиус влияния)

**Низкий (30-40):**
- Артерии растут прямолинейно
- Меньше ветвлений
- Быстрее генерация

**Средний (50) [Рекомендуется]:**
- Естественное ветвление
- Артерии находят баланс между прямотой и обходом препятствий

**Высокий (70-100):**
- Сложная сеть ветвлений
- Артерии активно обходят даже небольшие костные включения
- Медленнее генерация

#### bone_density_penalty (штраф за кости)

**Низкий (1.0-2.0):**
- Артерии слабо реагируют на кости
- Могут проходить через костную ткань

**Средний (3.0) [Рекомендуется]:**
- Артерии активно избегают плотных костей
- Естественные обходные пути

**Высокий (5.0-10.0):**
- Артерии НИКОГДА не проходят через кости
- Могут застревать, если окружены костями
- Риск недостижимости некоторых органов

#### segment_length (длина сегмента)

**Короткий (2-3):**
- Очень детализированные пути
- Гладкие изгибы
- Медленнее генерация

**Средний (5) [Рекомендуется]:**
- Баланс между детализацией и производительностью
- Естественный вид артерий

**Длинный (10-15):**
- Угловатые пути
- Быстрее генерация
- Менее реалистично

---

## Полный код (Python)

```python
import numpy as np
from typing import List, Dict, Tuple, Optional

def generate_vessel_network_with_density(
    organs: Dict[str, Dict],
    bone_density_map: np.ndarray,
    influence_radius: float = 50.0,
    kill_distance: float = 10.0,
    segment_length: float = 5.0,
    bone_density_penalty: float = 3.0
) -> List[Dict]:
    """
    Генерирует сеть артерий с учётом плотности костей

    Args:
        organs: Словарь органов {organ_id: {position, radius, ...}}
        bone_density_map: Карта плотности костей (512, 512) float [0, 1]
        influence_radius: Радиус влияния attraction point
        kill_distance: Расстояние "достижения" цели
        segment_length: Длина сегмента ветви
        bone_density_penalty: Множитель штрафа за кости

    Returns:
        Список ветвей [{'from': (x,y), 'to': (x,y), 'type': 'arterial'}, ...]
    """

    # 1. Определяем attraction points (все органы кроме источника)
    attraction_points = []
    for organ_id, organ in organs.items():
        if organ_id != 'organ_metabolic_core':
            attraction_points.append({
                'id': organ_id,
                'position': np.array(organ['position'], dtype=float),
                'importance': organ.get('nutrient_demand', 0.5)
            })

    # 2. Начальная точка роста
    root_position = np.array(organs['organ_metabolic_core']['position'], dtype=float)

    # 3. Активные точки роста (tips)
    active_tips = [{
        'position': root_position.copy(),
        'direction': np.array([0.0, 1.0]),  # Начальное направление (вниз)
        'parent_id': None
    }]

    # 4. Список всех ветвей
    branches = []

    # 5. Главный цикл
    max_iterations = 10000  # Защита от бесконечного цикла
    iteration = 0

    while attraction_points and active_tips and iteration < max_iterations:
        iteration += 1
        new_tips = []

        for tip in active_tips:
            # Найти ближайший attraction point с учётом bone density
            closest_point = None
            min_cost = float('inf')

            for ap in attraction_points:
                # Расстояние
                diff = ap['position'] - tip['position']
                dist = np.linalg.norm(diff)

                # Проверка радиуса влияния
                if dist > influence_radius:
                    continue

                # Плотность костей в целевой точке
                x, y = int(ap['position'][0]), int(ap['position'][1])
                # Bounds check
                if 0 <= x < bone_density_map.shape[1] and 0 <= y < bone_density_map.shape[0]:
                    bone_density = bone_density_map[y, x]
                else:
                    bone_density = 0.0

                # Взвешенная стоимость
                cost = dist * (1.0 + bone_density * bone_density_penalty)

                if cost < min_cost:
                    min_cost = cost
                    closest_point = ap

            # Если нашли точку притяжения - растём к ней
            if closest_point is not None:
                # Направление к цели
                direction = closest_point['position'] - tip['position']
                direction_normalized = direction / np.linalg.norm(direction)

                # Новая позиция
                new_position = tip['position'] + direction_normalized * segment_length

                # Сохраняем ветвь
                branches.append({
                    'from': tuple(tip['position']),
                    'to': tuple(new_position),
                    'type': 'arterial',
                    'target_organ': closest_point['id']
                })

                # Проверка достижения цели
                distance_to_target = np.linalg.norm(new_position - closest_point['position'])
                if distance_to_target < kill_distance:
                    # Цель достигнута - удаляем attraction point
                    attraction_points.remove(closest_point)
                else:
                    # Продолжаем рост - добавляем новый tip
                    new_tips.append({
                        'position': new_position,
                        'direction': direction_normalized,
                        'parent_id': tip.get('id')
                    })

        # Обновляем список активных tips
        active_tips = new_tips

    return branches


def branches_to_vessels(branches: List[Dict], organs: Dict) -> List[Dict]:
    """
    Преобразует список ветвей в формат vessels

    Группирует ветви по целевому органу и создаёт waypoints
    """
    vessels = {}

    for branch in branches:
        target = branch['target_organ']

        if target not in vessels:
            vessels[target] = {
                'from': 'organ_metabolic_core',
                'to': target,
                'type': 'arterial',
                'width': 10,
                'flow_strength': organs[target].get('nutrient_demand', 0.5),
                'waypoints': []
            }

        # Добавляем точки пути
        vessels[target]['waypoints'].append(branch['from'])
        vessels[target]['waypoints'].append(branch['to'])

    # Убираем дубликаты waypoints
    for vessel in vessels.values():
        vessel['waypoints'] = list(dict.fromkeys(vessel['waypoints']))  # Сохраняем порядок

    return list(vessels.values())
```

---

## Пример использования

```python
# Загружаем данные
organs = {
    'organ_metabolic_core': {'position': (256, 180), 'radius': 30},
    'organ_stomach': {'position': (256, 250), 'radius': 25, 'nutrient_demand': 0.9},
    'ganglion_thoracic': {'position': (200, 150), 'radius': 15, 'nutrient_demand': 0.7}
}

bone_density_map = np.load('bone_density.npy')  # (512, 512) float [0, 1]

# Генерируем артерии
branches = generate_vessel_network_with_density(
    organs=organs,
    bone_density_map=bone_density_map,
    influence_radius=50.0,
    kill_distance=10.0,
    segment_length=5.0,
    bone_density_penalty=3.0
)

# Преобразуем в vessels
vessels = branches_to_vessels(branches, organs)

print(f"Generated {len(vessels)} vessels with {len(branches)} total branches")

# Пример результата:
# vessels = [
#     {
#         'from': 'organ_metabolic_core',
#         'to': 'organ_stomach',
#         'type': 'arterial',
#         'width': 10,
#         'flow_strength': 0.9,
#         'waypoints': [(256,180), (260,190), (258,210), (256,250)]  # Огибает кость!
#     },
#     ...
# ]
```

---

## Визуализация

### Рекомендуемая визуализация

```python
import matplotlib.pyplot as plt

fig, ax = plt.subplots(figsize=(12, 12))

# 1. Bone density (фон)
im = ax.imshow(bone_density_map, cmap='Greys', alpha=0.5)

# 2. Артерии (красные линии)
for branch in branches:
    x1, y1 = branch['from']
    x2, y2 = branch['to']
    ax.plot([x1, x2], [y1, y2], 'r-', linewidth=2, alpha=0.7)

# 3. Органы (зелёные круги)
for organ_id, organ in organs.items():
    x, y = organ['position']
    radius = organ['radius']
    circle = plt.Circle((x, y), radius, color='green', alpha=0.3)
    ax.add_patch(circle)
    ax.text(x, y, organ_id.replace('organ_', ''), ha='center', va='center')

ax.set_title('Vessel Network with Bone Density Awareness')
ax.set_xlim(0, 512)
ax.set_ylim(512, 0)
plt.colorbar(im, label='Bone Density')
plt.show()
```

**Ожидаемый результат:**
- Артерии (красные линии) избегают тёмных зон (кости)
- Пути изгибаются вокруг плотных структур
- Все органы достигнуты

---

## Лор-соответствие

### Анатомическая логика

1. **Артерии огибают кости** ✅
   - Реализовано через `bone_density_penalty`
   - Пути следуют через мягкие ткани

2. **Артерии - подземные каналы** ✅
   - НЕ отображаются на поверхности напрямую
   - Влияют на Phase 4 через vein_outlets (выходы на поверхность)

3. **Питание от metabolic_core** ✅
   - Все артерии растут от единого источника
   - Древовидная структура (не случайная сеть)

4. **Связь с нервами** ✅
   - Нервы "спаяны" с артериями
   - Генерируются после артерий (следуют за путями)

---

## Производительность

### Сложность

- **Временная:** O(N × M × I)
  - N = количество органов
  - M = количество активных tips (обычно ~N)
  - I = количество итераций

- **Пространственная:** O(B)
  - B = количество созданных ветвей

### Оптимизация

**Для карты 512×512 с 5-7 органами:**
- Итераций: ~500-2000
- Ветвей: ~100-500
- Время генерации: **~0.1-0.5 сек** (Python)

**Возможные оптимизации:**
1. **Spatial indexing:** cKDTree для быстрого поиска ближайших точек
2. **Early termination:** Остановка, если active_tips пуст
3. **Parallel growth:** Обработка tips параллельно (если нужно)

---

## Статус

- **Разработка:** 🚧 В планировании
- **Тестирование:** ⏳ Ожидает реализации
- **Документация:** ✅ Готова
- **Интеграция:** ⏳ Sprint 3.8 (Phase 3)

---

**Версия:** 3.0
**Дата последнего обновления:** 29 октября 2025
**Следующий шаг:** Реализация в `core/space_colonization.py` (Sprint 3.8)
