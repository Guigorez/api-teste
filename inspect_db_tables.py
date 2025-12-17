import sqlite3
import pandas as pd

try:
    conn = sqlite3.connect('vendas_animoshop.db')
    tables = pd.read_sql_query("SELECT name FROM sqlite_master WHERE type='table'", conn)
    print("Tables in DB:")
    print(tables)
    conn.close()
except Exception as e:
    print(e)
