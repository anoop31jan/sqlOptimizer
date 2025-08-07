-- ===============================================
-- SQL OPTIMIZER DEMO QUERIES
-- Collection of test queries for demonstration
-- ===============================================

-- =============================================
-- DEMO 1: PERFORMANCE OPTIMIZATION ISSUES
-- =============================================

-- Query 1: Multiple Performance Issues
-- Issues: SELECT *, non-SARGable condition, function in WHERE
SELECT * FROM users WHERE UPPER(name) = 'JOHN';

-- Query 2: Missing WHERE Clause (High Severity)
-- Issues: No filtering, potential full table scan
SELECT id, name, email FROM users ORDER BY created_at DESC;

-- Query 3: Missing LIMIT (Medium Severity) 
-- Issues: Unbounded result set
SELECT * FROM products WHERE category = 'electronics' ORDER BY price;

-- =============================================
-- DEMO 2: JOIN OPTIMIZATION
-- =============================================

-- Query 4: Implicit JOIN (Old Style)
-- Issues: Comma syntax, potential Cartesian product
SELECT * FROM users u, orders o, products p 
WHERE u.id = o.user_id AND o.product_id = p.id 
ORDER BY o.created_at;

-- Query 5: Missing JOIN Condition
-- Issues: Cartesian product risk
SELECT * FROM users u 
JOIN orders o 
JOIN products p ON o.product_id = p.id;

-- =============================================
-- DEMO 3: SUBQUERY OPTIMIZATION
-- =============================================

-- Query 6: IN Subquery (Can be optimized to JOIN)
-- Issues: Subquery performance, potential for JOIN conversion
SELECT * FROM users 
WHERE id IN (SELECT user_id FROM orders WHERE total > 100);

-- Query 7: Correlated Subquery
-- Issues: Performance impact of correlation
SELECT u.name, 
       (SELECT COUNT(*) FROM orders o WHERE o.user_id = u.id) as order_count
FROM users u;

-- =============================================
-- DEMO 4: INDEX OPTIMIZATION
-- =============================================

-- Query 8: Leading Wildcard in LIKE
-- Issues: Cannot use index effectively
SELECT * FROM users WHERE name LIKE '%john%';

-- Query 9: Function on Column in WHERE
-- Issues: Prevents index usage
SELECT * FROM orders WHERE YEAR(created_at) = 2023;

-- Query 10: Multiple WHERE Conditions (Good for Index Demo)
-- Issues: Suggest composite index
SELECT * FROM orders 
WHERE status = 'completed' 
  AND total > 50 
  AND created_at >= '2023-01-01';

-- =============================================
-- DEMO 5: GOOD QUERY (No Issues)
-- =============================================

-- Query 11: Well-Optimized Query
-- Should show "Great job!" message
SELECT id, name, email, status
FROM users 
WHERE status = 'active' 
  AND created_at >= '2023-01-01'
  AND created_at < '2024-01-01'
ORDER BY created_at DESC 
LIMIT 50;

-- =============================================
-- DEMO 6: COMPLEX QUERY (High Complexity Score)
-- =============================================

-- Query 12: Complex Query with Multiple Issues
-- High complexity score demonstration
SELECT DISTINCT u.name, 
       COUNT(o.id) as order_count,
       SUM(o.total) as total_spent,
       CASE 
         WHEN SUM(o.total) > 1000 THEN 'VIP'
         WHEN SUM(o.total) > 500 THEN 'Premium'
         ELSE 'Regular'
       END as customer_tier
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
LEFT JOIN order_items oi ON o.id = oi.order_id  
LEFT JOIN products p ON oi.product_id = p.id
WHERE u.status = 'active'
GROUP BY u.id, u.name
HAVING COUNT(o.id) > 0
ORDER BY total_spent DESC;

-- =============================================
-- DEMO 7: QUICK TEST QUERIES
-- =============================================

-- Query 13: Simple SELECT * (Quick Demo)
SELECT * FROM users;

-- Query 14: DISTINCT without JOIN (Unnecessary)
SELECT DISTINCT name FROM users WHERE status = 'active';

-- Query 15: ORDER BY without LIMIT
SELECT name, email FROM users ORDER BY created_at DESC;

-- =============================================
-- EXPECTED DEMO RESULTS SUMMARY
-- =============================================

/*
Query 1-3: Performance issues (SELECT *, functions, missing WHERE/LIMIT)
Query 4-5: JOIN optimization (implicit joins, missing conditions)
Query 6-7: Subquery optimization (IN to JOIN, correlated subqueries)
Query 8-10: Index suggestions (LIKE wildcards, functions, composite indexes)
Query 11: Perfect query - should show success message
Query 12: High complexity score with multiple suggestion types
Query 13-15: Quick demonstration of common issues

Severity Distribution:
- High: Missing WHERE, missing JOIN conditions, non-SARGable
- Medium: SELECT *, implicit JOINs, index suggestions
- Low: DISTINCT usage, ORDER BY without LIMIT

Categories Covered:
- Performance: 8 queries
- Index: 6 queries  
- JOIN: 4 queries
- Structure: 3 queries
*/ 