# PiaxisCD Extension Guide

## Adding a New CAD/BIM Adapter

PiaxisCD uses an adapter pattern to support different CAD/BIM backends. The built-in `NativeAdapter` uses Python libraries (ezdxf, ifcopenshell, reportlab). You can add new adapters for Revit, AutoCAD, or any other platform.

### Adapter Interface

All adapters implement `CadBimAdapter`:

```python
from app.adapters.base import CadBimAdapter

class MyAdapter(CadBimAdapter):
    def create_project(self, project: Project) -> str:
        """Create project in external system, return ID."""
        ...

    def push_floorplan(self, project: Project) -> None:
        """Push the floor plan model to the external system."""
        ...

    def generate_views(self, project: Project, view_types: list[ViewType]) -> list[Any]:
        """Generate views (plans, elevations, sections)."""
        ...

    def export(self, project: Project, formats: list[str]) -> ExportPackage:
        """Export to specified formats, return package with files."""
        ...
```

### Revit / APS Integration

To integrate with Autodesk Revit via the APS (formerly Forge) platform:

1. **Create `app/adapters/revit_adapter.py`**
2. **Authentication**: Use APS OAuth2 with `client_credentials` grant
3. **Design Automation**: Use the Design Automation API to run Revit operations
4. **Model Push**: Convert domain `Wall`, `Door`, `Window` objects to Revit family parameters
5. **View Generation**: Use Revit's built-in view creation (floor plans, elevations, sections)
6. **Export**: Use Revit's export to DWG, IFC, PDF

```python
class RevitAdapter(CadBimAdapter):
    def __init__(self, client_id: str, client_secret: str):
        self.aps_client = APSClient(client_id, client_secret)

    def create_project(self, project: Project) -> str:
        # Create BIM360/ACC project or use Design Automation
        ...

    def export(self, project: Project, formats: list[str]) -> ExportPackage:
        # Submit Design Automation workitem
        # Poll for completion
        # Download results
        ...
```

### AutoCAD Integration

For AutoCAD integration via Design Automation:

1. **Create `app/adapters/autocad_adapter.py`**
2. Use AutoCAD's Design Automation API
3. Push DXF/DWG templates with room layouts
4. Use AutoCAD's dimensioning and annotation tools

### Registration

Register your adapter in `app/config.py`:

```python
ADAPTERS = {
    "native": NativeAdapter,
    "revit": RevitAdapter,
    "autocad": AutoCADAdapter,
}
```

## Adding New Export Formats

To add a new export format (e.g., SVG, DWG):

1. Add the format to `ExportFormat` enum in `app/domain/export.py`
2. Add an export method in `ExportAgent` (e.g., `_export_svg`)
3. Update the `run()` method to call your exporter when the format is requested

## Adding New View Types

1. Add view dataclass in `app/domain/views.py`
2. Update `ViewGenerator` to create the new view
3. Update `SheetComposer` to layout the view on sheets
4. Update `ExportAgent` to render the view in each format

## Adding New Schedule Types

1. Add schedule entry dataclass in `app/domain/schedules.py`
2. Add builder method in `ExportAgent._build_*_schedule()`
3. Render schedule in PDF export
