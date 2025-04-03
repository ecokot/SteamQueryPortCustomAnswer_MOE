import json
import os
from logger_config import get_logger

# Инициализация логгера
logger = get_logger()

# Файл для хранения данных о игроках
PLAYERS_DATA_FILE = "players_data.json"


class PlayerHandler:
    _instance = None  # Хранит единственный экземпляр класса

    def __new__(cls):
        """
        Создает единственный экземпляр класса (синглтон).
        """
        if cls._instance is None:
            logger.info("Создание нового экземпляра PlayerHandler.")
            cls._instance = super(PlayerHandler, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """
        Инициализация атрибутов экземпляра.
        Загружает данные о игроках из файла при запуске.
        """
        self.players_in_file = self._load_players_data()  # Словарь игроков в файле
        self.players = {}  # Словарь текущих игроков
        self.player_log_files = {}  # Словарь для отслеживания файлов, где игроки онлайн
        logger.debug(f"Инициализировано {len(self.players_in_file)} игроков из файла.")

    def _load_players_data(self):
        """
        Загружает данные о игроках из JSON-файла.
        Если файл не существует, создает пустой словарь.
        """
        if os.path.exists(PLAYERS_DATA_FILE):
            try:
                with open(PLAYERS_DATA_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # Проверяем, что данные содержат корректные ключи
                    for steam_id, player_data in list(data.items()):
                        if not isinstance(player_data, dict) or "name" not in player_data:
                            logger.warning(f"Некорректные данные для игрока {steam_id}. Пропускаем.")
                            del data[steam_id]
                    logger.info(f"Загружено {len(data)} записей из файла players_data.json.")
                    return data
            except (json.JSONDecodeError, FileNotFoundError) as e:
                logger.error(f"Ошибка при загрузке данных игроков: {e}")
                return {}
        else:
            logger.info("Файл players_data.json не найден. Создается новый файл.")
            return {}

    def _save_players_data(self):
        """
        Сохраняет данные о игроках в JSON-файл.
        """
        try:
            with open(PLAYERS_DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(self.players_in_file, f, indent=4, ensure_ascii=False)
            logger.debug("Данные игроков успешно сохранены в файл.")
        except Exception as e:
            logger.error(f"Ошибка при сохранении данных игроков: {e}")

    def handle_event(self, steam_id, player_name, operation_type, log_file):
        """
        Обрабатывает события входа/выхода игроков.
        :param steam_id: Steam ID игрока.
        :param player_name: Никнейм игрока.
        :param operation_type: Тип операции ('login' или 'logout').
        :param log_file: Файл логов, связанный с событием.
        """
        # Валидация входных данных
        if not steam_id or not isinstance(steam_id, str):
            logger.error(f"[{log_file}] Некорректный Steam ID: {steam_id}")
            return False

        if operation_type not in ("login", "logout"):
            logger.error(f"[{log_file}] Неизвестный тип операции: {operation_type}")
            return False

        # Обработка события
        if operation_type == "login":
            return self._handle_login(steam_id, player_name, log_file)
        elif operation_type == "logout":
            return self._handle_logout(steam_id, log_file)

    def _handle_login(self, steam_id, player_name, log_file):
        """
        Обрабатывает событие входа игрока.
        """
        # Если игрок уже онлайн, пропускаем
        if steam_id in self.players:
            logger.debug(f"[{log_file}] Игрок с ID {steam_id} уже онлайн. Пропускаем.")
            return False

        # Если ник не передан, проверяем, есть ли он в файле
        if not player_name:
            if steam_id in self.players_in_file and self.players_in_file[steam_id]["name"]:
                player_name = self.players_in_file[steam_id]["name"]
                logger.debug(f"[{log_file}] Ник для игрока {steam_id} взят из файла: {player_name}.")
            else:
                logger.warning(f"[{log_file}] Ошибка: Не найдено имя игрока для аккаунта {steam_id}.")
                return False

        # Добавляем или обновляем игрока в словарях
        if steam_id not in self.players:
            self.players[steam_id] = {"name": player_name, "score": 0, "duration": 0.0}
            logger.debug(f"[{log_file}] Игрок {player_name} ({steam_id}) добавлен в память.")

        if steam_id not in self.players_in_file:
            self.players_in_file[steam_id] = {"name": player_name, "score": 0, "duration": 0.0}
            logger.debug(f"[{log_file}] Игрок {player_name} ({steam_id}) добавлен в файл.")
        elif self.players_in_file[steam_id]["name"] != player_name:
            self.players_in_file[steam_id]["name"] = player_name
            logger.debug(f"[{log_file}] Ник игрока {steam_id} обновлен на {player_name}.")

        # Обновляем файлы и сохраняем данные
        self.player_log_files[steam_id] = log_file
        self._save_players_data()
        return True

    def _handle_logout(self, steam_id, log_file):
        """
        Обрабатывает событие выхода игрока.
        """
        if steam_id not in self.players:
            logger.warning(f"[{log_file}] Ошибка: Попытка выхода неизвестного игрока с ID {steam_id}.")
            return False

        if self.player_log_files.get(steam_id) != log_file:
            logger.debug(f"[{log_file}] Игрок с ID {steam_id} вышел из другого файла. Пропускаем.")
            return False

        # Удаляем игрока из словаря онлайн-игроков
        player_name = self.players[steam_id]["name"]
        del self.players[steam_id]
        del self.player_log_files[steam_id]
        logger.debug(f"[{log_file}] Игрок {player_name} ({steam_id}) отключился.")

        # Данные остаются в файле, так как файл выступает постоянным хранилищем
        return True

    def get_online_players(self):
        """
        Возвращает список текущих онлайн-игроков.
        """
        return [
            {"steam_id": steam_id, "name": data["name"], "score": data["score"], "duration": data["duration"]}
            for steam_id, data in self.players.items()
        ]