# main.py
from game import Game
from services.memory_service import MemoryService 

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
        memory_id="fact_001"
    )
    memory.add_memory(
        text="Древние руины в этих землях часто использовались некромантами для создания скелетов-стражей.",
        memory_id="fact_002"
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
        # 1. Проверяем, не умер ли игрок
        if game.player.is_dead():
            print("\nВаше приключение подошло к концу.")
            print("GAME OVER")
            break

        # 2. Спрашиваем игрока о его действии
        player_input = input("\n> ")

        if player_input.lower() in ["выход", "exit", "quit"]:
            print("До новых встреч, авантюрист!")
            break
        
        # 3. Передаем команду в игровой движок
        result_text = game.process_player_command(player_input)

        # 4. Печатаем нарративный результат
        print("\n" + result_text)

        # После каждого хода перепечатываем блок персонажа, чтобы видеть изменения HP, инвентаря и т.д.
        print("\n" + "-"*20)
        print(game.player)
        print("-"*20)

if __name__ == "__main__":
    run_console_version()