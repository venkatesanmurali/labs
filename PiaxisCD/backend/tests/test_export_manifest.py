"""Tests for export manifest and package."""
from pathlib import Path
from app.domain.export import ExportFile, ExportFormat, ExportManifest, ExportPackage


def test_manifest_to_dict():
    manifest = ExportManifest(
        project_name="Test",
        revision=1,
        formats=["dxf", "pdf"],
        total_sheets=3,
    )
    d = manifest.to_dict()
    assert d["project_name"] == "Test"
    assert d["revision"] == 1
    assert d["total_sheets"] == 3
    assert "dxf" in d["formats"]


def test_export_package_add_file():
    package = ExportPackage()
    ef = ExportFile(
        filename="test.dxf",
        format=ExportFormat.DXF,
        path=Path("/tmp/test.dxf"),
        size_bytes=1024,
        sheet_number="A1.01",
    )
    package.add_file(ef)
    assert package.file_count == 1
    assert package.manifest.files[0].filename == "test.dxf"


def test_manifest_files_serialization():
    manifest = ExportManifest(project_name="Test")
    manifest.files.append(ExportFile(
        filename="sheet.pdf",
        format=ExportFormat.PDF,
        size_bytes=2048,
    ))
    d = manifest.to_dict()
    assert len(d["files"]) == 1
    assert d["files"][0]["format"] == "pdf"
