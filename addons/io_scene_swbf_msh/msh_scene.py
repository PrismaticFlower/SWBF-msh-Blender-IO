""" Contains Scene object for representing a .msh file and the function to create one
    from a Blender scene.  """

from dataclasses import dataclass, field
from typing import List, Dict
from copy import copy

import bpy
from mathutils import Vector

from .msh_model import Model, Animation, ModelType
from .msh_material import *
from .msh_utilities import *


@dataclass
class SceneAABB:
    """ Class representing an axis-aligned bounding box. """

    AABB_INIT_MAX = -3.402823466e+38
    AABB_INIT_MIN = 3.402823466e+38

    max_: Vector = Vector((AABB_INIT_MAX, AABB_INIT_MAX, AABB_INIT_MAX))
    min_: Vector = Vector((AABB_INIT_MIN, AABB_INIT_MIN, AABB_INIT_MIN))

    def integrate_aabb(self, other):
        """ Merge another AABB with this AABB. """

        self.max_ = max_vec(self.max_, other.max_)
        self.min_ = min_vec(self.min_, other.min_)

    def integrate_position(self, position):
        """ Integrate a position with the AABB, potentially expanding it. """

        self.max_ = max_vec(self.max_, position)
        self.min_ = min_vec(self.min_, position)

@dataclass
class Scene:
    """ Class containing the scene data for a .msh """
    name: str = "Scene"
    materials: Dict[str, Material] = field(default_factory=dict)
    models: List[Model] = field(default_factory=list)

    animation: Animation = None

    skeleton: List[int] = field(default_factory=list)