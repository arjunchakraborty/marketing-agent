#!/usr/bin/env python3
"""Query and display all experiments from the database as JSON."""
import json
import sys
from pathlib import Path

# Add parent directory to path so we can import from app
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from app.core.config import settings


def resolve_database_url() -> str:
    """Resolve the database URL to an absolute path."""
    url = settings.database_url
    if url.startswith("sqlite:///"):
        relative_path = url.replace("sqlite:///", "")
        db_path = Path(relative_path)
        if not db_path.is_absolute():
            base_dir = Path(__file__).resolve().parents[1] / "app"
            db_path = (base_dir / relative_path).resolve()
        return f"sqlite:///{db_path}"
    return url


def query_experiments():
    """Query all experiment data and return as JSON."""
    database_url = resolve_database_url()
    print(f"Connecting to database: {database_url}", file=sys.stderr)
    
    engine = create_engine(database_url, future=True)
    
    results = {
        "experiment_runs": [],
        "campaign_analyses": [],
        "image_analyses": [],
        "visual_element_correlations": []
    }
    
    with engine.begin() as connection:
        # Query experiment runs
        print("Querying experiment_runs...", file=sys.stderr)
        result = connection.execute(text("SELECT * FROM experiment_runs ORDER BY created_at DESC"))
        for row in result:
            data = dict(row._mapping)
            # Parse JSON fields
            if data.get("config") and isinstance(data["config"], str):
                try:
                    data["config"] = json.loads(data["config"])
                except json.JSONDecodeError:
                    pass
            if data.get("results_summary") and isinstance(data["results_summary"], str):
                try:
                    data["results_summary"] = json.loads(data["results_summary"])
                except json.JSONDecodeError:
                    pass
            results["experiment_runs"].append(data)
        
        print(f"Found {len(results['experiment_runs'])} experiment runs", file=sys.stderr)
        
        # Query campaign analyses
        print("Querying campaign_analysis...", file=sys.stderr)
        result = connection.execute(text("SELECT * FROM campaign_analysis ORDER BY created_at DESC"))
        for row in result:
            data = dict(row._mapping)
            # Parse JSON fields
            if data.get("query_results") and isinstance(data["query_results"], str):
                try:
                    data["query_results"] = json.loads(data["query_results"])
                except json.JSONDecodeError:
                    pass
            if data.get("metrics") and isinstance(data["metrics"], str):
                try:
                    data["metrics"] = json.loads(data["metrics"])
                except json.JSONDecodeError:
                    pass
            if data.get("products_promoted") and isinstance(data["products_promoted"], str):
                try:
                    data["products_promoted"] = json.loads(data["products_promoted"])
                except json.JSONDecodeError:
                    pass
            results["campaign_analyses"].append(data)
        
        print(f"Found {len(results['campaign_analyses'])} campaign analyses", file=sys.stderr)
        
        # Query image analyses
        print("Querying image_analysis_results...", file=sys.stderr)
        result = connection.execute(text("SELECT * FROM image_analysis_results ORDER BY created_at DESC"))
        for row in result:
            data = dict(row._mapping)
            # Parse JSON fields
            if data.get("visual_elements") and isinstance(data["visual_elements"], str):
                try:
                    data["visual_elements"] = json.loads(data["visual_elements"])
                except json.JSONDecodeError:
                    pass
            if data.get("dominant_colors") and isinstance(data["dominant_colors"], str):
                try:
                    data["dominant_colors"] = json.loads(data["dominant_colors"])
                except json.JSONDecodeError:
                    pass
            results["image_analyses"].append(data)
        
        print(f"Found {len(results['image_analyses'])} image analyses", file=sys.stderr)
        
        # Query visual element correlations
        print("Querying visual_element_correlations...", file=sys.stderr)
        result = connection.execute(text("SELECT * FROM visual_element_correlations ORDER BY created_at DESC"))
        for row in result:
            data = dict(row._mapping)
            # Parse JSON fields
            if data.get("average_performance") and isinstance(data["average_performance"], str):
                try:
                    data["average_performance"] = json.loads(data["average_performance"])
                except json.JSONDecodeError:
                    pass
            results["visual_element_correlations"].append(data)
        
        print(f"Found {len(results['visual_element_correlations'])} visual element correlations", file=sys.stderr)
    
    return results


def main():
    """Main entry point."""
    try:
        results = query_experiments()
        # Print JSON to stdout
        print(json.dumps(results, indent=2, default=str))
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
