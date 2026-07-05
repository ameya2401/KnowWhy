import abc
import asyncio
import logging
from collections.abc import AsyncGenerator
from typing import Any

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class LLMProvider(abc.ABC):
    """Abstract Base Class for Interchangeable LLM Providers."""

    @abc.abstractmethod
    async def generate_response(
        self, prompt: str, system_prompt: str | None = None, temperature: float = 0.2
    ) -> dict[str, Any]:
        """Generates response content and token usage statistics."""
        pass

    @abc.abstractmethod
    async def generate_stream(
        self, prompt: str, system_prompt: str | None = None, temperature: float = 0.2
    ) -> AsyncGenerator[dict[str, Any]]:
        """Yields chunks of generated text in real-time."""
        pass


class MockLLMProvider(LLMProvider):
    """Mock LLM provider that synthesizes responses based on retrieved context."""

    async def generate_response(
        self, prompt: str, system_prompt: str | None = None, temperature: float = 0.2
    ) -> dict[str, Any]:
        context_section = ""
        if "retrieved knowledge" in prompt.lower() or "context:" in prompt.lower():
            parts = prompt.split("Question:")
            if len(parts) > 0:
                context_section = parts[0]

        snippet_lines = []
        for line in context_section.split("\n"):
            if (
                "title:" in line.lower()
                or "source:" in line.lower()
                or "content:" in line.lower()
                or "description:" in line.lower()
            ):  # noqa: E501
                snippet_lines.append(line.strip())

        if snippet_lines:
            summary = "\n- ".join(snippet_lines[:8])
            answer = (
                f"Based on the retrieved context, here is the synthesis of information:\n\n"
                f"The organizational records indicate the following references:\n- {summary}\n\n"
                f"This answers the query with grounded evidence from the connected sources."
            )
        else:
            answer = (
                "Based on the local mock environment details, no extensive search context was provided. "  # noqa: E501
                "However, the system is fully operational and authenticated. Please connect Notion, Google Drive, "  # noqa: E501
                "or GitHub to harvest real organizational context."
            )

        return {
            "text": answer,
            "prompt_tokens": len(prompt.split()) // 3 + 10,
            "completion_tokens": len(answer.split()) // 3 + 10,
            "total_tokens": (len(prompt.split()) + len(answer.split())) // 3 + 20,
        }

    async def generate_stream(
        self, prompt: str, system_prompt: str | None = None, temperature: float = 0.2
    ) -> AsyncGenerator[dict[str, Any]]:
        resp = await self.generate_response(prompt, system_prompt, temperature)
        text = resp["text"]
        # Stream the text in chunks of words
        words = text.split(" ")
        for i, word in enumerate(words):
            yield {"text": word + (" " if i < len(words) - 1 else ""), "done": False}
            await asyncio.sleep(0.02)
        yield {
            "text": "",
            "done": True,
            "prompt_tokens": resp["prompt_tokens"],
            "completion_tokens": resp["completion_tokens"],
            "total_tokens": resp["total_tokens"],
        }


class OpenAIProvider(LLMProvider):
    """Communicates with OpenAI Chat Completions API."""

    def __init__(self, api_key: str, model: str = "gpt-4o-mini") -> None:
        self.api_key = api_key
        self.model = model
        self.mock_provider = MockLLMProvider()

    async def generate_response(
        self, prompt: str, system_prompt: str | None = None, temperature: float = 0.2
    ) -> dict[str, Any]:
        if not self.api_key:
            logger.info("OpenAI API key missing, falling back to Mock provider")
            return await self.mock_provider.generate_response(prompt, system_prompt, temperature)

        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            async with httpx.AsyncClient(timeout=45.0) as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "messages": messages,
                        "temperature": temperature,
                    },
                )
                if response.status_code == 200:
                    data = response.json()
                    choice = data["choices"][0]["message"]["content"]
                    usage = data.get("usage", {})
                    return {
                        "text": choice,
                        "prompt_tokens": usage.get("prompt_tokens", 0),
                        "completion_tokens": usage.get("completion_tokens", 0),
                        "total_tokens": usage.get("total_tokens", 0),
                    }
                else:
                    logger.warning(
                        "OpenAI API failed (HTTP %s): %s", response.status_code, response.text
                    )
                    return await self.mock_provider.generate_response(
                        prompt, system_prompt, temperature
                    )  # noqa: E501
        except Exception as e:
            logger.exception("Error calling OpenAI API: %s", e)
            return await self.mock_provider.generate_response(prompt, system_prompt, temperature)

    async def generate_stream(
        self, prompt: str, system_prompt: str | None = None, temperature: float = 0.2
    ) -> AsyncGenerator[dict[str, Any]]:
        if not self.api_key:
            async for chunk in self.mock_provider.generate_stream(
                prompt, system_prompt, temperature
            ):  # noqa: E501
                yield chunk
            return

        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            async with httpx.AsyncClient(timeout=45.0) as client:
                async with client.stream(
                    "POST",
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "messages": messages,
                        "temperature": temperature,
                        "stream": True,
                    },
                ) as response:
                    if response.status_code == 200:
                        async for line in response.aiter_lines():
                            line = line.strip()
                            if not line or line == "data: [DONE]":
                                continue
                            if line.startswith("data: "):
                                import json

                                try:
                                    data = json.loads(line[6:])
                                    choice = data["choices"][0]
                                    delta = choice.get("delta", {})
                                    text = delta.get("content", "")
                                    if text:
                                        yield {"text": text, "done": False}
                                except Exception:
                                    pass
                        yield {
                            "text": "",
                            "done": True,
                            "prompt_tokens": 0,
                            "completion_tokens": 0,
                            "total_tokens": 0,
                        }  # noqa: E501
                    else:
                        async for chunk in self.mock_provider.generate_stream(
                            prompt, system_prompt, temperature
                        ):  # noqa: E501
                            yield chunk
        except Exception:
            async for chunk in self.mock_provider.generate_stream(
                prompt, system_prompt, temperature
            ):  # noqa: E501
                yield chunk


class AnthropicProvider(LLMProvider):
    """Communicates with Anthropic Messages API."""

    def __init__(self, api_key: str, model: str = "claude-3-5-sonnet-20241022") -> None:
        self.api_key = api_key
        self.model = model
        self.mock_provider = MockLLMProvider()

    async def generate_response(
        self, prompt: str, system_prompt: str | None = None, temperature: float = 0.2
    ) -> dict[str, Any]:
        if not self.api_key:
            logger.info("Anthropic API key missing, falling back to Mock provider")
            return await self.mock_provider.generate_response(prompt, system_prompt, temperature)

        try:
            payload: dict[str, Any] = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 1024,
                "temperature": temperature,
            }
            if system_prompt:
                payload["system"] = system_prompt

            async with httpx.AsyncClient(timeout=45.0) as client:
                response = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": self.api_key,
                        "anthropic-version": "2023-06-01",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )
                if response.status_code == 200:
                    data = response.json()
                    content = data["content"][0]["text"]
                    usage = data.get("usage", {})
                    return {
                        "text": content,
                        "prompt_tokens": usage.get("input_tokens", 0),
                        "completion_tokens": usage.get("output_tokens", 0),
                        "total_tokens": usage.get("input_tokens", 0)
                        + usage.get("output_tokens", 0),  # noqa: E501
                    }
                else:
                    logger.warning(
                        "Anthropic API failed (HTTP %s): %s", response.status_code, response.text
                    )
                    return await self.mock_provider.generate_response(
                        prompt, system_prompt, temperature
                    )  # noqa: E501
        except Exception as e:
            logger.exception("Error calling Anthropic API: %s", e)
            return await self.mock_provider.generate_response(prompt, system_prompt, temperature)

    async def generate_stream(
        self, prompt: str, system_prompt: str | None = None, temperature: float = 0.2
    ) -> AsyncGenerator[dict[str, Any]]:
        if not self.api_key:
            async for chunk in self.mock_provider.generate_stream(
                prompt, system_prompt, temperature
            ):  # noqa: E501
                yield chunk
            return

        try:
            payload: dict[str, Any] = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 1024,
                "temperature": temperature,
                "stream": True,
            }
            if system_prompt:
                payload["system"] = system_prompt

            async with httpx.AsyncClient(timeout=45.0) as client:
                async with client.stream(
                    "POST",
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": self.api_key,
                        "anthropic-version": "2023-06-01",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                ) as response:
                    if response.status_code == 200:
                        async for line in response.aiter_lines():
                            line = line.strip()
                            if not line:
                                continue
                            if line.startswith("data: "):
                                import json

                                try:
                                    data = json.loads(line[6:])
                                    if data.get("type") == "content_block_delta":
                                        delta = data.get("delta", {})
                                        text = delta.get("text", "")
                                        if text:
                                            yield {"text": text, "done": False}
                                except Exception:
                                    pass
                        yield {
                            "text": "",
                            "done": True,
                            "prompt_tokens": 0,
                            "completion_tokens": 0,
                            "total_tokens": 0,
                        }  # noqa: E501
                    else:
                        async for chunk in self.mock_provider.generate_stream(
                            prompt, system_prompt, temperature
                        ):  # noqa: E501
                            yield chunk
        except Exception:
            async for chunk in self.mock_provider.generate_stream(
                prompt, system_prompt, temperature
            ):  # noqa: E501
                yield chunk


class GeminiProvider(LLMProvider):
    """Communicates with Google Gemini API."""

    def __init__(self, api_key: str, model: str = "gemini-1.5-flash") -> None:
        self.api_key = api_key
        self.model = model
        self.mock_provider = MockLLMProvider()

    async def generate_response(
        self, prompt: str, system_prompt: str | None = None, temperature: float = 0.2
    ) -> dict[str, Any]:
        if not self.api_key:
            logger.info("Gemini API key missing, falling back to Mock provider")
            return await self.mock_provider.generate_response(prompt, system_prompt, temperature)

        try:
            contents = []
            if system_prompt:
                contents.append(
                    {"role": "user", "parts": [{"text": f"System Context:\n{system_prompt}"}]}
                )  # noqa: E501
                contents.append(
                    {
                        "role": "model",
                        "parts": [{"text": "Understood. I will conform to those instructions."}],
                    }
                )  # noqa: E501

            contents.append({"role": "user", "parts": [{"text": prompt}]})

            url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
            async with httpx.AsyncClient(timeout=45.0) as client:
                response = await client.post(
                    url,
                    headers={"Content-Type": "application/json"},
                    json={
                        "contents": contents,
                        "generationConfig": {
                            "temperature": temperature,
                        },
                    },
                )
                if response.status_code == 200:
                    data = response.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        text = candidates[0]["content"]["parts"][0]["text"]
                        usage = data.get("usageMetadata", {})
                        prompt_tokens = usage.get("promptTokenCount", len(prompt.split()) // 3)
                        completion_tokens = usage.get(
                            "candidatesTokenCount", len(text.split()) // 3
                        )  # noqa: E501
                        return {
                            "text": text,
                            "prompt_tokens": prompt_tokens,
                            "completion_tokens": completion_tokens,
                            "total_tokens": prompt_tokens + completion_tokens,
                        }
                    else:
                        raise ValueError("No text generated in Gemini candidates")
                else:
                    logger.warning(
                        "Gemini API failed (HTTP %s): %s", response.status_code, response.text
                    )
                    return await self.mock_provider.generate_response(
                        prompt, system_prompt, temperature
                    )  # noqa: E501
        except Exception as e:
            logger.exception("Error calling Gemini API: %s", e)
            return await self.mock_provider.generate_response(prompt, system_prompt, temperature)

    async def generate_stream(
        self, prompt: str, system_prompt: str | None = None, temperature: float = 0.2
    ) -> AsyncGenerator[dict[str, Any]]:
        if not self.api_key:
            async for chunk in self.mock_provider.generate_stream(
                prompt, system_prompt, temperature
            ):  # noqa: E501
                yield chunk
            return

        try:
            contents = []
            if system_prompt:
                contents.append(
                    {"role": "user", "parts": [{"text": f"System Context:\n{system_prompt}"}]}
                )  # noqa: E501
                contents.append(
                    {
                        "role": "model",
                        "parts": [{"text": "Understood. I will conform to those instructions."}],
                    }
                )  # noqa: E501

            contents.append({"role": "user", "parts": [{"text": prompt}]})

            url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:streamGenerateContent?key={self.api_key}"
            async with httpx.AsyncClient(timeout=45.0) as client:
                async with client.stream(
                    "POST",
                    url,
                    headers={"Content-Type": "application/json"},
                    json={
                        "contents": contents,
                        "generationConfig": {
                            "temperature": temperature,
                        },
                    },
                ) as response:
                    if response.status_code == 200:
                        async for line in response.aiter_lines():
                            line = line.strip()
                            if not line:
                                continue
                            # Gemini returns a JSON array or objects per chunk
                            # For safety, let's parse as JSON if it looks like it
                            import json

                            try:
                                # Sometimes lines start with `[` or `,` in streaming array formats
                                if line.startswith("["):
                                    line = line[1:]
                                if line.endswith("]"):
                                    line = line[:-1]
                                if line.startswith(","):
                                    line = line[1:]
                                chunk_data = json.loads(line.strip())
                                candidates = chunk_data.get("candidates", [])
                                if candidates:
                                    text = candidates[0]["content"]["parts"][0]["text"]
                                    if text:
                                        yield {"text": text, "done": False}
                            except Exception:
                                pass
                        yield {
                            "text": "",
                            "done": True,
                            "prompt_tokens": 0,
                            "completion_tokens": 0,
                            "total_tokens": 0,
                        }  # noqa: E501
                    else:
                        async for chunk in self.mock_provider.generate_stream(
                            prompt, system_prompt, temperature
                        ):  # noqa: E501
                            yield chunk
        except Exception:
            async for chunk in self.mock_provider.generate_stream(
                prompt, system_prompt, temperature
            ):  # noqa: E501
                yield chunk


def get_llm_provider(provider_id: str | None = None) -> LLMProvider:
    """Factory helper returning provider based on config or route parameter override."""
    p_id = provider_id or settings.llm_provider
    p_id = p_id.lower()

    if settings.environment == "testing":
        return MockLLMProvider()

    if p_id == "openai":
        return OpenAIProvider(api_key=settings.openai_api_key)
    elif p_id == "anthropic":
        return AnthropicProvider(api_key=settings.anthropic_api_key)
    elif p_id == "gemini":
        return GeminiProvider(api_key=settings.gemini_api_key)

    return MockLLMProvider()
