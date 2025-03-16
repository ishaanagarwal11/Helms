# handlers.py

from fastapi import APIRouter, HTTPException, Query
from typing import Optional

# Import configuration to use default namespace and log settings
import config

# Import Kubernetes utilities (we'll implement these functions in kubectl_utils.py)
from kubectl_utils import (
    get_logs,
    describe_pod,
    get_events,
    get_service_info
)

router = APIRouter()

@router.get("/get-logs")
async def api_get_logs(
    pod_name: str,
    namespace: str = Query(config.DEFAULT_NAMESPACE, description="Kubernetes namespace"),
    since_time: Optional[str] = Query(config.DEFAULT_LOG_SINCE_TIME, description="Time window for logs, e.g., '5m'"),
    tail_lines: Optional[int] = Query(100, description="Number of tail lines to retrieve")
):
    """
    Endpoint to fetch logs for a specified pod.
    """
    try:
        logs = get_logs(pod_name=pod_name, namespace=namespace, since_time=since_time, tail_lines=tail_lines)
        return {"pod_name": pod_name, "namespace": namespace, "logs": logs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/describe-pod")
async def api_describe_pod(
    pod_name: str,
    namespace: str = Query(config.DEFAULT_NAMESPACE, description="Kubernetes namespace")
):
    """
    Endpoint to return detailed description of a specific pod.
    """
    try:
        description = describe_pod(pod_name=pod_name, namespace=namespace)
        return {"pod_name": pod_name, "namespace": namespace, "description": description}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/get-events")
async def api_get_events(
    namespace: str = Query(config.DEFAULT_NAMESPACE, description="Kubernetes namespace"),
    since_time: Optional[str] = Query(None, description="Time window for events, e.g., '10m'")
):
    """
    Endpoint to fetch recent cluster events, optionally filtered by namespace and time.
    """
    try:
        events = get_events(namespace=namespace, since_time=since_time)
        return {"namespace": namespace, "events": events}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/get-svc")
async def api_get_service_info(
    service_name: str,
    namespace: str = Query(config.DEFAULT_NAMESPACE, description="Kubernetes namespace")
):
    """
    Endpoint to return details of a Kubernetes service.
    """
    try:
        svc_info = get_service_info(service_name=service_name, namespace=namespace)
        return {"service_name": service_name, "namespace": namespace, "service_info": svc_info}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
