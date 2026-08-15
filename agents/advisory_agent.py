"""
AdvisoryAgent - the "generative AI" reasoning core. Takes everything the
other agents have gathered (weather, soil, disease prediction, crop/growth
info) and synthesizes it into a farmer-readable advisory.

Two modes, controlled by LLM_PROVIDER in .env:
  - "anthropic" / "openai" / "gemini": calls the real LLM to freely
    generate the advisory text.
  - "template": zero-cost, zero-dependency fallback. Builds the advisory
    from a rule-based natural-language template engine instead of calling
    any external API. Still fully dynamic - every sentence is assembled
    from the actual field data, just not free-form generated.
"""

import json
from typing import Any, Dict, List

from agents.base_agent import BaseAgent
from config import LLM_PROVIDER


SYSTEM_PROMPT = """You are an agricultural advisory assistant embedded in a \
precision-farming platform. You are given structured sensor, weather, and \
disease-model data for a specific field. Produce a concise, practical \
advisory for the farmer.

Rules:
- Base every recommendation on the data provided. Do not invent readings.
- If data is missing for a section, say so briefly instead of guessing.
- Prioritize actionable guidance: irrigation, fertilization, pest/disease \
response, and timing.
- Keep the tone plain and direct, suitable for a working farmer, not an \
academic paper.
- Structure your answer with short headers: Summary, Irrigation, \
Nutrition, Disease/Pest, Timing Notes.
"""


class AdvisoryAgent(BaseAgent):
    name = "advisory_agent"

    def __init__(self, llm_client=None):
        super().__init__()
        self.use_template = LLM_PROVIDER == "template"
        if not self.use_template:
            from utils.llm_client import LLMClient
            self.llm = llm_client or LLMClient()

    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        payload = {
            "crop": context.get("crop"),
            "growth_stage": context.get("growth_stage"),
            "weather_summary": context.get("weather_summary"),
            "weather_forecast": context.get("weather_forecast"),
            "soil_assessment": context.get("soil_assessment"),
            "disease_prediction": context.get("disease_prediction"),
        }

        if self.use_template:
            advisory_text = self._generate_template_advisory(payload)
        else:
            prompt = (
                "Field data (JSON):\n"
                f"{json.dumps(payload, indent=2, default=str)}\n\n"
                "Write the advisory now."
            )
            advisory_text = self.llm.generate(SYSTEM_PROMPT, prompt, max_tokens=800)

        return {"crop_advisory": advisory_text}

    def _generate_template_advisory(self, data: Dict[str, Any]) -> str:
        crop = data.get("crop") or "your crop"
        stage = data.get("growth_stage") or "an unspecified growth stage"
        weather = data.get("weather_summary") or {}
        soil = data.get("soil_assessment") or {}
        disease = data.get("disease_prediction") or {}

        lines: List[str] = []

        lines.append("SUMMARY")
        status_bits = []
        if soil.get("status") == "needs_attention":
            status_bits.append("soil conditions need attention")
        elif soil.get("status") == "healthy":
            status_bits.append("soil conditions look healthy")
        if disease.get("alert"):
            status_bits.append(
                f"a possible '{disease.get('predicted_class')}' outbreak was flagged"
            )
        if not status_bits:
            status_bits.append("no major issues were detected in the available data")
        lines.append(
            f"For {crop} at {stage}, {', and '.join(status_bits)}. "
            "See sections below for specifics."
        )
        lines.append("")

        lines.append("IRRIGATION")
        rain_mm = weather.get("5day_total_rain_mm")
        rain_expected = weather.get("rain_expected")
        moisture_issue = next(
            (i for i in soil.get("issues", []) if "moisture" in i.lower()), None
        )
        if moisture_issue:
            lines.append(f"- {moisture_issue}.")
            if rain_expected:
                lines.append(
                    f"- {rain_mm}mm of rain is forecast over the next 5 days - "
                    "consider holding off irrigation until after it falls, then recheck."
                )
            else:
                lines.append(
                    "- Little to no rain is forecast in the next 5 days, so plan to "
                    "irrigate soon rather than waiting on rainfall."
                )
        else:
            lines.append(
                "- Soil moisture is within a normal range based on the latest reading; "
                "no irrigation action needed right now."
            )
        lines.append("")

        lines.append("NUTRITION")
        ph_issue = next((i for i in soil.get("issues", []) if "pH" in i), None)
        nutrients = soil.get("nutrients", {})
        if ph_issue:
            lines.append(f"- {ph_issue}.")
        if nutrients:
            n = nutrients.get("nitrogen_ppm")
            p = nutrients.get("phosphorus_ppm")
            k = nutrients.get("potassium_ppm")
            lines.append(
                f"- Current NPK readings: nitrogen {n} ppm, phosphorus {p} ppm, "
                f"potassium {k} ppm. Compare against {crop}'s recommended range for "
                f"{stage} and top up any nutrient trending low."
            )
        if not ph_issue and not nutrients:
            lines.append("- No soil nutrient data was provided for this check.")
        lines.append("")

        lines.append("DISEASE/PEST")
        if disease.get("predicted_class"):
            conf_pct = f"{disease.get('confidence', 0):.0%}"
            if disease.get("alert"):
                lines.append(
                    f"- The disease model flagged '{disease['predicted_class']}' "
                    f"with {conf_pct} confidence. Inspect the field in person before "
                    "applying any treatment, and isolate affected plants if confirmed."
                )
            else:
                lines.append(
                    f"- The disease model's top prediction was '{disease['predicted_class']}' "
                    f"({conf_pct} confidence), below the alert threshold - "
                    "no action needed, but keep monitoring."
                )
        else:
            lines.append("- No leaf image was submitted for this check.")
        lines.append("")

        lines.append("TIMING NOTES")
        avg_temp = weather.get("avg_temp_c")
        if avg_temp is not None:
            lines.append(
                f"- Average forecast temperature over the next 5 days is {avg_temp} C. "
                "Schedule field work (spraying, irrigation) during cooler parts of the "
                "day if temperatures run high."
            )
        else:
            lines.append("- No weather forecast was available for timing guidance.")

        lines.append("")
        lines.append(
            "[Generated by the rule-based advisory engine - "
            "no external LLM was called for this report.]"
        )

        return "\n".join(lines)