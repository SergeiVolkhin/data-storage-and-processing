#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ETL Скрипт (Шаг 2): Загрузка основных таблиц (Facts)
для схемы 'shop_db' из CSV-файлов.

Использует данные из справочников, загруженных в Шаге 1.
Скрипт транзакционный и идемпотентный.
"""

import os
import sys
import traceback
from typing import Dict, Any
from dotenv import load_dotenv

import pandas as pd
from sqlalchemy import create_engine, exc, text
from sqlalchemy.engine import Engine, Connection

# --- КОНФИГУРАЦИЯ ---
# Загружаем переменные из .env файла
load_dotenv()
DB_URL = os.getenv("DB_URL")

if not DB_URL:
    print("КРИТИЧЕСКАЯ ОШИБКА: Переменная окружения DB_URL не найдена.")
    print("Пожалуйста, создайте файл .env по шаблону .env.example")
    sys.exit(1)

SCHEMA_NAME = "shop_db"
CUSTOMER_FILE = "data/customer.csv"
TRANSACTION_FILE = "data/transaction.csv"
# ---------------------

def get_dim_map(conn: Connection, table_name: str, key_col: str, val_col: str) -> Dict:
    """
    Загружает справочник из БД и возвращает его в виде словаря (карты).
    """
    try:
        query = f"SELECT {key_col}, {val_col} FROM {SCHEMA_NAME}.{table_name}"
        df = pd.read_sql(query, conn)
        return df.set_index(key_col)[val_col].to_dict()
    except Exception as e:
        print(
            f"КРИТИЧЕСКАЯ ОШИБКА: Не удалось получить карту справочника {table_name}. "
            f"Шаг 1 был выполнен? Ошибка: {e}"
        )
        raise

def inject_unknown_record(
    conn: Connection,
    table_name: str,
    pk_col: str,
    name_col: str,
    unknown_id: int = 0,
    unknown_name: str = 'Unknown'
) -> None:
    """
    Вставляет 'Unknown' запись (ID=0) в справочник, если ее нет.
    """
    print(f" - Проверка наличия 'Unknown' (ID={unknown_id}) в {table_name}...")
    try:
        query = text(f"""
            INSERT INTO {SCHEMA_NAME}.{table_name} ({pk_col}, {name_col})
            VALUES (:id, :name)
            ON CONFLICT ({pk_col}) DO NOTHING
        """)
        conn.execute(query, {'id': unknown_id, 'name': unknown_name})
    except exc.SQLAlchemyError as e:
        print(f"Предупреждение/Ошибка при вставке 'Unknown' в {table_name}: {e}")


def inject_unknown_records(conn: Connection) -> None:
    """
    Блок 3: Внедрение "Unknown" записей (ID=0) для NOT NULL FK в products.
    """
    print("\nВнедрение 'Unknown' записей (для product_id=0)...")
    inject_unknown_record(conn, 'brands', 'id', 'brand_name', unknown_id=0)
    inject_unknown_record(conn, 'product_lines', 'id', 'line_name', unknown_id=0)
    inject_unknown_record(conn, 'product_classes', 'id', 'class_name', unknown_id=0)
    inject_unknown_record(conn, 'product_sizes', 'id', 'size_name', unknown_id=0)


def fetch_dimension_maps(conn: Connection) -> Dict[str, Any]:
    """
    Блок 4: Получение карт справочников из БД.
    """
    print("\nПолучение карт справочников из БД...")
    maps = {
        'brands': get_dim_map(conn, 'brands', 'brand_name', 'id'),
        'product_lines': get_dim_map(conn, 'product_lines', 'line_name', 'id'),
        'product_classes': get_dim_map(conn, 'product_classes', 'class_name', 'id'),
        'product_sizes': get_dim_map(conn, 'product_sizes', 'size_name', 'id'),
        'job_industries': get_dim_map(
            conn, 'job_industries', 'category_name', 'id'
        ),
        'wealth_segments': get_dim_map(
            conn, 'wealth_segments', 'segment_name', 'id'
        ),
        'order_statuses': get_dim_map(
            conn, 'order_statuses', 'status_name', 'id'
        ),
    }
    print(" - Все карты справочников получены.")
    return maps


def load_products_fact(
    conn: Connection, transaction_df_raw: pd.DataFrame, dim_maps: Dict[str, Any]
) -> None:
    """
    Блок 5: ОБРАБОТКА И ЗАГРУЗКА 'products'.
    """
    print(f"\nОбработка таблицы: {SCHEMA_NAME}.products...")

    existing_pids = pd.read_sql(
        f"SELECT product_id FROM {SCHEMA_NAME}.products", conn
    )['product_id']

    df_products = transaction_df_raw.drop_duplicates(subset=['product_id'])
    df_products = df_products[~df_products['product_id'].isin(existing_pids)]

    if df_products.empty:
        print(" - Нет новых продуктов для загрузки.")
        return

    df_products['list_price'] = pd.to_numeric(
        df_products['list_price'].str.replace(',', '.'), errors='coerce'
    )
    df_products['standard_cost'] = pd.to_numeric(
        df_products['standard_cost'].str.replace(',', '.'), errors='coerce'
    ).fillna(0)

    df_products['brand_id'] = df_products['brand'].map(
        dim_maps['brands']
    ).fillna(0).astype(int)
    df_products['product_line_id'] = df_products['product_line'].map(
        dim_maps['product_lines']
    ).fillna(0).astype(int)
    df_products['product_class_id'] = df_products['product_class'].map(
        dim_maps['product_classes']
    ).fillna(0).astype(int)
    df_products['product_size_id'] = df_products['product_size'].map(
        dim_maps['product_sizes']
    ).fillna(0).astype(int)

    product_cols = [
        'product_id', 'brand_id', 'product_line_id',
        'product_class_id', 'product_size_id',
        'list_price', 'standard_cost'
    ]
    df_products_final = df_products[product_cols]

    df_products_final.to_sql(
        'products', conn, schema=SCHEMA_NAME, if_exists='append', index=False
    )
    print(f" - Загружено {len(df_products_final)} новых записей в shop_db.products.")


def load_customers_fact(
    conn: Connection, customer_df_raw: pd.DataFrame, dim_maps: Dict[str, Any]
) -> None:
    """
    Блок 6: ОБРАБОТКА И ЗАГРУЗКА 'customers'.
    """
    print(f"\nОбработка таблицы: {SCHEMA_NAME}.customers...")
    existing_cids = pd.read_sql(
        f"SELECT customer_id FROM {SCHEMA_NAME}.customers", conn
    )['customer_id']
    df_cust = customer_df_raw[
        ~customer_df_raw['customer_id'].isin(existing_cids)
    ].copy()

    if df_cust.empty:
        print(" - Нет новых клиентов для загрузки.")
        return

    df_cust['gender'] = df_cust['gender'].map(
        {'Male': 'M', 'Female': 'F', 'F': 'F', 'U': 'U'}
    ).fillna('U')
    df_cust['deceased_indicator'] = df_cust['deceased_indicator'].map(
        {'Y': True, 'N': False}
    ).fillna(False)
    df_cust['owns_car'] = df_cust['owns_car'].map(
        {'Yes': True, 'No': False}
    ).fillna(False)
    df_cust['dob'] = pd.to_datetime(df_cust['DOB'], errors='coerce')

    df_cust['job_industry_category_id'] = df_cust['job_industry_category'].map(
        dim_maps['job_industries']
    )
    df_cust['wealth_segment_id'] = df_cust['wealth_segment'].map(
        dim_maps['wealth_segments']
    )

    customer_cols = [
        'customer_id', 'first_name', 'last_name', 'gender', 'dob',
        'job_title', 'job_industry_category_id', 'wealth_segment_id',
        'deceased_indicator', 'owns_car', 'address', 'postcode',
        'property_valuation'
    ]
    df_cust_final = df_cust[customer_cols]

    df_cust_final.to_sql(
        'customers', conn, schema=SCHEMA_NAME, if_exists='append', index=False
    )
    print(f" - Загружено {len(df_cust_final)} новых записей в shop_db.customers.")


def load_transactions_fact(
    conn: Connection,
    transaction_df_raw: pd.DataFrame,
    customer_df_raw: pd.DataFrame,
    dim_maps: Dict[str, Any]
) -> None:
    """
    Блок 7: ОБРАБОТКА И ЗАГРУЗКА 'transactions'.
    """
    print(f"\nОбработка таблицы: {SCHEMA_NAME}.transactions...")
    existing_tids = pd.read_sql(
        f"SELECT transaction_id FROM {SCHEMA_NAME}.transactions", conn
    )['transaction_id']
    df_trans = transaction_df_raw[
        ~transaction_df_raw['transaction_id'].isin(existing_tids)
    ].copy()

    # ФИЛЬТРАЦИЯ "СИРОТСКИХ" ТРАНЗАКЦИЙ
    valid_customer_ids = set(customer_df_raw['customer_id'])
    original_count = len(df_trans)
    df_trans = df_trans[df_trans['customer_id'].isin(valid_customer_ids)]
    dropped_count = original_count - len(df_trans)

    if dropped_count > 0:
        print(
            f" - ИНФО: Отброшено {dropped_count} транзакций "
            "из-за отсутствующего customer_id (например, 5034)."
        )

    if df_trans.empty:
        print(" - Нет новых валидных транзакций для загрузки.")
        return

    df_trans['online_order'] = df_trans['online_order'].astype('boolean')
    df_trans['transaction_date'] = pd.to_datetime(
        df_trans['transaction_date'], format='%m/%d/%Y'
    )

    df_trans['order_status_id'] = df_trans['order_status'].map(
        dim_maps['order_statuses']
    )

    transaction_cols = [
        'transaction_id', 'product_id', 'customer_id',
        'transaction_date', 'online_order', 'order_status_id'
    ]
    df_trans_final = df_trans[transaction_cols]

    df_trans_final.to_sql(
        'transactions', conn, schema=SCHEMA_NAME, if_exists='append', index=False
    )
    print(f" - Загружено {len(df_trans_final)} новых записей в shop_db.transactions.")


def main() -> None:
    """
    Главная функция-оркестратор ETL Шага 2.
    """
    print("--- Запуск ETL Шага 2: Загрузка Таблиц Фактов ---")

    try:
        engine: Engine = create_engine(DB_URL)

        with engine.begin() as conn:
            print("Подключение к БД установлено. Транзакция начата.")

            conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA_NAME}"))

            print("Чтение исходных CSV файлов...")
            customer_df_raw = pd.read_csv(CUSTOMER_FILE)
            transaction_df_raw = pd.read_csv(TRANSACTION_FILE)
            print(" - CSV файлы успешно загружены.")

            inject_unknown_records(conn)

            dim_maps = fetch_dimension_maps(conn)

            load_products_fact(conn, transaction_df_raw, dim_maps)

            load_customers_fact(conn, customer_df_raw, dim_maps)

            load_transactions_fact(
                conn, transaction_df_raw, customer_df_raw, dim_maps
            )

            print("\n--- ETL Шаг 2 успешно завершен ---")
            print("Транзакция зафиксирована (committed).")

    except (FileNotFoundError, exc.SQLAlchemyError) as e:
        print(f"\nКРИТИЧЕСКАЯ ОШИБКА во время ETL Шага 2: {e}")
        print("ТРАНЗАКЦИЯ ОТКАТИЛАСЬ. Данные в этой сессии не загружены.")
        traceback.print_exc()
        sys.exit(1)
    # pylint: disable=W0718
    except Exception as e:
        print(f"\nКРИТИЧЕСКАЯ ОШИБКА: Произошла непредвиденная ошибка: {e}")
        print("ТРАНЗАКЦИЯ ОТКАТИЛАСЬ.")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()