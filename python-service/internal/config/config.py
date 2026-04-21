import os
from dataclasses import dataclass

# Извлечение системных переменных окружения и их инкапсуляция в строгий типизированный датакласс.

@dataclass
class Config:
    """Спецификация параметров конфигурации сервиса."""
    db_host: str
    db_port: str
    db_user: str
    db_pass: str
    db_name: str
    db_pool_max_conn: int
    max_tx_retries: int
    service_port: str
    metrics_path: str

def load_config() -> Config:
    """
    Парсинг переменных окружения и формирование единого объекта конфигурации.
    Применение значений по умолчанию для инициализации в режиме локальной отладки.
    """
    return Config(
        db_host=os.getenv("DB_HOST", "localhost"),
        db_port=os.getenv("DB_PORT", "5432"),
        db_user=os.getenv("DB_USER", "postgres"),
        db_pass=os.getenv("DB_PASS", "postgres"),
        db_name=os.getenv("DB_NAME", "python_service"),
        db_pool_max_conn=int(os.getenv("DB_POOL_MAX_CONN", "5")),
        max_tx_retries=int(os.getenv("MAX_TX_RETRIES", "3")),
        service_port=os.getenv("SERVICE_PORT", "8080"),
        metrics_path=os.getenv("METRICS_PATH", "/metrics"),
    )

# Глобальный синглтон конфигурации для всего приложения
AppConfig = load_config()
