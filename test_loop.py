# test_loop.py (v2 - Исправлена ошибка синтаксиса)

# --- 1. Инициализация всего, что у нас уже есть ---
from models.character import Character
from services.intent_service import IntentService
from combat.physical_simulator import PhysicalSimulator

def main_game_loop():
    """
    Минимальный игровой цикл, который связывает существующие компоненты.
    """
    print("--- Запуск минимально играбельного цикла ---")

    # --- 2. Создаем "тестовую сцену" вручную ---
    player = Character(name="Герой")
    # У гоблина пока нет сложной BodySystem, используем старые добрые HP
    goblin = Character(name="Гоблин")
    goblin.hp = 15 
    
    # Инициализируем наши готовые сервисы
    intent_service = IntentService()
    # ВАЖНО: Мы используем ЗАГЛУШКУ симулятора, которую вы уже написали!
    physics_simulator = PhysicalSimulator() 
    
    print(f"\nНачало боя! {player.name} против {goblin.name} ({goblin.hp} HP)")
    print("Введите ваше действие (например, 'бью мечом по шее гоблина'):")

    # --- 3. Основной цикл игры ---
    while not goblin.is_dead():
        command = input("> ")
        if command in ["выход", "exit"]:
            break

        # --- 4. Соединяем куски вместе! ---
        
        # ШАГ А: Распознаем детали действия с помощью уже готового сервиса
        action_details = intent_service.extract_action_details(command)
        print(f"[DEBUG] Распознано: {action_details}")

        # ШАГ Б: Если это атака, используем ЗАГЛУШКУ симулятора
        if action_details.get("action") in ["strike", "slash", "stab", "shoot"]:
            
            # Мы передаем в симулятор то, что распознали
            # (оружие пока воображаемое, но это не важно)
            simulation_result = physics_simulator.simulate_attack(
                attacker=player,
                target=goblin,
                weapon=None, # Пока не важно
                action_details=action_details
            )

            # ШАГ В: Применяем РЕЗУЛЬТАТ ЗАГЛУШКИ к цели
            damage = int(simulation_result.damage_points)
            goblin.take_damage(damage)

            # ШАГ Г: Показываем результат игроку!
            print("--- Результат хода ---")
            
            # ИСПРАВЛЕНО: Используем тройные кавычки для многострочных f-строк
            print(f"""{simulation_result.narrative}""") # Описание от заглушки
            print(f"""(Гоблин получает {damage} урона. У него осталось {goblin.hp} HP)""")
        
        else:
            print("Вы решаете не атаковать.")

        if goblin.is_dead():
            print("\n🎉 ПОБЕДА! Гоблин повержен.")
            break

if __name__ == "__main__":
    main_game_loop()