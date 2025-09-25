import yaml

class TagRegistry:
    def __init__(self, filepath="data/tags_registry.yaml"):
        try:
            with open(filepath, 'r', encoding='utf-8') as file:
                self._data = yaml.safe_load(file)
            self._all_tags = self._flatten_tags()
            print("Реестр тегов успешно загружен.")
        except FileNotFoundError:
            print(f"ОШИБКА: Файл реестра тегов не найден по пути {filepath}")
            self._data = {}
            self._all_tags = set()

    def _flatten_tags(self) -> set:
        """Собирает все ID тегов из всех категорий в одно множество для быстрой проверки."""
        flat_set = set()
        for category_data in self._data.values():
            if 'tags' in category_data and isinstance(category_data['tags'], dict):
                flat_set.update(category_data['tags'].keys())
        return flat_set

    def validate_tag(self, tag_id: str) -> bool:
        """Проверяет, существует ли тег в реестре. Главная функция валидации."""
        return tag_id in self._all_tags

    def get_tag_info(self, tag_id: str) -> dict | None:
        """Возвращает полную информацию о теге (имя, описание)."""
        for category_data in self._data.values():
            if 'tags' in category_data and tag_id in category_data['tags']:
                return category_data['tags'][tag_id]
        return None