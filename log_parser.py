import re
import os
import asyncio
from collections import defaultdict
from logger_config import get_logger
import time
import subprocess
# Инициализация логгера
logger = get_logger()

# Регулярные выражения для парсинга строк
LOGIN_PATTERN_OLD = re.compile(r"PostLogin Account:\s*(\d+)")
JOIN_PATTERN_OLD = re.compile(r"Join succeeded:\s*([^\s]+)")
LOGOUT_PATTERN_OLD = re.compile(r"Logout Account:\s*(\d+)")

LOGIN_PATTERN_NEW = re.compile(r"ASGGameModeLobby::LobbyClientLogin NickName = ([^,]+), UniqueId = (\d+)")
LOGOUT_PATTERN_NEW = re.compile(r"ASGGameModeLobby::LobbyClientLogOut Account: (\d+)")

# Регулярное выражение для извлечения IP-адресов
IP_PATTERN = re.compile(r'accepted from: (\d+\.\d+\.\d+\.\d+):\d+')

# Параметры защиты от DDoS
DDOS_THRESHOLD = 150  # Максимальное количество попыток за интервал
DDOS_INTERVAL = 3     # Интервал проверки (в секундах)

async def parse_log(log_file, players, player_log_files):
    """
    Парсит файл логов: сначала полный парсинг, затем реальное время.
    Также добавлена защита от DDoS-атак.
    """
    if not os.path.exists(log_file):
        logger.error(f"Файл логов не найден: {log_file}")
        return

    logger.info(f"Начинаю полный парсинг логов из файла: {log_file}")

    try:
        # Читаем весь файл в список строк
        with open(log_file, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()

        # Для защиты от DDoS
        ip_count = defaultdict(int)
        start_time = time.time()
        blocked_ips = set()

        # Обрабатываем строки попарно для старого формата
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            next_line = lines[i + 1].strip() if i + 1 < len(lines) else None

            # Защита от DDoS: анализируем IP-адреса
            ip_match = IP_PATTERN.search(line)
            if ip_match:
                ip_address = ip_match.group(1)
                ip_count[ip_address] += 1

            # Проверяем интервал для защиты от DDoS
            if time.time() - start_time >= DDOS_INTERVAL:
                for ip, count in ip_count.items():
                    if count > DDOS_THRESHOLD and ip not in blocked_ips:
                        logger.warning(f"Обнаружен подозрительный IP: {ip} (попыток: {count}). Блокировка...")
                        block_ip(ip)
                        blocked_ips.add(ip)
                ip_count.clear()
                start_time = time.time()

            # Обработка строк входа (старый формат)
            login_match_old = LOGIN_PATTERN_OLD.search(line)
            if login_match_old:
                steam_id = login_match_old.group(1).strip()
                if steam_id in players:
                    logger.debug(f"[{log_file}] Игрок с ID {steam_id} уже онлайн. Пропускаем.")
                    i += 1
                    continue

                if next_line and JOIN_PATTERN_OLD.search(next_line):
                    player_name = JOIN_PATTERN_OLD.search(next_line).group(1).strip()
                    players[steam_id] = {"name": player_name, "score": 0, "duration": 0.0}
                    player_log_files[steam_id] = log_file  # Запоминаем файл, где игрок был найден
                    logger.info(f"[{log_file}] Игрок {player_name} ({steam_id}) подключился (старый формат).")
                    i += 1  # Пропускаем следующую строку
                else:
                    logger.warning(f"[{log_file}] Ошибка: Не найдено имя игрока для аккаунта {steam_id}.")
                i += 1
                continue

            # Обработка строк входа (новый формат)
            login_match_new = LOGIN_PATTERN_NEW.search(line)
            if login_match_new:
                steam_id = login_match_new.group(2).strip()
                if steam_id in players:
                    logger.debug(f"[{log_file}] Игрок с ID {steam_id} уже онлайн. Пропускаем.")
                    i += 1
                    continue

                player_name = login_match_new.group(1).strip()
                players[steam_id] = {"name": player_name, "score": 0, "duration": 0.0}
                player_log_files[steam_id] = log_file  # Запоминаем файл, где игрок был найден
                logger.info(f"[{log_file}] Игрок {player_name} ({steam_id}) подключился (новый формат).")
                i += 1
                continue

            # Обработка строк выхода (старый формат)
            logout_match_old = LOGOUT_PATTERN_OLD.search(line)
            if logout_match_old:
                steam_id = logout_match_old.group(1).strip()
                if steam_id in players:
                    # Проверяем, соответствует ли файл тому, где игрок был найден онлайн
                    if player_log_files.get(steam_id) != log_file:
                        logger.debug(f"[{log_file}] Игрок с ID {steam_id} вышел из другого файла. Пропускаем.")
                        i += 1
                        continue

                    player_name = players[steam_id]["name"]
                    del players[steam_id]
                    del player_log_files[steam_id]  # Удаляем запись о файле
                    logger.info(f"[{log_file}] Игрок {player_name} ({steam_id}) отключился (старый формат).")
                else:
                    logger.warning(f"[{log_file}] Ошибка: Попытка выхода неизвестного игрока с ID {steam_id}.")
                i += 1
                continue

            # Обработка строк выхода (новый формат)
            logout_match_new = LOGOUT_PATTERN_NEW.search(line)
            if logout_match_new:
                steam_id = logout_match_new.group(1).strip()
                if steam_id in players:
                    # Проверяем, соответствует ли файл тому, где игрок был найден онлайн
                    if player_log_files.get(steam_id) != log_file:
                        logger.debug(f"[{log_file}] Игрок с ID {steam_id} вышел из другого файла. Пропускаем.")
                        i += 1
                        continue

                    player_name = players[steam_id]["name"]
                    del players[steam_id]
                    del player_log_files[steam_id]  # Удаляем запись о файле
                    logger.info(f"[{log_file}] Игрок {player_name} ({steam_id}) отключился (новый формат).")
                else:
                    logger.warning(f"[{log_file}] Ошибка: Попытка выхода неизвестного игрока с ID {steam_id}.")
                i += 1
                continue

            i += 1

    except UnicodeDecodeError as e:
        logger.error(f"Ошибка декодирования файла {log_file}: {e}")
        return

    logger.info(f"Полный парсинг завершен. Текущий словарь players: {players}")

    # Режим реального времени
    logger.info(f"Перехожу в режим реального времени для файла: {log_file}")
    try:
        with open(log_file, "r", encoding="utf-8", errors="replace") as f:
            # Перемещаем указатель в конец файла
            f.seek(0, os.SEEK_END)

            # Для защиты от DDoS
            ip_count = defaultdict(int)
            start_time = time.time()
            blocked_ips = set()

            while True:
                line = f.readline()
                if not line:
                    await asyncio.sleep(0.1)  # Ждем новые строки
                    continue

                # Защита от DDoS: анализируем IP-адреса
                ip_match = IP_PATTERN.search(line)
                if ip_match:
                    ip_address = ip_match.group(1)
                    ip_count[ip_address] += 1

                # Проверяем интервал для защиты от DDoS
                if time.time() - start_time >= DDOS_INTERVAL:
                    for ip, count in ip_count.items():
                        if count > DDOS_THRESHOLD and ip not in blocked_ips:
                            logger.warning(f"Обнаружен подозрительный IP: {ip} (попыток: {count}). Блокировка...")
                            block_ip(ip)
                            blocked_ips.add(ip)
                    ip_count.clear()
                    start_time = time.time()

                # Обработка строк входа (старый формат)
                login_match_old = LOGIN_PATTERN_OLD.search(line)
                if login_match_old:
                    steam_id = login_match_old.group(1).strip()
                    if steam_id in players:
                        logger.debug(f"[{log_file}] Игрок с ID {steam_id} уже онлайн. Пропускаем.")
                        continue

                    next_line = f.readline().strip()  # Читаем следующую строку для имени игрока
                    if next_line and JOIN_PATTERN_OLD.search(next_line):
                        player_name = JOIN_PATTERN_OLD.search(next_line).group(1).strip()
                        players[steam_id] = {"name": player_name, "score": 0, "duration": 0.0}
                        player_log_files[steam_id] = log_file  # Запоминаем файл, где игрок был найден
                        logger.info(f"[{log_file}] Игрок {player_name} ({steam_id}) подключился (старый формат).")
                    else:
                        logger.warning(f"[{log_file}] Ошибка: Не найдено имя игрока для аккаунта {steam_id}.")

                # Обработка строк входа (новый формат)
                login_match_new = LOGIN_PATTERN_NEW.search(line)
                if login_match_new:
                    steam_id = login_match_new.group(2).strip()
                    if steam_id in players:
                        logger.debug(f"[{log_file}] Игрок с ID {steam_id} уже онлайн. Пропускаем.")
                        continue

                    player_name = login_match_new.group(1).strip()
                    players[steam_id] = {"name": player_name, "score": 0, "duration": 0.0}
                    player_log_files[steam_id] = log_file  # Запоминаем файл, где игрок был найден
                    logger.info(f"[{log_file}] Игрок {player_name} ({steam_id}) подключился (новый формат).")

                # Обработка строк выхода (старый формат)
                logout_match_old = LOGOUT_PATTERN_OLD.search(line)
                if logout_match_old:
                    steam_id = logout_match_old.group(1).strip()
                    if steam_id in players:
                        # Проверяем, соответствует ли файл тому, где игрок был найден онлайн
                        if player_log_files.get(steam_id) != log_file:
                            logger.debug(f"[{log_file}] Игрок с ID {steam_id} вышел из другого файла. Пропускаем.")
                            continue

                        player_name = players[steam_id]["name"]
                        del players[steam_id]
                        del player_log_files[steam_id]  # Удаляем запись о файле
                        logger.info(f"[{log_file}] Игрок {player_name} ({steam_id}) отключился (старый формат).")
                    else:
                        logger.warning(f"[{log_file}] Ошибка: Попытка выхода неизвестного игрока с ID {steam_id}.")

                # Обработка строк выхода (новый формат)
                logout_match_new = LOGOUT_PATTERN_NEW.search(line)
                if logout_match_new:
                    steam_id = logout_match_new.group(1).strip()
                    if steam_id in players:
                        # Проверяем, соответствует ли файл тому, где игрок был найден онлайн
                        if player_log_files.get(steam_id) != log_file:
                            logger.debug(f"[{log_file}] Игрок с ID {steam_id} вышел из другого файла. Пропускаем.")
                            continue

                        player_name = players[steam_id]["name"]
                        del players[steam_id]
                        del player_log_files[steam_id]  # Удаляем запись о файле
                        logger.info(f"[{log_file}] Игрок {player_name} ({steam_id}) отключился (новый формат).")
                    else:
                        logger.warning(f"[{log_file}] Ошибка: Попытка выхода неизвестного игрока с ID {steam_id}.")

    except UnicodeDecodeError as e:
        logger.error(f"Ошибка декодирования файла {log_file}: {e}")


def block_ip(ip_address):
    """
    Блокирует IP-адрес с помощью команды netsh.
    """
    command = f'netsh advfirewall firewall add rule name="Block Specific IP {ip_address}" dir=in action=block remoteip={ip_address}'
    try:
        subprocess.run(command, shell=True, check=True)
        logger.info(f"IP-адрес {ip_address} успешно заблокирован.")
    except subprocess.CalledProcessError as e:
        logger.error(f"Ошибка при блокировке IP-адреса {ip_address}: {e}")