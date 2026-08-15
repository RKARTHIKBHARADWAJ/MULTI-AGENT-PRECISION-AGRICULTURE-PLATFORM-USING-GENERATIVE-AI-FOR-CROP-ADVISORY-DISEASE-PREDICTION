"""
BaseAgent defines the contract every agent in the platform follows.
This keeps the Orchestrator dumb and generic: it just calls `.run(context)`
on each agent in turn and merges the returned dict back into a shared context.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict
from utils.logger import get_logger


class BaseAgent(ABC):
    name: str = "base_agent"

    def __init__(self):
        self.logger = get_logger(self.name)

    @abstractmethod
    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Take the shared context dict (built up by prior agents),
        do this agent's job, and return a dict of NEW keys to merge in.
        Must never raise - agents should catch their own errors and
        report {"<name>_error": str(e)} so one failing agent doesn't
        crash the whole pipeline.
        """
        raise NotImplementedError

    def safe_run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Wrapper the orchestrator actually calls - guarantees no crash."""
        self.logger.info(f"Starting {self.name}...")
        try:
            result = self.run(context)
            self.logger.info(f"{self.name} completed successfully.")
            return result
        except Exception as exc:
            self.logger.error(f"{self.name} failed: {exc}")
            return {f"{self.name}_error": str(exc)}
