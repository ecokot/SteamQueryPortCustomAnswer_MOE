from datetime import datetime, timedelta
from collections import defaultdict
import json
import os
from logger_config import get_logger
import subprocess
import asyncio

# Инициализация логгера
logger = get_logger()

BLOCKED_IPS_FILE = "blocked_ips.json"  # Файл для хранения заблокированных IP


def load_blocked_ips():
    """
    Загружает список заблокированных IP из файла JSON.
    """
    if os.path.exists(BLOCKED_IPS_FILE):
        try:
            with open(BLOCKED_IPS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            logger.error(f"Ошибка при загрузке заблокированных IP: {e}")
            return {}
    return {}


def save_blocked_ips(blocked_ips):
    """
    Сохраняет список заблокированных IP в файл JSON.
    """
    try:
        with open(BLOCKED_IPS_FILE, "w", encoding="utf-8") as f:
            json.dump(blocked_ips, f, indent=4)
    except Exception as e:
        logger.error(f"Ошибка при сохранении заблокированных IP: {e}")


def block_ip(ip_address):
    """
    Блокирует IP-адрес с помощью команды netsh.
    """
    command = f'netsh advfirewall firewall add rule name="Block Specific IP {ip_address}" dir=in action=block remoteip={ip_address}'
    try:
        # subprocess.run(command, shell=True, check=True)  # Раскомментируйте, если требуется реальная блокировка
        logger.info(f"IP-адрес {ip_address} успешно заблокирован.")
    except subprocess.CalledProcessError as e:
        logger.error(f"Ошибка при блокировке IP-адреса {ip_address}: {e}")


class DDOSProtection:
    def __init__(self, threshold, interval):
        """
        Инициализация защиты от DDoS.
        :param threshold: Максимальное количество запросов за интервал.
        :param interval: Интервал времени (в секундах).
        """
        self.threshold = threshold
        self.interval = interval
        self.ip_data = defaultdict(list)  # {ip: [timestamp1, timestamp2, ...]}
        self.blocked_ips = load_blocked_ips()  # Загружаем заблокированные IP
        self.cleanup_task = None  # Задача для периодической очистки

    def start_cleanup_task(self, loop):
        """
        Запускает фоновую задачу для периодической очистки старых записей и разблокировки IP.
        """
        if self.cleanup_task is None or self.cleanup_task.done():
            self.cleanup_task = loop.create_task(self.periodic_cleanup())

    async def periodic_cleanup(self):
        """
        Периодическая очистка старых записей и разблокировка IP.
        """
        while True:
            try:
                await asyncio.sleep(10)  # Очистка каждые 10 секунд
                current_time = datetime.now()

                # Очистка старых записей
                for ip in list(self.ip_data.keys()):
                    self.cleanup_old_requests(ip, current_time)

                # Разблокировка IP по истечении времени
                self.unblock_old_ips(current_time)
                save_blocked_ips(self.blocked_ips)  # Сохраняем обновленный список заблокированных IP

            except asyncio.CancelledError:
                logger.info("Задача периодической очистки остановлена.")
                break

    def process_ip(self, ip_address, timestamp):
        """
        Обрабатывает поступивший IP-адрес и временную метку.
        """
        # Преобразуем временную метку в объект datetime
        timestamp = datetime.strptime(timestamp, "%Y.%m.%d-%H.%M.%S:%f")

        # Добавляем временную метку в список для данного IP
        self.ip_data[ip_address].append(timestamp)

        # Очищаем старые записи (старше интервала)
        self.cleanup_old_requests(ip_address, timestamp)

        # Проверяем, превышает ли количество запросов порог
        if len(self.ip_data[ip_address]) > self.threshold:
            logger.warning(
                f"Обнаружен подозрительный IP: {ip_address} (попыток: {len(self.ip_data[ip_address])}). Блокировка...")
            self.block_and_save_ip(ip_address)
            del self.ip_data[ip_address]

    def cleanup_old_requests(self, ip_address, current_time):
        """
        Удаляет старые временные метки для IP-адреса.
        """
        threshold_time = current_time - timedelta(seconds=self.interval)
        self.ip_data[ip_address] = [t for t in self.ip_data[ip_address] if t > threshold_time]
        if not self.ip_data[ip_address]:
            del self.ip_data[ip_address]  # Удаляем IP, если нет актуальных записей

    def block_and_save_ip(self, ip_address):
        """
        Блокирует IP-адрес и сохраняет его в список заблокированных.
        """
        block_ip(ip_address)
        self.blocked_ips[ip_address] = datetime.now().isoformat()  # Сохраняем время блокировки
        save_blocked_ips(self.blocked_ips)  # Сохраняем сразу после блокировки

    def unblock_old_ips(self, current_time):
        """
        Разблокирует IP-адреса, заблокированные более одного дня назад.
        """
        one_day_ago = current_time - timedelta(days=1)
        for ip, blocked_time in list(self.blocked_ips.items()):
            try:
                blocked_time = datetime.fromisoformat(blocked_time)
                if blocked_time < one_day_ago:
                    logger.info(f"Разблокировка IP-адреса {ip} (время блокировки истекло).")
                    del self.blocked_ips[ip]
            except ValueError as e:
                logger.error(f"Ошибка при разблокировке IP {ip}: {e}")