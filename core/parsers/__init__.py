from core.parsers.base import BaseLogParser, LogIncident
from core.parsers.python_pytest import PytestLogParser
from core.parsers.node_npm import NodeNpmLogParser
from core.parsers.docker_build import DockerBuildLogParser
from core.parsers.universal import UniversalLogParser

PARSERS: list[BaseLogParser] = [
    PytestLogParser(),
    NodeNpmLogParser(),
    DockerBuildLogParser(),
    UniversalLogParser(),  # Fallback
]


def parse_ci_logs(raw_logs: str) -> LogIncident:
    for parser in PARSERS:
        if parser.can_parse(raw_logs):
            return parser.parse(raw_logs)
    return UniversalLogParser().parse(raw_logs)


__all__ = [
    "BaseLogParser",
    "LogIncident",
    "PytestLogParser",
    "NodeNpmLogParser",
    "DockerBuildLogParser",
    "UniversalLogParser",
    "parse_ci_logs",
]
