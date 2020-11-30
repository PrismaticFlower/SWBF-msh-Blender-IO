""" Misc utilities. """

from mathutils import Vector
from typing import List


def vec_to_str(vec):
    return "({:.4},{:.4},{:.4})".format(vec.x,vec.y,vec.z)

def quat_to_str(quat):
    return "({:.4},{:.4},{:.4},{:.4})".format(quat.x, quat.y, quat.z, quat.w)

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

    packed |= (int(color[0] * 255.0 + 0.5) << 16)
    packed |= (int(color[1] * 255.0 + 0.5) << 8)
    packed |= (int(color[2] * 255.0 + 0.5))
    packed |= (int(color[3] * 255.0 + 0.5) << 24)

    return packed

def unpack_color(color: int) -> List[float]:

    mask = int(0x000000ff)

    r = (color & (mask << 16)) / 255.0
    g = (color & (mask << 8)) / 255.0
    b = (color & mask) / 255.0
    a = (color & (mask << 24)) / 255.0

    return [r,g,b,a]
