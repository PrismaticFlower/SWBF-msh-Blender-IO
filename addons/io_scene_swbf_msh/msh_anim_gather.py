""" Gathers the Blender objects from the current scene and returns them as a list of
    Model objects. """

import bpy
import math
from enum import Enum
from typing import List, Set, Dict, Tuple
from itertools import zip_longest
from .msh_model import *
from .msh_model_utilities import *
from .msh_utilities import *
from .msh_model_gather import *


def gather_animdata(armature: bpy.types.Armature) -> List[Animation]:

    anim_data = Animation();

    action = armature.animation_data.action
    
    framerange = action.frame_range
    increment  = (framerange.y - framerange.x) / 20.0
    offset     = framerange.x;

    anim_data.bone_transforms[armature.parent.name] = []
    for bone in armature.data.bones:
        anim_data.bone_transforms[bone.name] = []

    for frame in range(21):
        frame_time = offset + frame * increment
        bpy.context.scene.frame_set(frame_time)

        anim_data.bone_transforms[armature.parent.name].append(ModelTransform()) #for testing

        for bone in armature.pose.bones:

            xform = ModelTransform()
            xform.translation = to_skeleton_vector_space(bone.location)
            xform.rotation = to_skeleton_rotation_space(bone.rotation_quaternion)
            		
            anim_data.bone_transforms[bone.name].append(xform)
            
            
    return [anim_data]


def get_basepose(armature: bpy.types.Armature) -> Animation:

    anim_data = Animation();
    anim_data.name = "basepose"

    bpy.context.scene.frame_set(0.0)

    anim_data.bone_transforms[armature.parent.name] = []
    for bone in armature.data.bones:
        anim_data.bone_transforms[bone.name] = []

    for frame in range(2):

        anim_data.bone_transforms[armature.parent.name].append(ModelTransform()) #for testing

        for bone in armature.pose.bones:

            xform = ModelTransform()
            xform.translation = to_skeleton_vector_space(bone.location)
            xform.rotation = to_skeleton_rotation_space(bone.rotation_quaternion)
            		
            anim_data.bone_transforms[bone.name].append(xform)
            
            
    return anim_data





