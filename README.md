# Silgarron RPG

Physics-based text RPG где AI — это физический движок.

## 🚀 Быстрый Старт

```bash
# 1. Клонировать репозиторий
git clone <repo-url>

# 2. Установить зависимости
pip install -r requirements.txt

# 3. Настроить .env
cp .env.example .env
# Добавить свой GEMINI_API_KEY

# 4. Запустить игру
python main.py

# 5. Или запустить API сервер
python api/main.py
```

## 📚 Документация

**Начни здесь:**
- [MASTER_PLAN.md](docs/MASTER_PLAN.md) - Общий план проекта
- [CURRENT_SPRINT.md](docs/sprints/CURRENT_SPRINT.md) - Текущие задачи

**Для разработчиков:**
- [Technical_Design_Document.md](docs/Technical_Design_Document.md) - Архитектура
- [ARCHITECTURE_DECISION.md](docs/ARCHITECTURE_DECISION.md) - Ключевые решения
- [DOCUMENTATION_GUIDE.md](docs/DOCUMENTATION_GUIDE.md) - Как вести документацию

## 🏗️ Текущий Статус

| Компонент | Статус | Готовность |
|-----------|--------|------------|
| Базовая архитектура | ✅ Реализовано | 75% |
| Command Routing | 🟡 Sprint 1 | 60% |
| Боевая система | 🟡 Skeleton | 35% |
| Генерация мира | 🟡 Частично | 40% |
| Physical Simulation | 🔴 Ожидает команду | 15% |

**Текущий спринт:** Sprint 1 - Director Refactoring (14-21 окт)

## 🎯 Архитектура

```
Player Command → IntentService (классификация)
    ↓
Director (выбор стратегии)
    ↓
┌───────────┬──────────────┬─────────────────┐
│CODE_ONLY  │ SIMPLE_LLM   │ COMPLEX_TOOL_CALL│
│(instant)  │ (1 API call) │ (2 API calls)    │
└───────────┴──────────────┴─────────────────┘
```

## 🤝 Contributing

1. Изучи [DOCUMENTATION_GUIDE.md](docs/DOCUMENTATION_GUIDE.md)
2. Выбери задачу из [CURRENT_SPRINT.md](docs/sprints/CURRENT_SPRINT.md)
3. Создай feature branch
4. Пиши тесты
5. Обнови документацию
6. Создай PR

## 📄 License

Этот проект содержит компоненты с разными лицензиями.

### Код

Весь исходный код в этом репозитории распространяется под лицензией **MIT License**. Полный текст лицензии можно найти в файле [LICENSE_CODE.md](LICENSE_CODE.md).

### Документация и Лор

Вся документация, включая лор, тексты и другие творческие материалы, распространяется под лицензией **Creative Commons Attribution-NoDerivatives 4.0 International (CC BY-ND 4.0)**. Это означает, что вы можете свободно копировать и делиться этими материалами с указанием авторства, но не можете изменять их или создавать на их основе производные работы.

Полный текст лицензии можно найти в файле [LICENSE_LORE.md](LICENSE_LORE.md).

## 🔗 Ссылки

- Документация: `docs/`
- API: `http://localhost:8000/docs` (после запуска)
