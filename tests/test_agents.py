"""
Basic sanity tests. These mock out network calls (weather API), the LLM
client, and the disease model, so they run fast and offline - useful for
CI. Run with:

    python -m pytest tests/ -v
"""

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agents.soil_agent import SoilAgent
from agents.decision_agent import DecisionAgent


def test_soil_agent_flags_low_moisture():
    agent = SoilAgent()
    context = {"soil_data": {"moisture_pct": 10.0, "ph": 6.5}}
    result = agent.run(context)

    assert result["soil_assessment"]["status"] == "needs_attention"
    assert any("moisture" in issue.lower() for issue in result["soil_assessment"]["issues"])


def test_soil_agent_healthy_case():
    agent = SoilAgent()
    context = {"soil_data": {"moisture_pct": 50.0, "ph": 6.8}}
    result = agent.run(context)

    assert result["soil_assessment"]["status"] == "healthy"
    assert result["soil_assessment"]["issues"] == []


def test_soil_agent_missing_data_reports_error_not_crash():
    agent = SoilAgent()
    result = agent.safe_run({})
    assert "soil_error" in result


def test_decision_agent_irrigation_high_priority_when_dry_and_no_rain():
    agent = DecisionAgent()
    context = {
        "soil_data": {"moisture_pct": 15.0},
        "weather_summary": {"rain_expected": False},
        "soil_assessment": {"issues": []},
        "disease_prediction": {},
    }
    result = agent.run(context)

    actions = result["farm_decisions"]
    assert actions[0]["action"] == "irrigate"
    assert actions[0]["priority"] == "high"


def test_decision_agent_disease_alert_triggers_action():
    agent = DecisionAgent()
    context = {
        "soil_data": {"moisture_pct": 50.0},
        "weather_summary": {"rain_expected": False},
        "soil_assessment": {"issues": []},
        "disease_prediction": {
            "alert": True,
            "predicted_class": "leaf_blight",
            "confidence": 0.87,
        },
    }
    result = agent.run(context)

    actions = [a["action"] for a in result["farm_decisions"]]
    assert "inspect_and_treat_disease" in actions


def test_decision_agent_no_issues_returns_no_action():
    agent = DecisionAgent()
    context = {
        "soil_data": {"moisture_pct": 50.0},
        "weather_summary": {"rain_expected": False},
        "soil_assessment": {"issues": []},
        "disease_prediction": {},
    }
    result = agent.run(context)
    assert result["farm_decisions"][0]["action"] == "no_action_needed"


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))
