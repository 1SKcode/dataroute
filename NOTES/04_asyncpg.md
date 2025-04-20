# Полное руководство по AsyncPG: асинхронная работа с PostgreSQL

## Содержание
1. [Введение в AsyncPG](#введение-в-asyncpg)
2. [Установка и настройка](#установка-и-настройка)
3. [Основные концепции](#основные-концепции)
4. [Базовые операции](#базовые-операции)
5. [Транзакции](#транзакции)
6. [Пулы соединений](#пулы-соединений)
7. [Типы данных PostgreSQL](#типы-данных-postgresql)
8. [Работа с JSON и JSONB](#работа-с-json-и-jsonb)
9. [Отличия от синхронных драйверов](#отличия-от-синхронных-драйверов)
10. [Оптимизация производительности](#оптимизация-производительности)
11. [Интеграция с SQLAlchemy](#интеграция-с-sqlalchemy)
12. [Лучшие практики](#лучшие-практики)

## Введение в AsyncPG

AsyncPG — это высокопроизводительная библиотека для Python, которая обеспечивает доступ к базам данных PostgreSQL с использованием асинхронного программирования. Она разработана с нуля для максимальной производительности и полного использования преимуществ как асинхронного Python (asyncio), так и PostgreSQL.

### Ключевые особенности:

- **Высокая производительность**: AsyncPG значительно быстрее других драйверов PostgreSQL для Python
- **Нативная поддержка asyncio**: полная интеграция с асинхронным программированием в Python
- **Поддержка современных функций PostgreSQL**: JSON, JSONB, массивы, диапазоны и другие типы данных
- **Эффективные пулы соединений**: оптимальное управление соединениями для высоконагруженных приложений
- **Прямой доступ к бинарному протоколу PostgreSQL**: минимальные накладные расходы при обмене данными

## Установка и настройка

### Установка

```bash
pip install asyncpg
```

### Требования:

- Python 3.7 или выше
- PostgreSQL 9.5 или выше

### Базовая настройка

```python
import asyncio
import asyncpg

async def main():
    # Установка соединения
    conn = await asyncpg.connect(
        user='postgres',
        password='password',
        database='mydatabase',
        host='localhost',
        port=5432
    )
    
    # Выполнение запроса
    version = await conn.fetchval('SELECT version()')
    print(f"PostgreSQL version: {version}")
    
    # Закрытие соединения
    await conn.close()

# Запуск асинхронной функции
asyncio.run(main())
```

## Основные концепции

### Асинхронное программирование

AsyncPG основан на asyncio — фреймворке для асинхронного программирования в Python. Использование ключевых слов `async`/`await` позволяет писать неблокирующий код, что особенно важно для I/O-bound операций, таких как запросы к базе данных.

### Соединения и транзакции

AsyncPG предоставляет два основных объекта:
- **Connection** — представляет соединение с базой данных
- **Transaction** — представляет транзакцию в рамках соединения

### Подготовленные выражения

AsyncPG автоматически создает и кэширует подготовленные выражения, что повышает производительность при повторном выполнении запросов.

### Отличия от традиционных ORM

AsyncPG — это низкоуровневый драйвер, который не предоставляет ORM-функциональность. Он фокусируется на производительности и прямом взаимодействии с PostgreSQL.

## Базовые операции

### Подключение к базе данных

```python
import asyncio
import asyncpg

async def connect_to_db():
    conn = await asyncpg.connect(
        user='postgres',
        password='password',
        database='mydatabase',
        host='localhost'
    )
    return conn
```

### Выполнение запросов

AsyncPG предоставляет несколько методов для выполнения запросов:

#### execute — выполнить запрос без возврата данных

```python
async def create_table(conn):
    await conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        )
    ''')
```

#### fetch — получить все строки результата

```python
async def get_all_users(conn):
    rows = await conn.fetch('SELECT * FROM users')
    for row in rows:
        print(f"User: {row['name']}, Email: {row['email']}")
    return rows
```

#### fetchrow — получить одну строку результата

```python
async def get_user_by_id(conn, user_id):
    row = await conn.fetchrow('SELECT * FROM users WHERE id = $1', user_id)
    if row:
        print(f"Found user: {row['name']}")
    return row
```

#### fetchval — получить одно значение

```python
async def count_users(conn):
    count = await conn.fetchval('SELECT COUNT(*) FROM users')
    print(f"Total users: {count}")
    return count
```

### Параметризованные запросы

PostgreSQL использует $1, $2, ... для обозначения параметров:

```python
async def add_user(conn, name, email):
    user_id = await conn.fetchval(
        'INSERT INTO users(name, email) VALUES($1, $2) RETURNING id',
        name, email
    )
    return user_id
```

### Выполнение нескольких запросов

```python
async def multiple_operations(conn):
    # Создаем новую таблицу
    await conn.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id),
            title TEXT NOT NULL,
            content TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Добавляем пользователя
    user_id = await conn.fetchval(
        'INSERT INTO users(name, email) VALUES($1, $2) RETURNING id',
        'John Doe', 'john@example.com'
    )
    
    # Добавляем пост для пользователя
    post_id = await conn.fetchval(
        'INSERT INTO posts(user_id, title, content) VALUES($1, $2, $3) RETURNING id',
        user_id, 'My First Post', 'Hello, world!'
    )
    
    return user_id, post_id
```

## Транзакции

### Базовое использование транзакций

```python
async def transfer_money(conn, from_account, to_account, amount):
    async with conn.transaction():
        # Снимаем деньги с одного счета
        await conn.execute(
            'UPDATE accounts SET balance = balance - $1 WHERE id = $2',
            amount, from_account
        )
        
        # Добавляем деньги на другой счет
        await conn.execute(
            'UPDATE accounts SET balance = balance + $1 WHERE id = $2',
            amount, to_account
        )
```

### Вложенные транзакции

AsyncPG поддерживает вложенные транзакции с помощью точек сохранения (savepoints):

```python
async def complex_operation(conn):
    async with conn.transaction():
        # Внешняя транзакция
        await conn.execute("INSERT INTO logs(message) VALUES('Starting operation')")
        
        try:
            async with conn.transaction():
                # Вложенная транзакция
                await conn.execute("UPDATE items SET status = 'processing' WHERE id = 1")
                # Ошибка в вложенной транзакции откатит только её
                raise Exception("Something went wrong")
        except Exception:
            await conn.execute("INSERT INTO logs(message) VALUES('Inner transaction failed')")
        
        # Внешняя транзакция продолжается
        await conn.execute("INSERT INTO logs(message) VALUES('Operation completed with issues')")
```

### Уровни изоляции транзакций

AsyncPG поддерживает все уровни изоляции транзакций PostgreSQL:

```python
import asyncpg

async def serializable_transaction(conn):
    tr = conn.transaction(isolation='serializable')
    await tr.start()
    try:
        # Выполняем операции с высоким уровнем изоляции
        await conn.execute("UPDATE accounts SET balance = balance - 100 WHERE id = 1")
        await conn.execute("INSERT INTO transactions(account_id, amount) VALUES(1, -100)")
        await tr.commit()
    except Exception:
        await tr.rollback()
        raise
```

## Пулы соединений

Для веб-приложений и других многопользовательских систем рекомендуется использовать пулы соединений.

### Создание пула

```python
import asyncpg
import asyncio

async def init_db():
    # Создание пула с 10 соединениями
    pool = await asyncpg.create_pool(
        user='postgres',
        password='password',
        database='mydatabase',
        host='localhost',
        min_size=5,    # Минимальное количество соединений
        max_size=20    # Максимальное количество соединений
    )
    return pool
```

### Использование пула

```python
async def get_user_data(pool, user_id):
    async with pool.acquire() as conn:
        return await conn.fetchrow('SELECT * FROM users WHERE id = $1', user_id)

async def main():
    pool = await init_db()
    try:
        # Одновременное выполнение множества запросов
        tasks = [get_user_data(pool, i) for i in range(1, 11)]
        results = await asyncio.gather(*tasks)
        
        for user in results:
            if user:
                print(f"User: {user['name']}")
    finally:
        # Закрытие пула при завершении
        await pool.close()
```

### Настройка таймаутов и повторных попыток

```python
pool = await asyncpg.create_pool(
    dsn='postgresql://postgres:password@localhost/mydatabase',
    min_size=5,
    max_size=20,
    max_queries=50000,        # Максимальное количество запросов на соединение
    max_inactive_connection_lifetime=300.0,  # 5 минут
    timeout=10.0,             # Таймаут ожидания соединения из пула
    command_timeout=60.0,     # Таймаут выполнения команды
    statement_cache_size=1000  # Размер кэша для подготовленных выражений
)
```

## Типы данных PostgreSQL

AsyncPG автоматически конвертирует типы данных между PostgreSQL и Python.

### Базовые соответствия типов

| PostgreSQL            | Python                                |
|-----------------------|---------------------------------------|
| integer, bigint       | int                                   |
| real, double precision| float                                 |
| bool                  | bool                                  |
| varchar, text         | str                                   |
| bytea                 | bytes                                 |
| date                  | datetime.date                         |
| time                  | datetime.time                         |
| timestamp             | datetime.datetime                     |
| timestamptz           | datetime.datetime с timezone          |
| interval              | datetime.timedelta                    |
| uuid                  | UUID                                  |
| json, jsonb           | dict, list, и т.д.                    |
| array                 | list                                  |

### Работа с массивами PostgreSQL

```python
async def array_example(conn):
    # Создание таблицы с массивом
    await conn.execute('''
        CREATE TABLE IF NOT EXISTS items (
            id SERIAL PRIMARY KEY,
            name TEXT,
            tags TEXT[]
        )
    ''')
    
    # Вставка данных с массивом
    await conn.execute(
        'INSERT INTO items(name, tags) VALUES($1, $2)',
        'Laptop', ['electronics', 'computer', 'gadget']
    )
    
    # Выборка с фильтрацией по элементу массива
    rows = await conn.fetch(
        'SELECT * FROM items WHERE $1 = ANY(tags)',
        'electronics'
    )
    
    return rows
```

### Пользовательские типы и enum

```python
async def enum_example(conn):
    # Создание enum типа
    await conn.execute('''
        DO $$ BEGIN
            CREATE TYPE user_status AS ENUM ('active', 'inactive', 'pending');
        EXCEPTION
            WHEN duplicate_object THEN NULL;
        END $$;
    ''')
    
    # Создание таблицы с enum
    await conn.execute('''
        CREATE TABLE IF NOT EXISTS accounts (
            id SERIAL PRIMARY KEY,
            username TEXT NOT NULL,
            status user_status NOT NULL DEFAULT 'pending'
        )
    ''')
    
    # Вставка данных с enum
    await conn.execute(
        'INSERT INTO accounts(username, status) VALUES($1, $2)',
        'johndoe', 'active'
    )
    
    # Выборка данных
    row = await conn.fetchrow(
        'SELECT * FROM accounts WHERE username = $1',
        'johndoe'
    )
    
    # AsyncPG автоматически преобразует enum в строку
    print(f"User status: {row['status']}")  # User status: active
```

## Работа с JSON и JSONB

PostgreSQL предоставляет мощную поддержку JSON и JSONB. AsyncPG автоматически преобразует эти типы в Python-объекты.

### Сохранение и извлечение JSON

```python
async def json_example(conn):
    # Создание таблицы с JSONB
    await conn.execute('''
        CREATE TABLE IF NOT EXISTS user_profiles (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id),
            data JSONB
        )
    ''')
    
    # Вставка данных
    user_data = {
        'preferences': {
            'theme': 'dark',
            'notifications': True
        },
        'social': {
            'twitter': '@johndoe',
            'github': 'johndoe'
        }
    }
    
    await conn.execute(
        'INSERT INTO user_profiles(user_id, data) VALUES($1, $2)',
        1, user_data  # Автоматическое преобразование dict в JSONB
    )
    
    # Чтение данных
    row = await conn.fetchrow(
        'SELECT * FROM user_profiles WHERE user_id = $1',
        1
    )
    
    # data автоматически преобразуется обратно в dict
    print(f"User theme: {row['data']['preferences']['theme']}")
```

### Запросы с JSON-полями

```python
async def search_by_json(conn, theme, social_network):
    # Поиск пользователей с определенной темой
    theme_users = await conn.fetch(
        "SELECT user_id FROM user_profiles WHERE data->'preferences'->>'theme' = $1",
        theme
    )
    
    # Поиск пользователей с указанной социальной сетью
    social_users = await conn.fetch(
        "SELECT user_id, data->'social'->$1 as username FROM user_profiles WHERE data->'social'->$1 IS NOT NULL",
        social_network
    )
    
    return theme_users, social_users
```

### Обновление JSON-полей

```python
async def update_preferences(conn, user_id, theme):
    # Обновление темы в JSON-структуре
    await conn.execute('''
        UPDATE user_profiles 
        SET data = jsonb_set(data, '{preferences,theme}', $1::jsonb, true)
        WHERE user_id = $2
    ''', json.dumps(theme), user_id)
```

## Отличия от синхронных драйверов

### Сравнение с psycopg2 и другими синхронными драйверами

#### 1. Асинхронная природа

- **AsyncPG**: Неблокирующие операции с использованием `async`/`await`
- **Psycopg2**: Блокирующие операции, которые останавливают выполнение программы

#### 2. Производительность

- **AsyncPG**: Оптимизирован для высокой производительности, использует бинарный протокол
- **Psycopg2**: Хорошая производительность, но уступает AsyncPG в многопоточных сценариях

#### 3. Синтаксис параметров

- **AsyncPG**: Использует `$1`, `$2`, ... для параметров
  ```python
  await conn.fetch('SELECT * FROM users WHERE id = $1', user_id)
  ```

- **Psycopg2**: Использует `%s` или именованные параметры
  ```python
  cur.execute('SELECT * FROM users WHERE id = %s', (user_id,))
  # или
  cur.execute('SELECT * FROM users WHERE id = %(id)s', {'id': user_id})
  ```

#### 4. Получение результатов

- **AsyncPG**:
  ```python
  rows = await conn.fetch('SELECT * FROM users')
  row = await conn.fetchrow('SELECT * FROM users LIMIT 1')
  value = await conn.fetchval('SELECT COUNT(*) FROM users')
  ```

- **Psycopg2**:
  ```python
  cur.execute('SELECT * FROM users')
  rows = cur.fetchall()
  
  cur.execute('SELECT * FROM users LIMIT 1')
  row = cur.fetchone()
  
  cur.execute('SELECT COUNT(*) FROM users')
  value = cur.fetchone()[0]
  ```

#### 5. Транзакции

- **AsyncPG**: Использует контекстный менеджер с `async with`
  ```python
  async with conn.transaction():
      # операции
  ```

- **Psycopg2**: Традиционный подход или контекстный менеджер
  ```python
  conn.begin()
  try:
      # операции
      conn.commit()
  except:
      conn.rollback()
  
  # или
  with conn:
      with conn.cursor() as cur:
          # операции
  ```

### Преимущества асинхронного подхода

1. **Масштабируемость**: Асинхронный код может обрабатывать гораздо больше одновременных соединений с меньшими накладными расходами.

2. **Эффективность использования ресурсов**: Вместо блокировки потока во время ожидания I/O операций, ваше приложение может выполнять другие задачи.

3. **Ответная реакция**: Асинхронные веб-приложения могут обрабатывать больше запросов без увеличения времени отклика.

4. **Производительность**: AsyncPG до 3-5 раз быстрее многих других драйверов PostgreSQL для Python.

### Примеры процессов, которые выигрывают от асинхронности

```python
import asyncio
import asyncpg
import time

async def measure_sync_vs_async():
    # Подключение к БД
    pool = await asyncpg.create_pool(
        user='postgres',
        password='password',
        database='test',
        host='localhost'
    )
    
    # Имитация задержки в БД
    await pool.execute('''
        CREATE OR REPLACE FUNCTION pg_sleep_random() 
        RETURNS void AS $$
        BEGIN
            PERFORM pg_sleep(random() * 0.1);
        END;
        $$ LANGUAGE plpgsql;
    ''')
    
    # Синхронный подход (последовательные запросы)
    start = time.time()
    for i in range(100):
        await pool.execute('SELECT pg_sleep_random()')
    sync_time = time.time() - start
    print(f"Sequential queries: {sync_time:.2f} seconds")
    
    # Асинхронный подход (параллельные запросы)
    start = time.time()
    tasks = [pool.execute('SELECT pg_sleep_random()') for _ in range(100)]
    await asyncio.gather(*tasks)
    async_time = time.time() - start
    print(f"Parallel queries: {async_time:.2f} seconds")
    print(f"Speedup: {sync_time / async_time:.2f}x")
    
    await pool.close()

# Результаты:
# Sequential queries: 5.04 seconds
# Parallel queries: 0.15 seconds
# Speedup: 33.60x
```

## Оптимизация производительности

### Стратегии оптимизации

#### 1. Используйте пулы соединений оптимального размера

```python
pool = await asyncpg.create_pool(
    dsn='postgresql://postgres:password@localhost/mydatabase',
    min_size=10,  # Должно соответствовать минимальной нагрузке
    max_size=10 * cpu_count,  # Пример: 10 соединений на ядро CPU
)
```

#### 2. Минимизируйте число запросов

```python
# Неоптимально: много отдельных запросов
async def get_user_with_posts_unoptimized(pool, user_id):
    async with pool.acquire() as conn:
        user = await conn.fetchrow('SELECT * FROM users WHERE id = $1', user_id)
        if not user:
            return None
        posts = await conn.fetch('SELECT * FROM posts WHERE user_id = $1', user_id)
        comments = []
        for post in posts:
            post_comments = await conn.fetch('SELECT * FROM comments WHERE post_id = $1', post['id'])
            comments.extend(post_comments)
        return {'user': user, 'posts': posts, 'comments': comments}

# Оптимизировано: один запрос с JOIN
async def get_user_with_posts_optimized(pool, user_id):
    async with pool.acquire() as conn:
        result = await conn.fetch('''
            SELECT 
                u.id AS user_id, u.name AS user_name, u.email AS user_email,
                p.id AS post_id, p.title AS post_title, p.content AS post_content,
                c.id AS comment_id, c.content AS comment_content, c.author AS comment_author
            FROM users u
            LEFT JOIN posts p ON u.id = p.user_id
            LEFT JOIN comments c ON p.id = c.post_id
            WHERE u.id = $1
        ''', user_id)
        
        if not result:
            return None
            
        # Обработка результата в структурированный формат...
        return process_result(result)
```

#### 3. Используйте batch-операции

```python
# Медленно: отдельные INSERT
async def add_users_slow(pool, users):
    async with pool.acquire() as conn:
        for user in users:
            await conn.execute(
                'INSERT INTO users(name, email) VALUES($1, $2)',
                user['name'], user['email']
            )

# Быстро: используем executemany
async def add_users_fast(pool, users):
    async with pool.acquire() as conn:
        await conn.executemany(
            'INSERT INTO users(name, email) VALUES($1, $2)',
            [(u['name'], u['email']) for u in users]
        )
```

#### 4. Используйте подготовленные выражения для повторяющихся запросов

```python
async def prepare_statements(conn):
    # Подготовка выражения
    get_user_stmt = await conn.prepare('SELECT * FROM users WHERE id = $1')
    
    # Многократное использование
    user1 = await get_user_stmt.fetchrow(1)
    user2 = await get_user_stmt.fetchrow(2)
```

#### 5. Кэширование запросов

```python
import functools
import asyncio

def async_lru_cache(maxsize=128, ttl=3600):
    """Простая реализация кэширования для асинхронных функций с TTL"""
    cache = {}
    
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            key = str(args) + str(kwargs)
            if key in cache:
                result, timestamp = cache[key]
                if time.time() - timestamp < ttl:
                    return result
            
            result = await func(*args, **kwargs)
            cache[key] = (result, time.time())
            
            # Очистка кэша, если он слишком велик
            if len(cache) > maxsize:
                oldest_key = min(cache.items(), key=lambda x: x[1][1])[0]
                del cache[oldest_key]
                
            return result
        return wrapper
    return decorator

# Использование
@async_lru_cache(maxsize=100, ttl=60)  # Кэш на 60 секунд
async def get_popular_products(pool, category_id):
    async with pool.acquire() as conn:
        return await conn.fetch(
            'SELECT * FROM products WHERE category_id = $1 ORDER BY views DESC LIMIT 10',
            category_id
        )
```

## Интеграция с SQLAlchemy

SQLAlchemy 1.4+ и 2.0+ предоставляют асинхронный API, который можно использовать с AsyncPG.

### Настройка SQLAlchemy с AsyncPG

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker

# Определение моделей
Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)

# Создание асинхронного движка с AsyncPG
engine = create_async_engine(
    "postgresql+asyncpg://postgres:password@localhost/mydatabase",
    echo=True,  # SQL-логирование
)

# Создание асинхронной фабрики сессий
async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)
```

### Выполнение запросов

```python
from sqlalchemy.future import select

async def get_user_by_email(email):
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.email == email)
        )
        return result.scalars().first()

async def create_user(name, email):
    async with async_session() as session:
        async with session.begin():
            user = User(name=name, email=email)
            session.add(user)
            # Транзакция будет автоматически зафиксирована
        return user

async def update_user(user_id, **kwargs):
    async with async_session() as session:
        async with session.begin():
            user = await session.get(User, user_id)
            if user:
                for key, value in kwargs.items():
                    setattr(user, key, value)
        return user
```

### AsyncPG с SQLAlchemy Core

```python
from sqlalchemy import Table, Column, Integer, String, MetaData
from sqlalchemy.ext.asyncio import create_async_engine

# Определение метаданных
metadata = MetaData()

users = Table(
    'users', metadata,
    Column('id', Integer, primary_key=True),
    Column('name', String),
    Column('email', String)
)

# Создание движка
engine = create_async_engine('postgresql+asyncpg://postgres:password@localhost/mydatabase')

# Создание таблиц
async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(metadata.create_all)

# Выполнение запроса
async def get_all_users():
    async with engine.connect() as conn:
        result = await conn.execute(users.select())
        return result.fetchall()
```

## Лучшие практики

### 1. Правильно закрывайте соединения

```python
async def example():
    # С использованием контекстного менеджера
    async with asyncpg.connect(dsn) as conn:
        # Соединение автоматически закроется
        await conn.execute("...")
    
    # Без контекстного менеджера
    conn = await asyncpg.connect(dsn)
    try:
        await conn.execute("...")
    finally:
        await conn.close()
```

### 2. Используйте транзакции правильно

```python
async def example():
    async with pool.acquire() as conn:
        async with conn.transaction():
            # Все операции в одной транзакции
            await conn.execute("UPDATE accounts SET balance = balance - 100 WHERE id = 1")
            await conn.execute("UPDATE accounts SET balance = balance + 100 WHERE id = 2")
```

### 3. Обрабатывайте исключения

```python
from asyncpg.exceptions import PostgresError

async def safe_operation(pool, user_id, amount):
    try:
        async with pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute(
                    "UPDATE accounts SET balance = balance - $1 WHERE user_id = $2",
                    amount, user_id
                )
                # Другие операции...
    except PostgresError as e:
        print(f"Database error: {e}")
        # Логирование, обработка ошибки...
        return False
    return True
```

### 4. Ограничивайте время выполнения запросов

```python
async def query_with_timeout(pool, query, *args, timeout=5.0):
    try:
        async with pool.acquire() as conn:
            return await asyncio.wait_for(
                conn.fetch(query, *args),
                timeout=timeout
            )
    except asyncio.TimeoutError:
        print(f"Query timed out after {timeout} seconds: {query}")
        # Обработка таймаута...
        return None
```

### 5. Используйте миграции

```python
# Пример использования Alembic с AsyncPG
# В alembic/env.py:

from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine

# Функция для асинхронного запуска миграций
async def run_migrations_online():
    connectable = create_async_engine(
        "postgresql+asyncpg://postgres:password@localhost/mydatabase"
    )
    
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

# Запуск миграций используя asyncio
def run_async_migrations():
    asyncio.run(run_migrations_online())
```

### 6. Мониторинг и логирование

```python
import logging
import time

async def logged_query(pool, query, *args):
    start_time = time.time()
    try:
        async with pool.acquire() as conn:
            result = await conn.fetch(query, *args)
            
        duration = time.time() - start_time
        if duration > 1.0:  # Логирование медленных запросов (> 1 сек)
            logging.warning(f"Slow query ({duration:.2f}s): {query}")
        else:
            logging.debug(f"Query completed in {duration:.2f}s: {query}")
            
        return result
    except Exception as e:
        logging.error(f"Query error: {e}, query: {query}, args: {args}")
        raise
```

### 7. Соблюдайте асинхронные паттерны

```python
# Избегайте блокирующих операций в асинхронном коде
async def bad_practice(pool):
    async with pool.acquire() as conn:
        result = await conn.fetch("SELECT * FROM large_table")
        
        # Плохо: блокирующая операция в асинхронном коде
        time.sleep(1)  
        
        # Плохо: синхронный цикл для тяжелых операций
        processed_data = []
        for row in result:
            processed_data.append(process_row_heavy_computation(row))
        
        return processed_data

# Правильный подход
async def good_practice(pool):
    async with pool.acquire() as conn:
        result = await conn.fetch("SELECT * FROM large_table")
        
        # Хорошо: асинхронная задержка
        await asyncio.sleep(1)
        
        # Хорошо: выполнение тяжелых вычислений в пуле потоков
        loop = asyncio.get_event_loop()
        processed_data = await loop.run_in_executor(
            None,  # Использовать пул потоков по умолчанию
            lambda: [process_row_heavy_computation(row) for row in result]
        )
        
        return processed_data
```

## Заключение

AsyncPG является высокопроизводительной асинхронной библиотекой для работы с PostgreSQL, которая идеально подходит для современных приложений Python, особенно для веб-серверов и API с высокой нагрузкой.

Ключевые преимущества AsyncPG по сравнению с традиционными драйверами:

1. **Высокая производительность** благодаря оптимизированному бинарному протоколу и эффективной реализации
2. **Асинхронность**, которая позволяет обрабатывать гораздо больше одновременных запросов
3. **Современный API**, основанный на возможностях asyncio
4. **Полная поддержка типов данных PostgreSQL**, включая JSON, массивы и кастомные типы

Использование AsyncPG вместе с асинхронными фреймворками, такими как FastAPI, Starlette или Sanic, позволяет создавать высокопроизводительные и масштабируемые веб-приложения, которые эффективно используют ресурсы сервера. 