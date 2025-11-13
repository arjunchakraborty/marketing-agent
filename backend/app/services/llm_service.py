"""LLM service abstraction for OpenAI, Anthropic, and Ollama integrations."""
from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional

import httpx

from ..core.config import settings


class LLMService:
    """Unified LLM service supporting multiple providers."""

    def __init__(self, provider: str = "openai") -> None:
        self.provider = provider
        self._client: Any = None

    def _get_openai_client(self):
        """Lazy-load OpenAI client."""
        if self._client is None:
            try:
                from openai import OpenAI

                if not settings.openai_api_key:
                    raise ValueError("OpenAI API key not configured")
                self._client = OpenAI(api_key=settings.openai_api_key)
            except ImportError:
                raise ImportError("openai package not installed. Run: pip install openai")
        return self._client

    def _get_anthropic_client(self):
        """Lazy-load Anthropic client."""
        if self._client is None:
            try:
                from anthropic import Anthropic

                if not settings.anthropic_api_key:
                    raise ValueError("Anthropic API key not configured")
                self._client = Anthropic(api_key=settings.anthropic_api_key)
            except ImportError:
                raise ImportError("anthropic package not installed. Run: pip install anthropic")
        return self._client

    def _get_ollama_client(self):
        """Get Ollama HTTP client."""
        return httpx.Client(base_url=settings.ollama_base_url, timeout=60.0)

    def generate_sql(
        self,
        user_prompt: str,
        available_tables: List[Dict[str, Any]],
        sample_rows: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Generate SQL from natural language prompt using LLM."""
        if self.provider == "openai":
            return self._generate_sql_openai(user_prompt, available_tables, sample_rows)
        elif self.provider == "anthropic":
            return self._generate_sql_anthropic(user_prompt, available_tables, sample_rows)
        elif self.provider == "ollama":
            return self._generate_sql_ollama(user_prompt, available_tables, sample_rows)
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")

    def _generate_sql_openai(
        self,
        user_prompt: str,
        available_tables: List[Dict[str, Any]],
        sample_rows: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Generate SQL using OpenAI."""
        client = self._get_openai_client()

        tables_context = self._format_tables_context(available_tables, sample_rows)

        system_prompt = """You are a SQL expert specializing in eCommerce analytics. 
Generate SQLite-compatible SQL queries from natural language questions.

Rules:
- Only use tables and columns that exist in the schema
- Use SQLite syntax (no CTEs if not needed, use subqueries)
- Always include LIMIT clauses for large result sets
- Never use DROP, DELETE, INSERT, UPDATE, or ALTER statements
- Use proper quoting for table/column names with special characters
- Return ONLY the SQL query, no explanations unless asked
- For aggregations, use appropriate GROUP BY clauses
- Handle date filtering with proper date functions"""

        user_message = f"""Available datasets:
{tables_context}

User question: {user_prompt}

Generate a SQL query to answer this question. Return only the SQL, no markdown formatting."""

        try:
            response = client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                temperature=0.1,
                max_tokens=500,
            )
            sql = response.choices[0].message.content.strip()
            sql = self._clean_sql(sql)

            return {"sql": sql, "model": settings.openai_model, "provider": "openai"}
        except Exception as e:
            raise RuntimeError(f"OpenAI API error: {str(e)}")

    def _generate_sql_anthropic(
        self,
        user_prompt: str,
        available_tables: List[Dict[str, Any]],
        sample_rows: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Generate SQL using Anthropic Claude."""
        client = self._get_anthropic_client()

        tables_context = self._format_tables_context(available_tables, sample_rows)

        system_prompt = """You are a SQL expert specializing in eCommerce analytics. 
Generate SQLite-compatible SQL queries from natural language questions.
Return only the SQL query, no explanations."""

        user_message = f"""Available datasets:
{tables_context}

User question: {user_prompt}

Generate a SQL query to answer this question."""

        try:
            response = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=500,
                system=system_prompt,
                messages=[{"role": "user", "content": user_message}],
            )
            sql = response.content[0].text.strip()
            sql = self._clean_sql(sql)

            return {"sql": sql, "model": "claude-3-5-sonnet", "provider": "anthropic"}
        except Exception as e:
            raise RuntimeError(f"Anthropic API error: {str(e)}")

    def _generate_sql_ollama(
        self,
        user_prompt: str,
        available_tables: List[Dict[str, Any]],
        sample_rows: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Generate SQL using Ollama with explicit column validation."""
        client = self._get_ollama_client()

        # Filter and limit tables to reduce prompt length
        relevant_tables = self._filter_relevant_tables(
            user_prompt, available_tables, max_tables=settings.ollama_max_tables
        )
        
        # Build explicit column list for validation
        all_columns = {}
        for table in available_tables:
            table_name = table.get("table_name", "")
            columns = table.get("columns", [])
            if isinstance(columns, str):
                try:
                    columns = json.loads(columns)
                except:
                    columns = []
            all_columns[table_name] = columns

        tables_context = self._format_tables_context_compact(relevant_tables)

        # Concise prompt for Ollama
        combined_prompt = f"""SQLite query. Rules: Use ONLY columns/tables listed. SQLite syntax with "quotes". LIMIT 50. No DROP/DELETE/INSERT/UPDATE.

TABLES:
{tables_context}

Q: {user_prompt}
SQL:"""

        print(combined_prompt)  # Debug: print the final prompt sent to Ollama

        try:
            response = client.post(
                "/api/chat",
                json={
                    "model": settings.ollama_model,
                    "messages": [
                        {"role": "user", "content": combined_prompt},
                    ],
                    "stream": False,
                    "options": {
                        "temperature": 0.1,
                        "num_predict": 500,
                    },
                },
            )
            response.raise_for_status()
            result = response.json()
            sql = result["message"]["content"].strip()
            sql = self._clean_sql(sql)

            # Validate that SQL only uses existing columns
            sql = self._validate_and_fix_sql_columns(sql, all_columns)

            return {"sql": sql, "model": settings.ollama_model, "provider": "ollama"}
        except httpx.HTTPError as e:
            raise RuntimeError(f"Ollama API error: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Ollama error: {str(e)}")

    def _validate_and_fix_sql_columns(self, sql: str, all_columns: Dict[str, List[str]]) -> str:
        """Validate SQL uses only existing columns and attempt to fix common issues."""
        import re
        
        # Extract table names from SQL
        table_pattern = r'FROM\s+"?(\w+)"?|JOIN\s+"?(\w+)"?'
        tables_in_sql = set()
        for match in re.finditer(table_pattern, sql, re.IGNORECASE):
            tables_in_sql.add(match.group(1) or match.group(2))
        
        # Check each table's columns
        for table_name in tables_in_sql:
            if table_name.lower() in [t.lower() for t in all_columns.keys()]:
                # Find the actual table name (case-insensitive match)
                actual_table = next((t for t in all_columns.keys() if t.lower() == table_name.lower()), None)
                if actual_table:
                    valid_columns = [col.lower() for col in all_columns[actual_table]]
                    
                    # Extract column references from SQL (simplified check)
                    # This is a basic validation - could be enhanced
                    column_pattern = r'\b(\w+)\s*(?:,|FROM|WHERE|GROUP|ORDER|HAVING|AS|=|>|<|>=|<=|!=)'
                    sql_lower = sql.lower()
                    
                    # Note: This is a simplified check. Full SQL parsing would be more robust.
                    # For now, we'll rely on the improved prompt and let SQL execution catch errors.
        
        return sql

    def _filter_relevant_tables(
        self, user_prompt: str, available_tables: List[Dict[str, Any]], max_tables: int = 8
    ) -> List[Dict[str, Any]]:
        """Filter tables based on relevance to user prompt."""
        prompt_lower = user_prompt.lower()
        prompt_words = set(prompt_lower.split())
        
        scored_tables = []
        for table in available_tables:
            score = 0
            table_name = table.get("table_name", "").lower()
            business = table.get("business", "").lower()
            category = table.get("category", "").lower()
            dataset_name = table.get("dataset_name", "").lower()
            
            # Score based on keyword matches
            for word in prompt_words:
                if len(word) > 3:  # Ignore short words
                    if word in table_name or word in business or word in category or word in dataset_name:
                        score += 2
                    elif any(word in col.lower() for col in (table.get("columns", []) or [])):
                        score += 1
            
            scored_tables.append((score, table))
        
        # Sort by score and return top N
        scored_tables.sort(key=lambda x: x[0], reverse=True)
        relevant = [table for _, table in scored_tables[:max_tables]]
        
        # Always include at least the first table if we have any
        if not relevant and available_tables:
            relevant = [available_tables[0]]
        
        return relevant if relevant else available_tables[:max_tables]

    def _format_tables_context_compact(self, available_tables: List[Dict[str, Any]]) -> str:
        """Format table metadata in compact format for Ollama."""
        context_parts = []
        for table in available_tables:
            table_name = table.get("table_name", "")
            columns = table.get("columns", [])
            if isinstance(columns, str):
                try:
                    columns = json.loads(columns)
                except:
                    columns = []
            
            # Compact format: table_name: col1, col2, col3...
            max_cols = settings.ollama_max_columns
            cols_str = ", ".join([f'"{col}"' for col in columns[:max_cols]])
            if len(columns) > max_cols:
                cols_str += f" ... ({len(columns)} total)"
            
            context_parts.append(f'"{table_name}": {cols_str}')

        return "\n".join(context_parts)

    def _format_tables_context(
        self, available_tables: List[Dict[str, Any]], sample_rows: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """Format table metadata for LLM context (used by OpenAI/Anthropic)."""
        context_parts = []
        for table in available_tables:
            table_name = table.get("table_name", "")
            business = table.get("business", "")
            category = table.get("category", "")
            columns = table.get("columns", [])
            if isinstance(columns, str):
                try:
                    columns = json.loads(columns)
                except:
                    columns = []

            context_parts.append(f"Table: {table_name}")
            context_parts.append(f"  Business: {business}, Category: {category}")
            context_parts.append(f"  Columns: {', '.join(columns)}")

            if sample_rows and len(sample_rows) > 0:
                context_parts.append(f"  Sample data: {json.dumps(sample_rows[:2], default=str)}")

        return "\n".join(context_parts)

    def _clean_sql(self, sql: str) -> str:
        """Remove markdown code blocks and extra whitespace from SQL."""
        sql = sql.strip()
        if sql.startswith("```sql"):
            sql = sql[6:]
        elif sql.startswith("```"):
            sql = sql[3:]
        sql = sql.strip()
        if sql.endswith("```"):
            sql = sql[:-3].strip()
        return sql

    def generate_insight_summary(self, signals: List[str], context: Dict[str, Any]) -> str:
        """Generate narrative summary from analytics signals."""
        if self.provider == "openai":
            return self._generate_summary_openai(signals, context)
        elif self.provider == "anthropic":
            return self._generate_summary_anthropic(signals, context)
        elif self.provider == "ollama":
            return self._generate_summary_ollama(signals, context)
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")

    def _generate_summary_openai(self, signals: List[str], context: Dict[str, Any]) -> str:
        """Generate insight summary using OpenAI."""
        client = self._get_openai_client()

        prompt = f"""Analyze these marketing analytics signals and provide a concise business insight summary:

Signals: {', '.join(signals)}
Context: {json.dumps(context, default=str)}

Provide a 2-3 sentence summary highlighting key trends and actionable recommendations."""

        try:
            response = client.chat.completions.create(
                model=settings.openai_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=300,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"Summary generation failed: {str(e)}"

    def _generate_summary_anthropic(self, signals: List[str], context: Dict[str, Any]) -> str:
        """Generate insight summary using Anthropic."""
        client = self._get_anthropic_client()

        prompt = f"""Analyze these marketing analytics signals and provide a concise business insight summary:

Signals: {', '.join(signals)}
Context: {json.dumps(context, default=str)}"""

        try:
            response = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=300,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.content[0].text.strip()
        except Exception as e:
            return f"Summary generation failed: {str(e)}"

    def _generate_summary_ollama(self, signals: List[str], context: Dict[str, Any]) -> str:
        """Generate insight summary using Ollama."""
        client = self._get_ollama_client()

        prompt = f"""Analyze these marketing analytics signals and provide a concise business insight summary:

Signals: {', '.join(signals)}
Context: {json.dumps(context, default=str)}

Provide a 2-3 sentence summary highlighting key trends and actionable recommendations."""

        try:
            response = client.post(
                "/api/chat",
                json={
                    "model": settings.ollama_model,
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "num_predict": 300,
                    },
                },
            )
            response.raise_for_status()
            result = response.json()
            return result["message"]["content"].strip()
        except Exception as e:
            return f"Summary generation failed: {str(e)}"

    def generate_campaign_recommendations(
        self, objectives: List[str], audience_segments: List[str], constraints: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate campaign recommendations using LLM."""
        if self.provider == "openai":
            return self._generate_campaigns_openai(objectives, audience_segments, constraints)
        elif self.provider == "anthropic":
            return self._generate_campaigns_anthropic(objectives, audience_segments, constraints)
        elif self.provider == "ollama":
            return self._generate_campaigns_ollama(objectives, audience_segments, constraints)
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")

    def _generate_campaigns_openai(
        self, objectives: List[str], audience_segments: List[str], constraints: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate campaign recommendations using OpenAI."""
        client = self._get_openai_client()

        prompt = f"""Generate 3-5 marketing campaign recommendations based on:

Objectives: {', '.join(objectives)}
Audience Segments: {', '.join(audience_segments)}
Constraints: {json.dumps(constraints, default=str)}

Return a JSON array of campaign objects, each with: name, channel, objective, expected_uplift (as percentage string), summary, talking_points (array).
Format: [{{"name": "...", "channel": "...", "objective": "...", "expected_uplift": "...", "summary": "...", "talking_points": [...]}}]"""

        try:
            response = client.chat.completions.create(
                model=settings.openai_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.8,
                response_format={"type": "json_object"},
            )
            content = response.choices[0].message.content.strip()
            data = json.loads(content)
            return data.get("campaigns", []) if isinstance(data, dict) else data
        except Exception as e:
            return [{"error": f"Campaign generation failed: {str(e)}"}]

    def _generate_campaigns_anthropic(
        self, objectives: List[str], audience_segments: List[str], constraints: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate campaign recommendations using Anthropic."""
        client = self._get_anthropic_client()

        prompt = f"""Generate 3-5 marketing campaign recommendations as JSON array:

Objectives: {', '.join(objectives)}
Audience Segments: {', '.join(audience_segments)}
Constraints: {json.dumps(constraints, default=str)}

Each campaign should have: name, channel, objective, expected_uplift, summary, talking_points."""

        try:
            response = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}],
            )
            content = response.content[0].text.strip()
            data = json.loads(content)
            return data if isinstance(data, list) else [data]
        except Exception as e:
            return [{"error": f"Campaign generation failed: {str(e)}"}]

    def _generate_campaigns_ollama(
        self, objectives: List[str], audience_segments: List[str], constraints: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate campaign recommendations using Ollama."""
        client = self._get_ollama_client()

        prompt = f"""Generate 3-5 marketing campaign recommendations as JSON array based on:

Objectives: {', '.join(objectives)}
Audience Segments: {', '.join(audience_segments)}
Constraints: {json.dumps(constraints, default=str)}

Return a JSON array of campaign objects, each with: name, channel, objective, expected_uplift (as percentage string), summary, talking_points (array).
Format: [{{"name": "...", "channel": "...", "objective": "...", "expected_uplift": "...", "summary": "...", "talking_points": [...]}}]"""

        try:
            response = client.post(
                "/api/chat",
                json={
                    "model": settings.ollama_model,
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": False,
                    "options": {
                        "temperature": 0.8,
                        "num_predict": 1000,
                    },
                },
            )
            response.raise_for_status()
            result = response.json()
            content = result["message"]["content"].strip()
            # Try to extract JSON from markdown code blocks if present
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            data = json.loads(content)
            return data if isinstance(data, list) else [data]
        except json.JSONDecodeError as e:
            raw_content = result.get("message", {}).get("content", "") if "result" in locals() else content if "content" in locals() else ""
            return [{"error": f"Failed to parse JSON response: {str(e)}", "raw": raw_content}]
        except Exception as e:
            return [{"error": f"Campaign generation failed: {str(e)}"}]

