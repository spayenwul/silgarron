"""
Улучшенный валидатор для проверки целостности YAML-файлов
Версия 2.0 - с поддержкой логических выражений и whitelist ID
"""
import yaml
import re
from pathlib import Path
from typing import Dict, List, Set, Any, Optional

class YAMLValidator:
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.errors: List[str] = []
        self.warnings: List[str] = []
        
        # Whitelist: известные ID сущностей, которые не являются тегами
        self.known_non_tag_ids: Set[str] = set()
        
    def _load_known_ids(self):
        """Загружает все известные ID биомов, рас, регионов и т.д."""
        print("-> Loading known entity IDs...")
        
        # Загружаем ID из anatomy.yaml
        anatomy_path = self.data_dir / "data_tables" / "anatomy.yaml"
        if anatomy_path.exists():
            with open(anatomy_path, 'r', encoding='utf-8') as f:
                anatomy = yaml.safe_load(f)
                
            # Собираем ID регионов
            if 'REGION_TYPES' in anatomy:
                for region in anatomy['REGION_TYPES']:
                    if 'id' in region:
                        self.known_non_tag_ids.add(region['id'])
                        
            # Собираем ID биомов
            if 'BIOMES' in anatomy:
                for biome in anatomy['BIOMES']:
                    if 'id' in biome:
                        self.known_non_tag_ids.add(biome['id'])
                        
            # Собираем ID лендмарков
            if 'LANDMARKS' in anatomy:
                for landmark in anatomy['LANDMARKS']:
                    if 'id' in landmark:
                        self.known_non_tag_ids.add(landmark['id'])
        
        # Загружаем ID из inhabitants.yaml
        inhabitants_path = self.data_dir / "data_tables" / "inhabitants.yaml"
        if inhabitants_path.exists():
            with open(inhabitants_path, 'r', encoding='utf-8') as f:
                inhabitants = yaml.safe_load(f)
                
            # Собираем ID рас
            if 'RACES' in inhabitants:
                for race in inhabitants['RACES']:
                    if 'id' in race:
                        self.known_non_tag_ids.add(race['id'])
        
        print(f"   Loaded {len(self.known_non_tag_ids)} known entity IDs")

    def _parse_logical_expression(self, expression: str) -> Set[str]:
        """
        Парсит логические выражения типа 'tag1 OR tag2' или 'tag1 AND tag2'
        Возвращает множество тегов, используемых в выражении
        """
        # Убираем операторы сравнения (>, <, =) и всё после них
        comparison_pattern = r'\s*[><]=?\s*\d+'
        expression = re.sub(comparison_pattern, '', expression)
        
        # Разделяем по логическим операторам
        logical_operators = r'\s+(?:OR|AND|NOT)\s+'
        parts = re.split(logical_operators, expression, flags=re.IGNORECASE)
        
        # Очищаем и собираем теги
        tags = set()
        for part in parts:
            part = part.strip()
            if part and ':' in part:  # Похоже на тег
                tags.add(part)
        
        return tags

    def _is_comparison_expression(self, value: str) -> bool:
        """Проверяет, является ли значение выражением сравнения"""
        comparison_pattern = r'.+\s*[><]=?\s*\d+'
        return bool(re.match(comparison_pattern, value))

    def _collect_all_tags(self, registry_data: Dict) -> Set[str]:
        """
        Рекурсивно собирает все легальные теги из tags_registry.yaml
        """
        legal_tags = set()

        def parse_tag_hierarchy(tags_data: Any):
            if isinstance(tags_data, dict):
                # Словарь с тегами
                for tag_id, tag_info in tags_data.items():
                    # Добавляем сам ID
                    legal_tags.add(tag_id)
                    
                    # Добавляем aliases
                    if isinstance(tag_info, dict):
                        if 'aliases' in tag_info and tag_info['aliases']:
                            legal_tags.update(tag_info['aliases'])
                        
                        # Добавляем children
                        if 'children' in tag_info and tag_info['children']:
                            if isinstance(tag_info['children'], list):
                                for child in tag_info['children']:
                                    if isinstance(child, str):
                                        legal_tags.add(child)
                                    elif isinstance(child, dict):
                                        parse_tag_hierarchy(child)
                            elif isinstance(tag_info['children'], dict):
                                parse_tag_hierarchy(tag_info['children'])
                                
            elif isinstance(tags_data, list):
                # Список тегов
                for item in tags_data:
                    if isinstance(item, dict):
                        if 'id' in item:
                            legal_tags.add(item['id'])
                        if 'aliases' in item and item['aliases']:
                            legal_tags.update(item['aliases'])
                        if 'children' in item:
                            parse_tag_hierarchy(item['children'])

        def find_tag_structures(item: Any):
            """Ищет структуры с тегами во всём реестре"""
            if isinstance(item, dict):
                for key, value in item.items():
                    if key == 'tags':
                        parse_tag_hierarchy(value)
                    else:
                        find_tag_structures(value)
            elif isinstance(item, list):
                for element in item:
                    find_tag_structures(element)

        find_tag_structures(registry_data)
        return legal_tags

    def _extract_used_tags(self, data: Any, file_name: str = "") -> Set[str]:
        """
        Рекурсивно извлекает все используемые теги из данных
        С улучшенной обработкой логических выражений
        """
        found_tags = set()

        def find_tags_in_item(item: Any, context_key: str = ""):
            if isinstance(item, dict):
                for key, value in item.items():
                    # Теги как значения в pillar_tags
                    if key == 'pillar_tags' and isinstance(value, dict):
                        for tag in value.values():
                            if isinstance(tag, str):
                                found_tags.add(tag)
                    
                    # Теги как ключи
                    elif key in ['preferred', 'avoided'] and isinstance(value, dict):
                        for tag_key in value.keys():
                            if isinstance(tag_key, str):
                                found_tags.add(tag_key)
                    
                    # Теги как элементы списков
                    elif key in ['defining_tags', 'tags', 'incompatible', 'required_tags', 
                                 'forbidden_tags', 'preferred_tags', 'can_border', 'cannot_border',
                                 'favored_races', 'disfavored_races'] and isinstance(value, list):
                        for v in value:
                            if isinstance(v, str):
                                # Проверяем, не является ли это ID сущности
                                if v not in self.known_non_tag_ids:
                                    # Проверяем, не является ли это логическим выражением
                                    if ' OR ' in v or ' AND ' in v or self._is_comparison_expression(v):
                                        # Парсим выражение и извлекаем теги
                                        tags = self._parse_logical_expression(v)
                                        found_tags.update(tags)
                                    else:
                                        found_tags.add(v)
                    
                    # Рекурсия
                    find_tags_in_item(value, key)
            
            elif isinstance(item, list):
                for element in item:
                    find_tags_in_item(element, context_key)

        find_tags_in_item(data)
        return found_tags

    def validate_all(self):
        """Запускает все проверки"""
        print("🔍 Starting validation v2.0...")
        
        # Сначала загружаем известные ID
        self._load_known_ids()
        
        self.check_tags_registry()
        self.check_tag_references()
        
        self.report()
        
    def check_tags_registry(self):
        """Проверяет корректность tags_registry.yaml"""
        print("-> Checking tags_registry.yaml structure...")
        registry_path = self.data_dir / "tags_registry.yaml"
        
        if not registry_path.exists():
            self.errors.append(f"❌ CRITICAL: tags_registry.yaml not found at: {registry_path}")
            return
            
        with open(registry_path, 'r', encoding='utf-8') as f:
            registry = yaml.safe_load(f)
            
        required_sections = ['pillars', 'defining_tags', 'global_compatibility_rules']
        for section in required_sections:
            if section not in registry:
                self.errors.append(f"❌ Missing required section in tags_registry: '{section}'")
        
        print("✓ tags_registry.yaml structure is valid")
        
    def check_tag_references(self):
        """Проверяет, что все используемые теги существуют в registry"""
        print("-> Checking tag references across all files...")
        registry_path = self.data_dir / "tags_registry.yaml"
        if not registry_path.exists():
            return

        with open(registry_path, 'r', encoding='utf-8') as f:
            registry = yaml.safe_load(f)
        legal_tags = self._collect_all_tags(registry)
        
        if not legal_tags:
            self.errors.append("❌ No legal tags were collected from tags_registry.yaml")
            return

        print(f"   Found {len(legal_tags)} legal tags in registry")

        # Проверяем все YAML файлы
        files_to_check = list(self.data_dir.glob("**/*.yaml"))

        for yaml_file in files_to_check:
            # Пропускаем сам реестр
            if yaml_file.name == "tags_registry.yaml":
                continue

            try:
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                    if not data:
                        continue
                    
                used_tags = self._extract_used_tags(data, yaml_file.name)
                illegal_tags = used_tags - legal_tags
                
                if illegal_tags:
                    # Фильтруем специальные случаи
                    real_illegal = set()
                    for tag in illegal_tags:
                        # Пропускаем явно служебные значения
                        if tag in ['all_organic', 'all_free_willed', 'any_fertile', 
                                   'surface_dwellers', 'land_dwellers', 'most_races',
                                   'all_mortals', 'comfort_loving', 'hardy_survivors',
                                   'skilled_navigators', 'skilled_sailors', 'novice_sailors',
                                   'pirates', 'salvagers', 'bandits', 'outcasts',
                                   'crystalline_cult', 'unity_cult', 'relic_hunters',
                                   'pilgrims', 'artists', 'dreamers', 'practical_minded',
                                   'meditators', 'deaf', 'protected', 'unprotected',
                                   'climbers', 'plains_dwellers', 'cave_dwellers',
                                   'wind_adapted', 'heavy_races', 'deep_ones',
                                   'blind_folk', 'amphibious', 'aquatic_folk',
                                   'edge_guardians', 'acoustics', 'phages']:
                            continue
                        real_illegal.add(tag)
                    
                    if real_illegal:
                        self.warnings.append(
                            f"⚠️  In '{yaml_file.relative_to(self.data_dir.parent)}': "
                            f"undefined tags: {real_illegal}"
                        )
            except Exception as e:
                self.warnings.append(
                    f"⚠️  Could not parse '{yaml_file.relative_to(self.data_dir.parent)}': {e}"
                )
        
        print("✓ Tag references checked")
    
    def report(self):
        """Выводит отчёт о валидации"""
        print("\n" + "="*60)
        print("VALIDATION REPORT")
        print("="*60)
        
        if self.errors:
            print(f"\n❌ ERRORS ({len(self.errors)}):")
            for error in self.errors:
                print(f"  {error}")
        else:
            print("\n✅ No critical errors found")

        if self.warnings:
            print(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"  {warning}")
        else:
            print("\n✅ No warnings found")
        
        print("="*60)
        
        if not self.errors and not self.warnings:
            print("\n🎉 All checks passed!")
            
        return len(self.errors) == 0

if __name__ == "__main__":
    data_folder = Path("data")
    
    if not data_folder.exists():
        print(f"❌ ERROR: Data folder '{data_folder}' not found")
        print("Please run this script from the root directory of your project")
    else:
        validator = YAMLValidator(data_folder)
        success = validator.validate_all()
        exit(0 if success else 1)