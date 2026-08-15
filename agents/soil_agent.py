"""
SoilAgent - reads soil sensor data (moisture, pH, N-P-K levels) either from
a JSON file (IoT export) or from values already present in the context,
and produces a health assessment other agents can use.

Expected soil_data schema:
{
    "moisture_pct": 32.5,
    "ph": 6.4,
    "nitrogen_ppm": 40,
    "phosphorus_ppm": 25,
    "potassium_ppm": 150
}
"""

import json
from pathlib import Path
from typing import Any, Dict
from agents.base_agent import BaseAgent
from config import SOIL_MOISTURE_LOW, SOIL_MOISTURE_HIGH


IDEAL_PH_RANGE = (6.0, 7.5)


class SoilAgent(BaseAgent):
    name = "soil_agent"

    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        soil_data = context.get("soil_data")

        soil_file = context.get("soil_file")
        if soil_data is None and soil_file:
            path = Path(soil_file)
            if not path.exists():
                return {"soil_error": f"soil_file not found: {soil_file}"}
            soil_data = json.loads(path.read_text())

        if soil_data is None:
            return {"soil_error": "No soil_data or soil_file provided in context"}

        moisture = soil_data.get("moisture_pct")
        ph = soil_data.get("ph")

        issues = []
        if moisture is not None:
            if moisture < SOIL_MOISTURE_LOW:
                issues.append(f"Soil moisture low ({moisture}%) - irrigation likely needed")
            elif moisture > SOIL_MOISTURE_HIGH:
                issues.append(f"Soil moisture high ({moisture}%) - risk of waterlogging")

        if ph is not None:
            if ph < IDEAL_PH_RANGE[0]:
                issues.append(f"Soil pH acidic ({ph}) - consider liming")
            elif ph > IDEAL_PH_RANGE[1]:
                issues.append(f"Soil pH alkaline ({ph}) - consider sulfur amendment")

        nutrients = {
            k: soil_data.get(k)
            for k in ("nitrogen_ppm", "phosphorus_ppm", "potassium_ppm")
            if k in soil_data
        }

        return {
            "soil_data": soil_data,
            "soil_assessment": {
                "status": "healthy" if not issues else "needs_attention",
                "issues": issues,
                "nutrients": nutrients,
            },
        }
