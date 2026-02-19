"""Tests for geometry primitives."""
from app.domain.geometry import BoundingBox, Line2D, Point2D


def test_point_distance():
    a = Point2D(0, 0)
    b = Point2D(3, 4)
    assert a.distance_to(b) == 5.0


def test_point_midpoint():
    a = Point2D(0, 0)
    b = Point2D(10, 10)
    mid = a.midpoint(b)
    assert mid.x == 5.0
    assert mid.y == 5.0


def test_line_length():
    line = Line2D(Point2D(0, 0), Point2D(3, 4))
    assert line.length == 5.0


def test_line_horizontal():
    line = Line2D(Point2D(0, 5), Point2D(10, 5))
    assert line.is_horizontal
    assert not line.is_vertical


def test_bounding_box_area():
    bb = BoundingBox(Point2D(0, 0), Point2D(5, 4))
    assert bb.area == 20.0
    assert bb.width == 5.0
    assert bb.height == 4.0


def test_bounding_box_contains():
    bb = BoundingBox(Point2D(0, 0), Point2D(10, 10))
    assert bb.contains(Point2D(5, 5))
    assert not bb.contains(Point2D(15, 5))


def test_bounding_box_intersects():
    a = BoundingBox(Point2D(0, 0), Point2D(5, 5))
    b = BoundingBox(Point2D(3, 3), Point2D(8, 8))
    c = BoundingBox(Point2D(6, 6), Point2D(10, 10))
    assert a.intersects(b)
    assert not a.intersects(c)
