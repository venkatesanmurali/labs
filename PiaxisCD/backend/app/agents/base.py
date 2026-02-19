"""Base agent interface for deterministic pipeline agents."""
from __future__ import annotations

import logging
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgentContext:
    seed: int = 42
    log_level: str = "INFO"
    config: dict[str, Any] = field(default_factory=dict)

    @property
    def rng(self) -> random.Random:
        return random.Random(self.seed)


class BaseAgent(ABC):
    def __init__(self, context: AgentContext | None = None):
        self.context = context or AgentContext()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(self.context.log_level)
        self.rng = self.context.rng

    @abstractmethod
    def run(self, *args, **kwargs) -> Any:
        ...

    def log(self, message: str):
        self.logger.info(f"[{self.__class__.__name__}] {message}")
