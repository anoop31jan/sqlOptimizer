import React, { useState } from 'react';
import axios from 'axios';
import { AnalysisResult, DATABASE_OPTIONS } from '../types';
import './QueryInput.css';

interface QueryInputProps {
  onAnalysisStart: () => void;
  onAnalysisComplete: (result: AnalysisResult) => void;
  isLoading: boolean;
}

const QueryInput: React.FC<QueryInputProps> = ({ 
  onAnalysisStart, 
  onAnalysisComplete, 
  isLoading 
}) => {
  const [query, setQuery] = useState('');
  const [databaseType, setDatabaseType] = useState('mysql');
  const [error, setError] = useState<string | null>(null);

  const sampleQueries = [
    {
      name: "Simple SELECT with issues",
      query: `SELECT * FROM users WHERE UPPER(name) = 'JOHN'`
    },
    {
      name: "Complex JOIN query", 
      query: `SELECT * FROM users u, orders o, products p 
WHERE u.id = o.user_id AND o.product_id = p.id 
ORDER BY o.created_at`
    },
    {
      name: "Subquery example",
      query: `SELECT * FROM users 
WHERE id IN (SELECT user_id FROM orders WHERE total > 100)`
    },
    {
      name: "Missing WHERE clause",
      query: `SELECT id, name, email FROM users ORDER BY created_at DESC`
    },
    {
      name: "Syntax error example",
      query: `selet * from users;`
    },
    {
      name: "Database-specific (MySQL)",
      query: `SELECT GROUP_CONCAT(name) FROM users GROUP BY department LIMIT 10`
    },
    {
      name: "Database-specific (SQL Server)",
      query: `SELECT TOP 10 * FROM users WITH (NOLOCK)`
    },
    {
      name: "Database-specific (Oracle)",
      query: `SELECT * FROM users WHERE ROWNUM <= 10`
    }
  ];

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!query.trim()) {
      setError('Please enter a SQL query');
      return;
    }

    setError(null);
    onAnalysisStart();

    try {
      const response = await axios.post('/analyze', {
        query: query.trim(),
        database_type: databaseType
      });
      
      onAnalysisComplete(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to analyze query');
      onAnalysisComplete({
        query: query.trim(),
        database_type: databaseType,
        suggestions: [],
        complexity_score: 0,
        execution_plan_tips: []
      });
    }
  };

  const handleSampleQuery = (sampleQuery: string) => {
    setQuery(sampleQuery);
    setError(null);
  };

  const clearQuery = () => {
    setQuery('');
    setError(null);
  };

  const selectedDatabase = DATABASE_OPTIONS.find(db => db.value === databaseType);

  return (
    <div className="query-input-container">
      <div className="query-input-section">
        <h2>📝 Enter Your SQL Query</h2>
        
        <form onSubmit={handleSubmit} className="query-form">
          {/* Database Selection */}
          <div className="database-selection">
            <label htmlFor="database-type" className="database-label">
              🗄️ Select Database Type:
            </label>
            <div className="database-dropdown">
              <select
                id="database-type"
                value={databaseType}
                onChange={(e) => setDatabaseType(e.target.value)}
                className="database-select"
                disabled={isLoading}
              >
                {DATABASE_OPTIONS.map((db) => (
                  <option key={db.value} value={db.value}>
                    {db.icon} {db.label}
                  </option>
                ))}
              </select>
              <div className="database-description">
                {selectedDatabase?.description}
              </div>
            </div>
          </div>

          <div className="textarea-container">
            <textarea
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder={`Enter your ${selectedDatabase?.label} query here...
Example: SELECT * FROM users WHERE age > 25`}
              className="query-textarea"
              rows={8}
              disabled={isLoading}
            />
            
            <div className="query-actions">
              <button
                type="button"
                onClick={clearQuery}
                className="btn btn-secondary"
                disabled={isLoading || !query.trim()}
              >
                Clear
              </button>
              
              <button
                type="submit"
                className="btn btn-primary"
                disabled={isLoading || !query.trim()}
              >
                {isLoading ? 'Analyzing...' : `Analyze ${selectedDatabase?.label} Query`}
              </button>
            </div>
          </div>
          
          {error && (
            <div className="error-message">
              ⚠️ {error}
            </div>
          )}
        </form>
      </div>

      <div className="sample-queries-section">
        <h3>💡 Try Sample Queries</h3>
        <div className="sample-queries">
          {sampleQueries.map((sample, index) => (
            <button
              key={index}
              onClick={() => handleSampleQuery(sample.query)}
              className="sample-query-btn"
              disabled={isLoading}
            >
              {sample.name}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};

export default QueryInput; 