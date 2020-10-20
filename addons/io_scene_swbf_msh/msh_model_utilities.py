""" Utilities for operating on msh_model objects. """

from typing import List
from .msh_model import *
from .msh_utilities import *
import mathutils
import math
from mathutils import Vector, Matrix

def scale_segments(scale: Vector, segments: List[GeometrySegment]):
    """ Scales are positions in the GeometrySegment list. """

    for segment in segments:
        segment.positions = [mul_vec(pos, scale) for pos in segment.positions]

def get_model_world_matrix(model: Model, models: List[Model]) -> Matrix:
    """ Gets a Blender Matrix for transforming the model into world space. """

    transform_stack: List[ModelTransform] = [model.transform]
    transform_stack.extend((parent.transform for parent in get_model_ancestors(model, models)))

    world_matrix: Matrix = Matrix()

    for transform in reversed(transform_stack):
        translation_matrix = Matrix.Translation(transform.translation)
        rotation_matrix = transform.rotation.to_matrix().to_4x4()

        world_matrix = world_matrix @ (translation_matrix @ rotation_matrix)

    return world_matrix

def sort_by_parent(models: List[Model]) -> List[Model]:
    """ Sorts a Model list so that models are ordered by their parent.
        Required for some tools to be able to load .msh files. """

    sorted_models: List[Model] = []

    for root in get_root_models(models):
        def add_children(model: Model):
            nonlocal sorted_models

            for child in get_model_children(model, models):
                sorted_models.append(child)
                add_children(child)

        sorted_models.append(root)
        add_children(root)

    return sorted_models

def reparent_model_roots(models: List[Model]) -> List[Model]:
    """ Reparents all root models in a list to a new empty node. """

    new_root: Model = Model()
    new_root.name = get_unique_scene_root_name(models)

    for model in models:
        if not model.parent:
            model.parent = new_root.name

    models.insert(0, new_root)

    return models

def has_multiple_root_models(models: List[Model]) -> bool:
    """ Checks if a list of Model objects has multiple roots. """

    return sum(1 for root in get_root_models(models)) > 1

def get_root_models(models: List[Model]) -> Model:
    """ Generator. Returns all Model objects in a list with no parent. """

    for model in models:
        if model.parent == "":
            yield model

def get_model_children(parent: Model, models: List[Model]) -> Model:
    """ Generator. Returns all Model objects in a list whose parent is
        the supplied model. """

    for model in models:
        if parent.name == model.parent:
            yield model

def get_model_ancestors(child: Model, models: List[Model]) -> Model:
    """ Generator. Yields the parent for a model, then yields the parent's parent,
        repeating until at the root model. """

    for model in models:
        if child.parent == model.name:
            child = model
            yield model

def get_unique_scene_root_name(models: List[Model]) -> Model:
    """ Returns a unique model name of the form of either "SceneRoot" or
        "SceneRoot{i}". """

    name: str = "SceneRoot"

    if is_model_name_unused(name, models):
        return name

    for i in range(len(models) + 1):
        name = f"SceneRoot{i}"

        if is_model_name_unused(name, models):
            return name

    return name

def is_model_name_unused(name: str, models: List[Model]) -> bool:
    """ Checks if there is no Model using a name in a list of models.  """

    for model in models:
        if model.name == name:
            return False

    return True


def convert_vector_space(vec: Vector) -> Vector:
    return Vector((-vec.x, vec.z, vec.y))

def convert_scale_space(vec: Vector) -> Vector:
    return Vector(vec.xzy)

def convert_rotation_space(quat: Quaternion) -> Quaternion:
    return Quaternion((-quat.w, quat.x, -quat.z, -quat.y))

