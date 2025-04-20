# Полное руководство по SQLAlchemy с акцентом на PostgreSQL

## Содержание
1. [Введение в SQLAlchemy](#введение-в-sqlalchemy)
2. [Архитектура SQLAlchemy](#архитектура-sqlalchemy)
3. [Настройка соединения](#настройка-соединения)
4. [Определение моделей данных](#определение-моделей-данных)
5. [Операции CRUD](#операции-crud)
6. [Запросы](#запросы)
7. [Отношения между моделями](#отношения-между-моделями)
8. [Миграции с Alembic](#миграции-с-alembic)
9. [Специфические особенности PostgreSQL](#специфические-особенности-postgresql)
10. [Лучшие практики и оптимизация](#лучшие-практики-и-оптимизация)

## Введение в SQLAlchemy

SQLAlchemy — это библиотека для работы с базами данных в Python, которая предоставляет полноценный набор хорошо известных паттернов проектирования для эффективной и высокопроизводительной работы с базами данных. Она позволяет разработчикам работать на разных уровнях абстракции при взаимодействии с реляционными базами данных.

### Основные возможности SQLAlchemy:

- **ORM (Object-Relational Mapping)** — отображение классов Python на таблицы базы данных
- **Expression Language** — создание SQL-запросов с помощью Python-выражений
- **Core** — низкоуровневый интерфейс для взаимодействия с БД
- **Dialect** — система абстракции различий между базами данных
- **Интеграция с различными БД** — PostgreSQL, MySQL, SQLite, Oracle и другие

В этом руководстве мы сосредоточимся на версии SQLAlchemy 2.0, которая представляет собой значительное обновление библиотеки с новыми подходами к работе с асинхронными операциями и многими другими улучшениями.

## Архитектура SQLAlchemy

SQLAlchemy имеет двухуровневую архитектуру:

### Core (Ядро)

Низкоуровневый API, который включает:

- **Engine** — основной интерфейс для подключения к БД
- **Connection Pool** — пул соединений для эффективного использования ресурсов
- **Dialect** — адаптеры для различных типов баз данных
- **Schema/Types** — определение схемы и типов данных
- **SQL Expression Language** — построение SQL-запросов

### ORM (Object-Relational Mapper)

Высокоуровневый API, который включает:

- **Session** — ключевой интерфейс для работы с объектами
- **Mappings** — описание связей между объектами Python и таблицами БД
- **Query API** — высокоуровневые операции запросов
- **Relationship API** — определение отношений между объектами

## Установка и первые шаги

### Установка

```bash
# Базовая установка
pip install sqlalchemy

# Для PostgreSQL также нужен драйвер
pip install psycopg2-binary  # Для синхронной работы
# или
pip install asyncpg  # Для асинхронной работы с asyncio
```

### Настройка соединения

#### Синхронное соединение (Core)

```python
from sqlalchemy import create_engine, text

# Формат URL: postgresql://username:password@host:port/database
engine = create_engine('postgresql://postgres:password@localhost:5432/mydatabase')

# Проверка соединения
with engine.connect() as conn:
    result = conn.execute(text("SELECT version()"))
    print(result.scalar())
```

#### Синхронное соединение (ORM)

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine('postgresql://postgres:password@localhost:5432/mydatabase')
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Пример использования сессии
def get_user(user_id):
    db = SessionLocal()
    try:
        result = db.execute(text("SELECT * FROM users WHERE id = :id"), {"id": user_id})
        return result.fetchone()
    finally:
        db.close()
```

#### Асинхронное соединение (SQLAlchemy 2.0+)

```python
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Формат URL: postgresql+asyncpg://username:password@host:port/database
async_engine = create_async_engine('postgresql+asyncpg://postgres:password@localhost:5432/mydatabase')

AsyncSessionLocal = sessionmaker(
    async_engine, class_=AsyncSession, expire_on_commit=False
)

async def get_user_async(user_id):
    async with AsyncSessionLocal() as session:
        result = await session.execute(text("SELECT * FROM users WHERE id = :id"), {"id": user_id})
        return result.fetchone()
```

## Определение моделей данных

### Объявление базового класса

```python
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
import datetime

Base = declarative_base()
```

### Определение моделей

```python
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    hashed_password = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    def __repr__(self):
        return f"<User {self.username}>"

class Post(Base):
    __tablename__ = "posts"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    content = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    def __repr__(self):
        return f"<Post {self.title}>"
```

### Создание таблиц

```python
# Создание всех таблиц
Base.metadata.create_all(bind=engine)

# Создание отдельной таблицы
User.__table__.create(bind=engine)
```

## Операции CRUD

### Create (Создание)

```python
from sqlalchemy.orm import Session

def create_user(db: Session, username: str, email: str, password: str):
    new_user = User(username=username, email=email, hashed_password=password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)  # Обновляет объект значениями из БД (например, для получения id)
    return new_user

# Использование
with SessionLocal() as db:
    user = create_user(db, "johndoe", "john@example.com", "hashed_password")
    print(f"Created user ID: {user.id}")
```

### Read (Чтение)

```python
def get_user(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()

def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(User).offset(skip).limit(limit).all()

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

# Использование
with SessionLocal() as db:
    user = get_user(db, 1)
    if user:
        print(f"Found user: {user.username}")
```

### Update (Обновление)

```python
def update_user(db: Session, user_id: int, **kwargs):
    db.query(User).filter(User.id == user_id).update(kwargs)
    db.commit()
    return get_user(db, user_id)

# Использование
with SessionLocal() as db:
    updated_user = update_user(db, 1, username="newusername", is_active=False)
    print(f"Updated user: {updated_user.username}, active: {updated_user.is_active}")
```

### Delete (Удаление)

```python
def delete_user(db: Session, user_id: int):
    user = get_user(db, user_id)
    if user:
        db.delete(user)
        db.commit()
        return True
    return False

# Использование
with SessionLocal() as db:
    success = delete_user(db, 1)
    print(f"User deleted: {success}")
```

## Запросы

### Базовые запросы

```python
# Выбор всех пользователей
users = db.query(User).all()

# Выбор определенных полей
usernames = db.query(User.username, User.email).all()

# Фильтрация
active_users = db.query(User).filter(User.is_active == True).all()

# Сортировка
sorted_users = db.query(User).order_by(User.username).all()

# Ограничение результатов
users_page = db.query(User).offset(10).limit(5).all()

# Подсчет
user_count = db.query(User).count()
```

### Фильтры и условия

```python
from sqlalchemy import and_, or_, not_

# Комбинирование условий
users = db.query(User).filter(
    and_(
        User.username.like('%john%'),
        or_(
            User.email.endswith('@gmail.com'),
            User.email.endswith('@yahoo.com')
        ),
        not_(User.is_active == False)
    )
).all()

# Альтернативный синтаксис
users = db.query(User).filter(
    User.username.like('%john%'),
    (User.email.endswith('@gmail.com') | User.email.endswith('@yahoo.com')),
    User.is_active == True
).all()
```

### Сложные запросы

```python
from sqlalchemy import func, desc, asc, text

# Агрегатные функции
post_counts = db.query(
    User.username, 
    func.count(Post.id).label('post_count')
).join(
    Post, User.id == Post.user_id
).group_by(
    User.username
).order_by(
    desc('post_count')
).all()

# Подзапросы
from sqlalchemy import subquery

active_user_ids_subquery = db.query(User.id).filter(User.is_active == True).subquery()
posts_by_active_users = db.query(Post).filter(Post.user_id.in_(active_user_ids_subquery)).all()

# Сырой SQL
raw_result = db.execute(text("SELECT * FROM users WHERE username LIKE :pattern"), {"pattern": "%john%"})
for row in raw_result:
    print(row)
```

## Отношения между моделями

SQLAlchemy предоставляет мощные инструменты для управления отношениями между моделями.

### Типы отношений

- **One-to-Many** (один ко многим)
- **Many-to-One** (многие к одному)
- **One-to-One** (один к одному)
- **Many-to-Many** (многие ко многим)

### Примеры определения отношений

```python
from sqlalchemy.orm import relationship, backref

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    
    # Один ко многим: один пользователь имеет много постов
    posts = relationship("Post", back_populates="author", cascade="all, delete-orphan")

class Post(Base):
    __tablename__ = "posts"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    content = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    
    # Многие к одному: много постов принадлежат одному пользователю
    author = relationship("User", back_populates="posts")

# Таблица для связи многие-ко-многим
user_roles = Table('user_roles', Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id', ondelete="CASCADE"), primary_key=True),
    Column('role_id', Integer, ForeignKey('roles.id', ondelete="CASCADE"), primary_key=True)
)

class Role(Base):
    __tablename__ = "roles"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(30), unique=True)
    
    # Многие ко многим: многие роли принадлежат многим пользователям
    users = relationship("User", secondary=user_roles, back_populates="roles")

# Добавляем отношение многие-ко-многим в класс User
User.roles = relationship("Role", secondary=user_roles, back_populates="users")
```

### Работа с отношениями

```python
# Создание взаимосвязанных объектов
with SessionLocal() as db:
    new_user = User(username="alice", email="alice@example.com")
    new_post = Post(title="My First Post", content="Hello World!")
    
    # Связываем объекты
    new_user.posts.append(new_post)
    
    # Сохраняем только пользователя, пост сохранится автоматически благодаря каскадным операциям
    db.add(new_user)
    db.commit()

# Загрузка связанных объектов
with SessionLocal() as db:
    user = db.query(User).filter(User.username == "alice").first()
    
    # Доступ к связанным постам
    for post in user.posts:
        print(f"Post by {user.username}: {post.title}")
```

### Жадная загрузка (Eager Loading)

```python
from sqlalchemy.orm import joinedload, selectinload, subqueryload

# joinedload - используется для one-to-one и many-to-one
users = db.query(User).options(joinedload(User.posts)).all()

# selectinload - эффективен для коллекций (one-to-many, many-to-many)
users = db.query(User).options(selectinload(User.posts)).all()

# subqueryload - для вложенных коллекций
users = db.query(User).options(subqueryload(User.posts)).all()
```

## Миграции с Alembic

Alembic — это инструмент миграции баз данных, который работает с SQLAlchemy.

### Настройка Alembic

```bash
# Установка
pip install alembic

# Инициализация
alembic init migrations
```

### Настройка файла конфигурации

В файле `alembic.ini`:

```ini
sqlalchemy.url = postgresql://postgres:password@localhost:5432/mydatabase
```

В файле `migrations/env.py`:

```python
from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# Импорт моделей и метаданных
from myapp.models import Base
target_metadata = Base.metadata

# ... другой код ...
```

### Создание и применение миграций

```bash
# Создание новой миграции
alembic revision --autogenerate -m "create users table"

# Применение миграций
alembic upgrade head

# Откат миграции
alembic downgrade -1

# Получение информации о миграциях
alembic current
alembic history
```

### Пример миграции

```python
# migrations/versions/123456789abc_create_users_table.py
"""create users table

Revision ID: 123456789abc
Revises: 
Create Date: 2023-06-01 12:00:00

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '123456789abc'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=50), nullable=False),
        sa.Column('email', sa.String(length=100), nullable=False),
        sa.Column('hashed_password', sa.String(length=100), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('username')
    )
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)

def downgrade():
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_table('users')
```

## Специфические особенности PostgreSQL в SQLAlchemy

PostgreSQL имеет много уникальных типов данных и функций, которые SQLAlchemy поддерживает через свой диалект PostgreSQL.

### Специфические типы данных PostgreSQL

```python
from sqlalchemy.dialects.postgresql import (
    ARRAY, JSONB, UUID, ENUM, TSQUERY, TSVECTOR
)
import uuid

class Product(Base):
    __tablename__ = "products"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    description = Column(String)
    tags = Column(ARRAY(String))  # Массив строк
    metadata = Column(JSONB)  # JSON с индексированием
    status = Column(ENUM('active', 'inactive', 'pending', name='product_status_enum'))
    search_vector = Column(TSVECTOR)  # Полнотекстовый поиск
```

### Индексы PostgreSQL

```python
from sqlalchemy import Index, func

# B-tree индекс (стандартный)
Index('ix_users_username', User.username)

# GIN индекс для массивов и JSONB
Index('ix_products_tags', Product.tags, postgresql_using='gin')
Index('ix_products_metadata', Product.metadata, postgresql_using='gin')

# Индекс для полнотекстового поиска
Index('ix_products_search_vector', Product.search_vector, postgresql_using='gin')
```

### Полнотекстовый поиск

```python
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import TSVECTOR

# Определение столбца с индексом для поиска
class Article(Base):
    __tablename__ = "articles"
    
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    content = Column(String, nullable=False)
    search_vector = Column(TSVECTOR)

# Создание индекса
Index('ix_articles_search_vector', Article.search_vector, postgresql_using='gin')

# Выполнение поиска
def search_articles(db: Session, query: str):
    search_term = func.plainto_tsquery('russian', query)  # 'russian' - используемый словарь
    return db.query(Article).filter(Article.search_vector.op('@@')(search_term)).all()

# Обновление search_vector при изменении статьи
def update_search_vector(db: Session, article_id: int):
    # to_tsvector объединяет поля title и content для поиска
    vector_expr = func.to_tsvector(
        'russian',  # словарь
        func.concat_ws(' ', Article.title, Article.content)
    )
    db.query(Article).filter(Article.id == article_id).update(
        {Article.search_vector: vector_expr},
        synchronize_session=False
    )
    db.commit()
```

### Работа с JSON/JSONB

```python
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import func

class Preference(Base):
    __tablename__ = "preferences"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    settings = Column(JSONB, default={})

# Запросы с использованием JSONB
def get_users_with_theme(db: Session, theme: str):
    # Поиск пользователей, у которых в настройках theme = 'dark'
    return db.query(User).join(Preference).filter(
        Preference.settings.op('->')('theme').astext == theme
    ).all()

# Обновление части JSON
def update_user_theme(db: Session, user_id: int, theme: str):
    db.query(Preference).filter(Preference.user_id == user_id).update(
        {Preference.settings: func.jsonb_set(
            Preference.settings,
            '{theme}',
            f'"{theme}"',
            True
        )},
        synchronize_session=False
    )
    db.commit()
```

### Хранимые процедуры и функции

```python
from sqlalchemy import text

# Вызов функции PostgreSQL
def get_user_posts_count(db: Session, user_id: int):
    result = db.execute(
        text("SELECT count_user_posts(:user_id)"),
        {"user_id": user_id}
    )
    return result.scalar()

# Создание функции в БД с помощью Alembic
"""
def upgrade():
    op.execute('''
    CREATE OR REPLACE FUNCTION count_user_posts(p_user_id INT)
    RETURNS INT AS $$
    DECLARE
        post_count INT;
    BEGIN
        SELECT COUNT(*) INTO post_count FROM posts WHERE user_id = p_user_id;
        RETURN post_count;
    END;
    $$ LANGUAGE plpgsql;
    ''')

def downgrade():
    op.execute('DROP FUNCTION IF EXISTS count_user_posts(INT);')
"""
```

## Транзакции и блокировки

### Базовые транзакции

```python
# Использование транзакции
def transfer_points(db: Session, from_user_id: int, to_user_id: int, points: int):
    try:
        # Снимаем баллы с одного пользователя
        db.query(User).filter(User.id == from_user_id).update(
            {User.points: User.points - points}
        )
        
        # Добавляем баллы другому пользователю
        db.query(User).filter(User.id == to_user_id).update(
            {User.points: User.points + points}
        )
        
        # Фиксируем транзакцию
        db.commit()
        return True
    except Exception as e:
        # Откатываем изменения при ошибке
        db.rollback()
        print(f"Error: {e}")
        return False
```

### Блокировки для предотвращения ошибок параллелизма

```python
from sqlalchemy.orm import with_for_update

def update_user_points_safely(db: Session, user_id: int, delta: int):
    # SELECT FOR UPDATE блокирует строку до окончания транзакции
    user = db.query(User).with_for_update().filter(User.id == user_id).first()
    if not user:
        return False
    
    user.points += delta
    db.commit()
    return True
```

## Лучшие практики и оптимизация

### Оптимизация запросов

1. **Используйте базовые SQL-принципы оптимизации**
   - Создавайте индексы для часто запрашиваемых полей
   - Используйте пагинацию для больших результатов
   - Избегайте SELECT * и выбирайте только нужные поля

2. **Оптимизируйте загрузку связанных объектов**
   - Используйте joinedload/selectinload для предварительной загрузки
   - Избегайте проблемы N+1 запросов

3. **Правильно используйте сессии**
   - Минимизируйте время жизни сессии
   - Используйте pool_size параметр для настройки пула соединений

### Пример оптимизированного кода

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, selectinload

# Оптимизированное соединение
engine = create_engine(
    'postgresql://user:password@localhost:5432/db',
    pool_size=20,  # Размер пула соединений
    max_overflow=10,  # Максимальное число дополнительных соединений
    pool_timeout=30,  # Тайм-аут ожидания соединения
    pool_recycle=1800,  # Переподключение через 30 минут
)

# Оптимизированный запрос с пагинацией и предзагрузкой
def get_users_with_posts(db, page=1, page_size=20):
    offset = (page - 1) * page_size
    return db.query(User).options(
        selectinload(User.posts)
    ).offset(offset).limit(page_size).all()
```

### Рекомендации по работе с PostgreSQL

1. **Используйте нативные типы PostgreSQL** — они более эффективны для запросов и хранения
2. **Знакомьтесь с документацией PostgreSQL** — многие функции могут значительно упростить ваш код
3. **Мониторьте запросы с помощью EXPLAIN ANALYZE** — анализ запросов поможет выявить узкие места
4. **Используйте миграции** — они обеспечивают безопасное изменение схемы БД
5. **Регулярно обслуживайте базу данных (VACUUM, REINDEX)** — для поддержания производительности

### Шаблон работы с БД в веб-приложениях

```python
# Выделение операций с БД в отдельный слой репозитория
class UserRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, username, email, password):
        user = User(username=username, email=email, hashed_password=password)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def get_by_id(self, user_id):
        return self.db.query(User).filter(User.id == user_id).first()
    
    def update(self, user_id, **kwargs):
        self.db.query(User).filter(User.id == user_id).update(kwargs)
        self.db.commit()
        return self.get_by_id(user_id)
    
    def delete(self, user_id):
        user = self.get_by_id(user_id)
        if user:
            self.db.delete(user)
            self.db.commit()
            return True
        return False

# Использование в FastAPI
from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

app = FastAPI()

# Зависимость для получения сессии БД
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Эндпоинт с использованием репозитория
@app.get("/users/{user_id}")
def read_user(user_id: int, db: Session = Depends(get_db)):
    repo = UserRepository(db)
    user = repo.get_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user
```

## Заключение

SQLAlchemy — это мощный и гибкий инструмент для работы с базами данных в Python. Он предоставляет высокоуровневый ORM и низкоуровневый Core API, что позволяет выбрать подходящий уровень абстракции для вашего проекта.

PostgreSQL, как самая продвинутая и функциональная открытая СУБД, получает особенно хорошую поддержку в SQLAlchemy, благодаря чему разработчики могут использовать все его мощные возможности из Python-кода.

Использование SQLAlchemy с PostgreSQL обеспечивает:
- Безопасность и защиту от SQL-инъекций
- Абстракцию от деталей реализации БД
- Поддержку сложных моделей данных и отношений
- Эффективную работу с транзакциями
- Управление схемой базы данных и миграциями

Следуя рекомендациям и лучшим практикам, описанным в этом руководстве, вы сможете создавать высокопроизводительные и надежные приложения, использующие все преимущества SQLAlchemy и PostgreSQL. 