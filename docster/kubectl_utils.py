# kubectl_utils.py

import subprocess
from typing import Optional

def run_command(command: list) -> str:
    """
    Helper function to run a command via subprocess.
    Raises an exception if the command fails.
    """
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        raise Exception(f"Command '{' '.join(command)}' failed with error: {result.stderr.strip()}")
    return result.stdout.strip()


def get_logs(pod_name: str, namespace: str, since_time: str, tail_lines: int) -> str:
    """
    Fetch logs for a specified pod.
    
    Args:
        pod_name (str): Name of the pod.
        namespace (str): Kubernetes namespace.
        since_time (str): Time window for logs (e.g., "5m").
        tail_lines (int): Number of tail lines to retrieve.
        
    Returns:
        str: Logs output.
    """
    # Construct the command:
    # Example: kubectl logs <pod_name> -n <namespace> --since=5m --tail=100
    command = [
        "kubectl", "logs", pod_name,
        "-n", namespace,
        f"--since={since_time}",
        f"--tail={tail_lines}"
    ]
    return run_command(command)


def describe_pod(pod_name: str, namespace: str) -> str:
    """
    Get detailed description of a pod.
    
    Args:
        pod_name (str): Name of the pod.
        namespace (str): Kubernetes namespace.
    
    Returns:
        str: Output of 'kubectl describe pod'.
    """
    command = [
        "kubectl", "describe", "pod", pod_name,
        "-n", namespace
    ]
    return run_command(command)


def get_events(namespace: str, since_time: Optional[str] = None) -> str:
    """
    Retrieve cluster events for a namespace.
    
    Args:
        namespace (str): Kubernetes namespace.
        since_time (Optional[str]): Time window for events (e.g., "10m").
                                     (Note: Filtering by time may need additional parsing.)
    
    Returns:
        str: Output of 'kubectl get events'.
    """
    # Base command to get events sorted by creation timestamp.
    command = [
        "kubectl", "get", "events",
        "-n", namespace,
        "--sort-by=.metadata.creationTimestamp"
    ]
    
    # If since_time is provided, you might add filtering in the future.
    # For now, we return all events sorted by time.
    return run_command(command)


def get_service_info(service_name: str, namespace: str) -> str:
    """
    Get details about a specific Kubernetes service.
    
    Args:
        service_name (str): Name of the service.
        namespace (str): Kubernetes namespace.
        
    Returns:
        str: Output of 'kubectl get svc'.
    """
    command = [
        "kubectl", "get", "svc", service_name,
        "-n", namespace,
        "-o", "yaml"  # Return output in YAML format for better readability
    ]
    return run_command(command)
