""" Contains Model and dependent types for constructing a scene hierarchy easilly
    saved to a .msh file. """

from dataclasses import dataclass, field
from typing import List
from enum import Enum
from mathutils import Vector, Quaternion

class ModelType(Enum):
    NULL = 0
    SKIN = 1
    CLOTH = 2
    BONE = 3
    STATIC = 4

class CollisionPrimitiveShape(Enum):
    SPHERE = 0
    # ELLIPSOID = 1
    CYLINDER = 2
    # MESH = 3
    CUBE = 4

@dataclass
class ModelTransform:
    """ Class representing a `TRAN` section in a .msh file. """

    translation: Vector = Vector((0.0, 0.0, 0.0))
    rotation: Quaternion = Quaternion((1.0, 0.0, 0.0, 0.0))

@dataclass
class GeometrySegment:
    """ Class representing a 'SEGM' section in a .msh file. """

    material_name: str = ""

    positions: List[Vector] = field(default_factory=list)
    normals: List[Vector] = field(default_factory=list)
    colors: List[List[float]] = None
    texcoords: List[Vector] = field(default_factory=list)
    # TODO: Skin support.

    polygons: List[List[int]] = field(default_factory=list)
    triangles: List[List[int]] = field(default_factory=list)
    triangle_strips: List[List[int]] = None

@dataclass
class CollisionPrimitive:
    """ Class representing a 'SWCI' section in a .msh file. """

    collision_primitive_shape: CollisionPrimitiveShape
    radius: float
    height: float
    length: float

@dataclass
class Model:
    """ Class representing a 'MODL' section in a .msh file. """

    name: str = "Model"
    parent: str = ""
    model_type: ModelType = ModelType.NULL
    hidden: bool = True

    transform: ModelTransform = ModelTransform()

    geometry: List[GeometrySegment] = None
    collisionprimitive: CollisionPrimitive = None
