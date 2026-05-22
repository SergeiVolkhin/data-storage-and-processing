#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Главный скрипт-оркестратор.
Запускает ETL-процессы в правильном порядке (Шаг 1, затем Шаг 2).
"""

import sys
import etl_1
import etl_2
from sqlalchemy import exc

def main_orchestrator():
    """
    Выполняет полный цикл ETL.
    """
    print("СТАРТ: ПОЛНЫЙ ETL-ЦИКЛ")

    try:
        # ШАГ 1: ЗАГРУЗКА СПРАВОЧНИКОВ
        print("\n1. Запуск etl_1 (Справочники)")
        etl_1.main()
        print("1. etl_1 (Справочники) УСПЕШНО ЗАВЕРШЕН")

        # ШАГ 2: ЗАГРУЗКА ОСНОВНЫХ ТАБЛИЦ
        print("\n2. Запуск etl_2 (Основные таблицы)")
        etl_2.main()
        print("2. etl_2 (Основные таблицы) УСПЕШНО ЗАВЕРШЕН")

        print("\nПОЛНЫЙ ETL-ЦИКЛ УСПЕШНО ЗАВЕРШЕН")

    except (FileNotFoundError, exc.SQLAlchemyError) as e:
        print(f"\nКРИТИЧЕСКАЯ ОШИБКА ETL: {e} ")
        print("Цикл прерван.")
        sys.exit(1)
    except Exception as e:
        print(f"\nНЕПРЕДВИДЕННАЯ ОШИБКА: {e} ")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main_orchestrator()