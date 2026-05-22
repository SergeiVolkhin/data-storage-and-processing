#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ETL Скрипт (Шаг 1): Загрузка таблиц-справочников
для схемы 'shop_db' из CSV-файлов

Скрипт идемпотентный: безопасно запускать повторно
"""
import os
import sys
import traceback
from typing import Tuple
from dotenv import load_dotenv

import pandas as pd
from sqlalchemy import create_engine, exc, text
from sqlalchemy.engine import Engine

# --- КОНФИГУРАЦИЯ ---
# Загружаем переменные из .env файла
load_dotenv()
DB_URL = os.getenv("DB_URL")

if not DB_URL:
    print("КРИТИЧЕСКАЯ ОШИБКА: Переменная окружения DB_URL не найдена")
    print("Пожалуйста, создайте файл .env по шаблону .env.example")
    sys.exit(1)

SCHEMA_NAME = "shop_db"
CUSTOMER_FILE = "data/customer.csv"
TRANSACTION_FILE = "data/transaction.csv"
# ---------------------

def load_simple_dimension(
    engine: Engine,
    df_source: pd.DataFrame,
    source_col: str,
    table_name: str,
    target_col: str,
    filter_na_string: bool = False
) -> None:
    """
    Загружает простой справочник (1 колонка) из исходного DataFrame в БД
    Проверяет существующие записи, чтобы избежать дубликатов
    """
    print(f"Обработка таблицы: {SCHEMA_NAME}.{table_name}...")
    try:
        # 1. Получаем уникальные значения из CSV
        data = df_source[source_col].dropna().unique().tolist()

        if filter_na_string:
            data = [item for item in data if str(item).lower() != 'n/a']

        df_dim = pd.DataFrame(data, columns=[target_col])

        if df_dim.empty:
            print(f" - В источнике нет данных для {table_name}, пропуск.")
            return

        # 2. Получаем существующие данные из БД для проверки
        try:
            existing_data = pd.read_sql(
                f"SELECT {target_col} FROM {SCHEMA_NAME}.{table_name}", engine
            )
            # 3. Находим только новые записи
            data_to_load = df_dim[
                ~df_dim[target_col].isin(existing_data[target_col])
            ]
        except exc.SQLAlchemyError as e:
            if "does not exist" in str(e):
                print(f" - Таблица {table_name} не найдена, будет создана и загружена.")
                data_to_load = df_dim
            else:
                raise

        # 4. Загружаем новые данные
        if data_to_load.empty:
            print(f" - Нет новых записей для {table_name}, пропуск.")
            return

        data_to_load.to_sql(
            table_name, engine, schema=SCHEMA_NAME, if_exists='append', index=False
        )
        print(
            f" - Успешно загружено {len(data_to_load)} "
            f"новых записей в {table_name}."
        )

    except (exc.SQLAlchemyError, KeyError) as e:
        print(f"ОШИБКА при обработке {table_name}: {e}")


def connect_db(db_url: str) -> Engine:
    """
    Подключается к БД и гарантирует наличие схемы.
    """
    try:
        engine = create_engine(db_url)
        with engine.connect() as conn:
            conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA_NAME}"))
            conn.commit()
        print(f"Подключение к БД установлено. Целевая схема: {SCHEMA_NAME}")
        return engine
    except exc.SQLAlchemyError as e:
        print(f"КРИТИЧЕСКАЯ ОШИБКА: Не удалось подключиться к БД: {e}")
        print("Пожалуйста, проверьте конфигурацию DB_URL в .env файле.")
        sys.exit(1)


def read_source_files(
    customer_file: str, transaction_file: str
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Читает исходные CSV-файлы в DataFrame.
    """
    try:
        print("Чтение исходных CSV файлов...")
        customer_df = pd.read_csv(customer_file)
        transaction_df = pd.read_csv(transaction_file)
        print(" - CSV файлы успешно загружены.")
        return customer_df, transaction_df
    except FileNotFoundError as e:
        print(f"КРИТИЧЕСКАЯ ОШИБКА: Исходный файл не найден: {e}")
        sys.exit(1)


def load_location_dims(engine: Engine, customer_df: pd.DataFrame) -> None:
    """
    Загружает зависимые справочники: countries, states, postcodes.
    """
    print("\n--- Загрузка справочников локаций (Страны, Штаты, Индексы) ---")

    # 3.1. Countries
    print("Обработка таблицы: shop_db.countries...")
    df_countries = customer_df[['country']].dropna().drop_duplicates().rename(
        columns={'country': 'country_name'}
    )
    try:
        existing_countries = pd.read_sql(
            f"SELECT country_name FROM {SCHEMA_NAME}.countries", engine
        )
        countries_to_load = df_countries[
            ~df_countries['country_name'].isin(existing_countries['country_name'])
        ]
    except exc.SQLAlchemyError:
        countries_to_load = df_countries

    if not countries_to_load.empty:
        countries_to_load.to_sql(
            'countries', engine, schema=SCHEMA_NAME, if_exists='append', index=False
        )
        print(f" - Загружено {len(countries_to_load)} новых записей в countries.")
    else:
        print(" - Нет новых записей для countries.")

    # 3.2. States (зависит от Countries)
    print("Обработка таблицы: shop_db.states...")
    countries_map = pd.read_sql(
        f"SELECT id, country_name FROM {SCHEMA_NAME}.countries", engine
    ).set_index('country_name')['id'].to_dict()

    customer_df['state_std'] = customer_df['state'].replace(
        {'VIC': 'Victoria', 'New South Wales': 'NSW'}
    )

    df_states = customer_df[['state_std', 'country']].dropna().drop_duplicates()
    df_states['country_id'] = df_states['country'].map(countries_map)
    df_states = df_states[['state_std', 'country_id']].rename(
        columns={'state_std': 'state_name'}
    ).dropna()
    df_states['country_id'] = df_states['country_id'].astype(int)

    try:
        existing_states = pd.read_sql(
            f"SELECT state_name, country_id FROM {SCHEMA_NAME}.states", engine
        )
        states_to_load = df_states.merge(
            existing_states, on=['state_name', 'country_id'], how='left', indicator=True
        )
        states_to_load = states_to_load[
            states_to_load['_merge'] == 'left_only'
        ].drop(columns='_merge')
    except exc.SQLAlchemyError:
        states_to_load = df_states

    if not states_to_load.empty:
        states_to_load.to_sql(
            'states', engine, schema=SCHEMA_NAME, if_exists='append', index=False
        )
        print(f" - Загружено {len(states_to_load)} новых записей в states.")
    else:
        print(" - Нет новых записей для states.")

    # 3.3. Postcodes (зависит от States)
    print("Обработка таблицы: shop_db.postcodes...")
    states_map = pd.read_sql(
        f"SELECT id, state_name FROM {SCHEMA_NAME}.states", engine
    ).set_index('state_name')['id'].to_dict()

    df_postcodes = customer_df[['postcode', 'state_std']].dropna().drop_duplicates()
    df_postcodes['state_id'] = df_postcodes['state_std'].map(states_map)
    df_postcodes = df_postcodes[['postcode', 'state_id']].dropna()
    df_postcodes['state_id'] = df_postcodes['state_id'].astype(int)

    try:
        existing_postcodes = pd.read_sql(
            f"SELECT postcode FROM {SCHEMA_NAME}.postcodes", engine
        )
        postcodes_to_load = df_postcodes[
            ~df_postcodes['postcode'].isin(existing_postcodes['postcode'])
        ]
    except exc.SQLAlchemyError:
        postcodes_to_load = df_postcodes

    if not postcodes_to_load.empty:
        postcodes_to_load.to_sql(
            'postcodes', engine, schema=SCHEMA_NAME, if_exists='append', index=False
        )
        print(f" - Загружено {len(postcodes_to_load)} новых записей в postcodes.")
    else:
        print(" - Нет новых записей для postcodes.")


def load_other_dims(
    engine: Engine, customer_df: pd.DataFrame, transaction_df: pd.DataFrame
) -> None:
    """
    Загружает все остальные справочники.
    """
    print("\n--- Загрузка остальных справочников ---")

    load_simple_dimension(
        engine,
        customer_df,
        'job_industry_category',
        'job_industries',
        'category_name',
        filter_na_string=True
    )
    load_simple_dimension(
        engine, customer_df, 'wealth_segment', 'wealth_segments', 'segment_name'
    )
    load_simple_dimension(
        engine, transaction_df, 'order_status', 'order_statuses', 'status_name'
    )
    load_simple_dimension(
        engine, transaction_df, 'brand', 'brands', 'brand_name'
    )
    load_simple_dimension(
        engine, transaction_df, 'product_line', 'product_lines', 'line_name'
    )
    load_simple_dimension(
        engine, transaction_df, 'product_class', 'product_classes', 'class_name'
    )
    load_simple_dimension(
        engine, transaction_df, 'product_size', 'product_sizes', 'size_name'
    )


def main() -> None:
    """
    Главная функция-оркестратор ETL Шага 1
    """
    print("--- Запуск ETL Шага 1: Загрузка Справочников ---")

    try:
        engine = connect_db(DB_URL)
        customer_df, transaction_df = read_source_files(
            CUSTOMER_FILE, TRANSACTION_FILE
        )
        load_location_dims(engine, customer_df)
        load_other_dims(engine, customer_df, transaction_df)

        print("\n--- ETL Шаг 1 успешно завершен ---")

    except (FileNotFoundError, exc.SQLAlchemyError) as e:
        print(f"\nКРИТИЧЕСКАЯ ОШИБКА во время ETL-процесса: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\nКРИТИЧЕСКАЯ ОШИБКА: Произошла непредвиденная ошибка: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()