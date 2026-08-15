"""
DecisionAgent - the "autonomous farm decision making" layer.

Deliberately rule-based and deterministic (not LLM-generated) for the
actual DECISIONS, because irrigation/pesticide actions should be
auditable and reproducible. The LLM-written `crop_advisory` text explains
the reasoning in natural language; this agent turns the same underlying
data into a prioritized, machine-actionable task list.
"""

from typing import Any, Dict, List
from agents.base_agent import BaseAgent
from config import SOIL_MOISTURE_LOW, SOIL_MOISTURE_HIGH, DISEASE_CONFIDENCE_ALERT


class DecisionAgent(BaseAgent):
    name = "decision_agent"

    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        actions: List[Dict[str, Any]] = []

        soil = context.get("soil_data") or {}
        soil_assessment = context.get("soil_assessment") or {}
        weather_summary = context.get("weather_summary") or {}
        disease = context.get("disease_prediction") or {}

        # --- Irrigation decision -------------------------------------
        moisture = soil.get("moisture_pct")
        rain_expected = weather_summary.get("rain_expected")

        if moisture is not None:
            if moisture < SOIL_MOISTURE_LOW and not rain_expected:
                actions.append({
                    "action": "irrigate",
                    "priority": "high",
                    "reason": (
                        f"Soil moisture at {moisture}% is below the "
                        f"{SOIL_MOISTURE_LOW}% threshold and no significant "
                        "rain is forecast in the next 5 days."
                    ),
                })
            elif moisture < SOIL_MOISTURE_LOW and rain_expected:
                actions.append({
                    "action": "monitor_soil",
                    "priority": "medium",
                    "reason": (
                        f"Soil moisture is low ({moisture}%) but rain is "
                        "forecast - hold irrigation and recheck after rainfall."
                    ),
                })
            elif moisture > SOIL_MOISTURE_HIGH:
                actions.append({
                    "action": "pause_irrigation",
                    "priority": "high",
                    "reason": f"Soil moisture at {moisture}% risks waterlogging.",
                })

        # --- Nutrient decision -----------------------------------------
        for issue in soil_assessment.get("issues", []):
            if "pH" in issue:
                actions.append({
                    "action": "soil_amendment",
                    "priority": "medium",
                    "reason": issue,
                })

        # --- Disease/pest response --------------------------------------
        if disease.get("alert"):
            actions.append({
                "action": "inspect_and_treat_disease",
                "priority": "high",
                "reason": (
                    f"Model predicts '{disease.get('predicted_class')}' with "
                    f"{disease.get('confidence'):.0%} confidence "
                    f"(threshold {DISEASE_CONFIDENCE_ALERT:.0%}). "
                    "Manual field inspection recommended before treatment."
                ),
            })

        if not actions:
            actions.append({
                "action": "no_action_needed",
                "priority": "low",
                "reason": "All monitored parameters are within normal ranges.",
            })

        # Sort so high-priority items surface first
        priority_rank = {"high": 0, "medium": 1, "low": 2}
        actions.sort(key=lambda a: priority_rank.get(a["priority"], 3))

        return {
            "farm_decisions": actions,
            "decision_summary": (
                f"{len(actions)} action(s) generated - "
                f"{sum(1 for a in actions if a['priority'] == 'high')} high priority."
            ),
        }
