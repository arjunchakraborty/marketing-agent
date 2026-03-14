"""Run a parameterized version of the user SQL against the project's SQLite DB
stored under `storage/marketing_agent.db` (as configured in `backend/app/core/config.py`).

Usage:
  python backend/app/scripts/run_custom_query.py --days-back 14 --limit 50

The script uses the project's `engine` so it will resolve the same DB file used by the app.
It protects against division-by-zero with NULLIF and prints results as JSON.
"""
import json
import traceback
from datetime import datetime, timedelta
from argparse import ArgumentParser

from sqlalchemy import text

# Import the project's engine (it resolves relative sqlite path to absolute storage/marketing_agent.db)
from backend.app.db.session import engine


DEFAULT_SQL = """
SELECT 
    b.category,
    SUM(CAST(s.gross_sales AS REAL)) AS total_sales,
    SUM(CAST(s.orders AS REAL)) AS total_orders,
    SUM(CAST(s.total_sales AS REAL) / NULLIF(CAST(s.orders AS REAL), 0)) AS roas,
    SUM(CAST(s.orders AS REAL) / NULLIF(CAST((s.total_visitors - s.total_sessions) AS REAL), 0)) AS blended_cpa
FROM 
    "avalon_sunshine_acquisition_sessions_over_time__avalon_sunshine_acquisition" a
JOIN 
    "avalon_sunshine_behavior_online_store_conversion_over_time_avalon_sunshine_behavior" b ON a.business_name = b.business_name AND a.category = b.category
JOIN 
    "rf_design_co_acquisition_sessions_over_time__rfdesignco_acquisition" c ON a.business_name = c.business_name AND a.category = c.category
WHERE 
    a.month >= :start_date
GROUP BY 
    b.category
LIMIT :limit;
"""


def run_query(days_back: int = 14, limit: int = 50, sql: str = DEFAULT_SQL):
    start_date = (datetime.utcnow() - timedelta(days=days_back)).date().isoformat()
    params = {"start_date": start_date, "limit": limit}

    print(f"Connecting to DB via project's engine and using start_date={start_date} limit={limit}")

    try:
        with engine.begin() as conn:
            result = conn.execute(text(sql), params)
            rows = [dict(r._mapping) for r in result]

        print(json.dumps({"rows": rows}, indent=2, default=str))
    except Exception as e:
        print("Query failed:")
        traceback.print_exc()


def main():
    p = ArgumentParser()
    p.add_argument("--days-back", type=int, default=14, help="how many days back to compare (default: 14)")
    p.add_argument("--limit", type=int, default=50, help="limit rows (default: 50)")
    p.add_argument("--sql-file", type=str, default=None, help="path to .sql file to use instead of built-in query")
    args = p.parse_args()

    sql = DEFAULT_SQL
    if args.sql_file:
        with open(args.sql_file, "r") as f:
            sql = f.read()

    run_query(days_back=args.days_back, limit=args.limit, sql=sql)


if __name__ == "__main__":
    main()
