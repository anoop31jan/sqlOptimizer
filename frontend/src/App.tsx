import React, { useState } from 'react';
import './App.css';
import QueryInput from './components/QueryInput';
import OptimizationResults from './components/OptimizationResults';
import { AnalysisResult } from './types';

function App() {
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleAnalysisComplete = (result: AnalysisResult) => {
    setAnalysisResult(result);
    setIsLoading(false);
  };

  const handleAnalysisStart = () => {
    setIsLoading(true);
    setAnalysisResult(null);
  };

  return (
    <div className="App">
      <header className="app-header">
        <div className="header-content">
          <h1>🚀 SQL Optimizer Dashboard</h1>
          <p>Analyze your SQL queries and get intelligent optimization suggestions</p>
        </div>
      </header>

      <main className="main-content">
        <div className="container">
          <QueryInput 
            onAnalysisStart={handleAnalysisStart}
            onAnalysisComplete={handleAnalysisComplete}
            isLoading={isLoading}
          />
          
          {isLoading && (
            <div className="loading-container">
              <div className="loading-spinner"></div>
              <p>Analyzing your query...</p>
            </div>
          )}
          
          {analysisResult && !isLoading && (
            <OptimizationResults result={analysisResult} />
          )}
        </div>
      </main>

      <footer className="app-footer">
        <p>SQL Optimizer Dashboard - Built for better query performance</p>
      </footer>
    </div>
  );
}

export default App; 