"""Test a SQL query against the database."""
import json
import sys
from sqlalchemy import text
from app.db.session import engine


def test_query(sql_query: str):
    """Execute a SQL query and return results."""
    print(f"Executing query:\n{sql_query}\n")
    print("=" * 80)
    
    try:
        with engine.begin() as conn:
            result = conn.execute(text(sql_query))
            rows = [dict(r._mapping) for r in result]
            
        print(f"\nQuery executed successfully. Found {len(rows)} rows.\n")
        print(json.dumps({"rows": rows}, indent=2, default=str))
        return rows
    except Exception as e:
        print(f"\nQuery failed with error:\n{str(e)}\n")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Query provided as command line argument
        query = sys.argv[1]
    else:
        # Default query from user
        query = """SELECT category, SUM(total_sales) FROM avalon_sunshine_customers_first_time_vs_returning_customer_sales_added_filter_traffic_avalon_sunshine_customers GROUP BY category ORDER BY SUM(total_sales) DESC LIMIT 50;"""
    
    test_query(query)

