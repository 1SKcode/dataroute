from typing import Dict, List, Any, Optional, Set
import asyncpg
import json
import asyncio
from pydantic import create_model, Field


class PgTargetWriter:
    """Writer для записи данных в PostgreSQL"""
    
    def __init__(
        self,
        schema_table: str,
        field_names: List[str],
        db_config: Optional[Dict[str, Any]] = None,
        skip_validation: bool = False
    ):
        """
        Инициализирует PostgreSQL writer.
        
        Args:
            schema_table: Имя таблицы в формате "schema.table"
            field_names: Список имен полей для записи
            db_config: Конфигурация подключения к базе данных
            skip_validation: Флаг для пропуска валидации данных (для тестирования)
        """
        self.schema_table = schema_table
        self.field_names = field_names
        self.db_config = db_config or {}
        self.schema, self.table = self._parse_schema_table(schema_table)
        self.connection_pool = None
        self.skip_validation = skip_validation
    
    def _parse_schema_table(self, schema_table: str) -> tuple:
        """Разбирает имя таблицы на схему и таблицу"""
        parts = schema_table.split('.')
        if len(parts) == 2:
            return parts[0], parts[1]
        return 'public', parts[0]
    
    async def connect(self) -> None:
        """Создает пул соединений с базой данных"""
        if not self.connection_pool:
            self.connection_pool = await asyncpg.create_pool(
                user=self.db_config.get('user', 'postgres'),
                password=self.db_config.get('password', ''),
                database=self.db_config.get('database', 'postgres'),
                host=self.db_config.get('host', 'localhost'),
                port=self.db_config.get('port', 5432),
                min_size=self.db_config.get('min_connections', 1),
                max_size=self.db_config.get('max_connections', 10)
            )
    
    async def close(self) -> None:
        """Закрывает пул соединений с базой данных"""
        if self.connection_pool:
            await self.connection_pool.close()
            self.connection_pool = None
    
    async def validate_fields(self) -> tuple:
        """
        Проверяет существование полей в таблице.
        
        Returns:
            Кортеж (is_valid, missing_fields)
        """
        # Подключаемся к базе данных, если еще не подключены
        await self.connect()
        
        async with self.connection_pool.acquire() as conn:
            # Получаем список столбцов таблицы
            query = """
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_schema = $1 AND table_name = $2
            """
            rows = await conn.fetch(query, self.schema, self.table)
            table_columns = {row['column_name'] for row in rows}
            
            # Проверяем, все ли поля существуют в таблице
            missing_fields = []
            for field in self.field_names:
                if field not in table_columns:
                    missing_fields.append(field)
            
            return len(missing_fields) == 0, missing_fields
    
    async def write(self, warehouse: List[Dict[str, Dict[str, Any]]]) -> None:
        """
        Записывает данные из warehouse в базу данных.
        
        Args:
            warehouse: Список словарей с данными для записи
        """
        if not warehouse:
            return
        
        # Подключаемся к базе данных, если еще не подключены
        await self.connect()
        
        # Начинаем транзакцию
        async with self.connection_pool.acquire() as conn:
            async with conn.transaction():
                for item in warehouse:
                    # Извлекаем данные для вставки
                    data = {}
                    for field_name, field_data in item.items():
                        if field_name in self.field_names:
                            data[field_name] = field_data.get('final_value')
                    
                    if not self.skip_validation:
                        # Создаем динамическую Pydantic-модель для валидации
                        model_fields = {}
                        for field_name, value in data.items():
                            field_type = type(value) if value is not None else str
                            model_fields[field_name] = (Optional[field_type], Field(None))
                        
                        DynamicModel = create_model('DynamicModel', **model_fields)
                        
                        # Валидируем данные через pydantic
                        validated_data = DynamicModel(**data).dict(exclude_none=True)
                    else:
                        # Пропускаем валидацию
                        validated_data = {k: v for k, v in data.items() if v is not None}
                    
                    # Если данных нет, пропускаем запись
                    if not validated_data:
                        continue
                    
                    # Формируем SQL-запрос для вставки
                    fields = list(validated_data.keys())
                    placeholders = [f"${i+1}" for i in range(len(fields))]
                    values = list(validated_data.values())
                    
                    query = f"""
                    INSERT INTO {self.schema}.{self.table} ({", ".join(fields)})
                    VALUES ({", ".join(placeholders)})
                    """
                    
                    # Выполняем запрос
                    await conn.execute(query, *values)
    
    def _get_python_type(self, type_name: str) -> type:
        """Преобразует имя типа в Python-тип"""
        type_mapping = {
            'int': int,
            'str': str,
            'float': float,
            'bool': bool,
            'None': type(None)
        }
        return type_mapping.get(type_name, str)
