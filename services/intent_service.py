import json
import re
import chromadb
import pymorphy3
from pathlib import Path
from typing import Dict, Any, List, Optional
import services.llm_service as llm

INTENTS_FILE = Path(__file__).parent.parent / "data/intents.json"
COLLECTION_NAME = "intent_recognition_collection"

class IntentService:
    def __init__(self):
        print("[INIT] Initializing Intent Recognition Service...")
        client = chromadb.Client()
        # 1. Получаем список ВСЕХ существующих коллекций
        existing_collections = [c.name for c in client.list_collections()]

        # 2. Проверяем, есть ли НАША коллекция в этом списке
        if COLLECTION_NAME in existing_collections:
            # 3. И удаляем ее, только если она была найдена
            print(f"[INFO] Clearing old intents collection ('{COLLECTION_NAME}')...")
            client.delete_collection(name=COLLECTION_NAME)

        # 4. Теперь мы можем безопасно создавать новую, чистую коллекцию
        self.collection = client.get_or_create_collection(name=COLLECTION_NAME)
        self._load_intents_into_chroma()

        # Морфологический анализатор для русского языка (Phase 2)
        print("[INIT] Initializing morphological analyzer...")
        self.morph = pymorphy3.MorphAnalyzer()

    def _load_intents_into_chroma(self):
        """Загружает все примеры из JSON в векторную базу."""
        with open(INTENTS_FILE, "r", encoding="utf-8") as f:
            intents_data = json.load(f)
        
        # Готовим данные для ChromaDB
        documents = [item['text'] for item in intents_data]
        metadatas = [item['metadata'] for item in intents_data]
        ids = [f"intent_{i}" for i in range(len(documents))]

        self.collection.add(documents=documents, metadatas=metadatas, ids=ids)
        print(f"[OK] Intents vector database loaded ({len(documents)} examples).")

    def recognize_intent(self, player_command: str) -> str:
        """
        Находит наиболее близкое намерение к команде игрока.
        """
        results = self.collection.query(
            query_texts=[player_command],
            n_results=1 # Нам нужен только один, самый похожий результат
        )

        if not results['metadatas'][0]:
            return "UNKNOWN" # На случай, если ничего не найдено

        # Извлекаем намерение из метаданных самого похожего примера
        recognized_intent = results['metadatas'][0][0]['intent']
        print(f"[INTENT] Recognized intent: '{player_command}' -> {recognized_intent}")
        return recognized_intent

    # ============================================
    # PHASE 2: ACTION DETAIL EXTRACTION
    # ============================================

    # Словари для маппинга (с нормализованными формами)
    ACTION_KEYWORDS = {
        "strike": ["бить", "ударять", "ударить", "удар"],
        "slash": ["рубить", "резать", "полоснуть", "рубануть"],
        "stab": ["колоть", "протыкать", "пронзать", "укол"],
        "shoot": ["стрелять", "выпускать", "пускать", "выстрел"],
        "dodge": ["увернуться", "уклониться", "уклоняться", "отскочить"],
        "block": ["блокировать", "парировать", "отбить", "прикрыться"],
        "cast": ["использовать", "колдовать", "применять", "кастовать"]
    }

    WEAPON_KEYWORDS = {
        "sword": ["меч", "клинок"],
        "dagger": ["кинжал", "нож"],
        "axe": ["топор", "секира"],
        "bow": ["лук", "стрела", "луковой"],  # Добавлена форма родительного падежа
        "staff": ["посох", "палка"],
        "fists": ["кулак", "рука"]
    }

    BODY_PART_KEYWORDS = {
        "head": ["голова", "череп", "лицо", "башка"],
        "neck": ["шея", "горло", "глотка"],
        "torso": ["грудь", "живот", "торс", "корпус", "тело"],
        "arm": ["рука", "плечо", "локоть", "запястье"],
        "leg": ["нога", "колено", "бедро", "голень"],
        "heart": ["сердце"]
    }

    TARGET_KEYWORDS = {
        "goblin": ["гоблин"],
        "orc": ["орк"],
        "skeleton": ["скелет", "костяк"],
        "spider": ["паук", "паучище"],
        "wolf": ["волк", "псина"]
    }

    MODIFIER_KEYWORDS = {
        "from_side": ["сбоку", "фланг"],
        "from_above": ["сверху", "разворот"],
        "with_force": ["сила", "мощно", "сильно"],
        "carefully": ["осторожно", "аккуратно", "точно"],
        "quickly": ["быстро", "молниеносно", "резко"]
    }

    def _normalize_command(self, command: str) -> List[str]:
        """
        Лемматизация команды для улучшения распознавания.

        "бью мечом" → ["бить", "меч"]
        """
        words = command.lower().split()
        normalized = []

        for word in words:
            # Очистка от знаков препинания
            word_clean = re.sub(r'[^\w]', '', word)
            if not word_clean:
                continue

            # Лемматизация
            parsed = self.morph.parse(word_clean)[0]
            lemma = parsed.normal_form
            normalized.append(lemma)

        return normalized

    def _extract_with_rules(self, normalized_words: List[str],
                           original_command: str) -> Dict[str, Any]:
        """
        Извлечение параметров через словари и нормализованные слова.
        """
        details = {}

        # 1. Действие (action)
        for action_type, keywords in self.ACTION_KEYWORDS.items():
            if any(kw in normalized_words for kw in keywords):
                details["action"] = action_type
                break

        # 2. Оружие (weapon)
        for weapon_type, keywords in self.WEAPON_KEYWORDS.items():
            if any(kw in normalized_words for kw in keywords):
                details["weapon"] = weapon_type
                break

        # 3. Часть тела (body_part)
        for body_part, keywords in self.BODY_PART_KEYWORDS.items():
            if any(kw in normalized_words for kw in keywords):
                details["body_part"] = body_part
                break

        # 4. Цель (target)
        for target_type, keywords in self.TARGET_KEYWORDS.items():
            if any(kw in normalized_words for kw in keywords):
                details["target"] = target_type
                break

        # 5. Модификаторы (modifier)
        for modifier_type, keywords in self.MODIFIER_KEYWORDS.items():
            if any(kw in normalized_words for kw in keywords):
                details["modifier"] = modifier_type
                break

        return details

    def _resolve_conflicts(self, details: Dict, normalized_words: List[str]) -> Dict:
        """
        Разрешение конфликтов ключевых слов.

        Пример: "атакую руку рукой" → weapon="fists", body_part="arm"
        """
        # Конфликт: "рука" как оружие VS часть тела
        if "рука" in normalized_words or "кулак" in normalized_words:
            # Приоритет 1: Если есть явное оружие, "рука" = body_part
            if details.get("weapon") and details["weapon"] != "fists":
                if details.get("body_part") == "arm":
                    pass  # Оставляем как есть
            # Приоритет 2: Если нет другого оружия, "рука" = weapon (fists)
            elif not details.get("weapon"):
                details["weapon"] = "fists"
                # Убираем из body_part если там тоже "рука"
                if details.get("body_part") == "arm":
                    details.pop("body_part")

        return details

    def _calculate_confidence(self, details: Dict) -> float:
        """
        Оценка уверенности на основе найденных параметров.

        Веса:
        - action: 0.4 (самое важное)
        - weapon: 0.2
        - body_part: 0.25
        - target: 0.15
        """
        score = 0.0
        weights = {
            "action": 0.4,
            "weapon": 0.2,
            "body_part": 0.25,
            "target": 0.15
        }

        for key, weight in weights.items():
            if details.get(key):
                score += weight

        return min(score, 1.0)

    def _clean_llm_json(self, text: str) -> str:
        """
        Очистка ответа LLM от markdown и лишних символов.

        ```json {...} ``` → {...}
        """
        # Убираем markdown блоки
        text = re.sub(r'```json\s*', '', text)
        text = re.sub(r'```\s*', '', text)

        # Извлекаем JSON между { и }
        match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', text)
        if match:
            return match.group(0)

        return text.strip()

    def _validate_llm_response(self, details: Dict) -> Optional[Dict]:
        """
        Валидация ответа LLM: проверяем, что значения входят в разрешенные списки.
        """
        if not details or details.get("confidence", 0) == 0:
            return None

        valid_values = {
            "action": list(self.ACTION_KEYWORDS.keys()),
            "weapon": list(self.WEAPON_KEYWORDS.keys()),
            "body_part": list(self.BODY_PART_KEYWORDS.keys()),
            "target": list(self.TARGET_KEYWORDS.keys()),
            "modifier": list(self.MODIFIER_KEYWORDS.keys())
        }

        validated = {"confidence": details["confidence"]}

        for key, allowed_values in valid_values.items():
            value = details.get(key)

            if value is None or value == "null":
                continue

            # Проверка валидности
            if value not in allowed_values:
                print(f"[WARN] LLM returned invalid value: {key}={value}")
                # Можно попытаться найти ближайшее валидное
                # Пока просто пропускаем
                continue

            validated[key] = value

        return validated if len(validated) > 1 else None  # Хотя бы 1 параметр кроме confidence

    def _extract_with_llm(self, command: str) -> Dict[str, Any]:
        """
        Использует Gemini Flash для сложных случаев.
        """
        prompt = f"""Ты - парсер боевых команд для RPG. Извлеки параметры из команды.

ВАЖНО: Верни ТОЛЬКО валидный JSON, без markdown, комментариев и лишнего текста.

Команда: "{command}"

Формат ответа:
{{
  "action": "strike|stab|shoot|slash|dodge|block|cast",
  "weapon": "sword|dagger|axe|bow|staff|fists",
  "body_part": "head|neck|torso|arm|leg|heart",
  "target": "goblin|orc|skeleton|spider|wolf",
  "modifier": "from_side|from_above|with_force|carefully|quickly"
}}

Если параметр не указан явно, используй null.
Твой ответ (только JSON):"""

        llm_request = {
            "prompt": prompt,
            "prompt_template_name": "intent_extraction",
            "game_state": "PARSING"
        }

        response_text = llm._send_prompt_to_gemini(llm_request)

        # Очистка от markdown-блоков
        response_text = self._clean_llm_json(response_text)

        try:
            details = json.loads(response_text)
            details["confidence"] = 1.0
            return details
        except json.JSONDecodeError as e:
            print(f"[WARN] LLM returned invalid JSON: {response_text}")
            print(f"[ERROR] {e}")
            return {"confidence": 0.0}

    def extract_action_details(self, command: str) -> Dict[str, Any]:
        """
        Главный метод извлечения деталей действия.

        Returns:
            {
                "action": str,
                "weapon": str,
                "body_part": str,
                "target": str,
                "modifier": str,
                "confidence": float
            }
        """
        # Шаг 1: Нормализация (лемматизация)
        normalized_words = self._normalize_command(command)

        # Шаг 2: Извлечение через правила
        details = self._extract_with_rules(normalized_words, command.lower())

        # Шаг 3: Разрешение конфликтов
        details = self._resolve_conflicts(details, normalized_words)

        # Шаг 4: Оценка уверенности
        confidence = self._calculate_confidence(details)
        details["confidence"] = confidence

        # Шаг 5: Fallback на LLM если низкая уверенность
        if confidence < 0.5:
            print(f"[WARN] Low confidence ({confidence:.2f}), requesting LLM...")
            llm_details = self._extract_with_llm(command)

            # Валидация ответа LLM
            validated_details = self._validate_llm_response(llm_details)

            if validated_details:
                return validated_details
            else:
                print("[WARN] LLM did not provide valid response, using rule-based result")

        return details