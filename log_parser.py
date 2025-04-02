import os
import asyncio
from collections import defaultdict
from logger_config import get_logger
from ddos_protection import DDOSProtection
from constants import (
    UNIFIED_LOGIN_PATTERN, LOGOUT_PATTERN_OLD, LOGOUT_PATTERN_NEW,
    IP_TIMESTAMP_PATTERN, DDOS_THRESHOLD, DDOS_INTERVAL
)
from async_watchdog import watch_directory
from player_handler import handle_player_event  # Импортируем новый обработчик

# Инициализация логгера
logger = get_logger()

async def parse_log(log_file, players, player_log_files):
    """
    Парсит файл логов: сначала полный парсинг, затем реальное время.
    Также добавлена защита от DDoS-атак.
    """
    if not os.path.exists(log_file):  # Используем синхронный метод
        logger.error(f"Файл логов не найден: {log_file}")
        return

    # Для защиты от DDoS
    ddos_protection = DDOSProtection(DDOS_THRESHOLD, DDOS_INTERVAL)
    loop = asyncio.get_event_loop()
    ddos_protection.start_cleanup_task(loop)  # Запускаем задачу очистки и разблокировки

    # Полный парсинг
    logger.info(f"Полный парсинг {log_file}")
    try:
        with open(log_file, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()

        for line in lines:
            # Защита от DDoS: анализируем IP-адреса и временные метки
            ip_timestamp_match = IP_TIMESTAMP_PATTERN.search(line)
            if ip_timestamp_match:
                timestamp = ip_timestamp_match.group(1)
                ip_address = ip_timestamp_match.group(2)
                ddos_protection.process_ip(ip_address, timestamp)

            # Обработка входа/выхода игроков
            handle_player_events(line, players, player_log_files, log_file)

    except Exception as e:
        logger.error(f"Ошибка при полном парсинге файла {log_file}: {e}")
        return

    logger.info(f"Полный парсинг {log_file} завершен. Текущий словарь players: {players}")

    # Режим реального времени с использованием watchdog
    logger.info(f"Перехожу в режим реального времени для файла: {log_file}")
    last_position = os.path.getsize(log_file)  # Последняя позиция чтения

    async def handle_file_change(file_path):
        nonlocal last_position
        if file_path != log_file:
            return

        try:
            with open(log_file, "r", encoding="utf-8", errors="replace") as f:
                f.seek(last_position)
                new_lines = f.readlines()
                last_position = f.tell()

            for line in new_lines:
                # Защита от DDoS: анализируем IP-адреса и временные метки
                ip_timestamp_match = IP_TIMESTAMP_PATTERN.search(line)
                if ip_timestamp_match:
                    timestamp = ip_timestamp_match.group(1)
                    ip_address = ip_timestamp_match.group(2)
                    ddos_protection.process_ip(ip_address, timestamp)

                # Обработка входа/выхода игроков
                handle_player_events(line, players, player_log_files, log_file)

        except Exception as e:
            logger.error(f"Ошибка при обработке изменений в файле {log_file}: {e}")

    # Начинаем отслеживать директорию файла
    directory = os.path.dirname(log_file)
    await watch_directory(directory, handle_file_change, loop)


def handle_player_events(line, players, player_log_files, log_file):
    """
    Обрабатывает события входа/выхода игроков.
    """
    # Обработка входа игрока
    login_match = UNIFIED_LOGIN_PATTERN.search(line)
    if login_match:
        steam_id = login_match.group(1) or login_match.group(4)  # Steam ID из старого или нового формата
        player_name = login_match.group(2) or login_match.group(3)  # Имя игрока из старого или нового формата
        handle_player_event(steam_id, player_name, "login", players, player_log_files, log_file)
        return

    # Обработка выхода игрока
    logout_match_old = LOGOUT_PATTERN_OLD.search(line)
    if logout_match_old:
        steam_id = logout_match_old.group(1).strip()
        handle_player_event(steam_id, None, "logout", players, player_log_files, log_file)
        return

    logout_match_new = LOGOUT_PATTERN_NEW.search(line)
    if logout_match_new:
        steam_id = logout_match_new.group(1).strip()
        handle_player_event(steam_id, None, "logout", players, player_log_files, log_file)
        return