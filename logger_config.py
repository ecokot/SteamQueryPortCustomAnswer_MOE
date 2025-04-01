import logging
from logging.handlers import TimedRotatingFileHandler

# Глобальная переменная для хранения основного логгера
_main_logger = None
_error_logger = None


def get_logger():
    """
    Возвращает основной логгер для записи всех событий.
    """
    global _main_logger
    if _main_logger is None:
        _main_logger = logging.getLogger("CustomQueryPortAnswer")
        _main_logger.setLevel(logging.DEBUG)

        # Обработчик для записи в файл с ротацией (основной лог)
        file_handler = TimedRotatingFileHandler(
            "logs/server.log", when="midnight", interval=1, backupCount=7, encoding="utf-8"
        )
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        file_handler.setFormatter(file_formatter)

        # Обработчик для вывода в консоль
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        console_handler.setFormatter(console_formatter)

        # Добавляем обработчики к логгеру
        _main_logger.addHandler(file_handler)
        _main_logger.addHandler(console_handler)

    return _main_logger


def get_error_logger():
    """
    Возвращает логгер для записи ошибок.
    """
    global _error_logger
    if _error_logger is None:
        _error_logger = logging.getLogger("ErrorLogger")
        _error_logger.setLevel(logging.ERROR)

        # Обработчик для записи ошибок в файл
        error_handler = logging.FileHandler("logs/errors.log", encoding="utf-8")
        error_handler.setLevel(logging.ERROR)
        error_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        error_handler.setFormatter(error_formatter)

        # Добавляем обработчик к логгеру ошибок
        _error_logger.addHandler(error_handler)

    return _error_logger