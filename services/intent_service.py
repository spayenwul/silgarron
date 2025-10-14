from typing import Dict, Any, List, Optional
import pymorphy3
import re
import chromadb
import json
from pathlib import Path

class IntentService:
    """
    IntentService (Player Intent Engine) - Движок Понимания Намерений Игрока.

    Архитектура:
    1.  Парсер-Планировщик: Основная задача - разобрать сложную, написанную
        естественным языком команду игрока на последовательность простых,
        атомарных действий (Action Queue).
    2.  "Тупой" и быстрый: Парсер не содержит сложной игровой логики, не знает
        свойств предметов или правил мира. Его цель - максимально быстро и точно
        извлечь НАМЕРЕНИЕ (action) и СУЩНОСТИ (instrument, target, body_part).
    3.  Универсальность: Оперирует понятием "инструмент", которым может быть
        любой объект в игре (меч, камень, книга), а не только "оружие".
    4.  Контекст: Умеет переносить контекст (например, цель атаки) из одной
        части команды в другую ("атакую гоблина мечом, а затем топором").

    Результатом работы является список словарей, где каждый словарь - это одно
    простое действие, готовое к передаче в основной игровой движок для симуляции.
    """

    def __init__(self):
        """
        Инициализирует морфологический анализатор и ChromaDB для классификации intent.
        """
        print("[INIT] Initializing Player Intent Engine...")
        self.morph = pymorphy3.MorphAnalyzer()

        # ChromaDB для классификации намерений
        self.chroma_client = chromadb.Client()
        self.intent_collection = self.chroma_client.get_or_create_collection(
            name="intent_recognition",
            metadata={"hnsw:space": "cosine"}
        )

        # Загружаем intents.json и заполняем ChromaDB
        self._load_intents_into_chroma()

        # Валидные типы сложности
        self.VALID_COMPLEXITY_TYPES = {"CODE_ONLY", "SIMPLE_LLM", "COMPLEX_TOOL_CALL"}

        # Маркеры для разбиения сложных команд на простые сегменты.
        self.SEQUENCE_MARKERS = [
            ", а затем ", ", потом ", ", после чего ", ", и затем ",
            "; ", ", ", " и "
        ]
        # Сортируем от самого длинного к самому короткому для корректной замены
        self.SEQUENCE_MARKERS.sort(key=len, reverse=True)

        # Определения базовых действий (интентов).
        self.ACTION_KEYWORDS = {
            "move": ["подойти", "подбежать", "отойти", "отбежать", "переместиться", "двинуться", "идти"],
            "dodge": ["увернуться", "уклониться", "отскочить", "уворот", "перекат"],
            "block": ["блокировать", "парировать", "отбить", "защититься", "защита", "блок"],
            "strike": ["бить", "ударить", "атаковать", "стукнуть", "удар", "атака", "бью"],
            "slash": ["рубить", "резать", "рассечь", "взмах", "рублю", "рубануть"],
            "stab": ["колоть", "проткнуть", "ткнуть", "укол", "выпад", "колю"],
            "shoot": ["стрелять", "выстрелить", "палить", "выстрел"],
            "throw": ["кинуть", "метнуть", "бросить", "кидок", "бросок", "кидаю"],
            "cast": ["использовать", "колдовать", "заклинание", "кастовать", "применить"],
        }

        # Определения частей тела.
        self.BODY_PART_KEYWORDS = {
            "head": ["голова", "череп", "лицо", "шлем", "башка", "висок", "глаз"],
            "neck": ["шея", "горло"],
            "torso": ["грудь", "живот", "торс", "корпус", "тело", "спина", "ребро", "бок"],
            "arm": ["рука", "плечо", "локоть", "предплечье", "кисть"],
            "leg": ["нога", "колено", "бедро", "голень", "стопа"],
        }
        
        # Определения модификаторов действия.
        self.MODIFIER_KEYWORDS = {
            "from_side": ["сбоку", "с фланга"],
            "from_above": ["сверху", "вниз", "в прыжке"],
            "from_behind": ["со спины", "сзади", "в спину"],
            "with_force": ["сильно", "мощно", "изо всех сил", "с размаху"],
            "carefully": ["осторожно", "аккуратно", "точно", "прицельно", "целясь"],
            "quickly": ["быстро", "молниеносно", "резко", "мгновенно"],
        }


    def parse_command_sequence(self, full_command: str) -> List[Dict[str, Any]]:
        action_queue: List[Dict[str, Any]] = []
        context: Dict[str, Any] = {}

        delimiter = "|SEQ|"
        temp_command = full_command.lower()
        for marker in self.SEQUENCE_MARKERS:
            temp_command = temp_command.replace(marker, delimiter)
        
        command_segments = [segment.strip() for segment in temp_command.split(delimiter)]

        for segment in command_segments:
            if not segment: continue
            
            action_details = self._extract_entities(segment)
            
            if (action_details.get("action") == "throw" and 
                "instrument_entity" not in action_details and 
                "target_entity" in action_details):
                action_details["instrument_entity"] = action_details.pop("target_entity")

            if "target_entity" not in action_details and "target_entity" in context:
                action_details["target_entity"] = context["target_entity"]
            
            if "instrument_entity" not in action_details and "instrument_entity" in context:
                 action_details["instrument_entity"] = context["instrument_entity"]
            
            if "action" in action_details:
                action_details["original_segment"] = segment
                action_queue.append(action_details)
                context.update(action_details)

        return action_queue

    def _extract_entities(self, command_segment: str) -> Dict[str, Any]:
        details: Dict[str, Any] = {}
        words = re.findall(r"[\w'-]+", command_segment.lower())
        
        if not words: return {}
        
        lemmas = [self.morph.parse(word)[0].normal_form for word in words]
        parsed_words = [self.morph.parse(word)[0] for word in words]
        used_indices = set()

        for i, lemma in enumerate(lemmas):
            for action, keywords in self.ACTION_KEYWORDS.items():
                if lemma in keywords or words[i] in keywords:
                    details["action"] = action; used_indices.add(i); break
            if "action" in details: break
        
        for i, lemma in enumerate(lemmas):
            if i in used_indices: continue
            for modifier, keywords in self.MODIFIER_KEYWORDS.items():
                if lemma in keywords: details["modifier"] = modifier; used_indices.add(i)
            for part, keywords in self.BODY_PART_KEYWORDS.items():
                if lemma in keywords:
                    details["body_part_entity"] = self.morph.parse(words[i])[0].normal_form
                    used_indices.add(i)

        for i, p_word in enumerate(parsed_words):
            if i in used_indices: continue
            
            tags = p_word.tag
            def get_full_entity_name(index, lemmatize=False):
                name_parts = [words[index]]
                if index > 0 and index - 1 not in used_indices:
                    prev_word_tags = parsed_words[index-1].tag
                    if 'ADJF' in prev_word_tags or 'PRTF' in prev_word_tags:
                        used_indices.add(index-1)
                        name_parts.insert(0, words[index-1])
                
                if lemmatize:
                    return self.morph.parse(name_parts[-1])[0].normal_form
                return " ".join(name_parts)

            if 'NOUN' in tags:
                is_target = False
                is_instrument = False

                if 'ablt' in tags:
                    is_instrument = True
                elif 'accs' in tags or 'gent' in tags:
                    is_target = True
                elif i > 0 and 'NOUN' in parsed_words[i].tag:
                    prep = lemmas[i-1]
                    # <<< ИСПРАВЛЕНИЕ: Добавляем предлог "в" в логику >>>
                    if prep in ["по", "к"] and 'datv' in tags:
                        is_target = True
                    elif prep == "в" and 'accs' in tags:
                        is_target = True

                if is_instrument:
                    details["instrument_entity"] = get_full_entity_name(i, lemmatize=True)
                    used_indices.add(i)
                elif is_target:
                    details["target_entity"] = get_full_entity_name(i, lemmatize=True)
                    used_indices.add(i)
                    if i > 0 and lemmas[i-1] in ["по", "к", "в"]:
                        used_indices.add(i-1)

        return details

    def _load_intents_into_chroma(self):
        """
        Загружает примеры из data/intents.json в ChromaDB для векторного поиска.
        """
        intents_path = Path(__file__).parent.parent / "data" / "intents.json"

        # Проверяем, не загружены ли уже данные
        try:
            count = self.intent_collection.count()
            if count > 0:
                print(f"[INIT] Intent collection already populated with {count} examples")
                return
        except:
            pass

        # Загружаем и добавляем в ChromaDB
        with open(intents_path, "r", encoding="utf-8") as f:
            intents_data = json.load(f)

        documents = []
        metadatas = []
        ids = []

        for i, item in enumerate(intents_data):
            documents.append(item["text"])
            metadatas.append(item["metadata"])
            ids.append(f"intent_{i}")

        self.intent_collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        print(f"[INIT] Loaded {len(documents)} intent examples into ChromaDB")

    def recognize_intent(self, player_command: str) -> Dict[str, str]:
        """
        Распознаёт намерение игрока и уровень сложности команды.

        Args:
            player_command: Команда игрока на естественном языке

        Returns:
            Dict с полями:
            - intent: тип намерения (COMBAT, EXPLORATION, и т.д.)
            - complexity_type: уровень сложности (CODE_ONLY, SIMPLE_LLM, COMPLEX_TOOL_CALL)

        Пример:
            >>> service.recognize_intent("посмотреть инвентарь")
            {"intent": "SELF_ACTION_CODE_ONLY", "complexity_type": "CODE_ONLY"}
        """
        # 1. Векторный поиск ближайшего примера
        results = self.intent_collection.query(
            query_texts=[player_command.lower()],
            n_results=1
        )

        if not results['metadatas'] or not results['metadatas'][0]:
            print(f"[WARN] No intent found for command: '{player_command}', using fallback")
            return {"intent": "UNKNOWN", "complexity_type": "SIMPLE_LLM"}

        metadata = results['metadatas'][0][0]
        intent = metadata.get("intent", "UNKNOWN")
        complexity_type = metadata.get("complexity_type", "SIMPLE_LLM")

        # 2. Применяем эвристические правила (второй слой защиты)
        complexity_type = self._apply_heuristics(player_command, complexity_type)

        # 3. Валидация complexity_type
        if complexity_type not in self.VALID_COMPLEXITY_TYPES:
            print(f"[WARN] Unknown complexity_type '{complexity_type}', falling back to SIMPLE_LLM")
            complexity_type = "SIMPLE_LLM"

        return {
            "intent": intent,
            "complexity_type": complexity_type
        }

    def _apply_heuristics(self, command: str, base_classification: str) -> str:
        """
        Применяет эвристические правила для корректировки классификации.

        Это второй слой защиты от ошибок векторной классификации.
        """
        command_lower = command.lower()

        # Ключевые слова для COMPLEX_TOOL_CALL
        complex_keywords = [
            'опрокинуть', 'бросить на', 'использовать окружение',
            'подпереть', 'кинуть', 'перерубить', 'толкнуть',
            'поджечь', 'отвлечь', 'ослепить', 'притвориться',
            'выманить', 'залезть', 'разбить', 'скомбинировать',
            'заморозить', 'запугать', 'срезать', ', чтобы'
        ]

        if any(keyword in command_lower for keyword in complex_keywords):
            return "COMPLEX_TOOL_CALL"

        # Ключевые слова для CODE_ONLY
        code_only_keywords = [
            'инвентарь', 'статистика', 'посмотреть на себя',
            'характеристики', 'в сумке', 'раны', 'здоровье',
            'сохранить', 'загрузить', 'карта', 'журнал', 'меню'
        ]

        if any(keyword in command_lower for keyword in code_only_keywords):
            return "CODE_ONLY"

        # Используем базовую классификацию
        return base_classification