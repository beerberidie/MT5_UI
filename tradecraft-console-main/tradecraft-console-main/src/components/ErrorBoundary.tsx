import React from 'react';

type Props = { children: React.ReactNode };

type State = { hasError: boolean; message?: string };

export default class ErrorBoundary extends React.Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: any): State {
    return { hasError: true, message: error?.message || String(error) };
  }

  componentDidCatch(error: any, info: any) {
    // Optional: log to backend later
    console.error('UI ErrorBoundary caught:', error, info);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-background text-text-primary flex items-center justify-center p-8">
          <div className="max-w-lg w-full bg-card border border-border rounded p-6 text-center">
            <h2 className="text-lg font-semibold mb-2">Something went wrong</h2>
            <p className="text-sm text-text-secondary mb-4">The UI hit an unexpected error. Try reloading the page.</p>
            {this.state.message && (
              <pre className="text-xs bg-panel p-3 rounded overflow-auto text-left">{this.state.message}</pre>
            )}
            <button type="button" onClick={() => window.location.reload()} className="btn-secondary mt-4">Reload</button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}

