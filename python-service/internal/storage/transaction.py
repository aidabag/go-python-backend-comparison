import asyncio
import random
from typing import Callable, Any, Awaitable
from functools import wraps
from asyncpg.exceptions import SerializationError, DeadlockDetectedError

from internal.config.config import AppConfig
import internal.storage.storage as storage

# Реализация менеджера транзакций для обработки конфликтов конкурентного доступа.

def is_retryable_error(exc: Exception) -> bool:
    """Классификация исключений на предмет ошибок блокировки PostgreSQL."""
    if isinstance(exc, (SerializationError, DeadlockDetectedError)):
        return True
    
    err_str = str(exc).lower()
    return (
        "serialization" in err_str or
        "deadlock" in err_str or
        "could not serialize" in err_str or
        "40001" in err_str
    )

def with_retry_transaction(func: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
    """Декоратор транзакции с механизмом перезапуска и внедрением соединения."""
    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        if storage.DB_POOL is None:
            raise RuntimeError("database pool not initialized")
            
        max_retries = AppConfig.max_tx_retries
        last_err = None

        for attempt in range(max_retries):
            try:
                # Извлечение свободного соединения
                async with storage.DB_POOL.acquire() as conn:
                    # Инициализация контекста SQL-транзакции
                    async with conn.transaction():
                        # Выполнение функции бизнес-логики
                        return await func(conn, *args, **kwargs)
            except Exception as exc:
                last_err = exc
                
                # Исключение несовместимых ошибок из цикла
                if not is_retryable_error(exc):
                    raise exc
                
                # Применение паузы перед следующей итерацией
                if attempt < max_retries - 1:
                    base_delay = random.uniform(0.05, 0.2)
                    await asyncio.sleep(base_delay * (2 ** attempt))
                    
        raise RuntimeError(f"transaction failed after {max_retries} retries: {last_err}")
    
    return wrapper
