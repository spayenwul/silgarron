"""
CODE_ONLY Strategy - мгновенные действия без вызовов AI.

Обрабатывает простые команды типа "посмотреть инвентарь", "статистика",
которые требуют только доступа к данным игрока без сложной логики.

Преимущества:
- Скорость: <10ms
- Стоимость: бесплатно
- Надёжность: не зависит от API
"""

from typing import Dict, Any
from logic.strategies.base_strategy import BaseStrategy


class CodeOnlyStrategy(BaseStrategy):
    """
    Стратегия для обработки простых команд без AI.

    Поддерживаемые интенты:
    - SELF_ACTION_CODE_ONLY: посмотреть на себя (инвентарь, статы, раны)
    - META_ACTION_CODE_ONLY: мета-действия (сохранить, загрузить, настройки)
    """

    def execute(self, game_instance: Any, command: str, details: Dict[str, Any]) -> str:
        """
        Выполнить простое действие без вызова AI.

        Args:
            game_instance: Экземпляр Game
            command: Оригинальная команда (используется для fallback)
            details: Dict с полем 'intent' для определения типа действия

        Returns:
            Строка с результатом для игрока
        """
        # Извлекаем intent из details (будет добавлен Director'ом)
        intent = details.get("intent", "UNKNOWN")

        # Обрабатываем различные CODE_ONLY интенты
        if intent == "SELF_ACTION_CODE_ONLY":
            return self._handle_self_action(game_instance, command)
        elif intent == "META_ACTION_CODE_ONLY":
            return self._handle_meta_action(game_instance, command)
        else:
            # Fallback если интент неизвестен
            return self._generic_code_only_response(game_instance, command)

    def _handle_self_action(self, game_instance: Any, command: str) -> str:
        """
        Обработка действий связанных с осмотром себя.

        Примеры: инвентарь, статистика, раны, здоровье
        """
        command_lower = command.lower()

        # Проверяем ключевые слова в команде
        if any(word in command_lower for word in ["инвентарь", "сумк", "вещ", "предмет"]):
            return self._show_inventory(game_instance)

        elif any(word in command_lower for word in ["статистик", "характеристик", "стат", "параметр"]):
            return self._show_stats(game_instance)

        elif any(word in command_lower for word in ["ран", "здоров", "повреж", "состоян"]):
            return self._show_health(game_instance)

        elif any(word in command_lower for word in ["оде", "экипиро", "надет", "броня", "оруж"]):
            return self._show_equipment(game_instance)

        else:
            # Если ключевое слово не распознано, показываем общую информацию
            return str(game_instance.player)

    def _handle_meta_action(self, game_instance: Any, command: str) -> str:
        """
        Обработка мета-действий (не игровых команд).

        Примеры: сохранить игру, загрузить, настройки
        """
        command_lower = command.lower()

        if any(word in command_lower for word in ["сохран", "save"]):
            return "💾 Для сохранения игры используйте команду в меню или напишите 'сохранить игру'.\n(Функция автосохранения будет добавлена в следующей версии)"

        elif any(word in command_lower for word in ["загруз", "load"]):
            return "📂 Для загрузки игры используйте меню при запуске программы."

        elif any(word in command_lower for word in ["настройк", "settings", "меню", "menu"]):
            return "⚙️ Меню настроек:\n- Сохранить игру\n- Загрузить игру\n- Выход из игры\n(Полноценное меню будет добавлено в следующих версиях)"

        elif any(word in command_lower for word in ["карт", "map", "где я"]):
            return self._show_location_info(game_instance)

        elif any(word in command_lower for word in ["журнал", "quest", "задан", "миссии"]):
            return "📖 Журнал заданий:\n(Система квестов будет добавлена в следующих версиях)\n\nТекущая локация: " + (game_instance.current_location.name if game_instance.current_location else "Неизвестно")

        else:
            return "❓ Неизвестная мета-команда. Доступные команды: инвентарь, статистика, карта, журнал, настройки."

    def _show_inventory(self, game_instance: Any) -> str:
        """Показать содержимое инвентаря."""
        if not game_instance.player:
            return "⚠️ Персонаж не инициализирован."

        inventory_str = str(game_instance.player.inventory)

        if "пуст" in inventory_str.lower() or "ничего нет" in inventory_str.lower():
            return f"🎒 Инвентарь пуст.\n\nВы находитесь в: {game_instance.current_location.name if game_instance.current_location else 'Неизвестно'}"

        return f"🎒 {inventory_str}"

    def _show_stats(self, game_instance: Any) -> str:
        """Показать характеристики персонажа."""
        if not game_instance.player:
            return "⚠️ Персонаж не инициализирован."

        player = game_instance.player

        stats_lines = [
            f"📊 === Характеристики: {player.name} ===",
            "",
            "🔹 Основные статы:",
        ]

        # Legacy stats
        for stat_name, stat_value in player.stats.items():
            stats_lines.append(f"  • {stat_name.capitalize()}: {stat_value}")

        stats_lines.append("")
        stats_lines.append("🔹 Физические параметры:")
        stats_lines.append(f"  • Сила: {player.physical_stats['strength_kg']:.0f} кг")
        stats_lines.append(f"  • Выносливость: {player.physical_stats['endurance_sec']:.0f} сек")
        stats_lines.append(f"  • Ловкость: {player.physical_stats['agility']:.1f}x")

        return "\n".join(stats_lines)

    def _show_health(self, game_instance: Any) -> str:
        """Показать состояние здоровья персонажа."""
        if not game_instance.player:
            return "⚠️ Персонаж не инициализирован."

        player = game_instance.player

        health_lines = [
            f"❤️ === Здоровье: {player.name} ===",
            "",
            f"HP: {player.hp}/{player.max_hp}",
        ]

        # Check if body system is available
        try:
            if hasattr(player, 'body') and player.body:
                blood_pct = (player.body.blood_volume / player.body.max_blood_volume) * 100
                health_lines.append(f"Кровь: {blood_pct:.0f}% ({player.body.blood_volume:.0f}/{player.body.max_blood_volume:.0f} мл)")
                health_lines.append(f"Сознание: {player.body.consciousness*100:.0f}%")

                if player.body.is_unconscious():
                    health_lines.append("")
                    health_lines.append("⚠️ ВЫ БЕЗ СОЗНАНИЯ!")

                if player.body.wounds:
                    health_lines.append("")
                    health_lines.append("🩹 Ранения:")
                    for wound in player.body.wounds:
                        health_lines.append(f"  • {wound.body_part.value}: {wound.severity.value} ({wound.bleeding_rate:.1f} мл/ход)")

                if player.body.status_effects:
                    health_lines.append("")
                    health_lines.append("💊 Эффекты:")
                    for effect in player.body.status_effects:
                        health_lines.append(f"  • {effect.type.value} ({effect.duration} ходов)")
        except:
            # Fallback if body system is not fully available
            pass

        if player.hp == player.max_hp:
            health_lines.append("")
            health_lines.append("✅ Вы в отличном состоянии!")
        elif player.hp < player.max_hp * 0.3:
            health_lines.append("")
            health_lines.append("⚠️ Вы тяжело ранены!")

        return "\n".join(health_lines)

    def _show_equipment(self, game_instance: Any) -> str:
        """Показать экипированные предметы."""
        if not game_instance.player:
            return "⚠️ Персонаж не инициализирован."

        # TODO: В будущем здесь будет полноценная система экипировки
        # Пока показываем инвентарь
        return "⚔️ Экипировка:\n(Система экипировки будет добавлена в следующих версиях)\n\n" + self._show_inventory(game_instance)

    def _show_location_info(self, game_instance: Any) -> str:
        """Показать информацию о текущей локации."""
        if not game_instance.current_location:
            return "⚠️ Локация не определена."

        location = game_instance.current_location

        info_lines = [
            f"🗺️ === {location.name} ===",
            "",
            location.description,
        ]

        if hasattr(location, 'tags') and location.tags:
            info_lines.append("")
            info_lines.append(f"Теги: {', '.join(location.tags)}")

        return "\n".join(info_lines)

    def _generic_code_only_response(self, game_instance: Any, command: str) -> str:
        """
        Универсальный fallback для неизвестных CODE_ONLY команд.

        Пытается интерпретировать команду по ключевым словам.
        """
        command_lower = command.lower()

        # Попробуем угадать намерение по ключевым словам
        if any(word in command_lower for word in ["я", "мен", "мо", "сво"]):
            return self._handle_self_action(game_instance, command)
        elif any(word in command_lower for word in ["где", "локац", "место", "вокруг"]):
            return self._show_location_info(game_instance)
        else:
            # Если ничего не подошло, показываем общую информацию
            return f"ℹ️ Быстрая информация:\n\n{str(game_instance.player)}\n\nТекущая локация: {game_instance.current_location.name if game_instance.current_location else 'Неизвестно'}"
