import os
from datetime import datetime, timedelta
import pandas as pd
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.utils.email import send_email

# Имя пула Admin -> Pools
DB_POOL_NAME = 'postgres_limit_pool'

# Определяем аргументы по умолчанию для DAG
default_args = {
    'owner': 'airflow',
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
    'pool': DB_POOL_NAME
}

# Путь к данным
DATA_PATH = '/opt/airflow/data_files'
# Email для уведомлений
ALERT_EMAIL = 'volkhin.sa@phystech.edu'


# Функции
def load_csv_to_postgres(file_name, table_name, delimiter=',', date_cols=None):
    """
    Шаг 1: Читает CSV и заливает в Postgres
    """
    file_path = os.path.join(DATA_PATH, file_name)
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Файл {file_path} не найден. Проверьте папку dags/data")

    # Читаем CSV
    df = pd.read_csv(file_path, sep=delimiter, parse_dates=date_cols)

    # Заливаем в базу
    hook = PostgresHook(postgres_conn_id='postgres_default')
    engine = hook.get_sqlalchemy_engine(engine_kwargs={
        'pool_pre_ping': True,
        'pool_recycle': 3600
    })

    print(f"Начинаем загрузку {len(df)} строк в таблицу {table_name}")

    # Разбиваем загрузку на итерации по 1000 строк
    df.to_sql(
        table_name,
        engine,
        if_exists='replace',
        index=False,
        chunksize=1000,
        method='multi' # множественный VALUES чтобы не построчный insert был 
    )
    print(f"Таблица {table_name} успешно загружена.")


def export_sql_to_csv(sql_query, file_name):
    """Шаг 2: Выгрузка"""
    hook = PostgresHook(postgres_conn_id='postgres_default')
    df = hook.get_pandas_df(sql_query)

    output_path = os.path.join(DATA_PATH, file_name)
    df.to_csv(output_path, index=False)
    print(f"Файл {file_name} сохранен.")


def check_results_and_notify(**kwargs):
    """Шаг 3: Проверка на пустоту файлов и отправка Email"""
    files_to_check = ['report_min_max.csv', 'report_wealth.csv']
    empty_files = []

    # 1. Проверяем файлы
    for fname in files_to_check:
        fpath = os.path.join(DATA_PATH, fname)
        try:
            df = pd.read_csv(fpath)
            if df.empty:
                empty_files.append(fname)
                print(f"Ошибка: Файл {fname} пуст!")
            else:
                print(f"Ок: Файл {fname} содержит {len(df)} строк.")
        except Exception as e:
            empty_files.append(f"{fname} (ошибка: {str(e)})")

    # 2. Если есть проблемы, шлем Email и роняем задачу
    if empty_files:
        error_msg = f"Отчеты пусты или отсутствуют: {', '.join(empty_files)}"
        try:
            send_email(
                to=ALERT_EMAIL,
                subject='[Airflow Alert] Empty Analytics Reports',
                html_content=f'<p>{error_msg}</p>'
            )
        except Exception as e:
            print(f"Ошибка отправки email: {e}")
        # Вызываем ошибку, чтобы Task стал красным
        raise ValueError(error_msg)


# Запросы
SQL_MIN_MAX = """
WITH totals AS (
    SELECT c.first_name, c.last_name, 
           COALESCE(SUM(oi.quantity * oi.item_list_price_at_sale), 0) as amount
    FROM customer c
    LEFT JOIN orders o ON c.customer_id = o.customer_id AND o.order_status = 'Approved'
    LEFT JOIN order_items oi ON o.order_id = oi.order_id
    GROUP BY c.customer_id, c.first_name, c.last_name
)
(SELECT *, 'Min_3' as type FROM totals ORDER BY amount ASC LIMIT 3)
UNION ALL
(SELECT *, 'Max_3' as type FROM totals ORDER BY amount DESC LIMIT 3);
"""

SQL_WEALTH_TOP = """
WITH ranks AS (
    SELECT c.first_name, c.last_name, c.wealth_segment,
           COALESCE(SUM(oi.quantity * oi.item_list_price_at_sale), 0) as revenue,
           ROW_NUMBER() OVER (PARTITION BY c.wealth_segment ORDER BY SUM(oi.quantity * oi.item_list_price_at_sale) DESC) as rn
    FROM customer c
    JOIN orders o ON c.customer_id = o.customer_id AND o.order_status = 'Approved'
    JOIN order_items oi ON o.order_id = oi.order_id
    GROUP BY c.customer_id, c.first_name, c.last_name, c.wealth_segment
)
SELECT first_name, last_name, wealth_segment, revenue
FROM ranks WHERE rn <= 5;
"""

# DAG
with DAG(
        'ecommerce_pipeline',
        default_args=default_args,
        schedule_interval='@daily',
        start_date=datetime(2025, 12, 16),
        catchup=False,
        tags=['etl', 'pool_optimized']
) as dag:
    # 1. Загрузка
    t_load_customer = PythonOperator(
        task_id='load_customer',
        python_callable=load_csv_to_postgres,
        op_kwargs={'file_name': 'customer.csv', 'table_name': 'customer', 'delimiter': ';', 'date_cols': ['DOB']}
    )
    t_load_product = PythonOperator(
        task_id='load_product',
        python_callable=load_csv_to_postgres,
        op_kwargs={'file_name': 'product.csv', 'table_name': 'product'}
    )
    t_load_orders = PythonOperator(
        task_id='load_orders',
        python_callable=load_csv_to_postgres,
        op_kwargs={'file_name': 'orders.csv', 'table_name': 'orders', 'date_cols': ['order_date']}
    )
    t_load_items = PythonOperator(
        task_id='load_items',
        python_callable=load_csv_to_postgres,
        op_kwargs={'file_name': 'order_items.csv', 'table_name': 'order_items'}
    )

    # 2. Аналитика
    t_calc_min_max = PythonOperator(
        task_id='calc_min_max',
        python_callable=export_sql_to_csv,
        op_kwargs={'sql_query': SQL_MIN_MAX, 'file_name': 'report_min_max.csv'}
    )
    t_calc_wealth = PythonOperator(
        task_id='calc_wealth',
        python_callable=export_sql_to_csv,
        op_kwargs={'sql_query': SQL_WEALTH_TOP, 'file_name': 'report_wealth.csv'}
    )

    # 3. Проверка
    t_quality_check = PythonOperator(
        task_id='check_results_notify',
        python_callable=check_results_and_notify
    )

    # 4. Финальное сообщение
    t_final_status = BashOperator(
        task_id='final_status_message',
        bash_command='echo "DAG successfully finished with Connection Pooling!"'
    )

    # Зависимости
    load_tasks = [t_load_customer, t_load_product, t_load_orders, t_load_items]
    analytics_tasks = [t_calc_min_max, t_calc_wealth]

    load_tasks >> t_calc_min_max
    load_tasks >> t_calc_wealth
    analytics_tasks >> t_quality_check
    t_quality_check >> t_final_status