import os
import asyncpg
from typing import Optional

# Инкапсуляция логики управления пулом соединений базы данных и поиска файлов.

DB_POOL: Optional[asyncpg.Pool] = None

async def init_db(dsn: str, max_conn: int) -> None:
    """
    Инициализация пула соединений PostgreSQL.
    Создание объекта пула и его сохранение в глобальном пространстве имен.
    """
    global DB_POOL
    DB_POOL = await asyncpg.create_pool(
        dsn=dsn,
        min_size=1,
        max_size=max_conn
    )

async def close_db() -> None:
    """
    Закрытие пула соединений.
    Освобождение системных ресурсов и обрыв активных сетевых сессий.
    """
    global DB_POOL
    if DB_POOL:
        await DB_POOL.close()
        DB_POOL = None

async def apply_migrations() -> None:
    """
    Исполнение миграций схемы базы данных при старте сервиса.
    Логика аналогична Golang-сервису: чтение 001_schema.sql и выполнение.
    """
    if DB_POOL is None:
        raise RuntimeError("database pool not initialized")

    try:
        # Чтение скрипта миграций через общий загрузчик
        schema = load_sql_file(os.path.join("migrations", "001_schema.sql"))
    except Exception as e:
        raise Exception(f"failed to load schema migration: {e}")

    async with DB_POOL.acquire() as conn:
        try:
            # Выполнение инструкций создания таблиц
            await conn.execute(schema)
            print("Successfully applied database migrations")
        except Exception as e:
            raise Exception(f"failed to apply schema migration: {e}")

def load_sql_file(filename: str) -> str:
    """
    Поиск и извлечение SQL-запроса из файловой системы.
    Реализация алгоритма сканирования директорий верхнего уровня для обнаружения пути sql/.
    """
    current_dir = os.getcwd()
    
    # Итеративный подъем по иерархии папок
    while True:
        sql_dir = os.path.join(current_dir, "sql")
        if os.path.isdir(sql_dir):
            file_path = os.path.join(sql_dir, filename)
            with open(file_path, "r", encoding="utf-8") as file:
                return file.read()
        
        parent_dir = os.path.dirname(current_dir)
        if parent_dir == current_dir:
            # Достижение корня файловой системы
            raise FileNotFoundError(f"sql file not found: {filename}")
        current_dir = parent_dir
