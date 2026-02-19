"""Export Agent - generates DXF, IFC, PDF, PNG from the composed model."""
from __future__ import annotations

import json
import math
import re
import zipfile
from pathlib import Path


def _safe_filename(name: str) -> str:
    """Remove characters unsafe for filenames."""
    return re.sub(r'[/<>:\"\\|?*]', '_', name)

from app.agents.base import BaseAgent
from app.agents.annotation_engine import AnnotationResult
from app.agents.sheet_composer import ComposedSheetSet
from app.domain.export import ExportFile, ExportFormat, ExportManifest, ExportPackage
from app.domain.project import Level, Project
from app.domain.schedules import (
    DoorSchedule,
    DoorScheduleEntry,
    RoomFinishEntry,
    RoomFinishSchedule,
    WindowSchedule,
    WindowScheduleEntry,
)


class ExportAgent(BaseAgent):
    """Exports the CD set to DXF, IFC, PDF, PNG formats."""

    def run(
        self,
        project: Project,
        level: Level,
        annotations: AnnotationResult,
        composed: ComposedSheetSet,
        output_dir: Path,
        formats: list[str] | None = None,
    ) -> ExportPackage:
        if formats is None:
            formats = ["dxf", "pdf", "png"]

        output_dir.mkdir(parents=True, exist_ok=True)
        self.log(f"Exporting to {output_dir} formats={formats}")

        package = ExportPackage(
            manifest=ExportManifest(
                project_name=project.name,
                project_number=project.number,
                revision=project.revision,
                formats=formats,
                total_sheets=len(composed.sheet_set.sheets),
            ),
            output_dir=output_dir,
        )

        # Build schedules
        door_schedule = self._build_door_schedule(level)
        window_schedule = self._build_window_schedule(level)
        room_schedule = self._build_room_schedule(level)

        for sheet in composed.sheet_set.sheets:
            if "dxf" in formats:
                ef = self._export_dxf(project, level, sheet, annotations, output_dir)
                package.add_file(ef)

            if "pdf" in formats:
                ef = self._export_pdf(project, level, sheet, annotations, output_dir,
                                      door_schedule, window_schedule, room_schedule)
                package.add_file(ef)

            if "png" in formats:
                ef = self._export_png(project, level, sheet, annotations, output_dir)
                package.add_file(ef)

        if "ifc" in formats:
            ef = self._export_ifc(project, level, output_dir)
            package.add_file(ef)

        # Write manifest
        manifest_path = output_dir / "manifest.json"
        manifest_path.write_text(json.dumps(package.manifest.to_dict(), indent=2))

        # Create zip
        zip_path = output_dir / f"{project.name.replace(' ', '_')}_CD.zip"
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for ef in package.manifest.files:
                if ef.path.exists():
                    zf.write(ef.path, ef.filename)
            zf.write(manifest_path, "manifest.json")

        package.zip_path = zip_path
        self.log(f"Export complete: {package.file_count} files, zip at {zip_path}")
        return package

    def _export_dxf(self, project, level, sheet, annotations, output_dir) -> ExportFile:
        """Export a sheet to DXF format using ezdxf."""
        import ezdxf
        from ezdxf.enums import TextEntityAlignment

        filename = f"{sheet.number}_{_safe_filename(sheet.name).replace(' ', '_')}.dxf"
        filepath = output_dir / filename

        doc = ezdxf.new("R2013")
        msp = doc.modelspace()

        # Setup layers
        from app.domain.layers import LAYERS
        for layer_name, layer_def in LAYERS.items():
            doc.layers.add(
                layer_name,
                color=layer_def.color,
                linetype=layer_def.linetype if layer_def.linetype in doc.linetypes else "Continuous",
            )

        # Draw walls
        for wall in level.walls:
            layer = "A-WALL-EXTR" if wall.is_exterior else "A-WALL"
            t = wall.thickness / 2

            if wall.line.is_horizontal:
                msp.add_line(
                    (wall.start.x, wall.start.y - t),
                    (wall.end.x, wall.end.y - t),
                    dxfattribs={"layer": layer},
                )
                msp.add_line(
                    (wall.start.x, wall.start.y + t),
                    (wall.end.x, wall.end.y + t),
                    dxfattribs={"layer": layer},
                )
            elif wall.line.is_vertical:
                msp.add_line(
                    (wall.start.x - t, wall.start.y),
                    (wall.end.x - t, wall.end.y),
                    dxfattribs={"layer": layer},
                )
                msp.add_line(
                    (wall.start.x + t, wall.start.y),
                    (wall.end.x + t, wall.end.y),
                    dxfattribs={"layer": layer},
                )
            else:
                # Diagonal wall - just draw centerline thick
                msp.add_line(
                    (wall.start.x, wall.start.y),
                    (wall.end.x, wall.end.y),
                    dxfattribs={"layer": layer},
                )

        # Draw doors
        for door in level.doors:
            p = door.position
            w = door.width / 2
            msp.add_line(
                (p.x - w, p.y), (p.x + w, p.y),
                dxfattribs={"layer": "A-DOOR"},
            )
            # Door swing arc
            msp.add_arc(
                center=(p.x - w, p.y),
                radius=door.width,
                start_angle=0,
                end_angle=90,
                dxfattribs={"layer": "A-DOOR-SWING"},
            )

        # Draw windows
        for window in level.windows:
            p = window.position
            w = window.width / 2
            msp.add_line(
                (p.x - w, p.y - 0.05), (p.x + w, p.y - 0.05),
                dxfattribs={"layer": "A-WIND"},
            )
            msp.add_line(
                (p.x - w, p.y + 0.05), (p.x + w, p.y + 0.05),
                dxfattribs={"layer": "A-WIND"},
            )
            # Glazing line
            msp.add_line(
                (p.x - w, p.y), (p.x + w, p.y),
                dxfattribs={"layer": "A-GLAZ"},
            )

        # Room tags
        for tag in annotations.room_tags:
            msp.add_text(
                tag.room_name,
                height=0.3,
                dxfattribs={"layer": "A-ROOM-NAME"},
            ).set_placement((tag.position.x, tag.position.y + 0.3), align=TextEntityAlignment.MIDDLE_CENTER)

            msp.add_text(
                f"{tag.area:.1f} m²",
                height=0.2,
                dxfattribs={"layer": "A-ROOM-AREA"},
            ).set_placement((tag.position.x, tag.position.y - 0.2), align=TextEntityAlignment.MIDDLE_CENTER)

            msp.add_text(
                tag.room_number,
                height=0.25,
                dxfattribs={"layer": "A-ROOM-NUMB"},
            ).set_placement((tag.position.x, tag.position.y + 0.7), align=TextEntityAlignment.MIDDLE_CENTER)

        # Dimensions
        for dim in annotations.dimensions:
            msp.add_line(
                (dim.start.x, dim.start.y),
                (dim.end.x, dim.end.y),
                dxfattribs={"layer": "A-DIMS"},
            )
            mid = dim.start.midpoint(dim.end)
            msp.add_text(
                f"{dim.value:.2f}",
                height=0.2,
                dxfattribs={"layer": "A-DIMS"},
            ).set_placement((mid.x, mid.y + 0.15), align=TextEntityAlignment.MIDDLE_CENTER)

        doc.saveas(filepath)
        size = filepath.stat().st_size

        return ExportFile(
            filename=filename,
            format=ExportFormat.DXF,
            path=filepath,
            size_bytes=size,
            sheet_number=sheet.number,
            description=f"DXF - {sheet.name}",
        )

    def _export_pdf(self, project, level, sheet, annotations, output_dir,
                    door_schedule, window_schedule, room_schedule) -> ExportFile:
        """Export a sheet to PDF using reportlab."""
        from reportlab.lib.pagesizes import landscape
        from reportlab.lib.units import mm
        from reportlab.pdfgen import canvas as pdf_canvas

        filename = f"{sheet.number}_{_safe_filename(sheet.name).replace(' ', '_')}.pdf"
        filepath = output_dir / filename

        pw = sheet.paper_width_mm * mm
        ph = sheet.paper_height_mm * mm
        c = pdf_canvas.Canvas(str(filepath), pagesize=(pw, ph))

        # Title block
        tb = sheet.title_block
        tb_x = pw - 200 * mm
        tb_y = 10 * mm
        c.setLineWidth(1.5)
        c.rect(tb_x, tb_y, 185 * mm, 55 * mm)
        c.setFont("Helvetica-Bold", 14)
        c.drawString(tb_x + 5 * mm, tb_y + 42 * mm, tb.project_name)
        c.setFont("Helvetica", 10)
        c.drawString(tb_x + 5 * mm, tb_y + 34 * mm, f"Sheet: {tb.sheet_number}")
        c.drawString(tb_x + 5 * mm, tb_y + 26 * mm, tb.sheet_name)
        c.drawString(tb_x + 5 * mm, tb_y + 18 * mm, f"Scale: {tb.scale}")
        c.drawString(tb_x + 5 * mm, tb_y + 10 * mm, f"Date: {tb.date}")
        c.drawString(tb_x + 100 * mm, tb_y + 10 * mm, f"Rev: {tb.revision}")
        c.drawString(tb_x + 5 * mm, tb_y + 2 * mm, f"Drawn by: {tb.drawn_by}")

        # Drawing area border
        margin = 15 * mm
        draw_bottom = 70 * mm
        c.setLineWidth(0.5)
        c.rect(margin, draw_bottom, pw - 2 * margin, ph - draw_bottom - margin)

        # Scale factor: model meters → PDF points
        scale_factor = 10 * mm  # 1 meter = 10mm on paper at 1:100
        origin_x = margin + 20 * mm
        origin_y = draw_bottom + 20 * mm

        def tx(x): return origin_x + x * scale_factor
        def ty(y): return origin_y + y * scale_factor

        # Draw walls
        c.setLineWidth(1.0)
        for wall in level.walls:
            lw = 2.0 if wall.is_exterior else 1.0
            c.setLineWidth(lw)
            c.line(tx(wall.start.x), ty(wall.start.y), tx(wall.end.x), ty(wall.end.y))

        # Draw doors
        c.setLineWidth(0.5)
        c.setStrokeColorRGB(0.8, 0, 0)
        for door in level.doors:
            p = door.position
            w = door.width / 2
            c.line(tx(p.x - w), ty(p.y), tx(p.x + w), ty(p.y))

        # Draw windows
        c.setStrokeColorRGB(0, 0.6, 0.8)
        for window in level.windows:
            p = window.position
            w = window.width / 2
            c.line(tx(p.x - w), ty(p.y), tx(p.x + w), ty(p.y))

        # Room labels
        c.setStrokeColorRGB(0, 0, 0)
        c.setFillColorRGB(0, 0, 0)
        for tag in annotations.room_tags:
            c.setFont("Helvetica-Bold", 8)
            c.drawCentredString(tx(tag.position.x), ty(tag.position.y) + 3 * mm, tag.room_name)
            c.setFont("Helvetica", 6)
            c.drawCentredString(tx(tag.position.x), ty(tag.position.y) - 2 * mm, f"{tag.area:.1f} m²")

        # Dimensions
        c.setFont("Helvetica", 5)
        c.setStrokeColorRGB(0.3, 0.3, 0)
        for dim in annotations.dimensions:
            c.setLineWidth(0.3)
            c.line(tx(dim.start.x), ty(dim.start.y), tx(dim.end.x), ty(dim.end.y))
            mid = dim.start.midpoint(dim.end)
            c.drawCentredString(tx(mid.x), ty(mid.y) + 1.5 * mm, f"{dim.value:.2f}")

        c.save()
        size = filepath.stat().st_size

        return ExportFile(
            filename=filename,
            format=ExportFormat.PDF,
            path=filepath,
            size_bytes=size,
            sheet_number=sheet.number,
            description=f"PDF - {sheet.name}",
        )

    def _export_png(self, project, level, sheet, annotations, output_dir) -> ExportFile:
        """Export a sheet to PNG using Pillow."""
        from PIL import Image, ImageDraw, ImageFont

        filename = f"{sheet.number}_{_safe_filename(sheet.name).replace(' ', '_')}.png"
        filepath = output_dir / filename

        # Image size (roughly matching paper at 72 DPI)
        img_w = int(sheet.paper_width_mm * 2.5)
        img_h = int(sheet.paper_height_mm * 2.5)
        img = Image.new("RGB", (img_w, img_h), "white")
        draw = ImageDraw.Draw(img)

        # Scale: meters → pixels
        scale = 25.0  # pixels per meter
        ox = 80  # origin offset
        oy = img_h - 180

        def tx(x): return int(ox + x * scale)
        def ty(y): return int(oy - y * scale)  # flip Y for image coords

        # Draw walls
        for wall in level.walls:
            lw = 3 if wall.is_exterior else 2
            draw.line(
                [(tx(wall.start.x), ty(wall.start.y)),
                 (tx(wall.end.x), ty(wall.end.y))],
                fill="black", width=lw,
            )

        # Draw doors (red)
        for door in level.doors:
            p = door.position
            w = door.width / 2
            draw.line(
                [(tx(p.x - w), ty(p.y)), (tx(p.x + w), ty(p.y))],
                fill="red", width=2,
            )

        # Draw windows (cyan)
        for window in level.windows:
            p = window.position
            w = window.width / 2
            draw.line(
                [(tx(p.x - w), ty(p.y)), (tx(p.x + w), ty(p.y))],
                fill="cyan", width=2,
            )

        # Room labels
        for tag in annotations.room_tags:
            px, py = tx(tag.position.x), ty(tag.position.y)
            draw.text((px - 30, py - 10), tag.room_name, fill="blue")
            draw.text((px - 20, py + 2), f"{tag.area:.1f}m²", fill="blue")

        # Title block area
        draw.rectangle([(img_w - 400, 10), (img_w - 10, 120)], outline="black", width=2)
        draw.text((img_w - 390, 15), sheet.title_block.project_name, fill="black")
        draw.text((img_w - 390, 35), f"Sheet: {sheet.number}", fill="black")
        draw.text((img_w - 390, 55), sheet.name, fill="black")
        draw.text((img_w - 390, 75), f"Scale: {sheet.title_block.scale}", fill="black")
        draw.text((img_w - 390, 95), f"Date: {sheet.title_block.date}", fill="gray")

        img.save(filepath)
        size = filepath.stat().st_size

        return ExportFile(
            filename=filename,
            format=ExportFormat.PNG,
            path=filepath,
            size_bytes=size,
            sheet_number=sheet.number,
            description=f"PNG - {sheet.name}",
        )

    def _export_ifc(self, project, level, output_dir) -> ExportFile:
        """Export building model to IFC."""
        filename = f"{_safe_filename(project.name).replace(' ', '_')}.ifc"
        filepath = output_dir / filename

        try:
            import ifcopenshell
            import ifcopenshell.api

            ifc = ifcopenshell.api.run("project.create_file")
            proj = ifcopenshell.api.run("root.create_entity", ifc, ifc_class="IfcProject", name=project.name)
            ifcopenshell.api.run("unit.assign_unit", ifc)

            context = ifcopenshell.api.run("context.add_context", ifc, context_type="Model")
            body = ifcopenshell.api.run(
                "context.add_context", ifc,
                context_type="Model", context_identifier="Body",
                target_view="MODEL_VIEW", parent=context,
            )

            site = ifcopenshell.api.run("root.create_entity", ifc, ifc_class="IfcSite", name="Site")
            ifcopenshell.api.run("aggregate.assign_object", ifc, products=[site], relating_object=proj)

            building = ifcopenshell.api.run("root.create_entity", ifc, ifc_class="IfcBuilding", name=project.name)
            ifcopenshell.api.run("aggregate.assign_object", ifc, products=[building], relating_object=site)

            storey = ifcopenshell.api.run(
                "root.create_entity", ifc, ifc_class="IfcBuildingStorey", name=level.name
            )
            ifcopenshell.api.run("aggregate.assign_object", ifc, products=[storey], relating_object=building)

            # Add spaces (rooms)
            for room in level.rooms:
                space = ifcopenshell.api.run(
                    "root.create_entity", ifc, ifc_class="IfcSpace", name=room.name
                )
                ifcopenshell.api.run("spatial.assign_container", ifc, products=[space], relating_structure=storey)

            # Add walls
            for wall in level.walls:
                ifc_wall = ifcopenshell.api.run(
                    "root.create_entity", ifc, ifc_class="IfcWall", name=f"Wall_{wall.id}"
                )
                ifcopenshell.api.run("spatial.assign_container", ifc, products=[ifc_wall], relating_structure=storey)

            # Add doors
            for door in level.doors:
                ifc_door = ifcopenshell.api.run(
                    "root.create_entity", ifc, ifc_class="IfcDoor", name=f"Door_{door.id}"
                )
                ifcopenshell.api.run("spatial.assign_container", ifc, products=[ifc_door], relating_structure=storey)

            # Add windows
            for window in level.windows:
                ifc_win = ifcopenshell.api.run(
                    "root.create_entity", ifc, ifc_class="IfcWindow", name=f"Window_{window.id}"
                )
                ifcopenshell.api.run("spatial.assign_container", ifc, products=[ifc_win], relating_structure=storey)

            ifc.write(str(filepath))

        except ImportError:
            # ifcopenshell not available - write placeholder
            filepath.write_text("IFC export requires ifcopenshell package")

        size = filepath.stat().st_size
        return ExportFile(
            filename=filename,
            format=ExportFormat.IFC,
            path=filepath,
            size_bytes=size,
            description="IFC Building Model",
        )

    def _build_door_schedule(self, level: Level) -> DoorSchedule:
        schedule = DoorSchedule()
        for i, door in enumerate(level.doors):
            schedule.entries.append(DoorScheduleEntry(
                mark=f"D{i + 1:02d}",
                room_from=door.host_room_id,
                room_to=door.target_room_id,
                width=door.width,
                height=door.height,
                door_type=door.door_type.value.title(),
            ))
        return schedule

    def _build_window_schedule(self, level: Level) -> WindowSchedule:
        schedule = WindowSchedule()
        for i, win in enumerate(level.windows):
            schedule.entries.append(WindowScheduleEntry(
                mark=f"W{i + 1:02d}",
                room=win.room_id,
                width=win.width,
                height=win.height,
                sill_height=win.sill_height,
                window_type=win.window_type.value.title(),
            ))
        return schedule

    def _build_room_schedule(self, level: Level) -> RoomFinishSchedule:
        schedule = RoomFinishSchedule()
        for i, room in enumerate(level.rooms):
            schedule.entries.append(RoomFinishEntry(
                number=str(100 + i + 1),
                name=room.name,
                area=room.actual_area,
                floor_finish=room.floor_finish,
                wall_finish=room.wall_finish,
                ceiling_finish=room.ceiling_finish,
                ceiling_height=room.ceiling_height,
            ))
        return schedule
