# 🔧 Финальные шаги миграции на Git Submodule

**Статус:** Лор уже запушен в приватный репозиторий `silgarron-lore` ✅

**Осталось:** Добавить его как submodule в основной проект

---

## ✅ Что уже сделано:

1. ✅ Создан приватный репозиторий `git@github.com:spayenwul/silgarron-lore.git`
2. ✅ Лор запушен (commit: `478b347 Initial lore commit`)
3. ✅ Создана документация:
   - `docs/GIT_SUBMODULE_SETUP.md` - полное руководство
   - `README.md` - обновлён с инструкциями

---

## 🚀 Финальные шаги (выполнить вручную)

### Проблема:
Директория `docs/lore` сейчас содержит отдельный git репозиторий, который не отслеживается в основном проекте. Нужно удалить эту директорию и добавить её как submodule.

### Почему вручную:
- Директория может быть занята IDE, файловым менеджером или антивирусом
- Критичная операция - лучше иметь полный контроль
- Можно закрыть все программы перед выполнением

---

## 📝 Команды для выполнения

### Шаг 1: Закрыть все программы

Закройте:
- VS Code / PyCharm / другие IDE
- File Explorer (если открыт в `E:\neuro_rpg\docs\lore`)
- Git GUI клиенты
- Любые программы, которые могут держать файлы

### Шаг 2: Открыть Git Bash в корне проекта

```bash
cd /e/neuro_rpg
pwd  # Должно показать: /e/neuro_rpg
```

### Шаг 3: Удалить существующую директорию docs/lore

**Вариант A: Через Git Bash (Linux-style)**
```bash
rm -rf docs/lore
```

**Вариант B: Через Windows CMD**
```cmd
rmdir /s /q docs\lore
```

**Вариант C: Вручную через File Explorer**
1. Открыть `E:\neuro_rpg\docs\`
2. Удалить папку `lore` (Shift + Delete для окончательного удаления)

### Шаг 4: Проверить, что директория удалена

```bash
ls docs/ | grep lore
# Не должно ничего показать
```

### Шаг 5: Добавить submodule

```bash
git submodule add git@github.com:spayenwul/silgarron-lore.git docs/lore
```

**Ожидаемый результат:**
```
Cloning into 'E:/neuro_rpg/docs/lore'...
remote: Enumerating objects: 23, done.
remote: Counting objects: 100% (23/23), done.
remote: Compressing objects: 100% (20/20), done.
remote: Total 23 (delta 0), reused 23 (delta 0), pack-reused 0
Receiving objects: 100% (23/23), 76.45 KiB | 1.74 MiB/s, done.
```

### Шаг 6: Проверить результат

```bash
# Проверить статус
git status

# Должны увидеть:
# Changes to be committed:
#   new file:   .gitmodules
#   new file:   docs/lore

# Проверить содержимое .gitmodules
cat .gitmodules

# Должно содержать:
# [submodule "docs/lore"]
#     path = docs/lore
#     url = git@github.com:spayenwul/silgarron-lore.git

# Проверить, что файлы лора на месте
ls docs/lore/

# Должны быть: Общее.md, Бестиарий.md, Боги/, Расы/
```

### Шаг 7: Закоммитить изменения

```bash
git add .gitmodules docs/lore

git commit -m "feat: Add silgarron-lore as Git Submodule

Added private lore repository as a submodule in docs/lore.

Submodule: git@github.com:spayenwul/silgarron-lore.git
Path: docs/lore
Commit: 478b347 Initial lore commit

Benefits:
- Separates public code from private lore content
- Independent version control for lore
- Easy access management via GitHub private repo
- Maintains single working directory structure

Setup for new developers:
  git clone --recurse-submodules <repo-url>

Or if already cloned:
  git submodule init
  git submodule update

Related: docs/GIT_SUBMODULE_SETUP.md

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

### Шаг 8: Запушить изменения

```bash
git push
```

---

## ✅ Финальная проверка

После выполнения всех шагов:

```bash
# Проверить submodule status
git submodule status
# Должно показать: +478b347... docs/lore (heads/main)

# Проверить, что лор доступен
cat docs/lore/Общее.md | head -5
# Должны увидеть начало файла с лором

# Проверить на GitHub
# Зайти на https://github.com/spayenwul/silgarron
# Должна быть папка docs/lore с серой иконкой и @ [commit hash]
```

---

## 🔄 Тестирование для новых разработчиков

Для проверки, что всё работает:

```bash
# В другой директории (например, /tmp/)
cd /tmp/

# Клонировать с submodules
git clone --recurse-submodules git@github.com:spayenwul/silgarron.git test-clone

cd test-clone

# Проверить, что лор склонирован
ls docs/lore/
# Должны быть: Общее.md, Бестиарий.md, и т.д.

# Проверить submodule
git submodule status
# Должен показать active submodule

# Если всё ОК - удалить тестовую копию
cd ..
rm -rf test-clone
```

---

## ⚠️ Troubleshooting

### Проблема: "fatal: destination path 'docs/lore' already exists"

**Решение:** Директория не была удалена. Повторить Шаг 3.

### Проблема: "Permission denied" при rm -rf

**Решение:**
1. Закрыть все программы, использующие файлы
2. Попробовать через Windows Explorer (Shift + Delete)
3. Перезагрузить компьютер и повторить

### Проблема: "Failed to clone 'git@github.com:spayenwul/silgarron-lore.git'"

**Решение:**
- Проверить SSH ключи: `ssh -T git@github.com`
- Убедиться, что у вас есть доступ к приватному репо
- Проверить, что репозиторий существует и приватный

### Проблема: Submodule добавлен, но файлов нет в docs/lore/

**Решение:**
```bash
git submodule update --init --recursive
```

---

## 📞 Помощь

Если что-то пошло не так:

1. **Не паникуйте** - у вас есть backup в `/tmp/lore-backup/`
2. **Проверьте статус:** `git status` и `git submodule status`
3. **Проверьте удалённые репозитории:**
   - Основной: `git remote -v`
   - Лор: `cd docs/lore && git remote -v`
4. **Обратитесь к полной документации:** `docs/GIT_SUBMODULE_SETUP.md`

---

## 🎯 После успешного выполнения

Вы получите:

✅ **Публичный репозиторий (silgarron):**
- Содержит весь код
- `docs/lore/` - это submodule (ссылка)
- Безопасно открыт для всех

✅ **Приватный репозиторий (silgarron-lore):**
- Содержит все секреты мира
- Доступен только вам и команде
- Независимый version control

✅ **Удобство работы:**
- Структура папок не изменилась
- Лор обновляется независимо
- Автоматическая синхронизация через git

---

**Удачи! 🚀**

**Время выполнения:** ~5-10 минут
**Сложность:** Средняя
**Критичность:** Высокая (но обратимая)
