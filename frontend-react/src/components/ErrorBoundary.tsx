import { Component } from 'react';
import type { ErrorInfo, ReactNode } from 'react';

interface Props {
    children: ReactNode;
}

interface State {
    hasError: boolean;
    error: Error | null;
}

class ErrorBoundary extends Component<Props, State> {
    public state: State = {
        hasError: false,
        error: null,
    };

    public static getDerivedStateFromError(error: Error): State {
        return { hasError: true, error };
    }

    public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
        console.error('ErrorBoundary caught:', error, errorInfo);
    }

    public render() {
        if (this.state.hasError) {
            return (
                <div className="min-h-screen flex items-center justify-center bg-bg-deep p-8">
                    <div className="glass p-8 rounded-3xl max-w-lg w-full text-center space-y-4 border border-red-500/20">
                        <div className="w-16 h-16 mx-auto bg-red-500/20 rounded-full flex items-center justify-center">
                            <span className="text-red-500 text-2xl font-bold">!</span>
                        </div>
                        <h2 className="text-xl font-bold text-white">Something went wrong</h2>
                        <p className="text-slate-400 text-sm">
                            {this.state.error?.message || 'An unexpected error occurred'}
                        </p>
                        <button
                            onClick={() => {
                                this.setState({ hasError: false, error: null });
                                window.location.href = '/dashboard';
                            }}
                            className="px-6 py-3 bg-brand-primary text-white rounded-xl font-bold hover:bg-brand-primary/80 transition-colors"
                        >
                            Return to Dashboard
                        </button>
                    </div>
                </div>
            );
        }

        return this.props.children;
    }
}

export default ErrorBoundary;
