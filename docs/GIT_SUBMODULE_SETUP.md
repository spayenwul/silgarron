# 🔐 Настройка Git Submodules для приватного лора

**Дата:** 23 октября 2025
**Цель:** Отделить публичный код от приватного контента (лор мира)
**Подход:** Git Submodules

---

## 📋 Архитектура

### Два репозитория:

1. **silgarron-game** (Публичный) ← Текущий репозиторий
   - Весь игровой код
   - Механики, сервисы, AI
   - Публичные ассеты
   - Документация (кроме лора)

2. **silgarron-lore** (Приватный) ← Новый репозиторий
   - Содержимое `docs/lore/`
   - Все секреты мира
   - Доступ только для команды

### Связь через Submodule:

```
silgarron-game/
├── docs/
│   ├── lore/  ← Git Submodule → silgarron-lore (приватный)
│   ├── architecture_decision.md
│   └── ...
├── core/
└── ...
```

---

## 🚀 Пошаговая инструкция по настройке

### Шаг 1: Создать приватный репозиторий silgarron-lore на GitHub

**Выполняется вручную через веб-интерфейс GitHub:**

1. Перейти на https://github.com/new
2. **Repository name:** `silgarron-lore`
3. **Description:** "Private lore content for Silgarron RPG"
4. **Visibility:** ✅ **Private** (очень важно!)
5. **Initialize:**
   - ❌ НЕ добавляйте README
   - ❌ НЕ добавляйте .gitignore
   - ❌ НЕ добавляйте лицензию
6. Нажать **"Create repository"**
7. Скопировать URL репозитория (будет вида: `https://github.com/spayenwul/silgarron-lore.git`)

---

### Шаг 2: Подготовить контент лора для нового репозитория

**Выполняется из корня проекта:**

```bash
# Создать временную директорию для нового репозитория
cd ..
mkdir silgarron-lore-temp
cd silgarron-lore-temp

# Скопировать всё содержимое docs/lore
cp -r ../neuro_rpg/docs/lore/* .

# Проверить содержимое
ls -la
```

**Ожидаемая структура:**
```
silgarron-lore-temp/
├── Бестиарий.md
├── Общее.md
├── Прошлое мира.md
├── Боги/
│   ├── Первый Крик.md
│   ├── Гость в Теле.md
│   └── ...
└── Расы/
    ├── Расы.md
    ├── Иловые ткачи.md
    └── ...
```

---

### Шаг 3: Инициализировать Git и запушить в приватный репозиторий

```bash
# Инициализировать git
git init

# Создать .gitattributes для правильной работы с кириллицей
cat > .gitattributes <<EOF
# Ensure all text files use LF line endings
* text=auto eol=lf

# Markdown files
*.md text

# Explicitly declare text files you want to always be normalized and converted
# to native line endings on checkout.
*.md text diff=markdown
EOF

# Создать README для репозитория лора
cat > README.md <<EOF
# Silgarron RPG - Lore Repository

**🔐 This is a PRIVATE repository**

Contains all lore, world-building details, and narrative secrets for Silgarron RPG.

## Structure

- \`Общее.md\` - Main world description (geography, physics, biology)
- \`Бестиарий.md\` - Bestiary
- \`Прошлое мира.md\` - World history
- \`Боги/\` - Gods and deities descriptions
- \`Расы/\` - Races and factions

## Access

This repository is private and accessible only to core team members.

## Usage

This repository is linked as a Git Submodule to the main game repository:
\`\`\`
silgarron-game/docs/lore/ → silgarron-lore (submodule)
\`\`\`

Do not share any content from this repository publicly.

---

**Project:** Silgarron RPG
**Status:** Active Development
**Confidentiality:** Private
EOF

# Добавить всё в git
git add .

# Первый коммит
git commit -m "Initial commit: Silgarron lore content

Contains:
- Main world description (Общее.md)
- Bestiary (Бестиарий.md)
- World history (Прошлое мира.md)
- Gods descriptions (Боги/)
- Races and factions (Расы/)

Total size: ~452KB
Files: 20+ markdown files

This content is private and confidential."

# Подключить remote (ЗАМЕНИТЕ URL НА ВАШ!)
git remote add origin https://github.com/spayenwul/silgarron-lore.git

# Переименовать ветку в main (если нужно)
git branch -M main

# Запушить
git push -u origin main
```

---

### Шаг 4: Удалить docs/lore из основного репозитория

**ВАЖНО:** Перед выполнением убедитесь, что Step 3 выполнен успешно и лор запушен в приватный репозиторий!

```bash
# Вернуться в основной репозиторий
cd ../neuro_rpg

# Удалить папку lore из git (но оставить на диске временно)
git rm -r docs/lore

# Закоммитить удаление
git commit -m "refactor: Remove lore directory (will be added as submodule)

Lore content moved to private repository silgarron-lore.
This is preparation for adding it as a Git Submodule.

Next step: git submodule add"

# НЕ ПУШИМ ПОКА! Сначала добавим submodule
```

---

### Шаг 5: Добавить silgarron-lore как submodule

```bash
# Добавить приватный репозиторий как submodule в docs/lore
git submodule add https://github.com/spayenwul/silgarron-lore.git docs/lore

# Git автоматически:
# 1. Склонирует silgarron-lore в docs/lore
# 2. Создаст файл .gitmodules
# 3. Добавит запись о submodule в git

# Проверить статус
git status

# Вы должны увидеть:
# new file:   .gitmodules
# new file:   docs/lore (это submodule commit reference)

# Закоммитить изменения
git commit -m "feat: Add silgarron-lore as Git Submodule

Added private lore repository as a submodule in docs/lore.

Submodule URL: https://github.com/spayenwul/silgarron-lore.git
Target path: docs/lore

Benefits:
- Separates public code from private content
- Allows independent version control for lore
- Maintains single working directory structure
- Easy to update lore independently

Setup for new developers:
  git clone --recurse-submodules https://github.com/spayenwul/silgarron.git

Or if already cloned:
  git submodule init
  git submodule update"

# Теперь можно пушить
git push
```

---

### Шаг 6: Обновить .gitignore (опционально)

Если вы хотите, чтобы локальные изменения в лоре не отслеживались в основном репо:

```bash
# Добавить в .gitignore (если нужно)
echo "# Lore submodule local changes" >> .gitignore
echo "docs/lore/*" >> .gitignore
echo "!docs/lore/.gitkeep" >> .gitignore

git add .gitignore
git commit -m "chore: Update .gitignore for lore submodule"
git push
```

**НО:** Обычно это НЕ нужно. Submodule работает как указатель на конкретный commit.

---

## 📚 Работа с Submodules для команды

### Для новых разработчиков (первое клонирование):

```bash
# Вариант 1: Клонировать с submodules сразу
git clone --recurse-submodules https://github.com/spayenwul/silgarron.git

# Вариант 2: Если уже склонировали без --recurse-submodules
git clone https://github.com/spayenwul/silgarron.git
cd silgarron
git submodule init
git submodule update
```

### Для существующих разработчиков (после добавления submodule):

```bash
# Получить обновления из основного репозитория
git pull

# Инициализировать и обновить submodules
git submodule init
git submodule update
```

### Обновление лора (для авторов контента):

```bash
# Перейти в директорию лора
cd docs/lore

# Это отдельный git репозиторий!
git status
git branch

# Внести изменения в лор...
# Например, отредактировать Общее.md

# Закоммитить в приватный репозиторий лора
git add Общее.md
git commit -m "lore: Update world breathing mechanics"
git push origin main

# Вернуться в основной репозиторий
cd ../..

# Основной репозиторий увидит, что submodule изменился
git status
# On branch main
# Changes not staged for commit:
#   modified:   docs/lore (new commits)

# Обновить ссылку на новый commit лора
git add docs/lore
git commit -m "chore: Update lore submodule to latest"
git push
```

### Получение обновлений лора (для других разработчиков):

```bash
# Получить обновления основного репозитория
git pull

# Обновить submodules до указанных коммитов
git submodule update --remote

# Или вручную:
cd docs/lore
git pull origin main
cd ../..
```

---

## 🔍 Проверка настройки

После всех шагов выполните:

```bash
# Проверить статус submodules
git submodule status

# Должно показать что-то вроде:
# 4a3b5c7d... docs/lore (heads/main)

# Проверить содержимое .gitmodules
cat .gitmodules

# Должно содержать:
# [submodule "docs/lore"]
#     path = docs/lore
#     url = https://github.com/spayenwul/silgarron-lore.git

# Проверить, что docs/lore существует и содержит файлы
ls -la docs/lore/
# Должны быть: Общее.md, Бестиарий.md, Боги/, Расы/ и т.д.

# Проверить, что это отдельный git репозиторий
cd docs/lore
git remote -v
# origin  https://github.com/spayenwul/silgarron-lore.git (fetch)
# origin  https://github.com/spayenwul/silgarron-lore.git (push)
```

---

## ⚠️ Важные замечания

### 1. Права доступа

Убедитесь, что `silgarron-lore` действительно **Private**:
- GitHub → Settings → Danger Zone → Change repository visibility → Private

### 2. Доступ для команды

Чтобы дать доступ доверенным разработчикам:
- GitHub → silgarron-lore → Settings → Collaborators → Add people

### 3. Authentication

При работе с приватным submodule потребуется аутентификация:

**Вариант A: HTTPS с токеном (рекомендуется)**
```bash
# Создать Personal Access Token на GitHub:
# Settings → Developer settings → Personal access tokens → Generate new token
# Права: repo (full control)

# При первом git push/pull Git попросит ввести:
# Username: ваш_username
# Password: ваш_token (НЕ пароль!)
```

**Вариант B: SSH (более удобно)**
```bash
# Изменить URL submodule на SSH
cd docs/lore
git remote set-url origin git@github.com:spayenwul/silgarron-lore.git

# Обновить .gitmodules в основном репо
cd ../..
# Вручную отредактировать .gitmodules:
# url = git@github.com:spayenwul/silgarron-lore.git

git add .gitmodules
git commit -m "chore: Switch lore submodule to SSH"
git push
```

### 4. .gitmodules tracking

Файл `.gitmodules` **должен** быть в основном репозитории. Он не секретный, он только указывает:
- Что есть submodule
- Где он находится (путь)
- Откуда его клонировать (URL)

---

## 🛠️ Типичные команды (шпаргалка)

```bash
# Клонировать проект с submodules
git clone --recurse-submodules <url>

# Добавить submodule
git submodule add <url> <path>

# Инициализировать submodules (после обычного clone)
git submodule init
git submodule update

# Обновить submodules до последних коммитов
git submodule update --remote

# Обновить submodule на конкретный коммит
cd docs/lore
git checkout <commit-hash>
cd ../..
git add docs/lore
git commit -m "chore: Pin lore to specific version"

# Удалить submodule (если понадобится)
git submodule deinit docs/lore
git rm docs/lore
rm -rf .git/modules/docs/lore
```

---

## 📖 Ссылки на документацию

- [Git Submodules Official Documentation](https://git-scm.com/book/en/v2/Git-Tools-Submodules)
- [GitHub: Working with submodules](https://github.blog/2016-02-01-working-with-submodules/)
- [Atlassian Git Submodules Tutorial](https://www.atlassian.com/git/tutorials/git-submodule)

---

## ✅ Контрольный список

Перед завершением убедитесь:

- [ ] Приватный репозиторий `silgarron-lore` создан на GitHub
- [ ] Лор запушен в `silgarron-lore` (Step 3)
- [ ] `docs/lore` удалён из основного репо (Step 4)
- [ ] Submodule добавлен: `git submodule add` (Step 5)
- [ ] `.gitmodules` существует и закоммичен
- [ ] `git submodule status` показывает активный submodule
- [ ] `docs/lore/` существует и содержит файлы
- [ ] Изменения запушены: `git push`
- [ ] Проверено клонирование на чистой машине (опционально)

---

## 🎯 Результат

После выполнения всех шагов:

✅ **Публичный репозиторий (silgarron-game):**
- Содержит весь код
- Не содержит секретов лора
- Может быть безопасно открыт

✅ **Приватный репозиторий (silgarron-lore):**
- Содержит все секреты мира
- Доступен только команде
- Независимый version control

✅ **Работа с проектом:**
- Структура папок не изменилась (`docs/lore/` на месте)
- Лор обновляется независимо
- Автоматическая синхронизация через git

---

**Статус:** Готово к выполнению
**Автор:** Claude (AI Assistant)
**Дата:** 23 октября 2025
