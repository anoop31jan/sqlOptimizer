# 🚀 SQL Optimizer Dashboard

A modern web application that analyzes SQL queries and provides intelligent optimization suggestions including indexes, joins, query structure improvements, and performance tips.

## ✨ Features

- **🔍 SQL Query Analysis**: Parse and analyze SQL queries for optimization opportunities
- **💡 Smart Suggestions**: Get recommendations for:
  - Index optimization
  - JOIN improvements  
  - Query structure enhancements
  - Performance optimizations
- **📊 Complexity Scoring**: Visual complexity assessment of your queries
- **🎯 Execution Tips**: Practical advice for better query execution
- **📱 Modern UI**: Beautiful, responsive interface with syntax highlighting
- **⚡ Real-time Analysis**: Instant feedback on query optimization

## 🏗️ Architecture

### Backend (Python FastAPI)
- **SQL Parser**: Uses `sqlparse` to analyze SQL structure
- **Rules Engine**: Comprehensive optimization rules for different SQL patterns
- **REST API**: Clean endpoints for query analysis
- **Extensible**: Easy to add new optimization rules

### Frontend (React TypeScript)
- **Modern UI**: Built with React 18 and TypeScript
- **Syntax Highlighting**: SQL syntax highlighting with react-syntax-highlighter
- **Responsive Design**: Works on desktop and mobile devices
- **Interactive Results**: Expandable suggestion cards with examples

## 🚀 Quick Start

### Prerequisites
- Python 3.8+ 
- Node.js 16+
- npm or yarn

### Backend Setup

1. **Navigate to backend directory**:
   ```bash
   cd backend
   ```

2. **Create virtual environment** (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Start the backend server**:
   ```bash
   python app.py
   ```
   
   The API will be available at `http://localhost:8000`

### Frontend Setup

1. **Navigate to frontend directory**:
   ```bash
   cd frontend
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Start the development server**:
   ```bash
   npm start
   ```
   
   The dashboard will open at `http://localhost:3000`

## 📝 Usage

1. **Open the dashboard** at `http://localhost:3000`
2. **Enter your SQL query** in the text area
3. **Click "Analyze Query"** to get optimization suggestions
4. **Review the results**:
   - Query complexity score
   - Detailed optimization suggestions
   - Code examples and recommendations
   - Execution plan tips

### Sample Queries to Try

```sql
-- Query with optimization issues
SELECT * FROM users WHERE UPPER(name) = 'JOHN'

-- Complex JOIN query
SELECT * FROM users u, orders o, products p 
WHERE u.id = o.user_id AND o.product_id = p.id 
ORDER BY o.created_at

-- Subquery that could be optimized
SELECT * FROM users 
WHERE id IN (SELECT user_id FROM orders WHERE total > 100)
```

## 🔧 API Endpoints

### `POST /analyze`
Analyze a SQL query and return optimization suggestions.

**Request Body**:
```json
{
  "query": "SELECT * FROM users WHERE age > 25"
}
```

**Response**:
```json
{
  "query": "SELECT * FROM users WHERE age > 25",
  "suggestions": [
    {
      "type": "performance",
      "severity": "medium", 
      "title": "Avoid SELECT *",
      "description": "Using SELECT * retrieves all columns...",
      "suggestion": "Specify only the columns you need...",
      "example": "SELECT id, name, email FROM users WHERE age > 25;"
    }
  ],
  "complexity_score": 15,
  "execution_plan_tips": [
    "Ensure WHERE clause columns have appropriate indexes"
  ]
}
```

### `GET /health`
Health check endpoint.

## 🎯 Optimization Rules

The analyzer includes rules for detecting:

### Performance Issues
- `SELECT *` usage
- Missing WHERE clauses
- Missing LIMIT clauses  
- Unnecessary DISTINCT usage

### Index Optimization
- Non-SARGable conditions (functions on columns)
- Leading wildcards in LIKE patterns
- Index suggestions for WHERE columns
- ORDER BY index recommendations

### JOIN Optimization  
- Implicit vs explicit JOINs
- Missing JOIN conditions
- Subquery to JOIN conversions

### Query Structure
- Correlated subqueries
- EXISTS vs IN optimization
- Function usage in WHERE clauses

## 🛠️ Development

### Adding New Optimization Rules

1. **Add rule method** to `SQLAnalyzer` class in `backend/app.py`:
   ```python
   def _check_new_rule(self, query: str, parsed) -> List[OptimizationSuggestion]:
       suggestions = []
       # Your rule logic here
       return suggestions
   ```

2. **Register the rule** in `__init__` method:
   ```python
   self.optimization_rules['new_rule'] = self._check_new_rule
   ```

### Frontend Customization

- **Styling**: Modify CSS files in `frontend/src/components/`
- **Components**: Add new React components in `frontend/src/components/`
- **Types**: Update TypeScript interfaces in `frontend/src/types.ts`

## 📦 Project Structure

```
SQLOptimizer/
├── backend/
│   ├── app.py              # FastAPI application and SQL analyzer
│   └── requirements.txt    # Python dependencies
├── frontend/
│   ├── public/
│   │   └── index.html     # HTML template
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── App.tsx        # Main App component
│   │   ├── App.css        # Main styles
│   │   ├── index.tsx      # React entry point
│   │   └── types.ts       # TypeScript interfaces
│   ├── package.json       # Node.js dependencies
│   └── tsconfig.json      # TypeScript configuration
└── README.md              # This file
```

## 🚀 Deployment

### Backend Deployment
```bash
# Install dependencies
pip install -r backend/requirements.txt

# Run with gunicorn for production
pip install gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker backend.app:app
```

### Frontend Deployment
```bash
# Build for production
cd frontend
npm run build

# Serve the build folder with any static file server
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

## 🙋‍♂️ Support

If you have questions or need help:
- Open an issue on GitHub
- Check the API documentation at `http://localhost:8000/docs` when running locally

---

**Built with ❤️ for better SQL performance** 