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

from .crc import to_crc




def extract_anim(armature: bpy.types.Armature, root_name: str) -> Animation:

    action = armature.animation_data.action

    # Set of bones to include in SKL2/animation stuff
    keyable_bones : Set[str] = set()
    
    msh_skel = armature.data.swbf_msh_skel

    has_preserved_skel = len(msh_skel) > 0

    if has_preserved_skel:
        for bone in msh_skel:
            #print("Adding {} from preserved skel to exported skeleton".format(bone.name))
            keyable_bones.add(bone.name)
    elif action:
        for group in action.groups:
            #print("Adding {} from action groups to exported skeleton".format(group.name))
            keyable_bones.add(group.name)


    anim = Animation();

    root_crc = to_crc(root_name)

    if not action:
        framerange = Vector((0.0,1.0))
    else:
        framerange = action.frame_range
    
    num_frames = math.floor(framerange.y - framerange.x) + 1
    increment  = (framerange.y - framerange.x) / (num_frames - 1)

    anim.end_index = num_frames - 1
    
    anim.bone_frames[root_crc] = ([], [])
    for bone in armature.data.bones:
        if bone.name in keyable_bones:
            anim.bone_frames[to_crc(bone.name)] = ([], [])

    for frame in range(num_frames):
        
        frame_time = framerange.x + frame * increment
        bpy.context.scene.frame_set(frame_time)


        rframe_dummy = RotationFrame(frame, convert_rotation_space(Quaternion()))
        tframe_dummy = TranslationFrame(frame, Vector((0.0,0.0,0.0)))

        anim.bone_frames[root_crc][0].append(tframe_dummy)
        anim.bone_frames[root_crc][1].append(rframe_dummy)


        for bone in armature.pose.bones:

            if bone.name not in keyable_bones:
                continue

            transform = bone.matrix

            if bone.parent:
                transform = bone.parent.matrix.inverted() @ transform
 
            loc, rot, _ = transform.decompose()

            rframe = RotationFrame(frame, convert_rotation_space(rot))
            tframe = TranslationFrame(frame, convert_vector_space(loc))

            anim.bone_frames[to_crc(bone.name)][0].append(tframe)
            anim.bone_frames[to_crc(bone.name)][1].append(rframe)


    return anim
