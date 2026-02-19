"""Tests for CAD layer definitions."""
from app.domain.layers import LAYERS, get_layer


def test_standard_layers_defined():
    assert "A-WALL" in LAYERS
    assert "A-DOOR" in LAYERS
    assert "A-WIND" in LAYERS
    assert "A-DIMS" in LAYERS
    assert "A-ROOM-NAME" in LAYERS


def test_get_layer():
    layer = get_layer("A-WALL")
    assert layer.name == "A-WALL"
    assert layer.lineweight == 0.50


def test_get_unknown_layer():
    layer = get_layer("UNKNOWN")
    assert layer.name == "UNKNOWN"
    assert layer.color == 7  # white default
