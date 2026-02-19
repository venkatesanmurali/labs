"""Schematic Plan Generator - rectangle packing with room placement, walls, doors, windows."""
from __future__ import annotations

import math
from dataclasses import dataclass, field

from app.agents.base import BaseAgent
from app.domain.geometry import (
    Door,
    DoorType,
    OpeningSide,
    Point2D,
    Wall,
    WallType,
    Window,
    WindowType,
)
from app.domain.program import ProgramRequirements, RoomRequirement
from app.domain.project import Building, Level, Project, Room, RoomFunction, Site


@dataclass
class PlacementResult:
    project: Project
    qc_issues: list[str] = field(default_factory=list)


class SchematicPlanGenerator(BaseAgent):
    """Deterministic room packing + wall/door/window placement."""

    def run(self, requirements: ProgramRequirements) -> PlacementResult:
        self.log("Starting schematic plan generation")
        expanded = requirements.expanded_rooms
        constraints = requirements.constraints

        # 1. Size rooms
        rooms = self._size_rooms(expanded, constraints)

        # 2. Pack rooms into grid
        rooms = self._pack_rooms(rooms, constraints)

        # 3. Create walls
        walls = self._create_walls(rooms, constraints)

        # 4. Place doors
        doors = self._place_doors(rooms, walls, constraints)

        # 5. Place windows
        windows = self._place_windows(rooms, walls, constraints)

        # 6. Assemble project
        level = Level(
            name="Level 1",
            elevation=0.0,
            floor_to_floor=constraints.floor_to_floor_height,
            rooms=rooms,
            walls=walls,
            doors=doors,
            windows=windows,
        )

        building = Building(name=requirements.project_name, levels=[level])
        site = Site(buildings=[building])
        project = Project(
            name=requirements.project_name,
            number=requirements.project_number,
            client=requirements.client,
            site=site,
        )

        # 7. QC checks
        qc_issues = self._run_qc(project, requirements)

        self.log(f"Generated plan: {len(rooms)} rooms, {len(walls)} walls, "
                 f"{len(doors)} doors, {len(windows)} windows, {len(qc_issues)} QC issues")

        return PlacementResult(project=project, qc_issues=qc_issues)

    def _size_rooms(self, room_reqs: list[RoomRequirement], constraints) -> list[Room]:
        """Convert requirements to sized Room objects."""
        rooms = []
        for i, req in enumerate(room_reqs):
            area = req.area
            # Determine reasonable aspect ratio (width:depth)
            aspect = 1.0 + self.rng.uniform(-0.3, 0.3)
            width = math.sqrt(area * aspect)
            depth = area / width

            # Round to nearest 0.1m
            width = round(width * 10) / 10
            depth = round(depth * 10) / 10

            room = Room(
                name=req.name,
                function=req.function,
                target_area=req.area,
                min_area=req.min_area,
                max_area=req.max_area,
                width=width,
                depth=depth,
                floor_finish=req.floor_finish,
                wall_finish=req.wall_finish,
                ceiling_finish=req.ceiling_finish,
                ceiling_height=req.ceiling_height,
            )
            rooms.append(room)
        return rooms

    def _pack_rooms(self, rooms: list[Room], constraints) -> list[Room]:
        """Pack rooms into a grid arrangement (largest first)."""
        # Sort by area descending for better packing
        rooms_sorted = sorted(rooms, key=lambda r: r.width * r.depth, reverse=True)

        wall_t = constraints.default_wall_thickness
        corridor_w = constraints.min_corridor_width
        max_w = constraints.max_footprint_width
        max_d = constraints.max_footprint_depth

        # Simple row-based packing
        x_cursor = wall_t  # start after exterior wall
        y_cursor = wall_t
        row_height = 0.0
        placed = []

        for room in rooms_sorted:
            # Check if room fits in current row
            if x_cursor + room.width + wall_t > max_w and placed:
                # Move to next row
                x_cursor = wall_t
                y_cursor += row_height + wall_t

            room.origin = Point2D(round(x_cursor, 2), round(y_cursor, 2))
            placed.append(room)

            x_cursor += room.width + wall_t
            row_height = max(row_height, room.depth)

        return placed

    def _create_walls(self, rooms: list[Room], constraints) -> list[Wall]:
        """Create walls around each room."""
        walls = []
        ext_t = constraints.exterior_wall_thickness
        int_t = constraints.default_wall_thickness
        height = constraints.floor_to_floor_height

        # Find building envelope
        if not rooms:
            return walls

        min_x = min(r.origin.x for r in rooms) - ext_t
        min_y = min(r.origin.y for r in rooms) - ext_t
        max_x = max(r.origin.x + r.width for r in rooms) + ext_t
        max_y = max(r.origin.y + r.depth for r in rooms) + ext_t

        # Exterior walls
        ext_walls = [
            Wall(start=Point2D(min_x, min_y), end=Point2D(max_x, min_y),
                 thickness=ext_t, height=height, wall_type=WallType.EXTERIOR),
            Wall(start=Point2D(max_x, min_y), end=Point2D(max_x, max_y),
                 thickness=ext_t, height=height, wall_type=WallType.EXTERIOR),
            Wall(start=Point2D(max_x, max_y), end=Point2D(min_x, max_y),
                 thickness=ext_t, height=height, wall_type=WallType.EXTERIOR),
            Wall(start=Point2D(min_x, max_y), end=Point2D(min_x, min_y),
                 thickness=ext_t, height=height, wall_type=WallType.EXTERIOR),
        ]
        walls.extend(ext_walls)

        # Interior walls between rooms
        for i, room_a in enumerate(rooms):
            for room_b in rooms[i + 1:]:
                shared_wall = self._find_shared_edge(room_a, room_b, int_t)
                if shared_wall:
                    walls.append(shared_wall)

        # Remaining room edges that need walls
        for room in rooms:
            bounds = room.bounds
            edges = [
                (Point2D(bounds.min_pt.x, bounds.min_pt.y), Point2D(bounds.max_pt.x, bounds.min_pt.y)),  # bottom
                (Point2D(bounds.max_pt.x, bounds.min_pt.y), Point2D(bounds.max_pt.x, bounds.max_pt.y)),  # right
                (Point2D(bounds.max_pt.x, bounds.max_pt.y), Point2D(bounds.min_pt.x, bounds.max_pt.y)),  # top
                (Point2D(bounds.min_pt.x, bounds.max_pt.y), Point2D(bounds.min_pt.x, bounds.min_pt.y)),  # left
            ]
            for start, end in edges:
                if not self._edge_has_wall(start, end, walls, tolerance=0.1):
                    wall_type = WallType.INTERIOR
                    # Check if on building perimeter
                    if (abs(start.x - min_x) < ext_t + 0.1 and abs(end.x - min_x) < ext_t + 0.1) or \
                       (abs(start.y - min_y) < ext_t + 0.1 and abs(end.y - min_y) < ext_t + 0.1) or \
                       (abs(start.x - max_x) < ext_t + 0.1 and abs(end.x - max_x) < ext_t + 0.1) or \
                       (abs(start.y - max_y) < ext_t + 0.1 and abs(end.y - max_y) < ext_t + 0.1):
                        continue  # Already covered by exterior wall
                    walls.append(Wall(
                        start=start, end=end,
                        thickness=int_t, height=height,
                        wall_type=wall_type,
                    ))

        return walls

    def _find_shared_edge(self, a: Room, b: Room, thickness: float) -> Wall | None:
        """Find shared wall between two adjacent rooms."""
        ab, bb = a.bounds, b.bounds
        tol = thickness + 0.05

        # Check if rooms share a vertical edge (a.right == b.left or vice versa)
        if abs(ab.max_pt.x - bb.min_pt.x) < tol:
            y_min = max(ab.min_pt.y, bb.min_pt.y)
            y_max = min(ab.max_pt.y, bb.max_pt.y)
            if y_max > y_min:
                x = (ab.max_pt.x + bb.min_pt.x) / 2
                return Wall(
                    start=Point2D(x, y_min), end=Point2D(x, y_max),
                    thickness=thickness, height=3.0, wall_type=WallType.INTERIOR,
                )

        if abs(bb.max_pt.x - ab.min_pt.x) < tol:
            y_min = max(ab.min_pt.y, bb.min_pt.y)
            y_max = min(ab.max_pt.y, bb.max_pt.y)
            if y_max > y_min:
                x = (bb.max_pt.x + ab.min_pt.x) / 2
                return Wall(
                    start=Point2D(x, y_min), end=Point2D(x, y_max),
                    thickness=thickness, height=3.0, wall_type=WallType.INTERIOR,
                )

        # Check horizontal shared edge
        if abs(ab.max_pt.y - bb.min_pt.y) < tol:
            x_min = max(ab.min_pt.x, bb.min_pt.x)
            x_max = min(ab.max_pt.x, bb.max_pt.x)
            if x_max > x_min:
                y = (ab.max_pt.y + bb.min_pt.y) / 2
                return Wall(
                    start=Point2D(x_min, y), end=Point2D(x_max, y),
                    thickness=thickness, height=3.0, wall_type=WallType.INTERIOR,
                )

        if abs(bb.max_pt.y - ab.min_pt.y) < tol:
            x_min = max(ab.min_pt.x, bb.min_pt.x)
            x_max = min(ab.max_pt.x, bb.max_pt.x)
            if x_max > x_min:
                y = (bb.max_pt.y + ab.min_pt.y) / 2
                return Wall(
                    start=Point2D(x_min, y), end=Point2D(x_max, y),
                    thickness=thickness, height=3.0, wall_type=WallType.INTERIOR,
                )

        return None

    def _edge_has_wall(self, start: Point2D, end: Point2D, walls: list[Wall], tolerance: float) -> bool:
        """Check if an edge is already covered by an existing wall."""
        mid = start.midpoint(end)
        for wall in walls:
            wall_mid = wall.start.midpoint(wall.end)
            if mid.distance_to(wall_mid) < tolerance + max(
                abs(end.x - start.x), abs(end.y - start.y)
            ) / 2:
                return True
        return False

    def _place_doors(self, rooms: list[Room], walls: list[Wall], constraints) -> list[Door]:
        """Place doors on shared walls between rooms."""
        doors = []
        door_width = constraints.min_door_width
        door_height = constraints.door_height
        placed_pairs = set()

        for i, room_a in enumerate(rooms):
            for j, room_b in enumerate(rooms):
                if i >= j:
                    continue
                pair_key = (min(room_a.id, room_b.id), max(room_a.id, room_b.id))
                if pair_key in placed_pairs:
                    continue

                # Find the shared wall
                for wall in walls:
                    if wall.wall_type == WallType.EXTERIOR:
                        continue
                    if self._wall_between_rooms(wall, room_a, room_b):
                        mid = wall.start.midpoint(wall.end)
                        door = Door(
                            position=mid,
                            width=door_width,
                            height=door_height,
                            door_type=DoorType.SINGLE,
                            swing_side=OpeningSide.LEFT,
                            wall_id=wall.id,
                            host_room_id=room_a.id,
                            target_room_id=room_b.id,
                        )
                        doors.append(door)
                        placed_pairs.add(pair_key)
                        break

        # Ensure every room has at least one door
        rooms_with_doors = set()
        for d in doors:
            rooms_with_doors.add(d.host_room_id)
            rooms_with_doors.add(d.target_room_id)

        for room in rooms:
            if room.id not in rooms_with_doors and rooms:
                # Place door on the first non-exterior wall touching this room
                for wall in walls:
                    if wall.wall_type != WallType.EXTERIOR:
                        mid = wall.start.midpoint(wall.end)
                        bounds = room.bounds
                        if (bounds.min_pt.x - 0.5 <= mid.x <= bounds.max_pt.x + 0.5 and
                                bounds.min_pt.y - 0.5 <= mid.y <= bounds.max_pt.y + 0.5):
                            doors.append(Door(
                                position=mid,
                                width=door_width,
                                height=door_height,
                                wall_id=wall.id,
                                host_room_id=room.id,
                            ))
                            break

        return doors

    def _wall_between_rooms(self, wall: Wall, a: Room, b: Room) -> bool:
        """Check if a wall lies between two rooms."""
        mid = wall.start.midpoint(wall.end)
        ab, bb = a.bounds, b.bounds
        tol = 0.5

        # Wall midpoint should be near both room boundaries
        near_a = (ab.min_pt.x - tol <= mid.x <= ab.max_pt.x + tol and
                  ab.min_pt.y - tol <= mid.y <= ab.max_pt.y + tol)
        near_b = (bb.min_pt.x - tol <= mid.x <= bb.max_pt.x + tol and
                  bb.min_pt.y - tol <= mid.y <= bb.max_pt.y + tol)
        return near_a and near_b

    def _place_windows(self, rooms: list[Room], walls: list[Wall], constraints) -> list[Window]:
        """Place windows on exterior walls for habitable rooms."""
        windows = []
        ext_walls = [w for w in walls if w.is_exterior]

        for room in rooms:
            needs_window = room.is_habitable
            if not needs_window:
                continue

            # Find exterior wall closest to this room
            bounds = room.bounds
            center = bounds.center

            best_wall = None
            best_dist = float("inf")
            for wall in ext_walls:
                wall_mid = wall.start.midpoint(wall.end)
                dist = center.distance_to(wall_mid)
                if dist < best_dist:
                    best_dist = dist
                    best_wall = wall

            if best_wall and best_wall.length >= 1.5:
                # Place window at midpoint of the wall segment near the room
                win_pos = best_wall.start.midpoint(best_wall.end)

                # Calculate window size based on room area (min 10% of floor area)
                min_win_area = room.actual_area * constraints.min_window_area_ratio
                win_width = max(1.2, min(min_win_area / constraints.window_height, best_wall.length * 0.6))
                win_width = round(win_width * 10) / 10

                windows.append(Window(
                    position=win_pos,
                    width=win_width,
                    height=constraints.window_height,
                    sill_height=constraints.window_sill_height,
                    window_type=WindowType.FIXED,
                    wall_id=best_wall.id,
                    room_id=room.id,
                ))

        return windows

    def _run_qc(self, project: Project, requirements: ProgramRequirements) -> list[str]:
        """Run quality control checks."""
        issues = []
        building = project.building
        if not building or not building.levels:
            issues.append("ERROR: No building or levels generated")
            return issues

        level = building.levels[0]

        # Check room areas
        for room in level.rooms:
            if room.min_area > 0 and room.actual_area < room.min_area:
                issues.append(
                    f"WARNING: {room.name} area {room.actual_area:.1f}m² "
                    f"below minimum {room.min_area:.1f}m²"
                )
            if room.max_area > 0 and room.actual_area > room.max_area:
                issues.append(
                    f"WARNING: {room.name} area {room.actual_area:.1f}m² "
                    f"exceeds maximum {room.max_area:.1f}m²"
                )

        # Check habitable rooms have windows
        rooms_with_windows = {w.room_id for w in level.windows}
        for room in level.rooms:
            if room.is_habitable and room.id not in rooms_with_windows:
                issues.append(f"WARNING: Habitable room '{room.name}' has no window")

        # Check door clearances
        for door in level.doors:
            for other_door in level.doors:
                if door.id >= other_door.id:
                    continue
                dist = door.position.distance_to(other_door.position)
                if dist < 0.9:
                    issues.append(
                        f"WARNING: Doors {door.id} and {other_door.id} "
                        f"too close ({dist:.2f}m)"
                    )

        # Check every room has a door
        rooms_with_doors = set()
        for d in level.doors:
            rooms_with_doors.add(d.host_room_id)
            rooms_with_doors.add(d.target_room_id)

        for room in level.rooms:
            if room.id not in rooms_with_doors:
                issues.append(f"WARNING: Room '{room.name}' has no door")

        return issues
