import os
import logging
import sys
from logging.handlers import RotatingFileHandler

# Создание директории logs, если её нет
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)

# Формат логов с функцией и строкой
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(name)s - %(funcName)s - Line %(lineno)d - %(message)s"

# Создание логгера

logger = logging.getLogger("AaEdu")

logger.setLevel(logging.INFO)  # Уровень логирования

# Консольный обработчик
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(logging.Formatter(LOG_FORMAT))

# Файловый обработчик с ротацией (10MB, хранит 5 файлов)
file_handler = RotatingFileHandler(os.path.join(log_dir, "app.log"), maxBytes=10_000_000, backupCount=5,
                                   encoding="utf-8")
file_handler.setFormatter(logging.Formatter(LOG_FORMAT))

# Добавляем обработчики в логгер
logger.addHandler(console_handler)
logger.addHandler(file_handler)
