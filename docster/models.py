# models.py
#docsting for this file

"""
This module defines Pydantic models for the API responses.

These models are used to define the structure of the JSON responses returned by the API endpoints.

Classes:
    LogChunk: Pydantic model for a single chunk of log lines.
    LogResponse: Pydantic model for the log response.
    DescribeResponse: Pydantic model for the pod description response.
    Event: Pydantic model for a single event.
    EventResponse: Pydantic model for the event response.
    ServiceResponse: Pydantic model for the service response.
"""

from pydantic import BaseModel
from typing import List, Optional

class LogChunk(BaseModel):
    chunk_index: int
    lines: List[str]

class LogResponse(BaseModel):
    pod_name: str
    namespace: str
    logs: List[LogChunk]
    metadata: Optional[dict] = None  # e.g., {"since_time": "5m", "total_chunks": 3}

class DescribeResponse(BaseModel):
    pod_name: str
    namespace: str
    description: str

class Event(BaseModel):
    event_type: str
    reason: str
    message: str
    timestamp: Optional[str] = None

class EventResponse(BaseModel):
    namespace: str
    events: List[Event]

class ServiceResponse(BaseModel):
    service_name: str
    namespace: str
    service_info: str
