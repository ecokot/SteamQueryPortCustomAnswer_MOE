import asyncio
import requests
from aiogram import Bot, Dispatcher, types
from logger_config import get_logger

# Инициализация логгера
logger = get_logger()

# Константы
STEAMCMD_API_URL = "https://api.steamcmd.net/v1/info/<APP_ID>"  # Замените <APP_ID> на ID вашего сервера
TELEGRAM_BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"  # Замените на токен вашего Telegram-бота
TELEGRAM_CHAT_ID = "YOUR_TELEGRAM_CHAT_ID"  # Замените на ID чата или канала

# Инициализация Telegram-бота
bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher(bot)

async def check_for_updates():
    """
    Проверяет наличие обновлений сервера через SteamCMD API.
    """
    try:
        response = requests.get(STEAMCMD_API_URL)
        response.raise_for_status()
        data = response.json()

        # Получаем текущую версию сервера
        current_version = data["data"]["<APP_ID>"]["buildid"]  # Замените <APP_ID> на ID вашего сервера
        logger.info(f"Текущая версия сервера: {current_version}")

        # Сравниваем с сохраненной версией (например, из файла или базы данных)
        last_known_version = load_last_known_version()
        if current_version != last_known_version:
            logger.info(f"Обнаружено новое обновление: {current_version}")
            await send_telegram_message(f"Новая версия сервера доступна: {current_version}")
            save_last_known_version(current_version)

    except Exception as e:
        logger.error(f"Ошибка при проверке обновлений: {e}")


def load_last_known_version():
    """
    Загружает последнюю известную версию сервера из файла.
    """
    try:
        with open("last_version.txt", "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        return None


def save_last_known_version(version):
    """
    Сохраняет текущую версию сервера в файл.
    """
    with open("last_version.txt", "w") as f:
        f.write(version)


async def send_telegram_message(message):
    """
    Отправляет сообщение в Telegram.
    """
    try:
        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        logger.info(f"Сообщение отправлено в Telegram: {message}")
    except Exception as e:
        logger.error(f"Ошибка при отправке сообщения в Telegram: {e}")


async def start_update_checker(interval=3600):
    """
    Запускает циклическую проверку обновлений.
    """
    while True:
        await check_for_updates()
        await asyncio.sleep(interval)


if __name__ == "__main__":
    # Запуск бота
    loop = asyncio.get_event_loop()
    loop.create_task(start_update_checker())
    loop.run_forever()