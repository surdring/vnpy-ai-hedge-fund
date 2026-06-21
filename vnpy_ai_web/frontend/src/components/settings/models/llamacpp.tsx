import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import { AlertTriangle, Brain, CheckCircle, Cpu, RefreshCw, Server } from 'lucide-react';
import { useEffect, useState } from 'react';

interface LlamaCppStatus {
  running: boolean;
  server_url: string;
  available_models: string[];
  error?: string;
}

export function LlamaCppSettings() {
  const [status, setStatus] = useState<LlamaCppStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchStatus = async () => {
    try {
      const response = await fetch('http://localhost:8000/llamacpp/status');
      if (response.ok) {
        const data = await response.json();
        setStatus(data);
        setError(null);
      } else {
        const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
        setError(`Failed to get status: ${errorData.detail}`);
      }
    } catch (err) {
      console.error('Failed to fetch llama.cpp status:', err);
      setError('Failed to connect to backend service');
    }
  };

  const refreshStatus = async () => {
    setLoading(true);
    setError(null);
    await fetchStatus();
    setLoading(false);
  };

  useEffect(() => {
    refreshStatus();
  }, []);

  const getStatusIcon = () => {
    if (!status) return <RefreshCw className="h-4 w-4 animate-spin text-muted-foreground" />;
    if (!status.running) return <AlertTriangle className="h-4 w-4 text-muted-foreground" />;
    return <CheckCircle className="h-4 w-4 text-muted-foreground" />;
  };

  const getStatusText = () => {
    if (!status) return "Checking...";
    if (!status.running) return "Not Running";
    return "Running";
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-primary mb-2">llama.cpp</h3>
          <p className="text-sm text-muted-foreground dark:text-muted-foreground">
            Connect to a local llama.cpp server with OpenAI-compatible API for enhanced privacy and performance.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="secondary" className="flex items-center gap-1">
            {getStatusIcon()}
            {getStatusText()}
          </Badge>
          <Button
            size="sm"
            onClick={refreshStatus}
            disabled={loading}
            className="text-primary hover:bg-primary/20 hover:text-primary bg-primary/10 border-primary/30 hover:border-primary/50"
          >
            <RefreshCw className={cn("h-4 w-4", loading && "animate-spin")} />
          </Button>
        </div>
      </div>

      {error && (
        <div className="bg-red-900/20 border border-red-600/30 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <AlertTriangle className="h-5 w-5 text-red-400 mt-0.5" />
            <div>
              <h4 className="font-medium text-red-300">Error</h4>
              <p className="text-sm text-red-400 mt-1">{error}</p>
            </div>
          </div>
        </div>
      )}

      {!status?.running && (
        <div className="bg-muted rounded-lg p-4">
          <div className="flex items-start gap-3">
            <Cpu className="h-5 w-5 text-muted-foreground mt-0.5" />
            <div>
              <h4 className="font-medium text-muted-foreground">llama.cpp Server Not Detected</h4>
              <p className="text-sm text-muted-foreground mt-1">
                To use llama.cpp, start the server with:{' '}
                <code className="bg-muted-foreground/20 px-1.5 py-0.5 rounded text-xs">
                  ./llama-server -m model.gguf --port 8080
                </code>
              </p>
              <p className="text-sm text-muted-foreground mt-1">
                The server exposes an OpenAI-compatible API at{' '}
                <code className="bg-muted-foreground/20 px-1.5 py-0.5 rounded text-xs">
                  http://localhost:8080/v1
                </code>
              </p>
            </div>
          </div>
        </div>
      )}

      {status?.running && (
        <div className="flex items-center justify-between bg-muted rounded-lg p-4">
          <div className="flex items-center gap-2">
            <CheckCircle className="h-5 w-5 text-primary" />
            <div>
              <span className="font-medium text-primary">
                llama.cpp Server Running
              </span>
              <p className="text-sm text-muted-foreground">
                Server available at {status.server_url}
              </p>
            </div>
          </div>
        </div>
      )}

      {status?.running && (
        <div className="space-y-2">
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-medium text-primary">Available Models</h3>
            <span className="text-xs text-muted-foreground">
              {status.available_models.length} models
            </span>
          </div>
          
          {status.available_models.length > 0 ? (
            <div className="space-y-1">
              {status.available_models.map((modelName) => (
                <div 
                  key={modelName} 
                  className="group flex items-center justify-between bg-muted hover-bg rounded-md px-3 py-2.5 transition-colors"
                >
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-sm truncate text-primary">{modelName}</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge className="text-xs text-primary bg-primary/10 border-primary/30 hover:bg-primary/20 hover:border-primary/50">
                      llama.cpp
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-muted-foreground">
              <Brain className="h-8 w-8 mx-auto mb-2 opacity-50" />
              <p className="text-sm">No models loaded</p>
              <p className="text-xs mt-1">Load a model with llama-server to see it here</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}