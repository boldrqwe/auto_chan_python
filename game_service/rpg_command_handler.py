import os
import requests
from telegram import InlineKeyboardMarkup, InlineKeyboardButton


class RPGGameCommandHandler:
    """Класс для обработки команд и взаимодействия с ChatGPT."""
    BASE_CHATGPT_URL = "https://autochanpython-production.up.railway.app/chat"

    def __init__(self):
        self.prompts_path = "prompts"  # Путь к папке с файлами промптов
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

    def load_prompt(self, action: str) -> str:
        """
        Загружает промпт из файла на основе действия.
        :param action: Действие игрока (ключ).
        :return: Текст промпта или основной промпт по умолчанию.
        """
        filename = f"{action}.txt"
        filepath = os.path.join(self.prompts_path, filename)
        try:
            with open(filepath, "r", encoding="utf-8") as file:
                return file.read().strip()
        except FileNotFoundError:
            return self.load_default_prompt()

    def load_default_prompt(self) -> str:
        """
        Загружает основной промпт по умолчанию.
        """
        try:
            base_dir = os.path.dirname(__file__)  # Путь к текущей папке
            filepath = os.path.join(base_dir, "prompts", "prompt.txt")
            with open(filepath, "r", encoding="utf-8") as file:
                return file.read()
        except FileNotFoundError:
            return "Добро пожаловать в игру! Ваше приключение начинается здесь."

    def fetch_chat_response(self, player_message: str, prompt: str) -> dict:
        """Отправляет запрос в ChatGPT и возвращает JSON-ответ."""
        payload = {"player_message": player_message, "prompt": prompt}
        try:
            response = requests.post(self.BASE_CHATGPT_URL, json=payload, timeout=10)
            response.raise_for_status()
            data = response.json()

            # Проверка на наличие нужных ключей в ответе
            if "description" not in data or "actions" not in data or "event_picture" not in data:
                return {
                    "description": "Ответ некорректен. Попробуйте снова.",
                    "actions": ["Продолжить"],
                    "event_picture": ""
                }
            return data
        except (requests.RequestException, ValueError):
            return {
                "description": "Ошибка при обращении к ChatGPT. Проверьте подключение к интернету.",
                "actions": ["Попробовать снова"],
                "event_picture": ""
            }

    def parse_response(self, chat_response: dict) -> (str, InlineKeyboardMarkup, str):
        """
        Парсит ответ ChatGPT и возвращает описание, кнопки и ASCII-арт.
        """
        description = chat_response.get("description", "Произошла ошибка.")
        actions = chat_response.get("actions", ["Продолжить"])
        event_picture = chat_response.get("event_picture", "")

        if not actions:  # Защита от пустого списка
            actions = ["Продолжить"]

        # Создание кнопок для действий
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton(action, callback_data=action)] for action in actions
        ])

        return description, buttons, event_picture


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
