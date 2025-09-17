# main.py
from game import Game
from services.memory_service import MemoryService 
from logic.constants import META_TYPE, TYPE_LORE


def run_console_version():
    """
    Запускает игру в режиме консоли.
    Отвечает только за ВВОД/ВЫВОД в консоль.
    """

    # -- ЭКСПЕРИМЕНТ С ПАМЯТЬЮ --
    # 1. Получаем доступ к сервису памяти
    memory = MemoryService()
    
    # 2. Добавляем в базу несколько "фактов" о мире.
    # ID должны быть уникальными строками.
    memory.add_memory(
        text="Королевство страдает от паучьей чумы. Даже в самых неожиданных местах можно найти огромных пауков.",
        memory_id="fact_001",
        metadata={META_TYPE: TYPE_LORE}
    )

    memory.add_memory(
        text="Древние руины в этих землях часто использовались некромантами для создания скелетов-стражей.",
        memory_id="fact_002",
        metadata={META_TYPE: TYPE_LORE}
    )
    # -----------------------------

    # Создаем экземпляр игры
    game = Game()
    game.start_new_game(player_name="Авантюрист")
    
    # Отображаем стартовое состояние ОДИН РАЗ
    print("\n" + "="*20)
    print(game.player)
    print("\n" + "="*20)
    print(game.current_location)
    print("="*20)

    # ИГРОВОЙ ЦИКЛ
    while True:
        if game.player and game.player.is_dead():
            print("\nВаше приключение подошло к концу.")
            print("GAME OVER")
            break

        player_input = input("\n> ")
        
        command_parts = player_input.lower().strip().split()
        if not command_parts:
            continue

        command_verb = command_parts[0]
        
        # --- СИСТЕМНЫЕ КОМАНДЫ ---

        if command_verb in ["выход", "exit", "quit", "выйти"]:
            print("До новых встреч, авантюрист!")
            break
        
        if command_verb == "save":
            if len(command_parts) > 1:
                save_name = command_parts[1]
                game.save_to_file(save_name)
            else:
                print("ИСПОЛЬЗОВАНИЕ: save <имя_файла>")
            continue # Пропускаем остаток цикла, чтобы не отправлять 'save' как игровое действие

        if command_verb == "load":
            if len(command_parts) > 1:
                save_name = command_parts[1]
                loaded_game = Game.load_from_file(save_name)
                if loaded_game:
                    game = loaded_game # Заменяем текущий объект игры на загруженный
                    # Сразу показываем игроку, где он оказался, для погружения
                    print("\n" + "="*20 + " ЗАГРУЗКА ЗАВЕРШЕНА " + "="*20)
                    print(game.player)
                    print(game.current_location)
                    print("="*58)
            else:
                print("ИСПОЛЬЗОВАНИЕ: load <имя_файла>")
            continue

        # --- ИГРОВОЕ ДЕЙСТВИЕ ---
        result_text = game.process_player_command(player_input)
        print("\n" + result_text)
        
        # Обновляем отображение состояния персонажа
        print("\n" + "-"*20)
        print(game.player)
        print("-"*20)

if __name__ == "__main__":
    run_console_version()