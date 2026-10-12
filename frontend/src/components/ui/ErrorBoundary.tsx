import { Component, ErrorInfo, ReactNode } from 'react';
import { AlertTriangle, RefreshCw, RotateCcw } from 'lucide-react';
import { Button } from './Button';

interface ErrorBoundaryProps {
  children: ReactNode;
  fallbackTitle?: string;
  fallbackMessage?: string;
  fallback?: ReactNode;
  onReset?: () => void;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

function sanitizeErrorMessage(msg?: string | null): string {
  if (!msg) return 'An unexpected rendering error occurred.';
  return msg
    .replace(/(?:api[_-]?key|token|secret|password|bearer)[=:\s]+[^\s&"']+/gi, '[REDACTED]')
    .replace(/http[s]?:\/\/[^\s]+/g, (url) => url.split('?')[0]);
}

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    };
  }

  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    this.setState({ errorInfo });
    const sanitized = sanitizeErrorMessage(error.message);
    console.error('ErrorBoundary caught an unhandled component error:', sanitized);
  }

  handleReset = (): void => {
    this.setState({ hasError: false, error: null, errorInfo: null });
    if (this.props.onReset) {
      this.props.onReset();
    }
  };

  handleReload = (): void => {
    window.location.reload();
  };

  render(): ReactNode {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      const displayMessage = sanitizeErrorMessage(this.state.error?.message);

      return (
        <div className="bg-white border border-rose-200 rounded-2xl p-8 max-w-xl mx-auto my-8 shadow-xs space-y-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-rose-50 text-rose-600 flex items-center justify-center shrink-0">
              <AlertTriangle className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-900">
                {this.props.fallbackTitle || 'Component Rendering Error'}
              </h3>
              <p className="text-xs text-slate-500">
                {this.props.fallbackMessage || 'An unexpected rendering error occurred while mounting this view.'}
              </p>
            </div>
          </div>

          {displayMessage && (
            <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg text-xs font-mono text-rose-700 break-words max-h-32 overflow-y-auto">
              {displayMessage}
            </div>
          )}

          <div className="flex items-center gap-3 pt-2">
            <Button
              variant="outline"
              size="sm"
              onClick={this.handleReset}
              leftIcon={<RotateCcw className="w-3.5 h-3.5" />}
            >
              Try Again
            </Button>
            <Button
              variant="primary"
              size="sm"
              onClick={this.handleReload}
              leftIcon={<RefreshCw className="w-3.5 h-3.5" />}
            >
              Reload Page
            </Button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
