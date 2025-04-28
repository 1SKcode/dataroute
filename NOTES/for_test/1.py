import time

import clickhouse_connect
import logging
from airflow.hooks.base import BaseHook

logging.basicConfig(level=logging.INFO)

# Подключение к ClickHouse
# connection = BaseHook.get_connection("clickhouse_155_conn")
client = clickhouse_connect.get_client(
    host="89.232.162.155",
    port=8123,
    username="akir",
    password="opaw47DxXkhTw3u2kX",
    database="postgres_etl",
    settings={
        "input_format_skip_unknown_fields": 1,
        "connect_timeout_with_failover_ms": 5000,
        "receive_timeout": 300000,
        "send_timeout": 300000
    }
)


def insert_in_ch(source_table, target_table, retries=2, delay=5):
    current_time = client.query("SELECT now()").result_rows[0][0]
    select_query = f"SELECT * FROM {source_table}"
    logging.info(f"Выполнение: {select_query}")

    for attempt in range(retries + 1):
        try:
            rows = client.query(select_query).result_rows
            if not rows:
                logging.info("[DONE] Все данные успешно считаны.")
                return False

            rows_with_time = [(current_time, *row) for row in rows]
            client.insert(target_table, rows_with_time)
            logging.info(f"[+++] {len(rows_with_time)} записей вставлено в {target_table}.")
            return True
        except Exception as e:
            logging.error(f"Ошибка (попытка {attempt + 1}): {e}", exc_info=True)
            if attempt < retries:
                logging.info(f"Попытка не удалась, повтор через {delay} секунд...")
                time.sleep(delay)
            else:
                logging.error("Превышено количество попыток.")
                return False

def drop_tables(query, table,  _client = client):
    try:
        _client.command(query)
        logging.info(f"Удалена таблица: {table}")
    except Exception as e:
        logging.error(f"Ошибка при удалении таблицы {table}: {e}", exc_info=True)

def drop_conn_tables():
    """
    Функция для удаления таблиц подключения к постгрес.
    """
    tables = ["conn_sitedb_site_blocks_view", "conn_sitedb_site_buildings_view", "conn_sitedb_site_flats_view"]
    for table in tables:
        query = f"DROP TABLE IF EXISTS postgres_etl.{table}"
        drop_tables(query=query, table=table)

def drop_replica_tables():
    tables = ["site_blocks_replica", "site_buildings_replica", "site_flats_replica"]
    for table in tables:
        query = f"DROP TABLE IF EXISTS postgres_etl.{table}"
        drop_tables(query=query, table=table)


def create_conn_tables(_client=client):
    """
    Функция для создания таблиц подключения к PostgreSQL
    """
    # connection_pg = BaseHook.get_connection("sitedb")

    # host = connection_pg.host
    # port = connection_pg.port
    # database = "sitedb"
    # user = connection_pg.login
    # password = connection_pg.password
    host = "188.72.109.181"
    port = 6432
    database = "sitedb"
    user = "admin"
    password = "/07uC76;A9Pq"

    for new_table, pg_table in {
        "conn_sitedb_site_blocks_view": "site_blocks_view",
        "conn_sitedb_site_buildings_view": "site_buildings_view",
        "conn_sitedb_site_flats_view": "site_flats_view"
    }.items():
        query = f"""
            CREATE TABLE postgres_etl.{new_table}
            ENGINE = PostgreSQL(
                '{host}:{port}',
                '{database}',
                '{pg_table}',
                '{user}',
                '{password}',
                'public',
                'connect_timeout=100,socket_timeout=100,client_encoding=UTF8'
            )
            """

        try:
            _client.command(query)
            logging.info(f"Создана таблица-драйвер: {new_table} для таблицы PostgreSQL: {pg_table}")
        except Exception as e:
            logging.error(f"Ошибка при создании драйвера {new_table} для {pg_table}: {e}", exc_info=True)
            raise


def create_table(table, body, orderby, _client = client):
    query = f'''
                    CREATE TABLE IF NOT EXISTS postgres_etl.{table}
                    (
                    `etl_create_datetime` DateTime64(6),
                    {body}
                    )
                    ENGINE = ReplacingMergeTree(etl_create_datetime)
                    ORDER BY {orderby}
                    SETTINGS allow_nullable_key = 1,
                    index_granularity = 8192;'''
    try:
        _client.command(query)
        logging.info(f"Создана таблица реплика: {table}")
    except Exception as e:
        logging.error(f"Ошибка при создании таблицы: {table}: {e}", exc_info=True)

def extract_columns_from_ddl(table, _client = client):
    query = f"SHOW CREATE TABLE postgres_etl.{table}"
    try:
        ddl = _client.command(query)
    except Exception as e:
        logging.error(f"Ошибка получения DDL: {e}", exc_info=True)
        pass

    # Находим индексы начала и конца
    start_idx = ddl.find('(')  # Найти первую открывающуюся скобку
    end_idx = ddl.find('ENGINE')  # Найти начало слова "ENGINE"

    # Оставляем только то, что между ними, и убираем закрывающую скобку ')'
    cleaned_text = ddl[start_idx + 1:end_idx].strip()  # Убираем первую скобку '(' и часть после 'ENGINE'

    # Убираем закрывающую скобку в конце
    cleaned_text = cleaned_text[:-5]

    # Заменяем экранированные символы новой строки, если нужно
    cleaned_text = cleaned_text.replace("\\n", "\n")

    return cleaned_text

def create_blocks_replica_table():
    ddl = extract_columns_from_ddl("conn_sitedb_site_blocks_view")
    create_table("site_blocks_replica", ddl, "block_uuid")

def create_buildings_replica_table():
    ddl = extract_columns_from_ddl("conn_sitedb_site_buildings_view")
    create_table("site_buildings_replica", ddl, "building_uuid")

def create_flats_replica_table():
    ddl = extract_columns_from_ddl("conn_sitedb_site_flats_view")
    create_table("site_flats_replica", ddl, "flats_uuid")


def insert_flats():
    status = insert_in_ch(
        source_table="postgres_etl.conn_sitedb_site_flats_view",
        target_table="postgres_etl.site_flats_replica"
    )
    return status

def insert_blocks():
    status = insert_in_ch(
        source_table="postgres_etl.conn_sitedb_site_blocks_view",
        target_table="postgres_etl.site_blocks_replica"
    )
    return status

def insert_buildings():
    status = insert_in_ch(
        source_table="postgres_etl.conn_sitedb_site_buildings_view",
        target_table="postgres_etl.site_buildings_replica"
    )
    return status

def optimize_tables(_client = client):
    tables = ["dict_collector_site_blocks", "dict_collector_site_buildings", "dict_collector_site_flats"]
    for table in tables:
        query = f"OPTIMIZE TABLE postgres_etl.{table} FINAL;"
        try:
            response = _client.command(query)
            logging.info(f"FINAL для таблицы {table} завершена. Ответ: {response}")
        except Exception as e:
            logging.error(f"Ошибка FINAL: {e}", exc_info=True)
            pass

def insert_dict_collector(_client = client):
    path = "/opt/airflow/dags/pg_sitedb_historical_ch_3_tables/sqls"
    tables = ["select_query_blocks", "select_query_buildings", "select_query_flats"]

    current_time = client.query("SELECT now()").result_rows[0][0]
    formatted_time = current_time.strftime('%Y-%m-%d %H:%M:%S')
    for table in tables:
        with open(f"{path}/{table}.sql", "r", encoding="utf-8") as file:
            sql_query = file.read()
        try:
            client.command(sql_query, parameters={"current_time": formatted_time})
            logging.info(f"УСПЕШНО: {table}")
        except Exception as e:
            logging.error(f"Ошибка {table}", exc_info=True)


def insert_normalize_historical(_client = client):
    path = "/opt/airflow/dags/pg_sitedb_historical_ch_3_tables/sqls"

    with open(f"{path}/insert_normalize_historical.sql", "r", encoding="utf-8") as file:
        sql_query = file.read()
    try:
        client.command(sql_query)
        logging.info(f"УСПЕШНО: insert_normalize_historical")
    except Exception as e:
        logging.error(f"Ошибка insert_normalize_historical", exc_info=True)




def run_etl():
    # 9:00
    drop_conn_tables()
    create_conn_tables()
    drop_replica_tables()

    create_blocks_replica_table()
    create_buildings_replica_table()
    time.sleep(60)
    create_flats_replica_table()

    insert_blocks()
    insert_buildings()
    insert_flats()



if __name__ == "__main__":
    run_etl()
