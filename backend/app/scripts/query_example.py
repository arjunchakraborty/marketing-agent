"""Small runnable examples showing how to query the DB in this project.

This file uses an in-memory SQLite DB so you can run it without touching your real project DB.
It demonstrates two common styles used in the codebase:
  - engine.begin() + connection.execute(text(...)) for raw SQL
  - Session(...).execute(...) for working with a session

Run:
  python backend/app/scripts/query_example.py

Also shows snippets for using the project `engine` and `get_session`.
"""
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session  


from datetime import datetime, timedelta



# Compute start date in Python (UTC date)
start_date = (datetime.utcnow() - timedelta(days=14)).date().isoformat()

# Use NULLIF to protect against divide-by-zero, cast to REAL for numeric ops if needed
sql = text("""
SELECT 
    b.category,
    SUM(CAST(s.gross_sales AS REAL)) AS total_sales,
    SUM(CAST(s.orders AS REAL)) AS total_orders,
    SUM(CAST(s.total_sales AS REAL) / NULLIF(CAST(s.orders AS REAL), 0)) AS roas,
    SUM(CAST(s.orders AS REAL) / NULLIF(CAST((s.total_visitors - s.total_sessions) AS REAL), 0)) AS blended_cpa
FROM 
    "avalon_sunshine_acquisition_sessions_over_time__avalon_sunshine_acquisition" a
JOIN 
    "avalon_sunshine_behavior_online_store_conversion_over_time_avalon_sunshine_behavior" b
      ON a.business_name = b.business_name AND a.category = b.category
JOIN 
    "rf_design_co_acquisition_sessions_over_time__rfdesignco_acquisition" c
      ON a.business_name = c.business_name AND a.category = c.category
WHERE 
    a.month >= :start_date
GROUP BY 
    b.category
LIMIT :limit;
""")

dfe 

with engine.begin() as conn:
    result = conn.execute(sql, {"start_date": start_date, "limit": 50})
    rows = [dict(r._mapping) for r in result]
    for row in rows:
        print(row)


def engine_example():
    print("== engine_example (in-memory SQLite) ==")
    eng = create_engine("sqlite:///:memory:", future=True)
    with eng.begin() as conn:
        # create table + insert
        conn.execute(text("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)"))
        conn.execute(text("INSERT INTO users (name) VALUES (:name)"), [{"name": "Alice"}, {"name": "Bob"}])

        # run a query (similar to AnalyticsService._load_available_datasets)
        result = conn.execute(text("SELECT id, name FROM users WHERE name LIKE :p"), {"p": "%A%"})
        rows = result.fetchall()
        print("rows (engine):", rows)


def session_example():
    print("== session_example (in-memory SQLite) ==")
    eng = create_engine("sqlite:///:memory:", future=True)

    # prepare data
    with eng.begin() as conn:
        conn.execute(text("CREATE TABLE items (id INTEGER PRIMARY KEY, value TEXT)"))
        conn.execute(text("INSERT INTO items (value) VALUES (:v)"), [{"v": "one"}, {"v": "two"}])

    # Use a Session to query (this mirrors how you'd use get_session() in FastAPI dependencies)
    with Session(eng) as session:
        res = session.execute(text("SELECT id, value FROM items WHERE value = :val"), {"val": "one"})
        rows = res.fetchall()
        print("rows (session):", rows)


if __name__ == "__main__":
    engine_example()
    session_example()

    # Example snippets for using the project's DB (don't execute here unless you're okay hitting the real DB file):
    print("\n== Project usage snippets (do not run automatically) ==")
    print("1) Raw SQL using project engine:")
    print('''
from backend.app.db.session import engine
from sqlalchemy import text

with engine.begin() as connection:
    result = connection.execute(text("SELECT * FROM my_table WHERE id = :id"), {"id": 1})
    rows = result.fetchall()
''')

    print("2) FastAPI dependency style (get_session):")
    print('''
from fastapi import Depends
from backend.app.db.session import get_session
from sqlalchemy.orm import Session

# in a FastAPI endpoint
def read_items(db: Session = Depends(get_session)):
    result = db.execute(text("SELECT * FROM items"))
    return [dict(r._mapping) for r in result]
''')
