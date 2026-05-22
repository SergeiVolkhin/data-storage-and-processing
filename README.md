# Системы хранения и обработки данных

Решённые домашние задания университетского курса «Системы хранения и обработки
данных» (2025). Шесть работ — от проектирования реляционной БД до автоматизации
расчётов в Apache Airflow. Каждое задание строится на реальных данных и решает
прикладную аналитическую задачу. Программа курса — в файле
[`syllabus-2025.pdf`](syllabus-2025.pdf).

Каждый модуль — отдельная папка с README, исходными данными и решением:
SQL-скриптами, Jupyter-ноутбуком или Python-кодом — в зависимости от темы.

## Модули

| № | Тема | Папка | Стек |
|---|------|-------|------|
| 1 | Проектирование БД, нормализация и ETL | [`01-data-modeling-etl`](01-data-modeling-etl/) | PostgreSQL · Python · pandas · SQLAlchemy |
| 2 | Основные операторы PostgreSQL | [`02-postgresql-operators`](02-postgresql-operators/) | PostgreSQL · SQL |
| 3 | Группировка данных и оконные функции | [`03-window-functions`](03-window-functions/) | PostgreSQL · SQL |
| 4 | Выборка и агрегация данных в MongoDB | [`04-mongodb`](04-mongodb/) | MongoDB · PyMongo · Python |
| 5 | Анализ данных на Spark SQL | [`05-spark-sql`](05-spark-sql/) | Apache Spark · PySpark |
| 6 | Автоматизация расчётов в Apache Airflow | [`06-airflow`](06-airflow/) | Apache Airflow · Python |

## Стек

PostgreSQL · SQL · Python · pandas · SQLAlchemy · MongoDB / PyMongo ·
Apache Spark (PySpark) · Apache Airflow · Jupyter

## Как запустить

Технологии в модулях разные, поэтому единого окружения нет — детали запуска
описаны в README каждой папки. У модулей, где нужен Python (01, 04, 05, 06),
есть свой `requirements.txt`:

```bash
git clone https://github.com/SergeiVolkhin/data-storage-and-processing.git
cd data-storage-and-processing/01-data-modeling-etl

python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux / macOS:
source .venv/bin/activate

pip install -r requirements.txt
```

Модули 02 и 03 — это чистый SQL: достаточно выполнить `schema/schema.sql`,
а затем `reports/script.sql` в PostgreSQL.

## Структура репозитория

```
.
├── 01-data-modeling-etl/      проектирование БД, нормализация, ETL
├── 02-postgresql-operators/   операторы PostgreSQL
├── 03-window-functions/       группировка и оконные функции
├── 04-mongodb/                выборка и агрегация в MongoDB
├── 05-spark-sql/              анализ данных на Spark SQL
├── 06-airflow/                автоматизация расчётов в Airflow
├── syllabus-2025.pdf          программа курса
└── README.md
```

## Автор

Вольхин Сергей Александрович

---

# Data Storage and Processing Systems

Completed homework for the university course "Data Storage and Processing
Systems" (2025). Six assignments, from designing a relational database to
automating workflows with Apache Airflow. Each one is built on real data and
solves an applied analytical task. The course program is in
[`syllabus-2025.pdf`](syllabus-2025.pdf).

Each module is a separate folder with a README, source data and a solution —
SQL scripts, a Jupyter notebook or Python code, depending on the topic.

## Modules

See the table above. The stacks differ across modules: PostgreSQL and SQL,
MongoDB with PyMongo, Apache Spark, and Apache Airflow.

## How to run

There is no single environment — setup details are in each folder's README.
Modules that use Python (01, 04, 05, 06) ship their own `requirements.txt`;
modules 02 and 03 are plain SQL: run `schema/schema.sql`, then
`reports/script.sql` in PostgreSQL.

## Author

Sergey Volkhin

## License

MIT — see [`LICENSE`](LICENSE).
