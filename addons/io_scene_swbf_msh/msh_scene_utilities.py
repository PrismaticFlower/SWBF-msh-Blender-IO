""" Contains Scene object for representing a .msh file and the function to create one
    from a Blender scene.  """

from dataclasses import dataclass, field
from typing import List, Dict
from copy import copy
import bpy
from mathutils import Vector
from .msh_model import Model, Animation, ModelType
from .msh_scene import Scene, SceneAABB
from .msh_model_gather import gather_models
from .msh_model_utilities import make_null, validate_geometry_segment, sort_by_parent, has_multiple_root_models, reparent_model_roots, get_model_world_matrix, inject_dummy_data
from .msh_model_triangle_strips import create_models_triangle_strips
from .msh_material import *
from .msh_material_gather import gather_materials
from .msh_material_utilities import remove_unused_materials
from .msh_utilities import *
from .msh_anim_gather import extract_anim



def set_scene_animation(scene : Scene, armature_obj : bpy.types.Object):

    if not scene or not armature_obj:
        return

    root = scene.models[0]
    scene.animation = extract_anim(armature_obj, root.name)







def create_scene(generate_triangle_strips: bool, apply_modifiers: bool, export_target: str, skel_only: bool) -> Tuple[Scene, bpy.types.Object]:
    """ Create a msh Scene from the active Blender scene. """

    scene = Scene()

    scene.name = bpy.context.scene.name

    scene.materials = gather_materials()

    scene.models, armature_obj = gather_models(apply_modifiers=apply_modifiers, export_target=export_target, skeleton_only=skel_only)
    scene.models = sort_by_parent(scene.models)

    if generate_triangle_strips:
        scene.models = create_models_triangle_strips(scene.models)
    else:
        for model in scene.models:
            if model.geometry:
                for segment in model.geometry:
                    segment.triangle_strips = segment.triangles

    # After generating triangle strips we must prune any segments that don't have
    # them, or else ZE and most versions of ZETools will crash.

    # We could also make models with no valid segments nulls, since they might as well be, 
    # but that could have unforseeable consequences further down the modding pipeline
    # and is not necessary to avoid the aforementioned crashes...
    for model in scene.models:
        if model.geometry is not None:
            # Doing this in msh_model_gather would be messy and the presence/absence
            # of triangle strips is required for a validity check.
            model.geometry = [segment for segment in model.geometry if validate_geometry_segment(segment)]
            #if not model.geometry:
            #    make_null(model)

    if has_multiple_root_models(scene.models):
        scene.models = reparent_model_roots(scene.models)

    scene.materials = remove_unused_materials(scene.materials, scene.models)
 

    root = scene.models[0]

    if skel_only and (root.model_type == ModelType.NULL or root.model_type == ModelType.BONE):
        # For ZenAsset
        inject_dummy_data(root)

    return scene, armature_obj


def create_scene_aabb(scene: Scene) -> SceneAABB:
    """ Create a SceneAABB for a Scene. """

    global_aabb = SceneAABB()

    for model in scene.models:
        if model.geometry is None or model.hidden:
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
