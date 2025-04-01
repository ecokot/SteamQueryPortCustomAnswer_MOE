import asyncio
from collections import defaultdict
import subprocess
import time
from logger_config import get_logger

# Инициализация логгера
logger = get_logger()

def block_ip(ip_address):
    """
    Блокирует IP-адрес с помощью команды netsh.
    """
    command = [
        'netsh', 'advfirewall', 'firewall', 'add', 'rule',
        f'name=Block Specific IP {ip_address}',
        'dir=in', 'action=block', f'remoteip={ip_address}'
    ]
    try:
        subprocess.run(command, check=True)
        logger.info(f"IP-адрес {ip_address} успешно заблокирован.")
    except subprocess.CalledProcessError as e:
        logger.error(f"Ошибка при блокировке IP-адреса {ip_address}: {e}")


async def monitor_ddos(log_file):
    """
    Мониторит логи на предмет подозрительной активности и блокирует IP-адреса.
    """
    ip_count = defaultdict(int)
    start_time = time.time()
    blocked_ips = set()

    with open(log_file, "r", encoding="utf-8", errors="replace") as f:
        f.seek(0, 2)  # Перемещаем указатель в конец файла

        while True:
            line = f.readline()
            if not line:
                await asyncio.sleep(0.1)  # Ждем новые строки
                continue

            # Анализируем IP-адреса
            match = IP_PATTERN.search(line)
            if match:
                ip_address = match.group(1)
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