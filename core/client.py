import time
import os
import json
from typing import Optional, List, Dict, Any, Generator, AsyncGenerator
from openai import OpenAI, AsyncOpenAI
from core.config import settings


class NebiusLLMClient:
    """
    OpenAI-compatible client for Nebius Token Factory,
    specialized for NVIDIA Nemotron models.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        mock_fallback: Optional[bool] = None,
    ):
        self.api_key = api_key or settings.nebius_api_key
        self.base_url = base_url or settings.nebius_base_url
        self.model = model or settings.nebius_model
        self.mock_fallback = (
            mock_fallback
            if mock_fallback is not None
            else settings.autofix_mock_fallback
        )

        self._has_real_key = bool(self.api_key and self.api_key.strip() and not self.api_key.startswith("your_"))
        
        if self._has_real_key:
            self.client = OpenAI(base_url=self.base_url, api_key=self.api_key)
            self.async_client = AsyncOpenAI(base_url=self.base_url, api_key=self.api_key)
        else:
            self.client = None
            self.async_client = None

    @property
    def is_using_mock(self) -> bool:
        return not self._has_real_key

    def complete(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.2,
        max_tokens: int = 2048,
    ) -> Dict[str, Any]:
        """
        Synchronous completion call.
        Returns dict with:
        - content: str
        - model: str
        - latency_ms: float
        - prompt_tokens: int
        - completion_tokens: int
        """
        start_time = time.time()

        if self._has_real_key and self.client:
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                latency_ms = (time.time() - start_time) * 1000
                choice = response.choices[0]
                usage = response.usage

                return {
                    "content": choice.message.content or "",
                    "model": self.model,
                    "latency_ms": round(latency_ms, 2),
                    "prompt_tokens": usage.prompt_tokens if usage else 0,
                    "completion_tokens": usage.completion_tokens if usage else 0,
                    "is_mock": False,
                }
            except Exception as e:
                if not self.mock_fallback:
                    raise e
                # Fall through to mock response if fallback enabled

        # Offline / Mock response mode
        time.sleep(0.3)  # Simulate fast Nebius TTFT
        latency_ms = (time.time() - start_time) * 1000
        mock_content = self._generate_mock_completion(messages)

        return {
            "content": mock_content,
            "model": f"{self.model} (Nebius Simulated)",
            "latency_ms": round(latency_ms, 2),
            "prompt_tokens": 420,
            "completion_tokens": 185,
            "is_mock": True,
        }

    async def acomplete(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.2,
        max_tokens: int = 2048,
    ) -> Dict[str, Any]:
        """Asynchronous completion call."""
        start_time = time.time()

        if self._has_real_key and self.async_client:
            try:
                response = await self.async_client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                latency_ms = (time.time() - start_time) * 1000
                choice = response.choices[0]
                usage = response.usage

                return {
                    "content": choice.message.content or "",
                    "model": self.model,
                    "latency_ms": round(latency_ms, 2),
                    "prompt_tokens": usage.prompt_tokens if usage else 0,
                    "completion_tokens": usage.completion_tokens if usage else 0,
                    "is_mock": False,
                }
            except Exception as e:
                if not self.mock_fallback:
                    raise e

        # Fallback
        time.sleep(0.2)
        latency_ms = (time.time() - start_time) * 1000
        mock_content = self._generate_mock_completion(messages)

        return {
            "content": mock_content,
            "model": f"{self.model} (Nebius Simulated)",
            "latency_ms": round(latency_ms, 2),
            "prompt_tokens": 420,
            "completion_tokens": 185,
            "is_mock": True,
        }

    def _generate_mock_completion(self, messages: List[Dict[str, str]]) -> str:
        """
        Smart deterministic mock generator for test scenarios when Nebius API key is not supplied.
        """
        user_prompt = ""
        for m in messages:
            if m.get("role") == "user":
                user_prompt += m.get("content", "") + " "

        prompt_lower = user_prompt.lower()

        # Scenario 1: Python math / calculator test failure
        if "calculator" in prompt_lower or "add" in prompt_lower or "math" in prompt_lower or "pytest" in prompt_lower:
            return json.dumps({
                "root_cause": "Off-by-one arithmetic error in the addition implementation. The function was adding +1 inadvertently.",
                "explanation": "The calculate_sum function contained a logic defect `return a + b + 1` instead of `return a + b`. Correcting this aligns the output with the expected test assertions.",
                "failing_file": "calculator.py",
                "patched_content": 'def add(a: int, b: int) -> int:\n    """Return the sum of two integers."""\n    return a + b\n\ndef multiply(a: int, b: int) -> int:\n    """Return the product of two integers."""\n    return a * b\n',
                "diff_summary": "- return a + b + 1\n+ return a + b"
            }, indent=2)

        # Scenario 2: TypeScript / Node validator error
        if "validator" in prompt_lower or "email" in prompt_lower or "ts" in prompt_lower or "jest" in prompt_lower:
            return json.dumps({
                "root_cause": "Regex in email validation function improperly accepted empty domain suffixes.",
                "explanation": "The regex string allowed trailing dots and empty domains. Updating the regex to require a 2+ character TLD resolves the failing unit test.",
                "failing_file": "validator.js",
                "patched_content": 'function isValidEmail(email) {\n  const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$/;\n  return emailRegex.test(email);\n}\n\nmodule.exports = { isValidEmail };\n',
                "diff_summary": "Fixed email regex to mandate valid top-level domain."
            }, indent=2)

        # Scenario 3: Dockerfile error
        if "docker" in prompt_lower or "apt-get" in prompt_lower:
            return json.dumps({
                "root_cause": "Missing apt-get update before apt-get install causing package 404 in Debian base image.",
                "explanation": "Debian bookworm images require running `apt-get update` in the same layer as `apt-get install -y --no-install-recommends` to ensure package lists are current.",
                "failing_file": "Dockerfile",
                "patched_content": 'FROM python:3.12-slim\nWORKDIR /app\nRUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates && rm -rf /var/lib/apt/lists/*\nCOPY . .\nCMD ["python", "main.py"]\n',
                "diff_summary": "Combined apt-get update && apt-get install with cache cleanup."
            }, indent=2)

        # Generic fallback
        return json.dumps({
            "root_cause": "Identified syntax or logic discrepancy in failing module based on stack trace inspection.",
            "explanation": "NVIDIA Nemotron reasoned across the stack trace and reconstructed the expected input/output contract.",
            "failing_file": "app.py",
            "patched_content": "# Auto-remediated by AutoFix CI via NVIDIA Nemotron\n",
            "diff_summary": "Auto-remediated syntax/assertion error."
        }, indent=2)


llm_client = NebiusLLMClient()
