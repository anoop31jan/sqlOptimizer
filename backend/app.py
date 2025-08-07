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

class OptimizationSuggestion(BaseModel):
    type: str
    severity: str
    title: str
    description: str
    suggestion: str
    example: Optional[str] = Field(default="")

class AnalysisResult(BaseModel):
    query: str
    suggestions: List[OptimizationSuggestion]
    complexity_score: int
    execution_plan_tips: List[str]

class SQLAnalyzer:
    def __init__(self):
        self.optimization_rules = {
            'select_star': self._check_select_star,
            'missing_where': self._check_missing_where,
            'non_sargable': self._check_non_sargable_conditions,
            'subquery_optimization': self._check_subqueries,
            'join_optimization': self._check_joins,
            'index_suggestions': self._suggest_indexes,
            'limit_clause': self._check_limit_clause,
            'order_by_optimization': self._check_order_by,
            'function_in_where': self._check_functions_in_where,
            'unnecessary_distinct': self._check_unnecessary_distinct
        }
    
    def analyze_query(self, query: str) -> AnalysisResult:
        # Parse the SQL query
        parsed = sqlparse.parse(query)[0]
        
        suggestions = []
        for rule_name, rule_func in self.optimization_rules.items():
            try:
                rule_suggestions = rule_func(query, parsed)
                if rule_suggestions:
                    suggestions.extend(rule_suggestions)
            except Exception as e:
                print(f"Error in rule {rule_name}: {e}")
        
        complexity_score = self._calculate_complexity(parsed)
        execution_tips = self._generate_execution_tips(parsed)
        
        return AnalysisResult(
            query=query,
            suggestions=suggestions,
            complexity_score=complexity_score,
            execution_plan_tips=execution_tips
        )
    
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
    
    def _generate_execution_tips(self, parsed) -> List[str]:
        tips = []
        query_str = str(parsed).upper()
        
        if "JOIN" in query_str:
            tips.append("Ensure JOIN conditions use indexed columns for better performance")
        
        if "GROUP BY" in query_str:
            tips.append("Consider adding indexes on GROUP BY columns")
        
        if "ORDER BY" in query_str:
            tips.append("Indexes on ORDER BY columns can eliminate sort operations")
        
        if "LIKE" in query_str:
            tips.append("Consider full-text search for complex text searches")
        
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
        
        result = analyzer.analyze_query(query.query)
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