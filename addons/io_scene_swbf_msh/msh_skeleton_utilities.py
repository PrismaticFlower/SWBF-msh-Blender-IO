""" Armature -> SWBF skeleton mapping functions """

import bpy
import math

from typing import List, Set, Dict, Tuple

from .msh_scene import Scene
from .msh_model import *
from .msh_model_utilities import *

from .crc import *


def get_bone_world_matrix(armature: bpy.types.Object, bone_name: str) -> Matrix:
    if bone_name in armature.data.bones:
        return armature.matrix_world @ armature.data.bones[bone_name].matrix_local
    else:
        return None


'''Returns all bones that should be marked as BONE'''
def get_real_BONES(armature: bpy.types.Armature) -> Set[str]:

    # First priority, add the names of the skeleton preserved on import
    skel_props = armature.data.swbf_msh_skel

    # Second, add all keyed bones
    action = armature.animation_data.action if armature.animation_data else None

    # Third, just add all bones in armature

    # Set of bones to include
    real_bones : Set[str] = set()

    if len(skel_props) > 0:
        for bone in skel_props:
            real_bones.add(bone.name)
    if action:
        for group in armature.animation_data.action.groups:
            real_bones.add(group.name)

    if len(skel_props) == 0 and action is None:
        for bone in armature.data.bones:
            real_bones.add(bone.name)

    return real_bones
