"""Isolated, secure Groq client for Phase 8 AI Analyst."""

import json
import logging
import os
import time
from typing import Any, Dict, Optional

import requests

from hexnil.exceptions import GroqApiError, GroqConfigurationError

logger = logging.getLogger("hexnil.explain.client")

DEFAULT_GROQ_ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"
DEFAULT_GROQ_MODEL = "llama-3.3-70b-versatile"


class GroqClient:
    """Secure client for communicating with Groq API. Credentials remain server-side only."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = DEFAULT_GROQ_MODEL,
        endpoint: str = DEFAULT_GROQ_ENDPOINT,
        timeout_seconds: float = 15.0,
    ):
        self.api_key = api_key or os.environ.get("GROQ_API_KEY")
        self.model = model
        self.endpoint = endpoint
        self.timeout_seconds = timeout_seconds

    def has_valid_key(self) -> bool:
        """Check if an API key is configured without exposing it."""
        return bool(self.api_key and self.api_key.strip())

    def complete(
        self,
        user_prompt: str,
        system_prompt: str,
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Execute chat completion request with constrained temperature and JSON output format."""
        if not self.has_valid_key():
            raise GroqConfigurationError()

        selected_model = model or self.model
        headers = {
            "Authorization": f"Bearer {self.api_key.strip()}",
            "Content-Type": "application/json",
            "User-Agent": "Hexnil-AI-Analyst/1.0",
        }

        payload = {
            "model": selected_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.1,
            "max_tokens": 2048,
        }

        start_time = time.perf_counter()
        try:
            # Safe log: never log headers, auth tokens, or raw prompts
            logger.info("Sending constrained inference request to Groq model '%s'", selected_model)
            response = requests.post(
                self.endpoint,
                headers=headers,
                json=payload,
                timeout=self.timeout_seconds,
            )
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0

            if response.status_code != 200:
                logger.error("Groq API returned HTTP status %d", response.status_code)
                raise GroqApiError(f"HTTP status {response.status_code}: {response.text[:200]}")

            res_json = response.json()
            choices = res_json.get("choices", [])
            if not choices or "message" not in choices[0]:
                raise GroqApiError("Malformed Groq response: missing 'choices[0].message'")

            content_text = choices[0]["message"].get("content", "")
            if not content_text:
                raise GroqApiError("Empty message content returned from Groq")

            try:
                parsed_data = json.loads(content_text)
            except json.JSONDecodeError as exc:
                raise GroqApiError(f"Groq response content is not valid JSON: {exc}")

            parsed_data["_latency_ms"] = elapsed_ms
            parsed_data["_model"] = selected_model
            return parsed_data

        except requests.exceptions.Timeout:
            logger.warning("Groq API request timed out after %.1fs", self.timeout_seconds)
            raise GroqApiError(f"Request timed out after {self.timeout_seconds}s")
        except requests.exceptions.RequestException as exc:
            # Sanitize exception message so it doesn't leak secrets or URLs with tokens
            safe_msg = str(exc.__class__.__name__)
            logger.warning("Groq network request failed: %s", safe_msg)
            raise GroqApiError(f"Network error during Groq API call ({safe_msg})")
