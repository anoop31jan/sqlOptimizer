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
  suggestions: OptimizationSuggestion[];
  complexity_score: number;
  execution_plan_tips: string[];
}

export interface SQLQuery {
  query: string;
} 