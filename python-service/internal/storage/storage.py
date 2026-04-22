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
    pid = os.getpid()
    print(f"[PID {pid}] Initializing database pool (max_conn={max_conn})")
    DB_POOL = await asyncpg.create_pool(
        dsn=dsn,
        min_size=1,
        max_size=max_conn
    )
    print(f"[PID {pid}] Database pool initialized [ID: {id(DB_POOL)}]")

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
    # Исполнение миграций схемы базы данных при старте сервиса.
    if DB_POOL is None:
        raise RuntimeError("database pool not initialized")

    async with DB_POOL.acquire() as conn:
        try:
            # Выполнение инструкций создания таблиц
            schema = load_sql_file(os.path.join("migrations", "001_schema.sql"))
            await conn.execute(schema)
            print("Successfully applied database schema")
            
            # Выполнение инструкций наполнения данными
            seed = load_sql_file(os.path.join("migrations", "002_seed.sql"))
            await conn.execute(seed)
            print("Successfully applied database seeding")
        except Exception as e:
            raise Exception(f"failed to apply migrations: {e}")

# Кэш загруженных SQL-файлов для предотвращения блокирующего чтения с диска
_sql_cache: dict[str, str] = {}

def load_sql_file(filename: str) -> str:
    """
    Поиск и извлечение SQL-запроса из файловой системы.
    Результат кэшируется в оперативной памяти для устранения
    блокирующего ввода-вывода при повторных обращениях.
    """
    # Возврат закэшированного результата при наличии
    if filename in _sql_cache:
        return _sql_cache[filename]

    current_dir = os.getcwd()
    
    # Итеративный подъем по иерархии папок
    while True:
        sql_dir = os.path.join(current_dir, "sql")
        if os.path.isdir(sql_dir):
            file_path = os.path.join(sql_dir, filename)
            with open(file_path, "r", encoding="utf-8") as file:
                content = file.read()
                # Сохранение результата в кэш
                _sql_cache[filename] = content
                return content
        
        parent_dir = os.path.dirname(current_dir)
        if parent_dir == current_dir:
            # Достижение корня файловой системы
            raise FileNotFoundError(f"sql file not found: {filename}")
        current_dir = parent_dir

