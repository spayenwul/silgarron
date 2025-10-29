# Shape Mask Guide - Центрирование континентов

## Обзор

**Shape Mask (Маска формы)** - это механизм для создания центрированных континентов с гарантированным океаном по краям карты.

### Проблема, которую решает

Стандартная генерация континентов с Perlin Noise создаёт случайные формы, которые могут:
- Выходить за границы карты
- Не иметь океана по краям
- Быть смещены от центра

### Решение

**Shape Mask** - это градиентная маска, которая умножается на базовый Perlin Noise:
- **Центр карты**: значение = 1.0 (полная интенсивность шума)
- **Края карты**: значение = 0.0 (шум подавлен)
- **Переход**: плавный градиент

**Результат:** Континент центрирован, океан гарантирован по краям.

---

## Математика

### Формула эллиптической маски

```python
# 1. Сетка координат
y, x = np.ogrid[:height, :width]

# 2. Нормализованное расстояние от центра (формула эллипса)
distance = sqrt(((x - cx)^2 / rx^2) + ((y - cy)^2 / ry^2))

# 3. Инвертируем (центр = 1.0, края = 0.0)
shape_mask = 1.0 - distance

# 4. Clamp в [0, 1]
shape_mask = clip(shape_mask, 0, 1)
```

### Применение к генерации

```python
# Базовый heightmap (Perlin Noise)
base_noise = generate_perlin_map(...)  # [0, 1]

# Умножение на маску формы
final_heightmap = base_noise * shape_mask

# Применение порога океана
continent_mask = (final_heightmap > sea_level)
```

---

## Конфигурация

### Файл: `config/world_generation_v2.yaml`

```yaml
continent:
  sea_level: 0.36  # Используется БЕЗ shape_mask

  # Маска формы (центрирование континента)
  shape_mask:
    enabled: false  # true = включить центрирование
    type: "ellipse"  # "ellipse" | "radial"
    radius_x: 0.35   # Радиус по X (0-1, доля ширины карты)
    radius_y: 0.45   # Радиус по Y (0-1, доля высоты карты)
    sea_level_override: 0.20  # Используется С shape_mask
```

### Параметры

| Параметр | Тип | Значение | Описание |
|----------|-----|----------|----------|
| `enabled` | bool | `false` | Включить/выключить shape mask |
| `type` | str | `"ellipse"` | Тип маски: `"ellipse"` (вытянутая) или `"radial"` (круглая) |
| `radius_x` | float | `0.35` | Радиус по оси X (0.0-1.0, доля от ширины карты) |
| `radius_y` | float | `0.45` | Радиус по оси Y (0.0-1.0, доля от высоты карты) |
| `sea_level_override` | float | `0.20` | Порог океана при включенной маске (обычно ниже, чем стандартный) |

---

## Почему `sea_level_override` ниже?

### Проблема

Умножение `base_noise * shape_mask` **уменьшает значения**:

```python
# БЕЗ маски:
base_noise[256, 256] = 0.7  # Центр карты
base_noise[0, 0] = 0.6      # Угол карты

# С маской:
final[256, 256] = 0.7 * 1.0 = 0.7  # Центр (маска = 1.0)
final[0, 0] = 0.6 * 0.0 = 0.0      # Угол (маска = 0.0)
```

### Решение

Используем **более низкий sea_level** при включенной маске:

| Режим | sea_level | Результат |
|-------|-----------|-----------|
| Без маски | `0.36` | 70-80% суши |
| С маской | `0.20` | 50-70% суши (после умножения на маску) |

---

## Использование

### Вариант 1: Через Python API

```python
from core.world_generator_v2 import WorldGeneratorV2

gen = WorldGeneratorV2()

# Включаем shape mask
gen.config['continent']['shape_mask']['enabled'] = True
gen.config['continent']['shape_mask']['type'] = 'ellipse'
gen.config['continent']['shape_mask']['radius_x'] = 0.35
gen.config['continent']['shape_mask']['radius_y'] = 0.45

# Генерируем континент
continent = gen._generate_continent("my_seed")

# Проверяем результат
print(f"Land: {continent.mask.sum() / (512*512) * 100:.1f}%")

# Проверяем океан на краях
edge_pixels = np.concatenate([
    continent.mask[0, :],   # Top
    continent.mask[-1, :],  # Bottom
    continent.mask[:, 0],   # Left
    continent.mask[:, -1]   # Right
])
ocean_pct = (1 - edge_pixels.sum() / len(edge_pixels)) * 100
print(f"Ocean at edges: {ocean_pct:.1f}%")  # Должно быть ~100%
```

### Вариант 2: Через конфиг-менеджер

```python
from services.world_config_v2 import WorldGenerationConfigV2

# Загружаем конфиг
config = WorldGenerationConfigV2.from_yaml('config/world_generation_v2.yaml')

# Изменяем параметры
config_dict = config.to_dict()
config_dict['continent']['shape_mask']['enabled'] = True
config_dict['continent']['shape_mask']['radius_x'] = 0.40  # Шире

# Сохраняем (или используем напрямую)
# config.save_to_yaml('config/world_generation_v2.yaml')
```

### Вариант 3: Прямое редактирование YAML

Откройте `config/world_generation_v2.yaml` и измените:

```yaml
shape_mask:
  enabled: true  # Было false
```

---

## Визуализация

### Основная визуализация (6 панелей)

```bash
python scripts/visualize_shape_mask.py --seed my_continent
```

**Панели:**
1. **Base Perlin Noise** - Исходный шум без маски
2. **Shape Mask** - Градиентная маска (центр=1, края=0)
3. **Combined** - Результат умножения (Noise * Mask)
4. **Without Shape Mask** - Континент без центрирования
5. **With Shape Mask** - Континент с центрированием
6. **Comparison** - Наложение обоих вариантов

**Результат:** `output/shape_mask_effect_my_continent.png` (~3-4 MB)

### Сравнение типов масок

```bash
python scripts/visualize_shape_mask.py --compare-types
```

**Показывает:**
- 3 варианта эллиптических масок (разные радиусы)
- 3 варианта круглых масок (radial)

**Результат:** `output/shape_mask_types_comparison.png`

---

## Настройка параметров

### 1. Размер континента (`radius_x`, `radius_y`)

**Меньшие радиусы (0.25-0.30):**
- Компактный континент
- Много океана по краям
- Изолированная форма

```yaml
radius_x: 0.25
radius_y: 0.35
```

**Средние радиусы (0.35-0.40) [Рекомендуется]:**
- Сбалансированный континент
- Умеренный океан
- Естественная форма

```yaml
radius_x: 0.35
radius_y: 0.45
```

**Большие радиусы (0.45-0.50):**
- Огромный континент
- Мало океана
- Может выходить за края

```yaml
radius_x: 0.45
radius_y: 0.55
```

### 2. Форма континента (`type`)

**Ellipse (вытянутый):**
- Удлинённая форма (как реальные континенты)
- Разные радиусы по X и Y
- Лучше для анатомической генерации (позвоночник)

```yaml
type: "ellipse"
radius_x: 0.35
radius_y: 0.45  # Выше, чем radius_x
```

**Radial (круглый):**
- Симметричная форма
- Одинаковый радиус во всех направлениях
- Проще, но менее органично

```yaml
type: "radial"
radius_x: 0.35  # radius_y игнорируется
```

### 3. Порог океана (`sea_level_override`)

**Низкий порог (0.15-0.20) [Рекомендуется]:**
- Больше суши (50-70%)
- Крупный континент
- Хорошая детализация

```yaml
sea_level_override: 0.20
```

**Средний порог (0.25-0.30):**
- Умеренно суши (30-50%)
- Средний континент
- Баланс

```yaml
sea_level_override: 0.28
```

**Высокий порог (0.35-0.40):**
- Мало суши (10-30%)
- Мелкий континент / архипелаг
- Может быть слишком мало суши

```yaml
sea_level_override: 0.35
```

---

## Рецепты для разных типов миров

### "Изолированный Континент" (остров в океане)

```yaml
shape_mask:
  enabled: true
  type: "ellipse"
  radius_x: 0.30
  radius_y: 0.40
  sea_level_override: 0.22
```

**Результат:** Компактный центральный континент, широкий океан.

### "Большой Континент" (по умолчанию)

```yaml
shape_mask:
  enabled: true
  type: "ellipse"
  radius_x: 0.35
  radius_y: 0.45
  sea_level_override: 0.20
```

**Результат:** Крупный вытянутый континент, умеренный океан.

### "Супер-Континент" (почти вся карта)

```yaml
shape_mask:
  enabled: true
  type: "ellipse"
  radius_x: 0.45
  radius_y: 0.55
  sea_level_override: 0.15
```

**Результат:** Огромный континент, минимум океана.

### "Круглый Мир" (симметричный)

```yaml
shape_mask:
  enabled: true
  type: "radial"
  radius_x: 0.38
  sea_level_override: 0.20
```

**Результат:** Круглый центральный континент.

---

## Технические детали

### Реализация в `WorldGeneratorV2`

```python
def _create_shape_mask(self, width: int, height: int,
                      mask_type: str = "ellipse",
                      radius_x: float = 0.35,
                      radius_y: float = 0.45) -> np.ndarray:
    """
    Создание градиентной маски для центрирования континента

    Returns:
        2D массив [0, 1] где 1.0 = центр, 0.0 = края
    """
    y, x = np.ogrid[:height, :width]
    center_x, center_y = width / 2, height / 2

    if mask_type == "ellipse":
        radius_x_px = width * radius_x
        radius_y_px = height * radius_y

        distance = np.sqrt(
            ((x - center_x)**2 / radius_x_px**2) +
            ((y - center_y)**2 / radius_y_px**2)
        )
    else:  # radial
        radius_px = min(width, height) * radius_x
        distance = np.sqrt((x - center_x)**2 + (y - center_y)**2) / radius_px

    shape_mask = 1.0 - distance
    return np.clip(shape_mask, 0, 1)
```

### Интеграция в `_generate_continent()`

```python
# 1. Генерация Perlin Noise
heightmap = generate_perlin_map(...)

# 2. Применение shape mask (если включено)
if shape_mask_enabled:
    shape_mask = self._create_shape_mask(...)
    heightmap = heightmap * shape_mask  # Умножение!

# 3. Выбор sea_level
if shape_mask_enabled and 'sea_level_override' in config:
    sea_level = config['shape_mask']['sea_level_override']
else:
    sea_level = config['sea_level']

# 4. Threshold + smoothing
continent_mask = (heightmap > sea_level)
```

---

## Тесты

Все 37 существующих тестов продолжают проходить с `shape_mask.enabled = false`.

### Тест с включенной маской

```python
def test_shape_mask_centers_continent():
    gen = WorldGeneratorV2()
    gen.config['continent']['shape_mask']['enabled'] = True
    gen.config['continent']['shape_mask']['sea_level_override'] = 0.20

    continent = gen._generate_continent('test_centered')

    # Проверяем океан на краях
    edge_pixels = np.concatenate([
        continent.mask[0, :],
        continent.mask[-1, :],
        continent.mask[:, 0],
        continent.mask[:, -1]
    ])

    ocean_edge_pct = (1 - edge_pixels.sum() / len(edge_pixels)) * 100

    assert ocean_edge_pct > 95, f"Edges should be ocean: {ocean_edge_pct}%"
```

---

## FAQ

### Q: Почему `enabled: false` по умолчанию?

**A:** Для обратной совместимости. Существующие тесты и генерация продолжают работать как раньше. Включайте вручную, когда нужно центрирование.

### Q: Можно ли комбинировать с параметрами Perlin Noise?

**A:** Да! Shape mask применяется **после** генерации Perlin Noise. Все параметры `scale`, `octaves`, `persistence` продолжают работать.

### Q: Что если континент всё равно слишком маленький?

**A:** Уменьшите `sea_level_override` (например, с 0.20 до 0.15).

### Q: Можно ли сделать континент не в центре?

**A:** Сейчас нет (маска всегда центрирована). Можно расширить `_create_shape_mask()` для добавления параметров `center_x`, `center_y`.

---

## Итоги

**Что реализовано:**
- [x] Метод `_create_shape_mask()` для создания эллиптических/круглых градиентов
- [x] Интеграция в `_generate_continent()` с умножением `heightmap * shape_mask`
- [x] Конфигурация в `world_generation_v2.yaml` с параметрами
- [x] Автоматический выбор `sea_level_override` при включенной маске
- [x] Визуализация эффекта (6 панелей + сравнение типов)
- [x] Backward compatibility (все 37 тестов проходят)

**Ключевые файлы:**
- `core/world_generator_v2.py`: Методы `_create_shape_mask()`, обновлённый `_generate_continent()`
- `config/world_generation_v2.yaml`: Секция `shape_mask`
- `scripts/visualize_shape_mask.py`: Визуализация эффекта
- `docs/sprint_3.6_implementation/SHAPE_MASK_GUIDE.md`: Этот файл

---

**Дата:** 2025-10-25
**Статус:** Shape Mask Implementation Complete
**Тестов:** 37/37 passing
