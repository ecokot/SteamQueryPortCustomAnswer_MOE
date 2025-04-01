from logger_config import get_logger
from constants import (
    LOGIN_PATTERN_OLD,
    JOIN_PATTERN_OLD,
    LOGOUT_PATTERN_OLD,
    LOGIN_PATTERN_NEW,
    LOGOUT_PATTERN_NEW
)
# Инициализация логгера
logger = get_logger()

def handle_player_login_old(line, next_line, players, player_log_files, log_file):
    """
    Обрабатывает вход игрока по старому формату.
    """
    login_match_old = LOGIN_PATTERN_OLD.search(line)
    if login_match_old:
        steam_id = login_match_old.group(1).strip()
        if steam_id in players:
            logger.debug(f"[{log_file}] Игрок с ID {steam_id} уже онлайн. Пропускаем.")
            return None

        if next_line and JOIN_PATTERN_OLD.search(next_line):
            player_name = JOIN_PATTERN_OLD.search(next_line).group(1).strip()
            players[steam_id] = {"name": player_name, "score": 0, "duration": 0.0}
            player_log_files[steam_id] = log_file
            logger.info(f"[{log_file}] Игрок {player_name} ({steam_id}) подключился (старый формат).")
            return True
        else:
            logger.warning(f"[{log_file}] Ошибка: Не найдено имя игрока для аккаунта {steam_id}.")
    return False


def handle_player_login_new(line, players, player_log_files, log_file):
    """
    Обрабатывает вход игрока по новому формату.
    """
    login_match_new = LOGIN_PATTERN_NEW.search(line)
    if login_match_new:
        steam_id = login_match_new.group(2).strip()
        if steam_id in players:
            logger.debug(f"[{log_file}] Игрок с ID {steam_id} уже онлайн. Пропускаем.")
            return None

        player_name = login_match_new.group(1).strip()
        players[steam_id] = {"name": player_name, "score": 0, "duration": 0.0}
        player_log_files[steam_id] = log_file
        logger.info(f"[{log_file}] Игрок {player_name} ({steam_id}) подключился (новый формат).")
        return True
    return False


def handle_player_logout(line, players, player_log_files, log_file):
    """
    Обрабатывает выход игрока.
    """
    logout_match_old = LOGOUT_PATTERN_OLD.search(line)
    if logout_match_old:
        steam_id = logout_match_old.group(1).strip()
        if steam_id in players:
            if player_log_files.get(steam_id) != log_file:
                logger.debug(f"[{log_file}] Игрок с ID {steam_id} вышел из другого файла. Пропускаем.")
                return None

            player_name = players[steam_id]["name"]
            del players[steam_id]
            del player_log_files[steam_id]
            logger.info(f"[{log_file}] Игрок {player_name} ({steam_id}) отключился (старый формат).")
            return True
        else:
            logger.warning(f"[{log_file}] Ошибка: Попытка выхода неизвестного игрока с ID {steam_id}.")
    return False