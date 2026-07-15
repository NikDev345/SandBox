from app.models.sql_generator import SQLGeneratorRequest, SQLGeneratorResponse, GenerationMode, SQLDialect, ExecutionCost
from app.services.gemini_service import GeminiService
import sqlparse, re
from sqlparse.sql import Identifier, IdentifierList
from sqlparse.tokens import Keyword
from typing import List

class SQLGeneratorService:

    @staticmethod
    def generate(request: SQLGeneratorRequest, user=None) -> SQLGeneratorResponse:
        """
        Main entry point for SQL generation.

        Workflow
        --------
        1. Validate request
        2. Generate SQL based on selected mode
        3. Format SQL
        4. Build metadata
        5. Return response
        """

        SQLGeneratorService._validate_request(request)

        if request.mode == GenerationMode.AI:
            sql = SQLGeneratorService._generate_from_ai_prompt(
                request.prompt
            )

        elif request.mode == GenerationMode.BUILDER:
            sql = SQLGeneratorService._generate_from_builder(
                request.builder,
                request.dialect
            )

        else:
            raise ValueError(f"Unsupported generation mode: {request.mode}")

        formatted_sql = SQLGeneratorService._format_sql(sql)

        return SQLGeneratorResponse(
            success=True,
            sql=sql,
            formatted_sql=formatted_sql,
            query_type=SQLGeneratorService._detect_query_type(sql),
            tables=SQLGeneratorService._extract_tables(sql),
            complexity=SQLGeneratorService._estimate_complexity(sql),
            execution_cost=SQLGeneratorService._estimate_execution_cost(sql),
        )
        
    @staticmethod
    def _validate_request(request) -> None:
        """
        Validates the incoming SQL generation request.

        Raises:
            ValueError: If the request is invalid.
        """

        if request is None:
            raise ValueError("Request cannot be None.")

        # -----------------------------
        # Validate generation mode
        # -----------------------------
        if request.mode not in (
            GenerationMode.AI,
            GenerationMode.BUILDER,
        ):
            raise ValueError("Invalid generation mode.")

        # -----------------------------
        # AI Mode
        # -----------------------------
        if request.mode == GenerationMode.AI:

            if not request.prompt:
                raise ValueError("Prompt is required.")

            if not request.prompt.strip():
                raise ValueError("Prompt cannot be empty.")

            return

        # -----------------------------
        # Builder Mode
        # -----------------------------
        builder = request.builder

        if builder is None:
            raise ValueError("Builder configuration is required.")

        if not builder.table:
            raise ValueError("Table name is required.")

        if not builder.table.strip():
            raise ValueError("Table name cannot be empty.")

        # -----------------------------
        # Validate Columns
        # -----------------------------
        if builder.columns:

            seen = set()

            for column in builder.columns:

                if not column.strip():
                    raise ValueError("Column name cannot be empty.")

                if column in seen:
                    raise ValueError(f"Duplicate column '{column}'.")

                seen.add(column)

        # -----------------------------
        # Validate Conditions
        # -----------------------------
        if builder.conditions:

            for index, condition in enumerate(builder.conditions, start=1):

                if not condition.field.strip():
                    raise ValueError(
                        f"Condition {index}: field is required."
                    )

                if not condition.operator.strip():
                    raise ValueError(
                        f"Condition {index}: operator is required."
                    )

                if condition.value is None:
                    raise ValueError(
                        f"Condition {index}: value is required."
                    )

        # -----------------------------
        # Validate Sort
        # -----------------------------
        if builder.sort:

            for index, sort in enumerate(builder.sort, start=1):

                if not sort.field.strip():
                    raise ValueError(
                        f"Sort {index}: field is required."
                    )

        # -----------------------------
        # Validate Joins
        # -----------------------------
        if builder.joins:

            for index, join in enumerate(builder.joins, start=1):

                if not join.table.strip():
                    raise ValueError(
                        f"Join {index}: table is required."
                    )

                if not join.left_column.strip():
                    raise ValueError(
                        f"Join {index}: left column is required."
                    )

                if not join.right_column.strip():
                    raise ValueError(
                        f"Join {index}: right column is required."
                    )

        # -----------------------------
        # Validate Limit
        # -----------------------------
        if builder.limit is not None:

            if builder.limit <= 0:
                raise ValueError("Limit must be greater than 0.")
            
    @staticmethod
    def _generate_from_builder(builder, dialect) -> str:
        """
        Generates a SQL query from the Visual Builder configuration.

        The query is assembled clause-by-clause.
        """

        query_parts = []

        # SELECT
        query_parts.append(
            SQLGeneratorService._build_select_clause(builder)
        )

        # FROM
        query_parts.append(
            SQLGeneratorService._build_from_clause(builder)
        )

        # JOINS
        join_clause = SQLGeneratorService._build_join_clause(builder)

        if join_clause:
            query_parts.append(join_clause)

        # WHERE
        where_clause = SQLGeneratorService._build_where_clause(builder)

        if where_clause:
            query_parts.append(where_clause)

        # GROUP BY
        group_by_clause = SQLGeneratorService._build_group_by_clause(builder)

        if group_by_clause:
            query_parts.append(group_by_clause)

        # HAVING
        having_clause = SQLGeneratorService._build_having_clause(builder)

        if having_clause:
            query_parts.append(having_clause)

        # ORDER BY
        order_by_clause = SQLGeneratorService._build_order_by_clause(builder)

        if order_by_clause:
            query_parts.append(order_by_clause)

        # LIMIT
        limit_clause = SQLGeneratorService._build_limit_clause(
            builder,
            dialect
        )

        if limit_clause:
            query_parts.append(limit_clause)

        return "\n".join(query_parts).strip() + ";"
    
    @staticmethod
    def _build_select_clause(builder) -> str:
        """
        Builds the SELECT clause.

        Examples
        --------
        SELECT *
        SELECT id, name, salary
        SELECT DISTINCT name, department
        """

        # Default to all columns
        columns = builder.columns or ["*"]

        cleaned_columns = []

        for column in columns:

            if not column:
                continue

            column = column.strip()

            if column:
                cleaned_columns.append(column)

        if not cleaned_columns:
            cleaned_columns = ["*"]

        select_clause = "SELECT"

        # Future-proof: supports builder.distinct if added later
        if getattr(builder, "distinct", False):
            select_clause += " DISTINCT"

        select_clause += " " + ", ".join(cleaned_columns)

        return select_clause
    
    @staticmethod
    def _build_from_clause(builder) -> str:
        """
        Builds the FROM clause.

        Examples
        --------
        FROM employees
        FROM company.employees
        FROM employees e
        """

        table = builder.table.strip()

        from_clause = f"FROM {table}"

        # Future support for table alias
        table_alias = getattr(builder, "table_alias", None)

        if table_alias:
            table_alias = table_alias.strip()

            if table_alias:
                from_clause += f" {table_alias}"

        return from_clause
    
    @staticmethod
    def _build_where_clause(builder) -> str:
        """
        Builds the WHERE clause.

        Example:
        WHERE salary > 50000
          AND department = 'IT'
          OR active = TRUE
        """

        if not builder.conditions:
            return ""

        clauses = []

        total_conditions = len(builder.conditions)

        for index, condition in enumerate(builder.conditions):

            field = condition.field.strip()
            operator = condition.operator.strip().upper()

            value = SQLGeneratorService._format_sql_value(
                condition.value,
                operator,
            )

            if value:
                clause = f"{field} {operator} {value}"
            else:
                clause = f"{field} {operator}"

            # Add AND/OR except for the last condition
            if index < total_conditions - 1:
                logical = (
                    condition.logical_operator.value
                    if condition.logical_operator
                    else "AND"
                )

                clause += f" {logical}"

            clauses.append(clause)

        return "WHERE\n    " + "\n    ".join(clauses)
    
    @staticmethod
    def _format_sql_value(value, operator: str) -> str:
        """
        Formats a Python value into a SQL-compatible value.

        Examples
        --------
        "IT"            -> 'IT'
        50000           -> 50000
        99.5            -> 99.5
        True            -> TRUE
        False           -> FALSE
        None            -> NULL
        """

        operator = operator.upper().strip()

        # -----------------------------
        # IS NULL / IS NOT NULL
        # -----------------------------
        if operator in ("IS NULL", "IS NOT NULL"):
            return ""

        # -----------------------------
        # None
        # -----------------------------
        if value is None:
            return "NULL"

        # -----------------------------
        # Boolean
        # -----------------------------
        if isinstance(value, bool):
            return "TRUE" if value else "FALSE"

        # -----------------------------
        # Numbers
        # -----------------------------
        if isinstance(value, (int, float)):
            return str(value)

        # -----------------------------
        # Strings
        # -----------------------------
        if isinstance(value, str):

            value = value.strip()

            # Empty string
            if value == "":
                return "''"

            # Escape single quotes
            value = value.replace("'", "''")

            # -------------------------
            # IN (...)
            # Input:
            # IT, HR, Finance
            # -------------------------
            if operator == "IN":

                values = []

                for v in value.split(","):
                    v = v.strip()
                    if v:
                        values.append("'" + v.replace("'", "''") + "'")

                return f"({', '.join(values)})"

            # -------------------------
            # BETWEEN
            # Input:
            # 1000,5000
            # -------------------------
            if operator == "BETWEEN":

                parts = [p.strip() for p in value.split(",")]

                if len(parts) != 2:
                    raise ValueError(
                        "BETWEEN requires exactly two comma-separated values."
                    )

                return f"{parts[0]} AND {parts[1]}"

            # -------------------------
            # LIKE
            # -------------------------
            if operator == "LIKE":
                return f"'{value}'"

            return f"'{value}'"

        # -----------------------------
        # List / Tuple
        # -----------------------------
        if isinstance(value, (list, tuple, set)):

            formatted = []

            for item in value:
                formatted.append(
                    SQLGeneratorService._format_sql_value(item, "=")
                )

            return f"({', '.join(formatted)})"

        # -----------------------------
        # Fallback
        # -----------------------------
        return f"'{str(value)}'"
    
    @staticmethod
    def _build_join_clause(builder) -> str:
        """
        Builds all JOIN clauses.

        Examples
        --------
        INNER JOIN departments
            ON employees.department_id = departments.id

        LEFT JOIN salaries s
            ON employees.id = s.employee_id
        """

        if not builder.joins:
            return ""

        join_clauses = []

        for join in builder.joins:

            join_type = join.join_type.value.upper()

            table = join.table.strip()

            on_condition = (
                f"{join.left_column} "
                f"{join.operator} "
                f"{join.right_column}"
            )

            clause = (
                f"{join_type} JOIN {table}\n"
                f"    ON {on_condition}"
            )

            join_clauses.append(clause)

        return "\n".join(join_clauses)
    
    @staticmethod
    def _build_group_by_clause(builder) -> str:
        """
        Builds the GROUP BY clause.

        Examples
        --------
        GROUP BY department

        GROUP BY department, role
        """

        if not builder.group_by:
            return ""

        columns = []

        for column in builder.group_by:

            if not column:
                continue

            column = column.strip()

            if column:
                columns.append(column)

        if not columns:
            return ""

        return f"GROUP BY {', '.join(columns)}"
    
    @staticmethod
    def _build_having_clause(builder) -> str:
        """
        Builds the HAVING clause.

        Example
        -------
        HAVING
            COUNT(*) > 5 AND
            AVG(salary) > 50000
        """

        if not builder.having:
            return ""

        clauses = []

        total_conditions = len(builder.having)

        for index, condition in enumerate(builder.having):

            field = condition.field.strip()

            operator = condition.operator.strip().upper()

            value = SQLGeneratorService._format_sql_value(
                condition.value,
                operator,
            )

            if value:
                clause = f"{field} {operator} {value}"
            else:
                clause = f"{field} {operator}"

            if index < total_conditions - 1:

                logical = (
                    condition.logical_operator.value
                    if condition.logical_operator
                    else "AND"
                )

                clause += f" {logical}"

            clauses.append(clause)

        return "HAVING\n    " + "\n    ".join(clauses)
    
    @staticmethod
    def _build_order_by_clause(builder) -> str:
        """
        Builds the ORDER BY clause.

        Examples
        --------
        ORDER BY salary DESC

        ORDER BY department ASC, salary DESC
        """

        if not builder.sort:
            return ""

        order_columns = []

        for sort in builder.sort:

            field = sort.field.strip()

            if not field:
                continue

            direction = sort.direction.value.upper()

            order_columns.append(f"{field} {direction}")

        if not order_columns:
            return ""

        return f"ORDER BY {', '.join(order_columns)}"
    
    @staticmethod
    def _build_limit_clause(builder, dialect) -> str:
        """
        Builds the LIMIT/TOP/FETCH clause based on SQL dialect.

        Examples
        --------
        MySQL:
            LIMIT 10

        PostgreSQL:
            LIMIT 10

        SQLite:
            LIMIT 10

        SQL Server:
            OFFSET 0 ROWS FETCH NEXT 10 ROWS ONLY

        Oracle:
            FETCH FIRST 10 ROWS ONLY
        """

        if builder.limit is None:
            return ""

        limit = builder.limit

        if dialect in (
            SQLDialect.MYSQL,
            SQLDialect.POSTGRESQL,
            SQLDialect.SQLITE,
        ):
            return f"LIMIT {limit}"

        if dialect == SQLDialect.SQLSERVER:
            return (
                f"OFFSET 0 ROWS "
                f"FETCH NEXT {limit} ROWS ONLY"
            )

        if dialect == SQLDialect.ORACLE:
            return f"FETCH FIRST {limit} ROWS ONLY"

        return f"LIMIT {limit}"
    
    @staticmethod
    def _format_sql(sql: str) -> str:
        """
        Formats a SQL query for readability.

        Features
        --------
        - Uppercases SQL keywords
        - Lowercases identifiers
        - Proper indentation
        - Reindents nested queries
        - Removes extra whitespace
        """

        if not sql or not sql.strip():
            return ""

        return sqlparse.format(
            sql,
            reindent=True,
            keyword_case="upper",
            identifier_case=None,
            strip_comments=False,
            use_space_around_operators=True,
        ).strip()
        
    @staticmethod
    def _detect_query_type(sql: str) -> str:
        """
        Detects the SQL query type.

        Examples
        --------
        SELECT ...
        INSERT ...
        UPDATE ...
        DELETE ...
        CREATE ...
        DROP ...
        ALTER ...
        WITH ...
        """

        if not sql:
            return "UNKNOWN"

        sql = sql.strip()

        if not sql:
            return "UNKNOWN"

        first_word = sql.split(None, 1)[0].upper()

        supported_types = {
            "SELECT",
            "INSERT",
            "UPDATE",
            "DELETE",
            "CREATE",
            "ALTER",
            "DROP",
            "TRUNCATE",
            "MERGE",
            "WITH",
            "CALL",
            "EXEC",
            "EXECUTE",
        }

        if first_word in supported_types:
            return first_word

        return "UNKNOWN"
    
    @staticmethod
    def _extract_tables(sql: str) -> List[str]:
        """
        Extracts table names from a SQL query.

        Supports:
        - FROM
        - JOIN
        - Multiple tables
        - Table aliases

        Returns:
            ['employees', 'departments']
        """

        if not sql:
            return []

        statement = sqlparse.parse(sql)

        if not statement:
            return []

        statement = statement[0]

        tables = []
        capture = False

        for token in statement.tokens:

            # Start collecting after FROM or JOIN
            if token.ttype is Keyword and token.value.upper() in (
                "FROM",
                "JOIN",
                "INNER JOIN",
                "LEFT JOIN",
                "RIGHT JOIN",
                "FULL JOIN",
            ):
                capture = True
                continue

            if not capture:
                continue

            if isinstance(token, Identifier):

                tables.append(token.get_real_name())

                capture = False

            elif isinstance(token, IdentifierList):

                for identifier in token.get_identifiers():
                    tables.append(identifier.get_real_name())

                capture = False

            elif token.ttype is Keyword:
                capture = False

        return list(dict.fromkeys(tables))
    
    @staticmethod
    def _estimate_complexity(sql: str) -> str:
        """
        Estimates SQL query complexity.

        Returns:
            - Simple
            - Moderate
            - Complex
            - Very Complex
        """

        if not sql:
            return "Unknown"

        sql_upper = sql.upper()

        score = 0

        # -----------------------------
        # JOINs
        # -----------------------------
        score += sql_upper.count(" JOIN") * 2

        # -----------------------------
        # WHERE
        # -----------------------------
        if " WHERE " in sql_upper:
            score += 1

        # -----------------------------
        # GROUP BY
        # -----------------------------
        if " GROUP BY " in sql_upper:
            score += 2

        # -----------------------------
        # HAVING
        # -----------------------------
        if " HAVING " in sql_upper:
            score += 2

        # -----------------------------
        # ORDER BY
        # -----------------------------
        if " ORDER BY " in sql_upper:
            score += 1

        # -----------------------------
        # Aggregations
        # -----------------------------
        for fn in (
            "COUNT(",
            "SUM(",
            "AVG(",
            "MIN(",
            "MAX(",
        ):
            score += sql_upper.count(fn)

        # -----------------------------
        # DISTINCT
        # -----------------------------
        if " DISTINCT " in sql_upper:
            score += 1

        # -----------------------------
        # UNION
        # -----------------------------
        score += sql_upper.count(" UNION") * 3

        # -----------------------------
        # Subqueries
        # Very rough heuristic
        # -----------------------------
        score += sql_upper.count("(SELECT") * 3

        # -----------------------------
        # CTEs
        # -----------------------------
        if sql_upper.startswith("WITH "):
            score += 3

        # -----------------------------
        # CASE expressions
        # -----------------------------
        score += sql_upper.count(" CASE ") * 2

        # -----------------------------
        # Window Functions
        # -----------------------------
        score += sql_upper.count(" OVER(") * 3
        score += sql_upper.count(" OVER (") * 3

        # -----------------------------
        # Complexity Rating
        # -----------------------------
        if score <= 2:
            return "Simple"

        if score <= 6:
            return "Moderate"

        if score <= 12:
            return "Complex"

        return "Very Complex"
    
    @staticmethod
    def _estimate_execution_cost(sql: str) -> str:
        """
        Estimates the execution cost of a SQL query.

        Returns:
            - Low
            - Medium
            - High
            - Very High
        """

        if not sql:
            return "Unknown"

        sql_upper = sql.upper()

        score = 0

        # -----------------------------
        # SELECT *
        # -----------------------------
        if "SELECT *" in sql_upper:
            score += 2

        # -----------------------------
        # JOINs
        # -----------------------------
        score += sql_upper.count(" JOIN") * 3

        # -----------------------------
        # WHERE
        # -----------------------------
        if " WHERE " not in sql_upper:
            score += 3

        # -----------------------------
        # GROUP BY
        # -----------------------------
        if " GROUP BY " in sql_upper:
            score += 2

        # -----------------------------
        # HAVING
        # -----------------------------
        if " HAVING " in sql_upper:
            score += 2

        # -----------------------------
        # ORDER BY
        # -----------------------------
        if " ORDER BY " in sql_upper:
            score += 2

        # -----------------------------
        # DISTINCT
        # -----------------------------
        if " DISTINCT " in sql_upper:
            score += 1

        # -----------------------------
        # UNION
        # -----------------------------
        score += sql_upper.count(" UNION") * 3

        # -----------------------------
        # Subqueries
        # -----------------------------
        score += sql_upper.count("(SELECT") * 3

        # -----------------------------
        # Window Functions
        # -----------------------------
        score += sql_upper.count(" OVER(") * 3
        score += sql_upper.count(" OVER (") * 3

        # -----------------------------
        # LIMIT reduces work
        # -----------------------------
        if " LIMIT " in sql_upper:
            score -= 1

        # -----------------------------
        # Execution Cost
        # -----------------------------
        if score <= 3:
            label = "Low"
        elif score <= 8:
            label = "Medium"
        elif score <= 14:
            label = "High"
        else:
            label = "Very High"
        
        score_map = {"Low": 20, "Medium": 48, "High": 72, "Very High": 92}
        
        return ExecutionCost(
            label=label,
            score=score_map[label],
            factors=[],   # populate with reasons if you want
        )
    
    @staticmethod
    def _generate_from_ai_prompt(prompt: str) -> str:
        """
        Generates SQL from a natural language prompt.

        This method should:
        1. Validate the prompt.
        2. Build the AI prompt.
        3. Call the LLM.
        4. Extract SQL from the response.
        5. Validate the generated SQL.
        """

        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty.")

        system_prompt = SQLGeneratorService._build_ai_system_prompt()

        user_prompt = prompt.strip()
        final_prompt = f"{system_prompt}\n\n{user_prompt}"
        # TODO:
        # Replace with your Gemini/OpenAI implementation.
        try:
            client = GeminiService()
            response = client.generate(final_prompt)
            sql = SQLGeneratorService._extract_sql(response)
            SQLGeneratorService._validate_generated_sql(sql)
            return sql
        except Exception as e:
            raise RuntimeError(
                f"Failed to generate SQL: {e}"
            ) from e
        
    @staticmethod
    def _build_ai_system_prompt() -> str:
        """
        Returns the system prompt used for SQL generation.
        """

        return """
You are an expert SQL engineer.

Generate ONLY valid SQL.

Rules:
- Return SQL only.
- Do not include explanations.
- Do not use markdown.
- Do not wrap the SQL inside ``` blocks.
- Use ANSI SQL unless instructed otherwise.
- Assume table and column names are correct.
- Never invent tables.
- Never invent columns.
- Prefer explicit column names over SELECT *.
- Generate clean, formatted SQL.
""".strip()

    @staticmethod
    def _extract_sql(response: str) -> str:
        """
        Extracts the SQL query from an AI response.

        Supports:
        - Plain SQL
        - ```sql ... ```
        - ``` ... ```
        - SQL surrounded by explanatory text

        Raises:
            ValueError: If no SQL could be extracted.
        """

        if not response or not response.strip():
            raise ValueError("AI returned an empty response.")

        response = response.strip()

        # ----------------------------------
        # Case 1: ```sql ... ```
        # ----------------------------------
        match = re.search(
            r"```sql\s*(.*?)```",
            response,
            flags=re.IGNORECASE | re.DOTALL,
        )

        if match:
            return match.group(1).strip()

        # ----------------------------------
        # Case 2: ``` ... ```
        # ----------------------------------
        match = re.search(
            r"```\s*(.*?)```",
            response,
            flags=re.DOTALL,
        )

        if match:
            return match.group(1).strip()

        # ----------------------------------
        # Case 3: Find first SQL keyword
        # ----------------------------------
        sql_keywords = (
            "SELECT",
            "INSERT",
            "UPDATE",
            "DELETE",
            "CREATE",
            "ALTER",
            "DROP",
            "TRUNCATE",
            "MERGE",
            "WITH",
        )

        upper = response.upper()

        positions = [
            upper.find(keyword)
            for keyword in sql_keywords
            if upper.find(keyword) != -1
        ]

        if positions:

            start = min(positions)

            sql = response[start:].strip()

            if not sql.endswith(";"):
                sql += ";"

            return sql

        raise ValueError("No SQL query found in AI response.")
    
    @staticmethod
    def _validate_generated_sql(sql: str) -> None:
        """
        Validates AI-generated SQL.

        Raises:
            ValueError: If the SQL is invalid.
        """

        if not sql:
            raise ValueError("Generated SQL is empty.")

        sql = sql.strip()

        if not sql:
            raise ValueError("Generated SQL is empty.")

        # -----------------------------
        # Remove trailing whitespace
        # -----------------------------
        sql = sql.rstrip()

        # -----------------------------
        # Markdown should never exist
        # -----------------------------
        if "```" in sql:
            raise ValueError(
                "Generated SQL contains markdown."
            )

        # -----------------------------
        # Placeholder detection
        # -----------------------------
        sql_upper = sql.upper()

# Only check for actual placeholder patterns, not operators
        placeholder_patterns = [
            r"<\w+>",           # <table_name>, <column>
            r"\{[\w\s]+\}",     # {table}, {column name}
            r"\[YOUR_\w+\]",    # [YOUR_TABLE], [YOUR_COLUMN]
            r"\bTODO\b",
            r"\bYOUR_TABLE\b",
            r"\bYOUR_COLUMN\b",
        ]

        for pattern in placeholder_patterns:
            if re.search(pattern, sql, re.IGNORECASE):
                raise ValueError(
                    "Generated SQL contains placeholders."
                )

        # -----------------------------
        # Starts with valid statement
        # -----------------------------
        valid_keywords = (
            "SELECT",
            "INSERT",
            "UPDATE",
            "DELETE",
            "CREATE",
            "ALTER",
            "DROP",
            "TRUNCATE",
            "MERGE",
            "WITH",
        )

        if not sql_upper.startswith(valid_keywords):
            raise ValueError(
                "Generated SQL starts with an invalid keyword."
            )

        # -----------------------------
        # Basic parenthesis validation
        # -----------------------------
        if sql.count("(") != sql.count(")"):
            raise ValueError(
                "Unbalanced parentheses detected."
            )

        # -----------------------------
        # Basic quote validation
        # -----------------------------
        if sql.count("'") % 2 != 0:
            raise ValueError(
                "Unbalanced single quotes detected."
            )

        # -----------------------------
        # Semicolon
        # -----------------------------
        if not sql.endswith(";"):
            raise ValueError(
                "Generated SQL must end with ';'."
            )

        # -----------------------------
        # Dangerous multiple statements
        # -----------------------------
        statements = [
            stmt.strip()
            for stmt in sql.split(";")
            if stmt.strip()
        ]

        if len(statements) > 1:
            raise ValueError(
                "Multiple SQL statements are not allowed."
            )

        # -----------------------------
        # Empty WHERE
        # -----------------------------
        if re.search(r"\bWHERE\s*;$", sql_upper):
            raise ValueError(
                "WHERE clause is incomplete."
            )

        # SQL passed validation
        return