import React from 'react';

const AI: React.FC = () => {
  return (
    <div className="min-h-screen bg-background text-text-primary">
      <div className="h-header bg-panel border-b border-border flex items-center px-4">
        <h1 className="text-lg font-semibold">AI</h1>
      </div>

      <div className="max-w-6xl mx-auto p-4">
        <div className="trading-panel">
          <div className="trading-header">
            <h3 className="font-medium">AI Assistant</h3>
          </div>
          <div className="trading-content">
            <p className="text-sm text-text-secondary">
              This is the AI main view. Predictions, suggestions, and strategy insights will render here.
            </p>
            <div className="mt-3 text-xs text-text-muted">
              Placeholder: integrate symbol-aware trends, risk-adjusted suggestions, and one-click order scaffolds.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AI;

