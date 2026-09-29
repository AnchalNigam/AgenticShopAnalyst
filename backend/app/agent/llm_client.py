"""Provider-agnostic LLM client supporting Google Gemini and OpenAI/Ollama."""

from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")


@dataclass
class ToolCallRequest:
    """Standardized representation of a tool call requested by an LLM."""

    id: str
    name: str
    args: dict[str, Any]


@dataclass
class LLMResponse:
    """Standardized representation of an LLM response."""

    content: str | None
    tool_calls: list[ToolCallRequest] = field(default_factory=list)
    raw_response: Any = None


class BaseLLMClient(ABC):
    """Abstract base class for all LLM providers."""

    @abstractmethod
    def chat(
        self,
        messages: list[dict[str, Any]],
        system_prompt: str,
        tools: list[dict[str, Any]] | None = None,
    ) -> LLMResponse:
        """Send a conversation turn to the LLM and return a standardized response."""
        pass


class GeminiClient(BaseLLMClient):
    """Client for Google Gemini models using the official google-genai SDK."""

    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        from google import genai

        self.api_key = api_key or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("Google API key not found. Set GOOGLE_API_KEY or GEMINI_API_KEY in .env.")

        # Default to gemini-3.5-flash (fast and active)
        self.model_name = model or os.getenv("LLM_MODEL", "gemini-3.5-flash")
        self.client = genai.Client(api_key=self.api_key)

    def chat(
        self,
        messages: list[dict[str, Any]],
        system_prompt: str,
        tools: list[dict[str, Any]] | None = None,
    ) -> LLMResponse:
        from google.genai import types

        # Build tools config
        tool_objects = []
        if tools:
            declarations = [
                types.FunctionDeclaration(
                    name=tool["name"],
                    description=tool.get("description", ""),
                    parameters_json_schema=tool.get("parameters", {}),
                )
                for tool in tools
            ]
            tool_objects.append(types.Tool(function_declarations=declarations))

        config = types.GenerateContentConfig(
            system_instruction=system_prompt,
            tools=tool_objects if tool_objects else None,
            temperature=0.0,  # Zero temperature for deterministic SQL generation
        )

        # Convert standardized message dicts to Gemini Content objects
        contents: list[types.Content] = []
        for msg in messages:
            role = msg["role"]
            if role == "user":
                contents.append(
                    types.Content(
                        role="user",
                        parts=[types.Part.from_text(text=msg["content"])],
                    )
                )
            elif role == "assistant":
                parts: list[types.Part] = []
                if msg.get("content"):
                    parts.append(types.Part.from_text(text=msg["content"]))
                if msg.get("tool_calls"):
                    for tc in msg["tool_calls"]:
                        parts.append(
                            types.Part.from_function_call(
                                name=tc.name,
                                args=tc.args,
                            )
                        )
                if parts:
                    contents.append(types.Content(role="model", parts=parts))
            elif role == "tool":
                # In Gemini SDK, tool responses have role='tool' and contain function_response
                response_data = msg.get("content")
                if isinstance(response_data, str):
                    try:
                        response_data = json.loads(response_data)
                    except Exception:
                        response_data = {"output": response_data}
                parts = [
                    types.Part.from_function_response(
                        name=msg.get("name", "execute_sql_query"),
                        response=response_data,
                    )
                ]
                contents.append(types.Content(role="tool", parts=parts))

        # Resilience: Try preferred model, fallback if 503 high demand spike occurs
        candidate_models = list(
            dict.fromkeys([self.model_name, "gemini-3.5-flash", "gemini-3.6-flash", "gemini-3.5-flash-lite"])
        )
        response = None
        last_error = None

        for candidate in candidate_models:
            try:
                response = self.client.models.generate_content(
                    model=candidate,
                    contents=contents,
                    config=config,
                )
                break
            except Exception as exc:
                err_str = str(exc).lower()
                if "503" in err_str or "unavailable" in err_str or "high demand" in err_str:
                    last_error = exc
                    continue
                raise exc

        if response is None:
            raise last_error or RuntimeError("Failed to generate response across all fallback models.")

        # Parse tool calls from Gemini response
        tool_calls: list[ToolCallRequest] = []
        if response.function_calls:
            for idx, fc in enumerate(response.function_calls):
                tool_calls.append(
                    ToolCallRequest(
                        id=f"call_{idx}_{fc.name}",
                        name=fc.name,
                        args=dict(fc.args) if fc.args else {},
                    )
                )

        return LLMResponse(
            content=response.text if not tool_calls else None,
            tool_calls=tool_calls,
            raw_response=response,
        )


class OpenAIClient(BaseLLMClient):
    """Client for OpenAI and OpenAI-compatible endpoints (Ollama, Groq, OpenRouter)."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
    ) -> None:
        from openai import OpenAI

        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "ollama")
        self.base_url = base_url or os.getenv("OPENAI_BASE_URL")
        self.model_name = model or os.getenv("LLM_MODEL", "gpt-4o-mini")
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)

    def chat(
        self,
        messages: list[dict[str, Any]],
        system_prompt: str,
        tools: list[dict[str, Any]] | None = None,
    ) -> LLMResponse:
        openai_tools = None
        if tools:
            openai_tools = [
                {
                    "type": "function",
                    "function": {
                        "name": tool["name"],
                        "description": tool.get("description", ""),
                        "parameters": tool.get("parameters", {}),
                    },
                }
                for tool in tools
            ]

        # Format messages for OpenAI / Groq tool-calling specs
        formatted_messages: list[dict[str, Any]] = [{"role": "system", "content": system_prompt}]
        for msg in messages:
            role = msg["role"]
            if role == "user":
                formatted_messages.append({"role": "user", "content": msg["content"]})
            elif role == "assistant":
                item: dict[str, Any] = {"role": "assistant", "content": msg.get("content")}
                if msg.get("tool_calls"):
                    item["tool_calls"] = [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.name,
                                "arguments": json.dumps(tc.args) if isinstance(tc.args, dict) else str(tc.args),
                            },
                        }
                        for tc in msg["tool_calls"]
                    ]
                formatted_messages.append(item)
            elif role == "tool":
                content_str = (
                    json.dumps(msg["content"])
                    if isinstance(msg["content"], (dict, list))
                    else str(msg.get("content", ""))
                )
                formatted_messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": msg.get("tool_call_id", "call_1"),
                        "content": content_str,
                    }
                )

        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=formatted_messages,
            tools=openai_tools,
            temperature=0.0,
        )

        choice = response.choices[0]
        tool_calls: list[ToolCallRequest] = []
        if choice.message.tool_calls:
            for tc in choice.message.tool_calls:
                args = {}
                try:
                    args = json.loads(tc.function.arguments)
                except Exception:
                    args = {"raw_arguments": tc.function.arguments}
                tool_calls.append(
                    ToolCallRequest(
                        id=tc.id,
                        name=tc.function.name,
                        args=args,
                    )
                )

        return LLMResponse(
            content=choice.message.content,
            tool_calls=tool_calls,
            raw_response=response,
        )


def get_llm_client() -> BaseLLMClient:
    """Factory function returning the configured LLM client based on .env settings."""
    provider = os.getenv("LLM_PROVIDER", "").lower()
    google_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")

    if provider == "openai" or (not provider and openai_key and not google_key):
        return OpenAIClient()
    if provider == "gemini" or (not provider and google_key):
        return GeminiClient()

    # Default to Gemini if a Google key exists
    if google_key:
        return GeminiClient()

    raise ValueError(
        "No LLM provider configured. Set GOOGLE_API_KEY for Gemini or OPENAI_API_KEY in your .env file."
    )
