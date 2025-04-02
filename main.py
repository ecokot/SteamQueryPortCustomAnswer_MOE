import asyncio
from query_server import QueryServer
from logger_config import get_logger

# Инициализация логгера
logger = get_logger()

# Конфигурация сервера
SERVER_IP = "192.168.1.3"
QUERY_PORT = 6014
LOG_FILES = [
    r"C:\moe\serv1\Myth of Empires Dedicated Server\MOE\Saved\Logs\tetst.log",
    "C:\\moe\\serv3\\Myth of Empires Dedicated Server\\MOE\\Saved\\Logs\\SceneServer_1007.log",
    "C:\\moe\\serv2\\Myth of Empires Dedicated Server\\MOE\\Saved\\Logs\\SceneServer_1006.log",
    "C:\\moe\\serv4\\Myth of Empires Dedicated Server\\MOE\\Saved\\Logs\\SceneServer_1008.log",
    "C:\\moe\\serv1\\Myth of Empires Dedicated Server\\MOE\\Saved\\Logs\\LobbyServer_70000.log"
]


async def main():
    logger.info("Запуск сервера...")
    server = QueryServer(SERVER_IP, QUERY_PORT, LOG_FILES)
    await server.main()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
