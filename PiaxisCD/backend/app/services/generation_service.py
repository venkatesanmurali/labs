"""Generation service - orchestrates the agent pipeline."""
from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.annotation_engine import CDAnnotationEngine
from app.agents.base import AgentContext
from app.agents.export_agent import ExportAgent
from app.agents.requirements_interpreter import RequirementsInterpreterAgent
from app.agents.schematic_plan import SchematicPlanGenerator
from app.agents.sheet_composer import SheetComposer
from app.agents.view_generator import ViewGenerator
from app.config import settings
from app.domain.sheets import PaperSize
from app.domain.views import ViewScale
from app.repositories.revision_repo import RevisionRepository
from app.schemas.generation import GenerationConfig

logger = logging.getLogger(__name__)


class GenerationService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = RevisionRepository(db)

    async def generate(
        self,
        project_id: str,
        requirements_data: dict | str,
        config: GenerationConfig,
    ) -> dict:
        """Run the full generation pipeline."""
        context = AgentContext(seed=config.seed)

        # 1. Create revision
        revision = await self.repo.create(
            project_id=project_id,
            status="running",
            requirements_json=json.dumps(requirements_data) if isinstance(requirements_data, dict) else requirements_data,
            config_json=config.model_dump_json(),
        )

        try:
            # 2. Parse requirements
            interpreter = RequirementsInterpreterAgent(context)
            requirements = interpreter.run(requirements_data)

            # 3. Generate schematic plan
            planner = SchematicPlanGenerator(context)
            plan_result = planner.run(requirements)
            project = plan_result.project

            level = project.building.levels[0]

            # 4. Generate annotations
            annotator = CDAnnotationEngine(context)
            annotations = annotator.run(level)

            # 5. Generate views
            scale_parts = config.scale.split(":")
            scale = ViewScale(int(scale_parts[0]), int(scale_parts[1]))
            view_gen = ViewGenerator(context)
            view_set = view_gen.run(level, scale)

            # 6. Compose sheets
            paper_size = PaperSize[config.paper_size]
            composer = SheetComposer(context)
            composed = composer.run(project, view_set, annotations, paper_size, scale)

            # 7. Export
            output_dir = settings.data_dir / project_id / revision.id
            output_dir.mkdir(parents=True, exist_ok=True)

            exporter = ExportAgent(context)
            package = exporter.run(
                project, level, annotations, composed,
                output_dir, config.formats,
            )

            # 8. Store artifacts in DB
            for ef in package.manifest.files:
                await self.repo.add_artifact(
                    revision_id=revision.id,
                    artifact_type=ef.format.value,
                    filename=ef.filename,
                    file_path=str(ef.path),
                    file_size=ef.size_bytes,
                    sheet_number=ef.sheet_number,
                    description=ef.description,
                )

            # Store zip
            if package.zip_path:
                await self.repo.add_artifact(
                    revision_id=revision.id,
                    artifact_type="zip",
                    filename=package.zip_path.name,
                    file_path=str(package.zip_path),
                    file_size=package.zip_path.stat().st_size,
                    description="Complete CD package",
                )

            # 9. Store QC issues
            for issue_msg in plan_result.qc_issues:
                severity = "warning"
                if issue_msg.startswith("ERROR"):
                    severity = "error"
                elif issue_msg.startswith("INFO"):
                    severity = "info"
                await self.repo.add_qc_issue(
                    revision_id=revision.id,
                    severity=severity,
                    category="generation",
                    message=issue_msg,
                )

            # Update revision status
            revision.status = "completed"
            revision.completed_at = datetime.now()
            await self.db.commit()

            artifacts = await self.repo.list_artifacts(revision.id)
            qc_issues = await self.repo.list_qc_issues(revision.id)

            return {
                "revision_id": revision.id,
                "status": "completed",
                "artifacts_count": len(artifacts),
                "qc_issues_count": len(qc_issues),
                "output_dir": str(output_dir),
            }

        except Exception as e:
            logger.exception("Generation failed")
            revision.status = "failed"
            await self.db.commit()
            raise


class DemoService:
    """Provides demo generation without database."""

    @staticmethod
    def generate_demo(output_dir: Path | None = None, seed: int = 42) -> dict:
        """Run a demo generation and return results."""
        context = AgentContext(seed=seed)

        if output_dir is None:
            output_dir = settings.data_dir / "demo"
        output_dir.mkdir(parents=True, exist_ok=True)

        # Demo requirements
        demo_requirements = {
            "project_name": "Demo Residence",
            "project_number": "DEMO-001",
            "client": "Demo Client",
            "rooms": [
                {"name": "Living Room", "function": "living", "area": 25},
                {"name": "Kitchen", "function": "kitchen", "area": 15},
                {"name": "Bedroom 1", "function": "bedroom", "area": 16},
                {"name": "Bedroom 2", "function": "bedroom", "area": 12},
                {"name": "Bathroom", "function": "bathroom", "area": 6},
                {"name": "Entry", "function": "lobby", "area": 4},
            ],
        }

        interpreter = RequirementsInterpreterAgent(context)
        requirements = interpreter.run(demo_requirements)

        planner = SchematicPlanGenerator(context)
        plan_result = planner.run(requirements)
        project = plan_result.project
        level = project.building.levels[0]

        annotator = CDAnnotationEngine(context)
        annotations = annotator.run(level)

        view_gen = ViewGenerator(context)
        view_set = view_gen.run(level)

        composer = SheetComposer(context)
        composed = composer.run(project, view_set, annotations)

        exporter = ExportAgent(context)
        package = exporter.run(project, level, annotations, composed, output_dir)

        return {
            "status": "completed",
            "project_name": project.name,
            "rooms": len(level.rooms),
            "walls": len(level.walls),
            "doors": len(level.doors),
            "windows": len(level.windows),
            "sheets": len(composed.sheet_set.sheets),
            "files": [f.filename for f in package.manifest.files],
            "qc_issues": plan_result.qc_issues,
            "output_dir": str(output_dir),
            "zip_path": str(package.zip_path) if package.zip_path else None,
        }
