from logger_config import get_logger

# Инициализация логгера
logger = get_logger()

def handle_player_event(steam_id, player_name, operation_type, players, player_log_files, log_file):
    """
    Обрабатывает события входа/выхода игроков.
    :param steam_id: Steam ID игрока.
    :param player_name: Никнейм игрока.
    :param operation_type: Тип операции ('login' или 'logout').
    :param players: Словарь текущих игроков.
    :param player_log_files: Словарь для отслеживания файлов, где игроки онлайн.
    :param log_file: Файл логов, связанный с событием.
    """
    if operation_type == "login":
        if steam_id in players:
            logger.debug(f"[{log_file}] Игрок с ID {steam_id} уже онлайн. Пропускаем.")
            return False

        if player_name:
            players[steam_id] = {"name": player_name, "score": 0, "duration": 0.0}
            player_log_files[steam_id] = log_file
            logger.debug(f"[{log_file}] Игрок {player_name} ({steam_id}) подключился.")
            return True
        else:
            logger.warning(f"[{log_file}] Ошибка: Не найдено имя игрока для аккаунта {steam_id}.")
            return False

    elif operation_type == "logout":
        if steam_id in players:
            if player_log_files.get(steam_id) != log_file:
                logger.debug(f"[{log_file}] Игрок с ID {steam_id} вышел из другого файла. Пропускаем.")
                return False
            player_name = players[steam_id]["name"]
            del players[steam_id]
            del player_log_files[steam_id]
            logger.debug(f"[{log_file}] Игрок {player_name} ({steam_id}) отключился.")
            return True
        else:
            logger.warning(f"[{log_file}] Ошибка: Попытка выхода неизвестного игрока с ID {steam_id}.")
            return False

    else:
        logger.error(f"[{log_file}] Неизвестный тип операции: {operation_type}")
        return False