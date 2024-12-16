import logging
import os
import requests
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
import re
from datetime import datetime


class RPGGameCommandHandler:
    """Класс для обработки команд и взаимодействия с ChatGPT."""
    BASE_CHATGPT_URL = "https://autochanpython-production.up.railway.app/chat"

    def __init__(self):
        # Настройка логирования
        logging.basicConfig(
            level=logging.INFO,  # Уровень логирования: DEBUG, INFO, WARNING, ERROR, CRITICAL
            format='%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        self.action_order = ['exploration', 'combat', 'trading', 'tavern']

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

    def get_next_action(self, user_data: dict) -> str:
        """Возвращает следующее действие в цикле на основе текущего состояния."""
        history = user_data.get('history', [])
        if not history:
            return 'exploration'

        # Последнее действие системы
        last_event = history[-1]
        for action in self.action_order:
            if action in last_event.lower():
                current_index = self.action_order.index(action)
                next_index = (current_index + 1) % len(self.action_order)
                return self.action_order[next_index]
        return 'exploration'

    def log_event(self, user_id: str, action: str, response: str, error: str = None):
        """Логирует событие в консоль."""
        if error:
            logging.error(f"User: {user_id}, Action: {action}, Response: {response}, Error: {error}")
        else:
            logging.info(f"User: {user_id}, Action: {action}, Response: {response}")

    def load_prompt(self, action: str) -> str:
        """
        Загружает промпт из файла на основе действия.
        :param action: Действие игрока (ключ).
        :return: Текст промпта или основной промпт по умолчанию.
        """
        filename = f"{action}.txt"  # Только имя файла без пути
        filepath = os.path.join(self.prompts_path, filename)
        logging.info(f"Loading prompt from: {filepath}")  # Отладка
        try:
            with open(filepath, "r", encoding="utf-8") as file:
                content = file.read().strip()
                logging.debug(f"Prompt content:\n{content}")  # Отладка
                return content
        except FileNotFoundError:
            logging.warning(f"Prompt file {filename} not found. Falling back to default prompt.")
            return self.load_default_prompt()

    def load_default_prompt(self) -> str:
        """
        Загружает основной промпт по умолчанию.
        """
        default_filename = "default.txt"
        default_filepath = os.path.join(self.prompts_path, default_filename)
        logging.info(f"Loading default prompt from: {default_filepath}")  # Отладка
        try:
            with open(default_filepath, "r", encoding="utf-8") as file:
                content = file.read().strip()
                logging.debug(f"Default prompt content:\n{content}")  # Отладка
                return content
        except FileNotFoundError:
            logging.error(f"Default prompt file {default_filename} not found.")
            return "Добро пожаловать в игру! Ваше приключение начинается здесь."

    def fetch_chat_response(self, player_message: str, prompt: str, user_data: dict, user_id: str) -> str:
        """Отправляет запрос в ChatGPT и возвращает строковый ответ с учетом контекста."""
        # Формируем полный промпт, включая историю
        history = user_data.get('history', [])
        limited_history = history[-10:]  # Ограничиваем историю последними 10 действиями
        history_text = "\n".join(limited_history)
        full_prompt = f"{prompt}\n\nИстория игры:\n{history_text}\n\nДействие игрока: {player_message}"

        payload = {"player_message": player_message, "prompt": full_prompt}
        try:
            response = requests.post(self.BASE_CHATGPT_URL, json=payload, timeout=10)
            response.raise_for_status()
            raw_response = response.text  # Используйте .text, если ответ не в формате JSON

            # Логирование полного ответа для отладки
            logging.info(f"Raw ChatGPT Response: {raw_response}")
            self.log_event(user_id=user_id, action=player_message, response=raw_response)

            # Проверка наличия необходимых тегов
            response = requests.post(self.BASE_CHATGPT_URL, json=payload, timeout=10)
            response.raise_for_status()
            raw_response = response.json()

            # Логирование полного ответа для отладки
            logging.info(f"Raw ChatGPT Response: {raw_response}")
            self.log_event(user_id="unknown", action=player_message, response=raw_response)

            # Проверка наличия необходимых тегов
            game_event = raw_response.get("response")

            return game_event

        except (requests.RequestException, ValueError) as e:
            logging.error(f"Error during request: {e}")
            self.log_event(user_id=user_id, action=player_message, response="", error=str(e))
            return ""

    def parse_response(self, chat_response: str, user_data: dict) -> (str, InlineKeyboardMarkup, str):
        """
        Парсит ответ ChatGPT и возвращает описание, кнопки и ASCII-арт.
        Извлекает содержимое между тегами DESCRIPTION, ACTIONS и EVENT_PICTURE.
        """
        # Регулярные выражения для поиска содержимого между тегами
        description_pattern = r'DESCRIPTION:\s*(.*?)\s*ACTIONS:'
        actions_pattern = r'ACTIONS:\s*(.*?)\s*EVENT_PICTURE:'
        event_picture_pattern = r'EVENT_PICTURE:\s*(.*)'

        description_match = re.search(description_pattern, chat_response, re.DOTALL | re.IGNORECASE)
        actions_match = re.search(actions_pattern, chat_response, re.DOTALL | re.IGNORECASE)
        event_picture_match = re.search(event_picture_pattern, chat_response, re.DOTALL | re.IGNORECASE)

        description = description_match.group(1).strip()
        actions = [action.strip() for action in actions_match.group(1).split(',')]
        event_picture = event_picture_match.group(1).strip()

        # Дополнительная проверка на наличие всех необходимых частей
        if not description or not actions or not event_picture:
            logging.error("Отсутствуют необходимые части в ответе.")
            return (
                "Произошла ошибка при обработке ответа. Попробуйте снова.",
                InlineKeyboardMarkup([[InlineKeyboardButton("Продолжить", callback_data="continue")]]),
                ""
            )

        # Генерируем уникальные идентификаторы для действий
        action_mapping = {}
        buttons = []
        for idx, action in enumerate(actions):
            action_id = f"action_{len(user_data.get('action_mapping', {}))}_{idx}"  # Уникальный ID
            action_mapping[action_id] = action
            buttons.append([InlineKeyboardButton(action, callback_data=action_id)])

        # Сохраняем сопоставление действий в user_data
        if 'action_mapping' not in user_data:
            user_data['action_mapping'] = {}
        user_data['action_mapping'].update(action_mapping)

        # Обновляем историю
        user_data.setdefault('history', []).append(f"Система: {description}")

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
        inventory = ", ".join([self.item_pool[item_id]["name"] for item_id in self.character["inventory"]]) if \
        self.character["inventory"] else "пусто"
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
