"""
Orchestrator - the coordination layer of the multi-agent system.

Design: a shared mutable `context` dict flows through an ordered list of
agents. Each agent reads whatever keys it needs from context and returns
new keys, which get merged back in before the next agent runs. This is a
simple, transparent alternative to a message-passing bus - easy to trace,
easy to unit test, and easy to extend (just append a new agent to the
pipeline).

Order matters: Weather and Soil run first (independent, no dependencies),
then Disease (independent), then Advisory (needs weather/soil/disease),
then Decision (needs the same raw data - deliberately NOT the advisory
text, so the auditable decision logic never depends on LLM output).
"""

from typing import Any, Dict, List
from agents.base_agent import BaseAgent
from agents.weather_agent import WeatherAgent
from agents.soil_agent import SoilAgent
from agents.disease_agent import DiseaseAgent
from agents.advisory_agent import AdvisoryAgent
from agents.decision_agent import DecisionAgent
from utils.logger import get_logger

logger = get_logger("orchestrator")


class Orchestrator:
    def __init__(self, agents: List[BaseAgent] = None):
        self.agents = agents or [
            WeatherAgent(),
            SoilAgent(),
            DiseaseAgent(),
            AdvisoryAgent(),
            DecisionAgent(),
        ]

    def run(self, initial_context: Dict[str, Any]) -> Dict[str, Any]:
        context = dict(initial_context)
        logger.info(f"Pipeline starting with {len(self.agents)} agents.")

        for agent in self.agents:
            result = agent.safe_run(context)
            context.update(result)

        logger.info("Pipeline complete.")
        return context
