"""
Async LLM client with factory pattern supporting OpenAI and Anthropic.
Integrates instructor for structured outputs.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Type, TypeVar, Union

import instructor
from openai import AsyncOpenAI
from anthropic import AsyncAnthropic
from django.conf import settings
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from .exceptions import LLMRateLimitError

logger = logging.getLogger(__name__)

T = TypeVar("T")


class BaseLLMClient(ABC):
    """Abstract base for async LLM clients."""

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1024,
        temperature: float = 0.7,
    ) -> str:
        """Generate text from prompt."""
        pass

    @abstractmethod
    async def generate_structured(
        self,
        prompt: str,
        response_model: Type[T],
        system_prompt: Optional[str] = None,
        max_tokens: int = 1024,
        temperature: float = 0.0,
    ) -> T:
        """Generate structured output using instructor."""
        pass


class OpenAIClient(BaseLLMClient):
    """OpenAI client with instructor integration."""

    def __init__(self, model: str = "gpt-4o", api_key: Optional[str] = None):
        self.model = model
        api_key = api_key or settings.OPENAI_API_KEY
        self.client = instructor.from_openai(
            AsyncOpenAI(api_key=api_key, base_url=settings.OLLAMA_BASE_URL or None)
        )

    @retry(
        retry=retry_if_exception_type(LLMRateLimitError),
        wait=wait_exponential(multiplier=1, min=4, max=60),
        stop=stop_after_attempt(3),
        reraise=True,
    )
    async def generate(self, prompt: str, system_prompt: Optional[str] = None, max_tokens: int = 1024, temperature: float = 0.7) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            return response.choices[0].message.content
        except Exception as e:
            if "rate_limit" in str(e).lower():
                raise LLMRateLimitError(str(e))
            raise

    async def generate_structured(
        self,
        prompt: str,
        response_model: Type[T],
        system_prompt: Optional[str] = None,
        max_tokens: int = 1024,
        temperature: float = 0.0,
    ) -> T:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        try:
            return await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                response_model=response_model,
                max_tokens=max_tokens,
                temperature=temperature,
            )
        except Exception as e:
            if "rate_limit" in str(e).lower():
                raise LLMRateLimitError(str(e))
            raise


class AnthropicClient(BaseLLMClient):
    """Anthropic Claude client with instructor integration."""

    def __init__(self, model: str = "claude-3-5-sonnet-20241022", api_key: Optional[str] = None):
        self.model = model
        api_key = api_key or settings.ANTHROPIC_API_KEY
        self.client = instructor.from_anthropic(
            AsyncAnthropic(api_key=api_key)
        )

    @retry(
        retry=retry_if_exception_type(LLMRateLimitError),
        wait=wait_exponential(multiplier=1, min=4, max=60),
        stop=stop_after_attempt(3),
        reraise=True,
    )
    async def generate(self, prompt: str, system_prompt: Optional[str] = None, max_tokens: int = 1024, temperature: float = 0.7) -> str:
        try:
            response = await self.client.messages.create(
                model=self.model,
                system=system_prompt,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature,
            )
            return response.content[0].text
        except Exception as e:
            if "rate_limit" in str(e).lower():
                raise LLMRateLimitError(str(e))
            raise

    async def generate_structured(
        self,
        prompt: str,
        response_model: Type[T],
        system_prompt: Optional[str] = None,
        max_tokens: int = 1024,
        temperature: float = 0.0,
    ) -> T:
        try:
            return await self.client.messages.create(
                model=self.model,
                system=system_prompt,
                messages=[{"role": "user", "content": prompt}],
                response_model=response_model,
                max_tokens=max_tokens,
                temperature=temperature,
            )
        except Exception as e:
            if "rate_limit" in str(e).lower():
                raise LLMRateLimitError(str(e))
            raise


class LLMClient:
    """
    Factory for async LLM clients.
    Usage:
        client = LLMClient.get_client(provider="openai")
        text = await client.generate(prompt)
    """

    _clients: Dict[str, BaseLLMClient] = {}

    @classmethod
    def get_client(cls, provider: str = "openai", **kwargs) -> BaseLLMClient:
        """Return a cached or new client instance."""
        key = f"{provider}:{kwargs}"
        if key not in cls._clients:
            if provider == "openai":
                cls._clients[key] = OpenAIClient(**kwargs)
            elif provider == "anthropic":
                cls._clients[key] = AnthropicClient(**kwargs)
            else:
                raise ValueError(f"Unsupported provider: {provider}")
        return cls._clients[key]