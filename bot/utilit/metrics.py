# bot/utilit/metrics.py
from prometheus_client import Counter, Histogram

# Счётчик успешных вызовов команды /start
start_command_counter = Counter(
    "bot_start_command_total",
    "Total number of /start commands handled"
)

# Гистограмма времени выполнения команды /start
start_command_duration = Histogram(
    "bot_start_command_duration_seconds",
    "Duration of /start command handling in seconds"
)

# Счётчик ошибок при обработке команды /start
start_command_errors = Counter(
    "bot_start_command_errors_total",
    "Total number of errors during /start command handling"
)
