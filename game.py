import random
from collections import defaultdict


class RPGGame:
    def __init__(self, bot):
        self.bot = bot  # Telegram Bot instance
        self.players = {}  # {user_id: {"name": str, "class": str, "stats": dict}}
        self.team_votes = defaultdict(list)  # {action: [user_id, user_id, ...]}
        self.current_event = None  # Stores the current event or scenario
        self.world_state = {"gold": 0, "resources": {}}  # Shared team state

    async def start_game(self, chat_id):
        self.world_state = {"gold": 0, "resources": {}}
        self.players = {}
        self.current_event = None
        await self.bot.send_message(chat_id,
                                    "Игра началась! Добавьтесь в команду, выберите класс и начинаем исследование мира! Используйте /join <имя> <класс>.")

    def join_game(self, user_id, name, player_class):
        if user_id in self.players:
            return f"{name}, вы уже в игре!"

        self.players[user_id] = {
            "name": name,
            "class": player_class,
            "stats": {
                "strength": 5,
                "agility": 5,
                "intelligence": 5,
                "charisma": 5,
                "health": 100,
            },
            "inventory": []
        }
        return f"{name} (Класс: {player_class}) успешно присоединился к игре!"

    async def initiate_event(self, chat_id):
        events = [
            "Вы нашли заброшенный храм. Что будете делать?",
            "Вы встретили банду гоблинов. Будете сражаться или убегать?",
            "Перед вами торговец. Хотите поторговать?",
        ]
        self.current_event = random.choice(events)
        self.team_votes.clear()
        await self.bot.send_message(chat_id, self.current_event)
        await self.bot.send_message(chat_id, "Голосуйте за действие: /vote <действие>")

    def register_vote(self, user_id, action):
        # Удаляем предыдущие голоса пользователя
        for key in self.team_votes:
            if user_id in self.team_votes[key]:
                self.team_votes[key].remove(user_id)

        self.team_votes[action].append(user_id)
        return f"Голос за '{action}' успешно зарегистрирован!"

    async def calculate_votes(self, chat_id):
        if not self.team_votes:
            await self.bot.send_message(chat_id, "Никто не проголосовал!")
            return

        # Подсчёт голосов
        votes_count = {action: len(voters) for action, voters in self.team_votes.items()}
        most_voted = max(votes_count, key=votes_count.get)

        await self.bot.send_message(chat_id, f"Действие с наибольшим количеством голосов: '{most_voted}'")
        await self.execute_action(chat_id, most_voted)

    async def execute_action(self, chat_id, action):
        # Пример реализации действий
        outcomes = {
            "исследовать": "Вы нашли сундук с золотом!",
            "сражаться": "Вы победили врагов, но потеряли часть здоровья.",
            "убежать": "Вы успешно убежали, но потеряли немного золота.",
            "торговать": "Вы обменяли часть ресурсов на полезные предметы.",
        }
        outcome = outcomes.get(action, "Ничего не произошло.")

        # Пример изменения состояния
        if action == "исследовать":
            self.world_state["gold"] += random.randint(10, 50)
        elif action == "сражаться":
            for player in self.players.values():
                player["stats"]["health"] -= random.randint(5, 15)

        await self.bot.send_message(chat_id, outcome)
        self.current_event = None

    async def show_stats(self, chat_id):
        stats_message = "Состояние команды:\n"
        for player in self.players.values():
            stats_message += f"{player['name']} (Класс: {player['class']}) - Здоровье: {player['stats']['health']}\n"
        stats_message += f"Общее золото команды: {self.world_state['gold']}"
        await self.bot.send_message(chat_id, stats_message)

