""" Contains Scene object for representing a .msh file and the function to create one
    from a Blender scene.  """

from dataclasses import dataclass, field
from typing import List
from copy import copy
import bpy
from mathutils import Vector
from .msh_model import Model
from .msh_model_gather import gather_models
from .msh_model_utilities import sort_by_parent, has_multiple_root_models, reparent_model_roots, get_model_world_matrix
from .msh_model_triangle_strips import create_models_triangle_strips
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
    models: List[Model] = field(default_factory=list)

def create_scene() -> Scene:
    """ Create a msh Scene from the active Blender scene. """

    scene = Scene()

    scene.name = bpy.context.scene.name

    scene.models = gather_models()
    scene.models = sort_by_parent(scene.models)
    scene.models = create_models_triangle_strips(scene.models)

    if has_multiple_root_models(scene.models):
        scene.models = reparent_model_roots(scene.models)

    return scene

def create_scene_aabb(scene: Scene) -> SceneAABB:
    """ Create a SceneAABB for a Scene. """

    global_aabb = SceneAABB()

    for model in scene.models:
        if model.geometry is None:
            continue

        model_world_matrix = get_model_world_matrix(model, scene.models)
        model_aabb = SceneAABB()

        for segment in model.geometry:
            segment_aabb = SceneAABB()

            for pos in segment.positions:
                segment_aabb.integrate_position(model_world_matrix @ pos)

            model_aabb.integrate_aabb(segment_aabb)

        global_aabb.integrate_aabb(model_aabb)

    return global_aabb
