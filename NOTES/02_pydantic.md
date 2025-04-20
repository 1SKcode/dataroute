# Полное руководство по Pydantic

## Содержание
1. [Введение в Pydantic](#введение-в-pydantic)
2. [Основные концепции](#основные-концепции)
3. [Базовые типы данных](#базовые-типы-данных)
4. [Модели и схемы](#модели-и-схемы)
5. [Валидация данных](#валидация-данных)
6. [Сложные типы и структуры](#сложные-типы-и-структуры)
7. [Работа с JSON](#работа-с-json)
8. [Интеграция с другими библиотеками](#интеграция-с-другими-библиотеками)
9. [Продвинутые возможности](#продвинутые-возможности)
10. [Лучшие практики](#лучшие-практики)

## Введение в Pydantic

Pydantic — это библиотека для валидации данных и управления настройками в Python, использующая аннотации типов. Она обеспечивает принудительное применение типов во время выполнения, генерирует полезные сообщения об ошибках и предоставляет инструменты для проверки сложных структур данных.

### Ключевые особенности Pydantic:

- **Строгая типизация**: проверка типов данных во время выполнения
- **Высокая производительность**: написана с использованием Rust-подобного кода на Python
- **Интуитивно понятный API**: использование стандартных аннотаций типов Python
- **Расширяемость**: возможность создания пользовательских типов и валидаторов
- **Интеграция с другими инструментами**: совместимость с FastAPI, SQLAlchemy и др.

> **Важно**: В этом руководстве рассматривается Pydantic v2, выпущенный в 2023 году, который имеет значительные отличия от v1.

## Основные концепции

### Установка

```bash
pip install pydantic
```

Для использования всех возможностей:

```bash
pip install "pydantic[email]"  # Дополнительные валидаторы
```

### Базовая модель

```python
from pydantic import BaseModel, Field

class User(BaseModel):
    id: int
    name: str
    email: str
    is_active: bool = True  # Значение по умолчанию
    
# Создание экземпляра
user = User(id=1, name="John Doe", email="john@example.com")

# Доступ к данным
print(user.name)  # John Doe
print(user.model_dump())  # Преобразование в словарь
```

### Валидация при создании

```python
try:
    # Этот код вызовет ошибку, так как id должен быть int
    invalid_user = User(id="not-an-integer", name="John", email="john@example.com")
except Exception as e:
    print(str(e))
    # Output: 1 validation error for User
    # id
    #   Input should be a valid integer [type=int_type, input_value='not-an-integer', input_type=str]
```

## Базовые типы данных

Pydantic поддерживает все стандартные типы данных Python, а также расширенные типы из модуля `typing`:

### Простые типы

- `str` - строка
- `int` - целое число
- `float` - число с плавающей точкой
- `bool` - логическое значение
- `bytes` - байты
- `None` - None/null

### Составные типы

- `list` - список
- `tuple` - кортеж
- `dict` - словарь
- `set` - множество
- `frozenset` - неизменяемое множество

### Специальные типы

- `Any` - любой тип
- `Union` - объединение типов (в Python 3.10+ можно использовать `|`)
- `Optional` - опциональный тип (эквивалент `Union[T, None]`)
- `Literal` - литеральное значение
- `Annotated` - тип с дополнительными метаданными

### Примеры использования базовых типов

```python
from typing import List, Dict, Optional, Union, Literal
from pydantic import BaseModel

class Product(BaseModel):
    id: int
    name: str
    price: float
    tags: List[str] = []  # Список строк
    metadata: Dict[str, str] = {}  # Словарь ключ:строка, значение:строка
    description: Optional[str] = None  # Опциональное поле
    size: Union[int, str]  # Поле может быть числом или строкой
    status: Literal["active", "inactive", "pending"] = "active"  # Только одно из этих значений
```

## Модели и схемы

### Определение моделей

```python
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, EmailStr

class Address(BaseModel):
    street: str
    city: str
    country: str
    postal_code: str

class User(BaseModel):
    id: int
    username: str = Field(..., min_length=3, max_length=50)  # ... означает обязательное поле
    email: EmailStr
    full_name: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    addresses: List[Address] = []  # Вложенная модель

# Создание с вложенной моделью
user = User(
    id=1,
    username="johndoe",
    email="john@example.com",
    addresses=[{"street": "123 Main St", "city": "New York", "country": "USA", "postal_code": "10001"}]
)
```

### Наследование моделей

```python
class BaseUser(BaseModel):
    id: int
    username: str
    email: str

class AdminUser(BaseUser):
    permissions: List[str]
    is_superuser: bool = False

# AdminUser включает все поля из BaseUser плюс собственные поля
admin = AdminUser(id=1, username="admin", email="admin@example.com", permissions=["read", "write", "delete"])
```

### Дополнительная конфигурация моделей

```python
from pydantic import ConfigDict

class User(BaseModel):
    model_config = ConfigDict(
        title="User Model",
        validate_assignment=True,  # Валидация при присваивании
        extra="forbid",  # Запрещает дополнительные поля
        str_strip_whitespace=True,  # Убирает пробелы из строк
        validate_default=True,  # Валидирует значения по умолчанию
        frozen=False,  # Если True, модель становится неизменяемой
    )
    
    id: int
    name: str
```

## Валидация данных

### Валидаторы полей

```python
from pydantic import BaseModel, Field, field_validator

class User(BaseModel):
    username: str = Field(..., min_length=3)
    password: str = Field(..., min_length=8)
    
    @field_validator('password')
    @classmethod
    def password_must_contain_special_char(cls, v: str) -> str:
        if not any(char in "!@#$%^&*()_+" for char in v):
            raise ValueError("Password must contain at least one special character")
        return v
```

### Валидация нескольких полей

```python
from pydantic import BaseModel, field_validator, model_validator

class UserRegistration(BaseModel):
    username: str
    password: str
    password_confirm: str
    
    @model_validator(mode='after')
    def passwords_match(self) -> 'UserRegistration':
        if self.password != self.password_confirm:
            raise ValueError("Passwords do not match")
        return self
```

### Предварительная и пост-обработка полей

```python
from pydantic import BaseModel, field_validator

class User(BaseModel):
    name: str
    email: str
    
    @field_validator('name')
    @classmethod
    def capitalize_name(cls, v: str) -> str:
        return v.title()
    
    @field_validator('email')
    @classmethod
    def lowercase_email(cls, v: str) -> str:
        return v.lower()
```

### Кастомные типы и валидаторы

```python
from pydantic import BaseModel, GetCoreSchemaHandler, GetJsonSchemaHandler
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import core_schema
from typing import Annotated, Any, List

class PositiveInt(int):
    """Целое число больше нуля"""
    
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
        
    @classmethod
    def validate(cls, v):
        if not isinstance(v, int):
            raise TypeError("Must be an integer")
        if v <= 0:
            raise ValueError("Must be a positive integer")
        return v
    
    @classmethod
    def __get_pydantic_core_schema__(
        cls, _source_type: Any, _handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        return core_schema.with_info_plain_validator_function(
            cls.validate,
            core_schema.int_schema(),
            serialization=core_schema.int_schema(),
        )

# Использование кастомного типа
class Product(BaseModel):
    id: PositiveInt
    name: str
    quantity: PositiveInt

# Кастомный тип с помощью Annotated
def validate_even(v: int) -> int:
    if v % 2 != 0:
        raise ValueError("Value must be even")
    return v

EvenInt = Annotated[int, validate_even]

class Config(BaseModel):
    port: EvenInt  # Должно быть четным числом
```

## Сложные типы и структуры

### Работа с вложенными моделями

```python
from typing import List, Dict
from pydantic import BaseModel

class Category(BaseModel):
    id: int
    name: str

class Tag(BaseModel):
    id: int
    name: str

class Product(BaseModel):
    id: int
    name: str
    price: float
    category: Category
    tags: List[Tag] = []
    attributes: Dict[str, str] = {}

# Создание сложного объекта
product = Product(
    id=1,
    name="Laptop",
    price=999.99,
    category={"id": 1, "name": "Electronics"},
    tags=[
        {"id": 1, "name": "tech"},
        {"id": 2, "name": "computer"}
    ],
    attributes={"color": "black", "weight": "2kg"}
)
```

### Работа с рекурсивными моделями

```python
from typing import List, Optional
from pydantic import BaseModel

class TreeNode(BaseModel):
    value: str
    children: List['TreeNode'] = []  # Рекурсивное определение

# Для работы рекурсивных моделей нужно обновить ссылки
TreeNode.model_rebuild()

# Создание дерева
root = TreeNode(
    value="root",
    children=[
        TreeNode(value="child1"),
        TreeNode(
            value="child2",
            children=[
                TreeNode(value="grandchild1")
            ]
        )
    ]
)
```

### Дискриминированные объединения

```python
from typing import Literal, Union
from pydantic import BaseModel, Field

class Dog(BaseModel):
    type: Literal["dog"]
    name: str
    breed: str

class Cat(BaseModel):
    type: Literal["cat"]
    name: str
    meow_sound: str

class Bird(BaseModel):
    type: Literal["bird"]
    name: str
    can_fly: bool

# Дискриминированное объединение - поле "type" определяет тип объекта
Pet = Union[Dog, Cat, Bird]

def process_pet(pet: Pet):
    if pet.type == "dog":
        return f"{pet.name} is a {pet.breed} dog"
    elif pet.type == "cat":
        return f"{pet.name} says {pet.meow_sound}"
    elif pet.type == "bird":
        fly_status = "can fly" if pet.can_fly else "cannot fly"
        return f"{pet.name} is a bird that {fly_status}"

# Использование
dog = Dog(type="dog", name="Rex", breed="Labrador")
cat = Cat(type="cat", name="Whiskers", meow_sound="Meeeow")

print(process_pet(dog))  # Rex is a Labrador dog
print(process_pet(cat))  # Whiskers says Meeeow
```

## Работа с JSON

### Сериализация и десериализация

```python
from datetime import datetime
from pydantic import BaseModel

class User(BaseModel):
    id: int
    name: str
    created_at: datetime = Field(default_factory=datetime.now)

# Создание экземпляра
user = User(id=1, name="John")

# Сериализация в JSON
json_str = user.model_dump_json()
print(json_str)  # {"id": 1, "name": "John", "created_at": "2023-06-01T12:00:00"}

# Десериализация из JSON
user_data = '{"id": 2, "name": "Jane", "created_at": "2023-06-02T14:30:00"}'
user2 = User.model_validate_json(user_data)
print(user2.name)  # Jane
```

### Настройка сериализации

```python
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional

class User(BaseModel):
    model_config = ConfigDict(
        json_encoders={
            datetime: lambda dt: dt.strftime("%Y-%m-%d")  # Кастомный формат даты
        },
        populate_by_name=True,  # Позволяет использовать псевдонимы при создании
    )
    
    id: int
    username: str
    birth_date: Optional[datetime] = None
    email: str = Field(alias="emailAddress")  # Псевдоним поля

# Создание с использованием псевдонимов
user = User(id=1, username="john", emailAddress="john@example.com")

# Сериализация с учетом настроек
json_data = user.model_dump_json()
print(json_data)
# {"id": 1, "username": "john", "birth_date": null, "emailAddress": "john@example.com"}

# Использование различных режимов сериализации
print(user.model_dump(by_alias=False))  # Использовать имена полей, а не псевдонимы
print(user.model_dump(exclude={"birth_date"}))  # Исключить определенные поля
print(user.model_dump(include={"id", "username"}))  # Включить только указанные поля
```

## Интеграция с другими библиотеками

### FastAPI

Pydantic идеально интегрируется с FastAPI для валидации данных запросов и ответов:

```python
from fastapi import FastAPI
from pydantic import BaseModel, EmailStr

app = FastAPI()

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr

@app.post("/users/", response_model=UserResponse)
async def create_user(user: UserCreate):
    # Данные уже валидированы благодаря Pydantic
    # Создаем пользователя в базе и возвращаем ответ
    return UserResponse(
        id=1,
        username=user.username,
        email=user.email
    )
```

### SQLAlchemy с Pydantic

```python
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session
from pydantic import BaseModel

# SQLAlchemy модель
Base = declarative_base()

class UserDB(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    email = Column(String)

# Pydantic модели
class UserBase(BaseModel):
    username: str
    email: str

class UserCreate(UserBase):
    password: str  # Не сохраняется в БД

class User(UserBase):
    id: int
    
    class Config:
        orm_mode = True  # В Pydantic v2 это from_attributes=True

# Пример использования
engine = create_engine("sqlite:///test.db")
Base.metadata.create_all(engine)

def create_user(db: Session, user: UserCreate):
    db_user = UserDB(username=user.username, email=user.email)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return User.model_validate(db_user)
```

## Продвинутые возможности

### Генерические модели

```python
from typing import Generic, TypeVar, List
from pydantic import BaseModel

T = TypeVar('T')

class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    size: int

class User(BaseModel):
    id: int
    name: str

# Использование с конкретным типом
user_response = PaginatedResponse[User](
    items=[User(id=1, name="John"), User(id=2, name="Jane")],
    total=100,
    page=1,
    size=10
)
```

### Динамическое создание моделей

```python
from pydantic import create_model, Field

# Динамическое создание модели во время выполнения
UserModel = create_model(
    'UserModel',
    id=(int, ...),
    name=(str, ...),
    email=(str, Field(..., pattern=r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')),
    is_active=(bool, True)
)

# Использование созданной модели
user = UserModel(id=1, name="John", email="john@example.com")
print(user)
```

### Экспорт схемы JSON

```python
from pydantic import BaseModel
import json

class User(BaseModel):
    id: int
    name: str
    email: str

# Получение JSON-схемы модели
schema = User.model_json_schema()
print(json.dumps(schema, indent=2))
```

### Условная валидация

```python
from typing import Optional
from pydantic import BaseModel, Field, model_validator

class SignupForm(BaseModel):
    username: str
    password: str
    password_confirm: Optional[str] = None
    reset_token: Optional[str] = None
    
    @model_validator(mode='after')
    def check_passwords_match(self) -> 'SignupForm':
        # Если есть токен сброса, подтверждение пароля не требуется
        if self.reset_token:
            return self
            
        # В противном случае пароли должны совпадать
        if self.password != self.password_confirm:
            raise ValueError("Passwords do not match")
        return self
```

### Типизированные словари

```python
from typing import Dict, Any
from pydantic import BaseModel, TypeAdapter

# Валидация словаря с известной структурой
user_dict = {
    "id": 1,
    "name": "John",
    "email": "john@example.com"
}

class User(BaseModel):
    id: int
    name: str
    email: str

# Валидация словаря
user = TypeAdapter(User).validate_python(user_dict)
print(user.model_dump())

# Для сложных случаев, когда ключи динамические
metadata_validator = TypeAdapter(Dict[str, int])
metadata = metadata_validator.validate_python({"count": 1, "size": 10})
print(metadata)  # {'count': 1, 'size': 10}
```

## Лучшие практики

### 1. Используйте строгую типизацию для чувствительных данных

```python
from typing import Literal
from pydantic import BaseModel, EmailStr, HttpUrl, SecretStr

class User(BaseModel):
    email: EmailStr  # Специальный тип для email
    password: SecretStr  # Скрывает содержимое при выводе
    website: HttpUrl  # Валидирует URL
    role: Literal["admin", "user", "guest"]  # Ограниченный набор значений
```

### 2. Разделяйте модели ввода, бизнес-логики и вывода

```python
from pydantic import BaseModel, EmailStr, SecretStr

# Входные данные от пользователя
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: SecretStr

# Модель для хранения в базе данных
class UserInDB(BaseModel):
    id: int
    username: str
    email: str
    hashed_password: str

# Модель для ответа API
class UserResponse(BaseModel):
    id: int
    username: str
    email: str
```

### 3. Используйте Field для документирования и валидации

```python
from pydantic import BaseModel, Field

class Product(BaseModel):
    id: int = Field(..., description="Уникальный идентификатор продукта")
    name: str = Field(..., min_length=3, description="Название продукта")
    price: float = Field(..., gt=0, description="Цена продукта в рублях")
    description: str = Field("", max_length=1000, description="Описание продукта")
```

### 4. Обрабатывайте ошибки валидации

```python
from pydantic import BaseModel, ValidationError

class User(BaseModel):
    username: str
    age: int

try:
    User(username="john", age="not-a-number")
except ValidationError as e:
    print(e.json())  # JSON-форматированные ошибки
    
    # Извлечение информации о конкретных ошибках
    for error in e.errors():
        print(f"Field: {error['loc'][0]}, Error: {error['msg']}")
```

### 5. Используйте псевдонимы для совместимости с внешними API

```python
from pydantic import BaseModel, Field

class User(BaseModel):
    user_id: int = Field(..., alias="userId")
    first_name: str = Field(..., alias="firstName")
    last_name: str = Field(..., alias="lastName")
    
# Создание объекта с JSON-данными, использующими camelCase
user = User.model_validate({"userId": 1, "firstName": "John", "lastName": "Doe"})

# При сериализации можно выбрать формат
print(user.model_dump(by_alias=True))  # Использовать псевдонимы (camelCase)
print(user.model_dump(by_alias=False))  # Использовать имена полей (snake_case)
```

### 6. Используйте частичную валидацию при необходимости

```python
from typing import Optional
from pydantic import BaseModel

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    
# Все поля опциональны, подходит для частичного обновления (PATCH)
user_update = UserUpdate(username="new_username")
```

### 7. Определяйте пользовательские валидаторы для сложной логики

```python
from pydantic import BaseModel, field_validator
import re

class Password(BaseModel):
    value: str
    
    @field_validator('value')
    @classmethod
    def strong_password(cls, v: str) -> str:
        """Проверка на сложность пароля"""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain an uppercase letter")
            
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain a lowercase letter")
            
        if not re.search(r"\d", v):
            raise ValueError("Password must contain a digit")
            
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError("Password must contain a special character")
            
        return v
```

## Заключение

Pydantic — мощный инструмент для валидации данных и управления типами в Python. Он особенно полезен в контексте веб-приложений, API и любых других систем, где требуется валидация входных данных. Библиотека продолжает активно развиваться, добавляя новые возможности и улучшая производительность.

Переход на Pydantic v2 принес значительные улучшения производительности, более чистый API и расширенные возможности валидации. Активное использование Pydantic в вашем проекте сделает код более надежным, безопасным и самодокументируемым. 