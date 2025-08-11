export interface OptimizationSuggestion {
  type: string;
  severity: 'low' | 'medium' | 'high';
  title: string;
  description: string;
  suggestion: string;
  example?: string;
}

export interface AnalysisResult {
  query: string;
  database_type: string;
  suggestions: OptimizationSuggestion[];
  complexity_score: number;
  execution_plan_tips: string[];
  syntax_errors?: string[];
}

export interface SQLQuery {
  query: string;
  database_type: string;
}

export interface DatabaseOption {
  value: string;
  label: string;
  description: string;
  icon: string;
}

export const DATABASE_OPTIONS: DatabaseOption[] = [
  {
    value: 'mysql',
    label: 'MySQL',
    description: 'Open-source relational database',
    icon: '🐬'
  },
  {
    value: 'postgresql',
    label: 'PostgreSQL',
    description: 'Advanced open-source database',
    icon: '🐘'
  },
  {
    value: 'oracle',
    label: 'Oracle',
    description: 'Enterprise database system',
    icon: '🔴'
  },
  {
    value: 'sqlserver',
    label: 'SQL Server',
    description: 'Microsoft database system',
    icon: '🟦'
  }
]; 