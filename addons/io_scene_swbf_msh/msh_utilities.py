""" Misc utilities. """

from mathutils import Vector

def add_vec(l: Vector, r: Vector) -> Vector:
    return Vector(v0 + v1 for v0, v1 in zip(l, r))

def sub_vec(l: Vector, r: Vector) -> Vector:
    return Vector(v0 - v1 for v0, v1 in zip(l, r))

def mul_vec(l: Vector, r: Vector) -> Vector:
    return Vector(v0 * v1 for v0, v1 in zip(l, r))

def div_vec(l: Vector, r: Vector) -> Vector:
    return Vector(v0 / v1 for v0, v1 in zip(l, r))

def max_vec(l: Vector, r: Vector) -> Vector:
    return Vector(max(v0, v1) for v0, v1 in zip(l, r))

def min_vec(l: Vector, r: Vector) -> Vector:
    return Vector(min(v0, v1) for v0, v1 in zip(l, r))

def pack_color(color) -> int:
    packed = 0

    packed |= (int(color[0] * 255.0 + 0.5) << 8)
    packed |= (int(color[1] * 255.0 + 0.5) << 16)
    packed |= (int(color[2] * 255.0 + 0.5))
    packed |= (int(color[3] * 255.0 + 0.5) << 24)

    return packed
