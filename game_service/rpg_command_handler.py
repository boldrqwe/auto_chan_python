import os
import requests
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
import json

class RPGGameCommandHandler:
    """Класс для обработки команд и взаимодействия с ChatGPT."""
    BASE_CHATGPT_URL = "https://autochanpython-production.up.railway.app/chat"

    def __init__(self):
        # Устанавливаем абсолютный путь к папке с промптами
        self.prompts_path = os.path.join(os.path.dirname(__file__), "prompts")
        self.character = {
            "name": "Игрок",
            "class": "Воин",
            "health": 100,
            "stamina": 100,
            "magic": 50,
            "inventory": [],
            "experience": 0,
            "level": 1,
            "skills": []
        }
        self.item_pool = {}  # Словарь для хранения предметов

    @staticmethod
    def parse_json(input_str: str):
        """Парсит JSON из строки."""
        try:
            escaped_str = input_str.strip()
            parsed_json = json.loads(escaped_str)
            return parsed_json
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")
            return None

    def load_prompt(self, action: str) -> str:
        """
        Загружает промпт из файла на основе действия.
        :param action: Действие игрока (ключ).
        :return: Текст промпта или основной промпт по умолчанию.
        """
        filename = f"{action}.txt"  # Только имя файла без пути
        filepath = os.path.join(self.prompts_path, filename)
        print(f"Loading prompt from: {filepath}")  # Отладка
        try:
            with open(filepath, "r", encoding="utf-8") as file:
                content = file.read().strip()
                print(f"Prompt content:\n{content}")  # Отладка
                return content
        except FileNotFoundError:
            print(f"Prompt file {filename} not found. Falling back to default prompt.")
            return self.load_default_prompt()

    def load_default_prompt(self) -> str:
        """
        Загружает основной промпт по умолчанию.
        """
        default_filename = "default.txt"
        default_filepath = os.path.join(self.prompts_path, default_filename)
        print(f"Loading default prompt from: {default_filepath}")  # Отладка
        try:
            with open(default_filepath, "r", encoding="utf-8") as file:
                content = file.read().strip()
                print(f"Default prompt content:\n{content}")  # Отладка
                return content
        except FileNotFoundError:
            print(f"Default prompt file {default_filename} not found.")
            return "Добро пожаловать в игру! Ваше приключение начинается здесь."

    def fetch_chat_response(self, player_message: str, prompt: str) -> dict:
        """Отправляет запрос в ChatGPT и возвращает JSON-ответ."""
        payload = {"player_message": player_message, "prompt": prompt}
        try:
            response = requests.post(self.BASE_CHATGPT_URL, json=payload, timeout=10)
            response.raise_for_status()
            raw_response = response.text

            # Используем parse_json для обработки строки JSON
            parsed_response = self.parse_json(raw_response)

            if parsed_response:
                print("ChatGPT Response:", json.dumps(parsed_response, ensure_ascii=False, indent=2))
                return parsed_response.get("response", {})
            else:
                return self.default_answer()
        except (requests.RequestException, ValueError) as e:
            print(f"Error during request: {e}")
            return self.default_answer()

    def default_answer(self):
        return {
            "description": "Ответ некорректен. Попробуйте снова.",
            "actions": ["Продолжить"],
            "event_picture": ""
        }

    def parse_response(self, chat_response: str, user_data: dict) -> (str, InlineKeyboardMarkup, str):
        """
        Парсит ответ ChatGPT и возвращает описание, кнопки и ASCII-арт.
        Также генерирует уникальные callback_data для кнопок и сохраняет их в user_data.
        """
        parsed_response = self.parse_json(chat_response)

        if not parsed_response or not isinstance(parsed_response, dict):
            return (
                "Произошла ошибка при обработке ответа. Попробуйте снова.",
                InlineKeyboardMarkup([[InlineKeyboardButton("Продолжить", callback_data="continue")]]),
                ""
            )

        description = parsed_response.get("description", "Произошла ошибка.")
        actions = parsed_response.get("actions", ["Продолжить"])
        event_picture = parsed_response.get("event_picture", "")

        if not isinstance(actions, list) or not all(isinstance(action, str) for action in actions):
            actions = ["Продолжить"]

        # Генерируем уникальные идентификаторы для действий
        action_mapping = {}
        buttons = []
        for idx, action in enumerate(actions):
            action_id = f"action_{idx}"
            action_mapping[action_id] = action
            buttons.append([InlineKeyboardButton(action, callback_data=action_id)])

        # Сохраняем сопоставление действий в user_data
        user_data['action_mapping'] = action_mapping

        return description, InlineKeyboardMarkup(buttons), event_picture

    def add_experience(self, amount: int):
        """Добавляет опыт и проверяет повышение уровня."""
        self.character["experience"] += amount
        max_experience = self.character["level"] * 100
        if self.character["experience"] >= max_experience:
            self.character["experience"] -= max_experience
            self.character["level"] += 1
            self.character["skills"].append(f"Новый навык {len(self.character['skills']) + 1}")

    def add_to_inventory(self, item: dict):
        """Добавляет предмет в инвентарь."""
        item_id = item.get("id")
        if item_id:
            self.item_pool[item_id] = item  # Сохраняем предмет в пуле
            self.character["inventory"].append(item_id)

    def use_item(self, item_id: str) -> str:
        """Использует предмет из инвентаря."""
        if item_id in self.item_pool:
            item = self.item_pool[item_id]
            effect = item.get("effect", "Предмет не оказывает эффекта.")
            # Удаляем предмет из инвентаря
            self.character["inventory"].remove(item_id)
            del self.item_pool[item_id]
            return f"Вы использовали предмет: {item['name']}. {effect}"
        return "Такого предмета нет в вашем инвентаре."

    def get_characteristics(self) -> str:
        """Возвращает строку с текущими характеристиками персонажа."""
        inventory = ", ".join([self.item_pool[item_id]["name"] for item_id in self.character["inventory"]]) if self.character["inventory"] else "пусто"
        return (
            f"Имя: {self.character['name']}\n"
            f"Класс: {self.character['class']}\n"
            f"Уровень: {self.character['level']}\n"
            f"Опыт: {self.character['experience']} / {self.character['level'] * 100}\n"
            f"Здоровье: {self.character['health']}\n"
            f"Стамина: {self.character['stamina']}\n"
            f"Магия: {self.character['magic']}\n"
            f"Инвентарь: {inventory}\n"
            f"Навыки: {', '.join(self.character['skills']) if self.character['skills'] else 'нет навыков'}"
        )
