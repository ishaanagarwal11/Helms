# config.py

# Server configuration for the Bridge API
SERVER_HOST = "127.0.0.1"  # Use "0.0.0.0" if you want the server accessible from external hosts
SERVER_PORT = 8000         # Port where the API server will listen

# Kubernetes-related configuration
DEFAULT_NAMESPACE = "default"   # The Kubernetes namespace to use by default
LOG_CHUNK_SIZE = 100            # Number of log lines per chunk (for large log outputs)
DEFAULT_LOG_SINCE_TIME = "5m"   # Default time window for fetching logs (e.g., last 5 minutes)

# Additional configurations can be added here if needed
# For example, you might include paths to your kubeconfig file, authentication tokens, etc.
