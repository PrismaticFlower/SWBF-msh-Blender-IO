""" Contains Model and dependent types for constructing a scene hierarchy easilly
    saved to a .msh file. """

from dataclasses import dataclass, field
from typing import List, Tuple, Dict
from enum import Enum
from mathutils import Vector, Quaternion

class ModelType(Enum):
    NULL = 0
    SKIN = 1
    CLOTH = 2
    BONE = 3
    STATIC = 4
    SHADOWVOLUME = 6

class CollisionPrimitiveShape(Enum):
    SPHERE = 0
    ELLIPSOID = 1
    CYLINDER = 2
    MESH = 3
    BOX = 4

@dataclass
class ModelTransform:
    """ Class representing a `TRAN` section in a .msh file. """

    translation: Vector = field(default_factory=Vector)
    rotation: Quaternion = field(default_factory=Quaternion)

@dataclass
class VertexWeight:
    """ Class representing a vertex weight in a .msh file. """

    weight: float = 1.0
    bone: int = 0

@dataclass
class GeometrySegment:
    """ Class representing a 'SEGM' section in a .msh file. """

    material_name: str = field(default_factory=str)

    positions: List[Vector] = field(default_factory=list)
    normals: List[Vector] = field(default_factory=list)
    colors: List[List[float]] = None
    texcoords: List[Vector] = field(default_factory=list)

    weights: List[List[VertexWeight]] = None

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

    bone_map: List[str] = None

    geometry: List[GeometrySegment] = None
    collisionprimitive: CollisionPrimitive = None


@dataclass
class RotationFrame:

    index : int = 0
    rotation : Quaternion = field(default_factory=Quaternion)


@dataclass
class TranslationFrame:

    index : int = 0
    translation : Vector = field(default_factory=Vector)  


@dataclass
class Animation:
    """ Class representing 'CYCL' + 'KFR3' sections in a .msh file """

    name: str = "fullanimation"
    bone_frames: Dict[int, Tuple[List[TranslationFrame], List[RotationFrame]]] = field(default_factory=dict)

    framerate: float = 29.97
    start_index : int = 0
    end_index   : int = 0
