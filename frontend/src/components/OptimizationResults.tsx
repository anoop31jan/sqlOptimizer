import React, { useState } from 'react';
import { AnalysisResult } from '../types';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneLight } from 'react-syntax-highlighter/dist/esm/styles/prism';
import './OptimizationResults.css';

interface OptimizationResultsProps {
  result: AnalysisResult;
}

const OptimizationResults: React.FC<OptimizationResultsProps> = ({ result }) => {
  const [expandedSuggestions, setExpandedSuggestions] = useState<Set<number>>(new Set());

  const toggleSuggestion = (index: number) => {
    const newExpanded = new Set(expandedSuggestions);
    if (newExpanded.has(index)) {
      newExpanded.delete(index);
    } else {
      newExpanded.add(index);
    }
    setExpandedSuggestions(newExpanded);
  };

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'high': return '🔴';
      case 'medium': return '🟡';
      case 'low': return '🟢';
      default: return '🔵';
    }
  };

  const getSeverityClass = (severity: string) => {
    return `severity-${severity}`;
  };

  const getComplexityLevel = (score: number) => {
    if (score <= 20) return { level: 'Simple', color: 'green' };
    if (score <= 40) return { level: 'Moderate', color: 'orange' };
    if (score <= 70) return { level: 'Complex', color: 'red' };
    return { level: 'Very Complex', color: 'darkred' };
  };

  const complexity = getComplexityLevel(result.complexity_score);

  return (
    <div className="optimization-results">
      <div className="results-header">
        <h2>📊 Analysis Results</h2>
        <div className="query-summary">
          <div className="complexity-badge">
            <span className="complexity-label">Complexity:</span>
            <span className={`complexity-value ${complexity.color}`}>
              {complexity.level} ({result.complexity_score}/100)
            </span>
          </div>
        </div>
      </div>

      <div className="analyzed-query-section">
        <h3>🔍 Analyzed Query</h3>
        <div className="query-display">
          <SyntaxHighlighter
            language="sql"
            style={oneLight}
            customStyle={{
              padding: '1rem',
              borderRadius: '8px',
              fontSize: '14px',
              lineHeight: '1.5'
            }}
          >
            {result.query}
          </SyntaxHighlighter>
        </div>
      </div>

      <div className="suggestions-section">
        <h3>💡 Optimization Suggestions</h3>
        
        {result.suggestions.length === 0 ? (
          <div className="no-suggestions">
            <div className="success-icon">✅</div>
            <h4>Great job!</h4>
            <p>No optimization issues found in your query. Your SQL looks good!</p>
          </div>
        ) : (
          <div className="suggestions-list">
            {result.suggestions.map((suggestion, index) => (
              <div
                key={index}
                className={`suggestion-card ${getSeverityClass(suggestion.severity)}`}
              >
                <div
                  className="suggestion-header"
                  onClick={() => toggleSuggestion(index)}
                >
                  <div className="suggestion-title">
                    <span className="severity-icon">
                      {getSeverityIcon(suggestion.severity)}
                    </span>
                    <span className="title-text">{suggestion.title}</span>
                    <span className="suggestion-type">{suggestion.type}</span>
                  </div>
                  <button className="expand-button">
                    {expandedSuggestions.has(index) ? '▼' : '▶'}
                  </button>
                </div>

                <div className="suggestion-description">
                  {suggestion.description}
                </div>

                {expandedSuggestions.has(index) && (
                  <div className="suggestion-details">
                    <div className="suggestion-recommendation">
                      <h5>📋 Recommendation:</h5>
                      <p>{suggestion.suggestion}</p>
                    </div>

                    {suggestion.example && (
                      <div className="suggestion-example">
                        <h5>💻 Example:</h5>
                        <SyntaxHighlighter
                          language="sql"
                          style={oneLight}
                          customStyle={{
                            fontSize: '12px',
                            padding: '0.8rem',
                            borderRadius: '6px',
                            margin: 0
                          }}
                        >
                          {suggestion.example}
                        </SyntaxHighlighter>
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {result.execution_plan_tips.length > 0 && (
        <div className="execution-tips-section">
          <h3>🎯 Execution Plan Tips</h3>
          <div className="tips-list">
            {result.execution_plan_tips.map((tip, index) => (
              <div key={index} className="tip-item">
                <span className="tip-icon">💡</span>
                <span className="tip-text">{tip}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="summary-stats">
        <div className="stat-item">
          <span className="stat-label">Total Suggestions:</span>
          <span className="stat-value">{result.suggestions.length}</span>
        </div>
        <div className="stat-item">
          <span className="stat-label">High Priority:</span>
          <span className="stat-value high">
            {result.suggestions.filter(s => s.severity === 'high').length}
          </span>
        </div>
        <div className="stat-item">
          <span className="stat-label">Medium Priority:</span>
          <span className="stat-value medium">
            {result.suggestions.filter(s => s.severity === 'medium').length}
          </span>
        </div>
        <div className="stat-item">
          <span className="stat-label">Low Priority:</span>
          <span className="stat-value low">
            {result.suggestions.filter(s => s.severity === 'low').length}
          </span>
        </div>
      </div>
    </div>
  );
};

export default OptimizationResults; 