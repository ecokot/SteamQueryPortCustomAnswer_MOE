import struct
import random
from logger_config import get_logger

# Инициализация логгера
logger = get_logger()

async def handle_info_query(data, addr, players):
    """
    Обрабатывает запрос A2S_INFO.
    """
    logger.info(f"Получен корректный запрос A2S_INFO от {addr}")

    # Формируем ответ
    extra_data_flags = 0x80 | 0x10 | 0x20 | 0x01  # Флаги: порт, Steam ID, keywords, Game ID
    packed_port = struct.pack('<H', 6014)  # Порт сервера (16-битное целое, little-endian)
    steam_id = 90263762545778710
    packed_steam_id = struct.pack('<Q', steam_id)  # Steam ID (uint64, little-endian)
    game_id = 1794810
    packed_game_id = struct.pack('<Q', game_id)  # Game ID (uint64, little-endian)
    keywords = b'BUILDID:0,OWNINGID:90263762545778710,OWNINGNAME:[RU]Siberian MOE,SESSIONFLAGS:552,MATCHTIMEOUT_f:120.000000,GameMode_s:SG\x00'

    response = (
        b'\xFF\xFF\xFF\xFF' +  # Префикс ответа
        b'I' +                 # Тип ответа (A2S_INFO)
        b'\x11' +              # Версия протокола (17)
        b'[RU][PVE]Big Siberian MOE\x00' +  # Название сервера
        b'Map_Lobby\x00' +                  # Карта
        b'MOE\x00' +                        # Папка игры
        b'MOE\x00' +                        # Игра
        b'\x00\x00' +                       # ID игры (0)
        struct.pack('B', len(players)) +    # Игроки (текущее количество)
        b'\x64' +                           # Максимум игроков (100)
        b'\x00' +                           # Боты (0)
        b'd' +                              # Тип сервера ('d' для dedicated)
        b'w' +                              # Платформа ('w' для Windows)
        b'\x00' +                           # Пароль (password_protected)
        b'\x01' +                           # VAC (1 - включен, 0 - выключен)
        b'1.99\x00' +                       # Версия игры
        struct.pack('B', extra_data_flags) +  # Extra Data Flags
        packed_port +                         # Порт сервера (если установлен флаг 0x80)
        packed_steam_id +                     # Steam ID (если установлен флаг 0x10)
        keywords +                            # Keywords (если установлен флаг 0x20)
        packed_game_id                        # Game ID (если установлен флаг 0x01)
    )
    logger.debug(f"Отправлен ответ на запрос A2S_INFO: {response}")
    return response


async def handle_challenge_query(data, addr, challenge_numbers):
    """
    Обрабатывает запрос A2S_SERVERQUERY_GETCHALLENGE.
    """
    logger.info(f"Получен корректный запрос A2S_SERVERQUERY_GETCHALLENGE от {addr}")

    # Генерируем случайный challenge number
    challenge_number = random.randint(1, 2**32 - 1)
    packed_challenge_number = struct.pack('<I', challenge_number)  # Little-endian

    # Сохраняем challenge number для этого адреса
    challenge_numbers[addr] = challenge_number
    logger.info(f"Сгенерирован challenge number: {challenge_number}")

    # Формируем ответ
    response = b'\xFF\xFF\xFF\xFFA' + packed_challenge_number
    logger.debug(f"Отправлен ответ на запрос A2S_SERVERQUERY_GETCHALLENGE: {response}")
    return response


async def handle_player_query(data, addr, challenge_numbers, players):
    """
    Обрабатывает запрос A2S_PLAYER.
    """
    logger.info(f"Получен корректный запрос A2S_PLAYER от {addr}")

    # Извлекаем challenge number (последние 4 байта)
    challenge_number = data[-4:]
    received_challenge_number = struct.unpack('<I', challenge_number)[0]
    logger.debug(f"Challenge number: {received_challenge_number}")

    # Если challenge number не равен 0, проверяем его
    if received_challenge_number != 0:
        expected_challenge_number = challenge_numbers.get(addr)
        if expected_challenge_number is None or expected_challenge_number != received_challenge_number:
            logger.error(
                f"Некорректный challenge number: ожидался {expected_challenge_number}, получен {received_challenge_number}")
            return None

        # Удаляем challenge number из памяти после использования
        del challenge_numbers[addr]

    # Формируем ответ
    response = b'\xFF\xFF\xFF\xFFD' + struct.pack('B', len(players))  # Количество игроков
    for idx, (steam_id, player_data) in enumerate(players.items()):
        response += struct.pack('B', idx + 1)  # Идентификатор игрока
        response += player_data["name"].encode('utf-8') + b'\x00'  # Имя игрока
        response += struct.pack('<i', player_data["score"])  # Счет игрока (little-endian)
        response += struct.pack('<f', player_data["duration"])  # Время игры (little-endian)

    logger.debug(f"Отправлен ответ на запрос A2S_PLAYER: {response}")
    return response