import pytest
from core.parsers import (
    PytestLogParser,
    NodeNpmLogParser,
    DockerBuildLogParser,
    UniversalLogParser,
    parse_ci_logs,
)

PYTEST_SAMPLE = """
=================================== FAILURES ===================================
__________________________ test_add_positive_numbers ___________________________
    def test_add_positive_numbers():
>       assert add(2, 3) == 5
E       assert 6 == 5
E        +  where 6 = add(2, 3)
test_calculator.py:5: AssertionError
=========================== short test summary info ============================
FAILED test_calculator.py::test_add_positive_numbers - assert 6 == 5
"""

NODE_SAMPLE = """
FAIL src/validator.test.ts
  ● Email Validator › should reject email missing domain
    AssertionError [ERR_ASSERTION]: Missing domain should fail
      Expected: false
      Received: true
"""

DOCKER_SAMPLE = """
=> ERROR [2/3] RUN apt-get install -y --no-install-recommends curl
ERROR: failed to solve: process returned a non-zero code: 100
"""


def test_pytest_parser():
    parser = PytestLogParser()
    assert parser.can_parse(PYTEST_SAMPLE)
    incident = parser.parse(PYTEST_SAMPLE)
    assert incident.framework == "pytest"
    assert incident.failing_file == "test_calculator.py"
    assert incident.error_type == "AssertionError"


def test_node_parser():
    parser = NodeNpmLogParser()
    assert parser.can_parse(NODE_SAMPLE)
    incident = parser.parse(NODE_SAMPLE)
    assert incident.framework == "jest"
    assert incident.failing_file == "src/validator.test.ts"


def test_docker_parser():
    parser = DockerBuildLogParser()
    assert parser.can_parse(DOCKER_SAMPLE)
    incident = parser.parse(DOCKER_SAMPLE)
    assert incident.framework == "docker"
    assert incident.exit_code == 100


def test_auto_dispatcher():
    inc = parse_ci_logs(PYTEST_SAMPLE)
    assert inc.framework == "pytest"
