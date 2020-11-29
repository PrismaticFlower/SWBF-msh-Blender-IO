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


def extract_anim(armature: bpy.types.Armature) -> Animation:

    action = armature.animation_data.action
    anim = Animation();

    if not action:
        framerange = Vector((0.0,1.0))
    else:
        framerange = action.frame_range
    
    num_frames = math.floor(framerange.y - framerange.x) + 1
    increment  = (framerange.y - framerange.x) / (num_frames - 1)

    anim.end_index = num_frames - 1
    
    anim.bone_transforms["DummyRoot"] = []
    for bone in armature.data.bones:
        anim.bone_transforms[bone.name] = []

    for frame in range(num_frames):

        #if frame % 10 == 0:
        #    print("Sample frame {}:".format(frame))

        frame_time = framerange.x + frame * increment
        bpy.context.scene.frame_set(frame_time)

        anim.bone_transforms["DummyRoot"].append(ModelTransform())
        for bone in armature.pose.bones:

            transform = bone.matrix

            if bone.parent:
                transform = bone.parent.matrix.inverted() @ transform
 
            loc, rot, _ = transform.decompose()

            xform = ModelTransform()
            xform.rotation = convert_rotation_space(rot)
            xform.translation = convert_vector_space(loc)

            #if frame % 10 == 0:
            #    print("\t{:10}: loc {:15} rot {:15}".format(bone.name, vec_to_str(xform.translation), quat_to_str(xform.rotation)))

            anim.bone_transforms[bone.name].append(xform)

    return anim
