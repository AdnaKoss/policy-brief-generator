from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Type, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class LLMProvider(ABC):
    """Common interface every LLM backend implements: send a system prompt
    and user content, get back an instance of the given Pydantic schema."""

    @abstractmethod
    def generate_structured(self, system_prompt: str, user_content: str, schema: Type[T]) -> T:
        ...
