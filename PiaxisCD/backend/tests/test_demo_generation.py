"""Tests for demo generation service (end-to-end without DB)."""
import json
from pathlib import Path

from app.services.generation_service import DemoService


def test_demo_generation(tmp_path: Path):
    result = DemoService.generate_demo(output_dir=tmp_path)
    assert result["status"] == "completed"
    assert result["rooms"] == 6
    assert result["sheets"] >= 3
    assert len(result["files"]) > 0

    # Check files exist
    for filename in result["files"]:
        filepath = tmp_path / filename
        assert filepath.exists(), f"Missing: {filename}"

    # Check manifest
    manifest_path = tmp_path / "manifest.json"
    assert manifest_path.exists()
    manifest = json.loads(manifest_path.read_text())
    assert manifest["project_name"] == "Demo Residence"
    assert len(manifest["files"]) > 0


def test_demo_deterministic(tmp_path: Path):
    r1 = DemoService.generate_demo(output_dir=tmp_path / "r1", seed=42)
    r2 = DemoService.generate_demo(output_dir=tmp_path / "r2", seed=42)
    assert r1["rooms"] == r2["rooms"]
    assert r1["walls"] == r2["walls"]
    assert r1["doors"] == r2["doors"]
    assert r1["sheets"] == r2["sheets"]
