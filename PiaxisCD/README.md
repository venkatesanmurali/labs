# PiaxisCD - Construction Documents Generator

Production-quality POC that generates Construction Document (CD) sets from room/building requirements. Produces multi-view sheets with DXF, IFC, PDF, and PNG exports using deterministic agent modules.

## Quick Start

```bash
# Install dependencies
make setup

# Create database (requires MySQL 8.0)
make db

# Start backend (port 8000)
make backend

# Start frontend (port 5173)
make frontend

# Or run a demo without database
make demo
```

## Architecture

```
PiaxisCD/
├── backend/          # Python FastAPI + SQLAlchemy
│   ├── app/
│   │   ├── domain/   # Pure AEC domain models
│   │   ├── agents/   # Deterministic pipeline agents
│   │   ├── adapters/ # CAD/BIM backend adapters
│   │   ├── models/   # SQLAlchemy DB models
│   │   ├── schemas/  # Pydantic API schemas
│   │   ├── services/ # Business logic orchestration
│   │   └── routes/   # FastAPI routers
├── frontend/         # React + TypeScript + Vite + Tailwind
├── shared/           # Shared schemas (JSON Schema)
└── samples/          # Sample requirement files
```

## Agent Pipeline

The generation pipeline consists of deterministic agents (no LLM calls):

1. **RequirementsInterpreterAgent** - Parses text or JSON into structured program requirements
2. **SchematicPlanGenerator** - Rectangle packing algorithm: sizes rooms, packs into grid, creates walls, places doors and windows
3. **CDAnnotationEngine** - Adds dimensions, room tags, elevation/section markers
4. **ViewGenerator** - Derives floor plan, RCP, elevations, and sections
5. **SheetComposer** - Composes sheets with viewports, title blocks, scale bars
6. **ExportAgent** - Generates DXF (ezdxf), IFC (ifcopenshell), PDF (reportlab), PNG (Pillow)

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | /api/projects | Create project |
| GET | /api/projects | List projects |
| GET | /api/projects/:id | Get project |
| POST | /api/projects/:id/inputs/requirements | Submit JSON requirements |
| POST | /api/projects/:id/inputs/requirements-text | Submit text requirements |
| POST | /api/projects/:id/generate | Generate CD set |
| GET | /api/projects/:id/revisions/:rev/artifacts | List artifacts |
| GET | /api/projects/:id/revisions/:rev/download | Download ZIP package |
| POST | /api/demo | Run demo generation |

## Demo Mode

Demo mode generates a complete CD set for a sample 6-room residence without requiring a database:

```bash
make demo
# Or via API:
curl -X POST http://localhost:8000/api/demo
```

## Export Formats

- **DXF** - Layered CAD drawing (AIA layer standards), dimensions, annotations
- **IFC** - BIM model with IfcBuilding, IfcSpace, IfcWall, IfcDoor, IfcWindow
- **PDF** - Sheet set with title blocks, scaled views, schedules
- **PNG** - Raster rendering of each sheet

## Extending

See [EXTENSION_GUIDE.md](EXTENSION_GUIDE.md) for adding Revit, AutoCAD, or APS adapters.

## Tech Stack

- **Backend**: Python 3.11, FastAPI, Pydantic v2, SQLAlchemy, MySQL 8.0
- **Frontend**: React 18, TypeScript, Vite, Tailwind CSS
- **Exports**: ezdxf, ifcopenshell, reportlab, Pillow
