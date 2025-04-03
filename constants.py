import re


# Паттерн для извлечения IP-адреса и временной метки
IP_TIMESTAMP_PATTERN = re.compile(
    r"\[(\d{4}\.\d{2}\.\d{2}-\d{2}\.\d{2}\.\d{2}:\d{3})\].*accepted from: (\d+\.\d+\.\d+\.\d+)"
)

# Регулярные выражения для парсинга строк
LOGIN_PATTERN_OLD = re.compile(r"PostLogin Account:\s*(\d+)")
JOIN_PATTERN_OLD = re.compile(r"Join succeeded:\s*([^\s]+)")
LOGOUT_PATTERN_OLD = re.compile(r"Logout Account:\s*(\d+)")

LOGIN_PATTERN_NEW = re.compile(r"ASGGameModeLobby::LobbyClientLogin NickName = ([^,]+), UniqueId = (\d+)")
LOGOUT_PATTERN_NEW = re.compile(r"ASGGameModeLobby::LobbyClientLogOut Account: (\d+)")

# Регулярное выражение для извлечения IP-адресов
IP_PATTERN = re.compile(r'accepted from: (\d+\.\d+\.\d+\.\d+):\d+')

# Параметры защиты от DDoS
DDOS_THRESHOLD = 50  # Максимальное количество попыток за интервал
DDOS_INTERVAL = 5    # Интервал проверки (в секундах)

UNIFIED_LOGIN_PATTERN = re.compile(
    r"(?:PostLogin Account:\s*(\d+))|"
    r"(?:ASGGameModeLobby::LobbyClientLogin NickName = ([^,]+), UniqueId = (\d+))"
)