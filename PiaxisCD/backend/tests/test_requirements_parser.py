"""Tests for RequirementsInterpreterAgent."""
from app.agents.requirements_interpreter import RequirementsInterpreterAgent
from app.domain.project import RoomFunction


def test_parse_json_requirements():
    agent = RequirementsInterpreterAgent()
    data = {
        "project_name": "Test Project",
        "rooms": [
            {"name": "Living Room", "function": "living", "area": 25},
            {"name": "Kitchen", "function": "kitchen", "area": 15},
        ],
    }
    result = agent.run(data)
    assert result.project_name == "Test Project"
    assert len(result.rooms) == 2
    assert result.rooms[0].function == RoomFunction.LIVING
    assert result.rooms[0].area == 25


def test_parse_text_requirements():
    agent = RequirementsInterpreterAgent()
    text = """# My House
Living Room: 25 sqm
Kitchen: 15 sqm
2x Bedrooms: 16 sqm
Bathroom: 6 sqm
"""
    result = agent.run(text)
    assert result.project_name == "My House"
    assert len(result.rooms) == 4
    # 2x Bedrooms should create one entry with count=2
    bedroom = next(r for r in result.rooms if "Bedroom" in r.name)
    assert bedroom.count == 2
    assert bedroom.area == 16


def test_parse_json_string():
    agent = RequirementsInterpreterAgent()
    import json
    data = json.dumps({"rooms": [{"name": "Room A", "area": 20}]})
    result = agent.run(data)
    assert len(result.rooms) == 1
    assert result.rooms[0].area == 20


def test_expanded_rooms():
    agent = RequirementsInterpreterAgent()
    data = {"rooms": [{"name": "Bedroom", "function": "bedroom", "area": 15, "count": 3}]}
    result = agent.run(data)
    expanded = result.expanded_rooms
    assert len(expanded) == 3
    assert all("Bedroom" in r.name for r in expanded)
