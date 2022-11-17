import os
from typing import Dict, List, Tuple

import sqlite3


conn = sqlite3.connect(os.path.join("db", "unions.db"))
cursor = conn.cursor()


def insert(table: str, column_values: Dict):
    columns = ', '.join(column_values.keys())
    values = [tuple(column_values.values())]
    placeholders = ", ".join("?" * len(column_values.keys()))
    cursor.executemany(
        f"INSERT INTO {table} "
        f"({columns}) "
        f"VALUES ({placeholders})",
        values)
    conn.commit()


def get_user(user_id: int):
    cursor.execute(
        f"SELECT user_id FROM users "
        f"WHERE user_id={user_id}")
    user = cursor.fetchall()
    return user


def get_users_unions(user_id: int, columns: List[str] = None) -> List[Tuple]:
    if not columns:
        columns = ['union_id', 'name', 'rebate', 'user_id']
    columns_joined = ", ".join(columns)
    cursor.execute(
        f"SELECT {columns_joined}  FROM unions "
        f"WHERE user_id={user_id}")
    unions = cursor.fetchall()
    result = []
    for row in unions:
        dict_row = {}
        for index, column in enumerate(columns):
            dict_row[column] = row[index]
        result.append(dict_row)
    return result


def get_unions_clubs(union_id: int, columns: List[str] = None) -> List[Tuple]:
    if not columns:
        columns = ['club_id', 'name', 'comission', 'participate', 'union_id']
    columns_joined = ", ".join(columns)
    cursor.execute(
        f"SELECT {columns_joined} FROM clubs "
        f"WHERE union_id={union_id}")
    clubs = cursor.fetchall()
    result = []
    for row in clubs:
        dict_row = {}
        for index, column in enumerate(columns):
            dict_row[column] = row[index]
        result.append(dict_row)
    return result


def fetchall(table: str, columns: List[str]) -> List[Tuple]:
    columns_joined = ", ".join(columns)
    cursor.execute(f"SELECT {columns_joined} FROM {table}")
    rows = cursor.fetchall()
    result = []
    for row in rows:
        dict_row = {}
        for index, column in enumerate(columns):
            dict_row[column] = row[index]
        result.append(dict_row)
    return result


def delete(table: str, row_id: int) -> None:
    row_id = int(row_id)
    cursor.execute(f"delete from {table} where id={row_id}")
    conn.commit()


def get_cursor():
    return cursor


def _init_db():
    """Инициализирует БД"""
    with open("createdb.sql", "r") as f:
        sql = f.read()
    cursor.executescript(sql)
    conn.commit()


def check_db_exists():
    """Проверяет, инициализирована ли БД, если нет — инициализирует"""
    cursor.execute("SELECT name FROM sqlite_master "
                   "WHERE type='table' AND name='expense'")
    table_exists = cursor.fetchall()
    if table_exists:
        return
    _init_db()
