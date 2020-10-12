""" Contains Model and dependent types for constructing a scene hierarchy easilly
    saved to a .msh file. """

from dataclasses import dataclass, field
from typing import List, Dict, Tuple
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
    BOX = 4

@dataclass
class ModelTransform:
    """ Class representing a `TRAN` section in a .msh file. """

    translation: Vector = field(default_factory=Vector)
    rotation: Quaternion = field(default_factory=Quaternion)

@dataclass
class GeometrySegment:
    """ Class representing a 'SEGM' section in a .msh file. """

    material_name: str = ""

    positions: List[Vector] = field(default_factory=list)
    weights: List[Tuple[int, float]] = None
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

    shape: CollisionPrimitiveShape = CollisionPrimitiveShape.SPHERE
    radius: float = 0.0
    height: float = 0.0
    length: float = 0.0

@dataclass
class Model:
    """ Class representing a 'MODL' section in a .msh file. """

    name: str = "Model"
    parent: str = ""
    model_type: ModelType = ModelType.NULL
    hidden: bool = True

    transform: ModelTransform = field(default_factory=ModelTransform)

    geometry: List[GeometrySegment] = None
    collisionprimitive: CollisionPrimitive = None

@dataclass
class Animation:
    """ Class representing 'CYCL' + 'KFR3' sections in a .msh file """

    name: str = "open"
    anim_type: str = "HardSkinned"
    bone_transforms: Dict[str, List[ModelTransform]] = field(default_factory=dict)
    
