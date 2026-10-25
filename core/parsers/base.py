from abc import ABC, abstractmethod
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import uuid


class LogIncident(BaseModel):
    id: str = Field(default_factory=lambda: f"inc_{uuid.uuid4().hex[:8]}")
    framework: str = "generic"  # pytest, jest, tsc, docker, generic
    raw_logs: str
    failure_summary: str
    error_type: str = "GeneralFailure"
    failing_file: Optional[str] = None
    line_number: Optional[int] = None
    failing_test_name: Optional[str] = None
    stack_trace: str = ""
    exit_code: int = 1
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BaseLogParser(ABC):
    @abstractmethod
    def can_parse(self, raw_logs: str) -> bool:
        """Returns True if this parser can handle the provided logs."""
        pass

    @abstractmethod
    def parse(self, raw_logs: str) -> LogIncident:
        """Parses the raw logs into a structured LogIncident."""
        pass
