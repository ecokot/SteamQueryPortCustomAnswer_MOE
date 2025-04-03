import asyncio
import re
import asyncio_dgram
from handlers import handle_info_query, handle_challenge_query, handle_player_query
from log_parser import parse_log
from logger_config import get_logger
from player_handler import  PlayerHandler

# Инициализация логгера
logger = get_logger()

ph = PlayerHandler()

class QueryServer:
    def __init__(self, server_ip, query_port, log_files):
        self.server_ip = server_ip
        self.query_port = query_port
        self.log_files = log_files
        self.challenge_numbers = {}
        self.players = {}  # Словарь для хранения данных о текущих игроках
        self.player_log_files = {}  # Словарь для отслеживания файлов, где игроки онлайн
        logger.info(f"Сервер инициализирован. IP: {server_ip}, Порт: {query_port}")

    async def main(self):
        # Запуск задач для парсинга логов
        logger.info("Запуск задач для парсинга логов...")
        for log_file in self.log_files:
            asyncio.create_task(parse_log(log_file))

        # Ожидание входящих UDP-запросов
        logger.info(f"Ожидание запросов на порту {self.query_port}...")
        stream = await asyncio_dgram.bind((self.server_ip, self.query_port))

        while True:
            try:
                data, addr = await stream.recv()
                logger.debug(f"Получен запрос от {addr}: {data}")

                # Определяем тип запроса и вызываем соответствующий обработчик
                response = await self.route_request(data, addr)

                if response:
                    await stream.send(response, addr)
                    logger.debug(f"Отправлен ответ клиенту {addr}")
                else:
                    logger.warning("Некорректный запрос.")

            except Exception as e:
                logger.error(f"Произошла ошибка: {e}")

    async def route_request(self, data, addr):
        """
        Определяет тип запроса и передает его соответствующему обработчику.
        """
        # Проверяем, является ли запрос A2S_INFO
        info_query_pattern = re.compile(rb'^\xFF\xFF\xFF\xFFTSource Engine Query\x00$')
        if info_query_pattern.match(data):
            return await handle_info_query(data, addr, ph.get_online_players())

        # Проверяем, является ли запрос A2S_SERVERQUERY_GETCHALLENGE
        challenge_query_pattern = re.compile(rb'^\xFF\xFF\xFF\xFFU\x00\x00\x00\x00$')
        if challenge_query_pattern.match(data):
            return await handle_challenge_query(data, addr, self.challenge_numbers)

        # Проверяем, является ли запрос A2S_PLAYER
        player_query_pattern = re.compile(rb'^\xFF\xFF\xFF\xFF[UV](.{4})$')
        if player_query_pattern.match(data):
            return await handle_player_query(data, addr, self.challenge_numbers, ph.get_online_players())

        # Если запрос не соответствует ни одному из шаблонов
        logger.warning(f"Некорректный запрос от {addr}: {data}")
        return None