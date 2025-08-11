from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import re
import sqlparse
from sqlparse.sql import IdentifierList, Identifier, Function
from sqlparse.tokens import Keyword, DML

app = FastAPI(title="SQL Optimizer", description="SQL Query Optimization Dashboard")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SQLQuery(BaseModel):
    query: str
    database_type: str = Field(default="mysql", description="Database type: mysql, postgresql, oracle, sqlserver")

class OptimizationSuggestion(BaseModel):
    type: str
    severity: str
    title: str
    description: str
    suggestion: str
    example: Optional[str] = Field(default="")

class AnalysisResult(BaseModel):
    query: str
    database_type: str
    suggestions: List[OptimizationSuggestion]
    complexity_score: int
    execution_plan_tips: List[str]
    syntax_errors: List[str] = Field(default_factory=list)

class SQLAnalyzer:
    def __init__(self):
        self.optimization_rules = {
            'syntax_validation': self._check_syntax_errors,
            'select_star': self._check_select_star,
            'missing_where': self._check_missing_where,
            'non_sargable': self._check_non_sargable_conditions,
            'subquery_optimization': self._check_subqueries,
            'join_optimization': self._check_joins,
            'index_suggestions': self._suggest_indexes,
            'limit_clause': self._check_limit_clause,
            'order_by_optimization': self._check_order_by,
            'function_in_where': self._check_functions_in_where,
            'unnecessary_distinct': self._check_unnecessary_distinct,
            'database_specific': self._check_database_specific_rules
        }
        
        # Database-specific configurations
        self.database_configs = {
            'mysql': {
                'limit_keyword': 'LIMIT',
                'top_keyword': None,
                'quote_char': '`',
                'string_concat': 'CONCAT',
                'date_functions': ['NOW()', 'CURDATE()', 'CURTIME()', 'DATE()', 'YEAR()', 'MONTH()', 'DAY()'],
                'specific_functions': ['GROUP_CONCAT', 'IFNULL', 'IF'],
                'supports_cte': True,
                'supports_window_functions': True,
                'max_index_length': 767,
                'case_sensitive': False
            },
            'postgresql': {
                'limit_keyword': 'LIMIT',
                'top_keyword': None,
                'quote_char': '"',
                'string_concat': '||',
                'date_functions': ['NOW()', 'CURRENT_DATE', 'CURRENT_TIME', 'DATE_PART()', 'EXTRACT()'],
                'specific_functions': ['STRING_AGG', 'COALESCE', 'NULLIF'],
                'supports_cte': True,
                'supports_window_functions': True,
                'max_index_length': None,
                'case_sensitive': True
            },
            'oracle': {
                'limit_keyword': None,
                'top_keyword': None,
                'quote_char': '"',
                'string_concat': '||',
                'date_functions': ['SYSDATE', 'CURRENT_DATE', 'SYSTIMESTAMP', 'EXTRACT()', 'TO_DATE()'],
                'specific_functions': ['LISTAGG', 'NVL', 'NVL2', 'DECODE'],
                'supports_cte': True,
                'supports_window_functions': True,
                'max_index_length': None,
                'case_sensitive': False,
                'uses_rownum': True,
                'dual_table': True
            },
            'sqlserver': {
                'limit_keyword': None,
                'top_keyword': 'TOP',
                'quote_char': '[',
                'string_concat': '+',
                'date_functions': ['GETDATE()', 'CURRENT_TIMESTAMP', 'DATEPART()', 'DATEDIFF()', 'YEAR()', 'MONTH()', 'DAY()'],
                'specific_functions': ['STRING_AGG', 'ISNULL', 'IIF', 'CHOOSE'],
                'supports_cte': True,
                'supports_window_functions': True,
                'max_index_length': 900,
                'case_sensitive': False,
                'uses_go': True
            }
        }
        
        # Common misspellings of SQL keywords (database-agnostic)
        self.common_misspellings = {
            'SELET': 'SELECT',
            'SELCT': 'SELECT',
            'SLECT': 'SELECT',
            'SEELCT': 'SELECT',
            'FORM': 'FROM',
            'FRON': 'FROM',
            'WHRE': 'WHERE',
            'WHER': 'WHERE',
            'WERE': 'WHERE',
            'WEHRE': 'WHERE',
            'JION': 'JOIN',
            'JONIN': 'JOIN',
            'JONI': 'JOIN',
            'INNNER': 'INNER',
            'INENR': 'INNER',
            'LEFFT': 'LEFT',
            'RIHGT': 'RIGHT',
            'RIGTH': 'RIGHT',
            'OERDER': 'ORDER',
            'ORDRE': 'ORDER',
            'ORDR': 'ORDER',
            'GROPU': 'GROUP',
            'GRPOU': 'GROUP',
            'HAVIG': 'HAVING',
            'HAVNG': 'HAVING',
            'INSER': 'INSERT',
            'INSRT': 'INSERT',
            'UPDAT': 'UPDATE',
            'UPDAE': 'UPDATE',
            'DELET': 'DELETE',
            'DELEET': 'DELETE',
            'CREAT': 'CREATE',
            'CRAETE': 'CREATE',
            'DISTINC': 'DISTINCT',
            'DISTINT': 'DISTINCT'
        }
    
    def analyze_query(self, query: str, database_type: str = "mysql") -> AnalysisResult:
        # Validate database type
        if database_type not in self.database_configs:
            database_type = "mysql"  # Default fallback
        
        # Check for syntax errors first
        syntax_errors = []
        
        try:
            # Parse the SQL query
            parsed = sqlparse.parse(query)[0]
        except Exception as e:
            syntax_errors.append(f"SQL parsing failed: {str(e)}")
            # Return early with syntax errors
            return AnalysisResult(
                query=query,
                database_type=database_type,
                suggestions=[],
                complexity_score=0,
                execution_plan_tips=[],
                syntax_errors=syntax_errors
            )
        
        suggestions = []
        for rule_name, rule_func in self.optimization_rules.items():
            try:
                if rule_name in ['syntax_validation', 'database_specific']:
                    rule_result = rule_func(query, parsed, database_type)
                    if isinstance(rule_result, list) and len(rule_result) > 0:
                        if rule_name == 'syntax_validation' and isinstance(rule_result[0], str):
                            # These are syntax errors
                            syntax_errors.extend(rule_result)
                        else:
                            # These are optimization suggestions
                            suggestions.extend(rule_result)
                else:
                    rule_suggestions = rule_func(query, parsed)
                    if rule_suggestions:
                        suggestions.extend(rule_suggestions)
            except Exception as e:
                print(f"Error in rule {rule_name}: {e}")
        
        complexity_score = self._calculate_complexity(parsed)
        execution_tips = self._generate_execution_tips(parsed, database_type)
        
        return AnalysisResult(
            query=query,
            database_type=database_type,
            suggestions=suggestions,
            complexity_score=complexity_score,
            execution_plan_tips=execution_tips,
            syntax_errors=syntax_errors
        )
    
    def _check_syntax_errors(self, query: str, parsed, database_type: str) -> List[str]:
        syntax_errors = []
        query_upper = query.upper()
        db_config = self.database_configs[database_type]
        
        # Remove string literals and comments to avoid false positives
        cleaned_query = re.sub(r"'[^']*'", "", query_upper)  # Remove single-quoted strings
        cleaned_query = re.sub(r'"[^"]*"', "", cleaned_query)  # Remove double-quoted strings
        cleaned_query = re.sub(r'--.*$', "", cleaned_query, flags=re.MULTILINE)  # Remove line comments
        cleaned_query = re.sub(r'/\*.*?\*/', "", cleaned_query, flags=re.DOTALL)  # Remove block comments
        
        # Split query into tokens (words)
        words = re.findall(r'\b[A-Z_][A-Z0-9_]*\b', cleaned_query)
        
        # Check for common misspellings
        for word in words:
            if word in self.common_misspellings:
                correct_word = self.common_misspellings[word]
                syntax_errors.append(f"Possible misspelling: '{word}' should be '{correct_word}'")
        
        # Database-specific syntax checks
        if database_type == 'mysql':
            # MySQL-specific checks
            if 'TOP ' in query_upper:
                syntax_errors.append("MySQL doesn't support TOP keyword. Use LIMIT instead.")
            if re.search(r'\bROWNUM\b', query_upper):
                syntax_errors.append("MySQL doesn't support ROWNUM. Use LIMIT for row limiting.")
        
        elif database_type == 'postgresql':
            # PostgreSQL-specific checks
            if 'TOP ' in query_upper:
                syntax_errors.append("PostgreSQL doesn't support TOP keyword. Use LIMIT instead.")
            if re.search(r'\bROWNUM\b', query_upper):
                syntax_errors.append("PostgreSQL doesn't support ROWNUM. Use LIMIT and OFFSET for row limiting.")
            if re.search(r'\bIFNULL\s*\(', query_upper):
                syntax_errors.append("PostgreSQL doesn't support IFNULL. Use COALESCE instead.")
        
        elif database_type == 'oracle':
            # Oracle-specific checks
            if 'LIMIT ' in query_upper:
                syntax_errors.append("Oracle doesn't support LIMIT keyword. Use ROWNUM or FETCH FIRST for row limiting.")
            if 'AUTO_INCREMENT' in query_upper:
                syntax_errors.append("Oracle doesn't support AUTO_INCREMENT. Use SEQUENCE and TRIGGER instead.")
        
        elif database_type == 'sqlserver':
            # SQL Server-specific checks
            if 'LIMIT ' in query_upper:
                syntax_errors.append("SQL Server doesn't support LIMIT keyword. Use TOP or OFFSET-FETCH instead.")
            if re.search(r'\bROWNUM\b', query_upper):
                syntax_errors.append("SQL Server doesn't support ROWNUM. Use TOP or ROW_NUMBER() instead.")
            if 'AUTO_INCREMENT' in query_upper:
                syntax_errors.append("SQL Server doesn't support AUTO_INCREMENT. Use IDENTITY instead.")
        
        # Check for unmatched parentheses
        open_parens = query.count('(')
        close_parens = query.count(')')
        if open_parens != close_parens:
            syntax_errors.append(f"Unmatched parentheses: {open_parens} opening, {close_parens} closing")
        
        # Check for basic keyword order violations
        if 'SELECT' in query_upper and 'FROM' in query_upper:
            select_pos = query_upper.find('SELECT')
            from_pos = query_upper.find('FROM')
            if select_pos > from_pos:
                syntax_errors.append("Invalid syntax: 'FROM' appears before 'SELECT'")
        
        # Check for WHERE after ORDER BY (common mistake)
        if 'WHERE' in query_upper and 'ORDER BY' in query_upper:
            where_pos = query_upper.find('WHERE')
            order_pos = query_upper.find('ORDER BY')
            if where_pos > order_pos:
                syntax_errors.append("Invalid syntax: 'WHERE' clause should come before 'ORDER BY'")
        
        # Check for GROUP BY after ORDER BY
        if 'GROUP BY' in query_upper and 'ORDER BY' in query_upper:
            group_pos = query_upper.find('GROUP BY')
            order_pos = query_upper.find('ORDER BY')
            if group_pos > order_pos:
                syntax_errors.append("Invalid syntax: 'GROUP BY' clause should come before 'ORDER BY'")
        
        return syntax_errors
    
    def _check_select_star(self, query: str, parsed) -> List[OptimizationSuggestion]:
        suggestions = []
        if "SELECT *" in query.upper() or "SELECT\n*" in query.upper():
            suggestions.append(OptimizationSuggestion(
                type="performance",
                severity="medium",
                title="Avoid SELECT *",
                description="Using SELECT * retrieves all columns, which can impact performance",
                suggestion="Specify only the columns you need in the SELECT clause",
                example="SELECT id, name, email FROM users; -- Instead of SELECT * FROM users;"
            ))
        return suggestions
    
    def _check_missing_where(self, query: str, parsed) -> List[OptimizationSuggestion]:
        suggestions = []
        query_upper = query.upper()
        
        # Check for SELECT without WHERE clause
        if ("SELECT" in query_upper and 
            "WHERE" not in query_upper and 
            "LIMIT" not in query_upper and
            "JOIN" not in query_upper):
            suggestions.append(OptimizationSuggestion(
                type="performance",
                severity="high",
                title="Missing WHERE clause",
                description="Queries without WHERE clauses scan entire tables",
                suggestion="Add a WHERE clause to filter rows or use LIMIT for testing",
                example="SELECT * FROM users WHERE status = 'active' LIMIT 100;"
            ))
        return suggestions
    
    def _check_non_sargable_conditions(self, query: str, parsed) -> List[OptimizationSuggestion]:
        suggestions = []
        query_upper = query.upper()
        
        # Check for functions on columns in WHERE clause
        function_patterns = [
            r'WHERE\s+\w*\(\s*\w+\s*\)',
            r'WHERE\s+UPPER\s*\(',
            r'WHERE\s+LOWER\s*\(',
            r'WHERE\s+SUBSTRING\s*\(',
            r'WHERE\s+LEFT\s*\(',
            r'WHERE\s+RIGHT\s*\('
        ]
        
        for pattern in function_patterns:
            if re.search(pattern, query_upper):
                suggestions.append(OptimizationSuggestion(
                    type="index",
                    severity="high",
                    title="Non-SARGable condition detected",
                    description="Functions on columns in WHERE clauses prevent index usage",
                    suggestion="Avoid functions on columns in WHERE clauses or create computed columns",
                    example="WHERE name = 'JOHN' -- Instead of WHERE UPPER(name) = 'JOHN'"
                ))
                break
        
        # Check for LIKE with leading wildcards
        if re.search(r"LIKE\s+['\"]%", query_upper):
            suggestions.append(OptimizationSuggestion(
                type="index",
                severity="medium",
                title="Leading wildcard in LIKE",
                description="LIKE patterns starting with % cannot use indexes effectively",
                suggestion="Avoid leading wildcards or consider full-text search",
                example="WHERE name LIKE 'John%' -- Instead of WHERE name LIKE '%John%'"
            ))
        
        return suggestions
    
    def _check_subqueries(self, query: str, parsed) -> List[OptimizationSuggestion]:
        suggestions = []
        query_upper = query.upper()
        
        # Check for correlated subqueries
        if "IN (" in query_upper and "SELECT" in query_upper:
            suggestions.append(OptimizationSuggestion(
                type="join",
                severity="medium",
                title="Consider replacing subquery with JOIN",
                description="Subqueries can often be optimized by converting to JOINs",
                suggestion="Replace IN subqueries with INNER JOINs when possible",
                example="""
-- Instead of:
SELECT * FROM users WHERE id IN (SELECT user_id FROM orders);
-- Use:
SELECT DISTINCT u.* FROM users u INNER JOIN orders o ON u.id = o.user_id;
"""
            ))
        
        # Check for EXISTS vs IN
        if " IN (" in query_upper:
            suggestions.append(OptimizationSuggestion(
                type="performance",
                severity="low",
                title="Consider EXISTS instead of IN",
                description="EXISTS can be faster than IN for subqueries",
                suggestion="Use EXISTS when checking for existence rather than specific values",
                example="""
-- Instead of:
WHERE id IN (SELECT user_id FROM orders)
-- Consider:
WHERE EXISTS (SELECT 1 FROM orders WHERE user_id = users.id)
"""
            ))
        
        return suggestions
    
    def _check_joins(self, query: str, parsed) -> List[OptimizationSuggestion]:
        suggestions = []
        query_upper = query.upper()
        
        # Check for implicit joins (comma-separated tables)
        tables_pattern = r'FROM\s+(\w+\s*,\s*\w+)'
        if re.search(tables_pattern, query_upper):
            suggestions.append(OptimizationSuggestion(
                type="join",
                severity="medium",
                title="Use explicit JOINs",
                description="Implicit joins (comma-separated) are less clear and harder to optimize",
                suggestion="Replace implicit joins with explicit INNER/LEFT/RIGHT JOINs",
                example="""
-- Instead of:
SELECT * FROM users u, orders o WHERE u.id = o.user_id;
-- Use:
SELECT * FROM users u INNER JOIN orders o ON u.id = o.user_id;
"""
            ))
        
        # Check for missing JOIN conditions
        join_count = query_upper.count("JOIN")
        on_count = query_upper.count(" ON ")
        
        if join_count > on_count and "CROSS JOIN" not in query_upper:
            suggestions.append(OptimizationSuggestion(
                type="join",
                severity="high",
                title="Missing JOIN conditions",
                description="JOINs without proper ON conditions can create Cartesian products",
                suggestion="Ensure all JOINs have appropriate ON conditions",
                example="INNER JOIN orders o ON u.id = o.user_id"
            ))
        
        return suggestions
    
    def _suggest_indexes(self, query: str, parsed) -> List[OptimizationSuggestion]:
        suggestions = []
        query_upper = query.upper()
        
        # Extract WHERE conditions
        where_match = re.search(r'WHERE\s+(.*?)(?:\s+ORDER\s+BY|\s+GROUP\s+BY|\s+HAVING|\s+LIMIT|$)', query_upper, re.DOTALL)
        
        if where_match:
            where_clause = where_match.group(1)
            
            # Find column references in WHERE clause
            column_patterns = re.findall(r'\b(\w+)\s*[=<>!]', where_clause)
            
            if column_patterns:
                unique_columns = list(set(column_patterns))
                suggestions.append(OptimizationSuggestion(
                    type="index",
                    severity="medium",
                    title="Consider adding indexes",
                    description=f"Columns used in WHERE clause could benefit from indexes: {', '.join(unique_columns)}",
                    suggestion="Create indexes on frequently queried columns",
                    example=f"CREATE INDEX idx_column_name ON table_name ({', '.join(unique_columns[:3])});"
                ))
        
        # Check for ORDER BY columns
        order_by_match = re.search(r'ORDER\s+BY\s+([\w,\s]+)', query_upper)
        if order_by_match:
            order_columns = [col.strip() for col in order_by_match.group(1).split(',')]
            suggestions.append(OptimizationSuggestion(
                type="index",
                severity="low",
                title="Consider index for ORDER BY",
                description="ORDER BY operations can benefit from indexes",
                suggestion="Create an index on ORDER BY columns for better sorting performance",
                example=f"CREATE INDEX idx_sort ON table_name ({', '.join(order_columns[:2])});"
            ))
        
        return suggestions
    
    def _check_limit_clause(self, query: str, parsed) -> List[OptimizationSuggestion]:
        suggestions = []
        query_upper = query.upper()
        
        if ("SELECT" in query_upper and 
            "LIMIT" not in query_upper and 
            "TOP" not in query_upper and
            "WHERE" not in query_upper):
            suggestions.append(OptimizationSuggestion(
                type="performance",
                severity="medium",
                title="Consider adding LIMIT clause",
                description="Queries without LIMIT can return large result sets",
                suggestion="Add LIMIT clause when you don't need all results",
                example="SELECT * FROM users LIMIT 100;"
            ))
        
        return suggestions
    
    def _check_order_by(self, query: str, parsed) -> List[OptimizationSuggestion]:
        suggestions = []
        query_upper = query.upper()
        
        if "ORDER BY" in query_upper and "LIMIT" not in query_upper:
            suggestions.append(OptimizationSuggestion(
                type="performance",
                severity="low",
                title="ORDER BY without LIMIT",
                description="Sorting entire result sets can be expensive",
                suggestion="Consider adding LIMIT when using ORDER BY if you don't need all sorted results",
                example="SELECT * FROM users ORDER BY created_at DESC LIMIT 50;"
            ))
        
        return suggestions
    
    def _check_functions_in_where(self, query: str, parsed) -> List[OptimizationSuggestion]:
        suggestions = []
        query_upper = query.upper()
        
        # Check for common functions that prevent index usage
        problematic_functions = ['YEAR(', 'MONTH(', 'DAY(', 'DATEPART(', 'CONVERT(', 'CAST(']
        
        for func in problematic_functions:
            if func in query_upper and 'WHERE' in query_upper:
                suggestions.append(OptimizationSuggestion(
                    type="index",
                    severity="medium",
                    title="Function in WHERE clause prevents index usage",
                    description=f"Using {func.rstrip('(')} in WHERE clause can prevent index usage",
                    suggestion="Consider using range conditions instead of functions",
                    example="""
-- Instead of: WHERE YEAR(date_col) = 2023
-- Use: WHERE date_col >= '2023-01-01' AND date_col < '2024-01-01'
"""
                ))
                break
        
        return suggestions
    
    def _check_unnecessary_distinct(self, query: str, parsed) -> List[OptimizationSuggestion]:
        suggestions = []
        query_upper = query.upper()
        
        if "SELECT DISTINCT" in query_upper and "JOIN" not in query_upper:
            suggestions.append(OptimizationSuggestion(
                type="performance",
                severity="low",
                title="Review DISTINCT usage",
                description="DISTINCT can be expensive and may not be necessary",
                suggestion="Ensure DISTINCT is actually needed or consider using GROUP BY",
                example="-- Only use DISTINCT when you actually have duplicates to remove"
            ))
        
        return suggestions
    
    def _check_database_specific_rules(self, query: str, parsed, database_type: str) -> List[OptimizationSuggestion]:
        suggestions = []
        query_upper = query.upper()
        db_config = self.database_configs[database_type]
        
        # Database-specific optimization suggestions
        if database_type == 'mysql':
            # MySQL-specific optimizations
            if 'MYISAM' not in query_upper and 'ENGINE' not in query_upper:
                if 'CREATE TABLE' in query_upper:
                    suggestions.append(OptimizationSuggestion(
                        type="database-specific",
                        severity="medium",
                        title="Specify storage engine for MySQL",
                        description="MySQL supports multiple storage engines with different characteristics",
                        suggestion="Specify ENGINE=InnoDB for ACID compliance and foreign keys, or ENGINE=MyISAM for read-heavy workloads",
                        example="CREATE TABLE users (...) ENGINE=InnoDB;"
                    ))
            
            if 'GROUP_CONCAT' not in query_upper and re.search(r'GROUP\s+BY.*STRING_AGG', query_upper):
                suggestions.append(OptimizationSuggestion(
                    type="database-specific",
                    severity="low",
                    title="Use MySQL's GROUP_CONCAT instead of STRING_AGG",
                    description="MySQL uses GROUP_CONCAT function for string aggregation",
                    suggestion="Replace STRING_AGG with GROUP_CONCAT for MySQL compatibility",
                    example="SELECT GROUP_CONCAT(name) FROM users GROUP BY department;"
                ))
        
        elif database_type == 'postgresql':
            # PostgreSQL-specific optimizations
            if 'VACUUM' not in query_upper and 'DELETE' in query_upper:
                suggestions.append(OptimizationSuggestion(
                    type="database-specific",
                    severity="medium",
                    title="Consider VACUUM after large DELETE operations",
                    description="PostgreSQL uses MVCC which can leave dead tuples after DELETE operations",
                    suggestion="Run VACUUM or VACUUM ANALYZE after large DELETE operations to reclaim space",
                    example="-- After large deletes:\nVACUUM ANALYZE table_name;"
                ))
            
            if 'ILIKE' not in query_upper and re.search(r'UPPER\s*\(.*LIKE', query_upper):
                suggestions.append(OptimizationSuggestion(
                    type="database-specific",
                    severity="low",
                    title="Use ILIKE for case-insensitive searches in PostgreSQL",
                    description="PostgreSQL's ILIKE operator provides case-insensitive pattern matching",
                    suggestion="Use ILIKE instead of UPPER() with LIKE for better performance",
                    example="WHERE name ILIKE '%john%' -- Instead of WHERE UPPER(name) LIKE '%JOHN%'"
                ))
        
        elif database_type == 'oracle':
            # Oracle-specific optimizations
            if 'ROWNUM' not in query_upper and 'LIMIT' in query_upper:
                suggestions.append(OptimizationSuggestion(
                    type="database-specific",
                    severity="high",
                    title="Oracle doesn't support LIMIT - use ROWNUM or FETCH FIRST",
                    description="Oracle uses different syntax for limiting result sets",
                    suggestion="Use ROWNUM in WHERE clause or FETCH FIRST clause (Oracle 12c+)",
                    example="""
-- Oracle 11g and earlier:
SELECT * FROM (SELECT * FROM users ORDER BY id) WHERE ROWNUM <= 10;
-- Oracle 12c+:
SELECT * FROM users ORDER BY id FETCH FIRST 10 ROWS ONLY;
"""
                ))
            
            if 'DUAL' not in query_upper and re.search(r'SELECT\s+\d', query_upper):
                suggestions.append(OptimizationSuggestion(
                    type="database-specific",
                    severity="low",
                    title="Use DUAL table for constant values in Oracle",
                    description="Oracle requires a FROM clause, use DUAL for selecting constants",
                    suggestion="Use FROM DUAL when selecting constant values or expressions",
                    example="SELECT 1, 'test', SYSDATE FROM DUAL;"
                ))
        
        elif database_type == 'sqlserver':
            # SQL Server-specific optimizations
            if 'NOLOCK' in query_upper:
                suggestions.append(OptimizationSuggestion(
                    type="database-specific",
                    severity="high",
                    title="Avoid NOLOCK hint in SQL Server",
                    description="NOLOCK can cause dirty reads and inconsistent data",
                    suggestion="Use READ UNCOMMITTED isolation level or snapshot isolation instead of NOLOCK",
                    example="SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED; -- Instead of WITH (NOLOCK)"
                ))
            
            if 'TOP' not in query_upper and 'LIMIT' in query_upper:
                suggestions.append(OptimizationSuggestion(
                    type="database-specific",
                    severity="high",
                    title="SQL Server doesn't support LIMIT - use TOP or OFFSET-FETCH",
                    description="SQL Server uses TOP keyword or OFFSET-FETCH clause for limiting results",
                    suggestion="Use TOP for simple limits or OFFSET-FETCH for pagination",
                    example="""
-- Simple limit:
SELECT TOP 10 * FROM users;
-- Pagination:
SELECT * FROM users ORDER BY id OFFSET 10 ROWS FETCH NEXT 10 ROWS ONLY;
"""
                ))
        
        return suggestions
    
    def _calculate_complexity(self, parsed) -> int:
        query_str = str(parsed).upper()
        score = 0
        
        # Base complexity factors
        score += query_str.count("JOIN") * 2
        score += query_str.count("SUBQUERY") * 3
        score += query_str.count("UNION") * 2
        score += query_str.count("CASE") * 1
        score += query_str.count("GROUP BY") * 1
        score += query_str.count("ORDER BY") * 1
        score += query_str.count("HAVING") * 2
        
        # Function complexity
        score += len(re.findall(r'\w+\s*\(', query_str)) * 1
        
        return min(score, 100)  # Cap at 100
    
    def _generate_execution_tips(self, parsed, database_type: str) -> List[str]:
        tips = []
        query_str = str(parsed).upper()
        db_config = self.database_configs[database_type]
        
        if "JOIN" in query_str:
            tips.append("Ensure JOIN conditions use indexed columns for better performance")
        
        if "GROUP BY" in query_str:
            tips.append("Consider adding indexes on GROUP BY columns")
        
        if "ORDER BY" in query_str:
            tips.append("Indexes on ORDER BY columns can eliminate sort operations")
        
        if "LIKE" in query_str:
            if database_type == 'postgresql':
                tips.append("Consider using PostgreSQL's full-text search (tsvector) for complex text searches")
            elif database_type == 'mysql':
                tips.append("Consider using MySQL's FULLTEXT indexes for complex text searches")
            elif database_type == 'sqlserver':
                tips.append("Consider using SQL Server's Full-Text Search for complex text searches")
            else:
                tips.append("Consider full-text search for complex text searches")
        
        # Database-specific tips
        if database_type == 'mysql':
            tips.append("Consider using MySQL's query cache for repeated queries")
            if "InnoDB" not in query_str.upper():
                tips.append("Use InnoDB storage engine for ACID compliance and better concurrency")
        
        elif database_type == 'postgresql':
            tips.append("Use EXPLAIN ANALYZE to get actual execution statistics")
            tips.append("Consider using PostgreSQL's partial indexes for filtered queries")
        
        elif database_type == 'oracle':
            tips.append("Use Oracle's Cost-Based Optimizer hints if needed")
            tips.append("Consider using Oracle's materialized views for complex aggregations")
        
        elif database_type == 'sqlserver':
            tips.append("Use SQL Server's execution plans to identify bottlenecks")
            tips.append("Consider using SQL Server's columnstore indexes for analytical queries")
        
        if len(tips) == 0:
            tips.append("Query looks straightforward - ensure your tables have appropriate indexes")
        
        return tips

# Initialize analyzer
analyzer = SQLAnalyzer()

@app.post("/analyze", response_model=AnalysisResult)
async def analyze_sql_query(query: SQLQuery):
    try:
        if not query.query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        result = analyzer.analyze_query(query.query, query.database_type)
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.get("/")
async def root():
    return {"message": "SQL Optimizer API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 