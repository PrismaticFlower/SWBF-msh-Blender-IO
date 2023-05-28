""" Gathers the Blender objects from the current scene and returns them as a list of
    Model objects. """

import bpy
import bmesh
import math

from enum import Enum
from typing import List, Set, Dict, Tuple

from .msh_scene import Scene
from .msh_material_to_blend import *
from .msh_model import *
from .msh_skeleton_utilities import *
from .msh_skeleton_to_blend import *
from .msh_model_gather import get_is_model_hidden
from .msh_mesh_to_blend import model_to_mesh_object


from .crc import *

import os


# Extracts and applies anims in the scene to the currently selected armature
def extract_and_apply_anim(filename : str, scene : Scene):

    arma = bpy.context.view_layer.objects.active

    if not arma or arma.type != 'ARMATURE':
        raise Exception("Select an armature to attach the imported animation to!")

    if scene.animation is None:
        raise Exception("No animation found in msh file!")
    else:
        head, tail = os.path.split(filename)
        anim_name = tail.split(".")[0]

        if anim_name in bpy.data.actions:
            bpy.data.actions.remove(bpy.data.actions[anim_name], do_unlink=True)

            for nt in arma.animation_data.nla_tracks:
                if anim_name == nt.strips[0].name:
                    arma.animation_data.nla_tracks.remove(nt)


        action = bpy.data.actions.new(anim_name)
        action.use_fake_user = True

        if not arma.animation_data:
            arma.animation_data_create()


        # Record the starting transforms of each bone.  Pose space is relative
        # to bones starting transforms.  Starting = in edit mode
        bone_bind_poses = {}

        bpy.context.view_layer.objects.active = arma
        bpy.ops.object.mode_set(mode='EDIT')

        for edit_bone in arma.data.edit_bones:
            if edit_bone.parent:
                bone_local = edit_bone.parent.matrix.inverted() @ edit_bone.matrix
            else:
                bone_local = arma.matrix_local @ edit_bone.matrix

            bone_bind_poses[edit_bone.name] = bone_local.inverted()

        bpy.ops.object.mode_set(mode='OBJECT')


        for bone in arma.pose.bones:
            if to_crc(bone.name) in scene.animation.bone_frames:

                bind_mat = bone_bind_poses[bone.name]

                translation_frames, rotation_frames = scene.animation.bone_frames[to_crc(bone.name)]

                loc_data_path = "pose.bones[\"{}\"].location".format(bone.name)
                rot_data_path = "pose.bones[\"{}\"].rotation_quaternion".format(bone.name)


                fcurve_rot_w = action.fcurves.new(rot_data_path, index=0, action_group=bone.name)
                fcurve_rot_x = action.fcurves.new(rot_data_path, index=1, action_group=bone.name)
                fcurve_rot_y = action.fcurves.new(rot_data_path, index=2, action_group=bone.name)
                fcurve_rot_z = action.fcurves.new(rot_data_path, index=3, action_group=bone.name)

                for frame in rotation_frames:
                    i = frame.index
                    q = (bind_mat @ convert_rotation_space(frame.rotation).to_matrix().to_4x4()).to_quaternion()

                    fcurve_rot_w.keyframe_points.insert(i,q.w)
                    fcurve_rot_x.keyframe_points.insert(i,q.x)
                    fcurve_rot_y.keyframe_points.insert(i,q.y)
                    fcurve_rot_z.keyframe_points.insert(i,q.z)

                fcurve_loc_x = action.fcurves.new(loc_data_path, index=0, action_group=bone.name)
                fcurve_loc_y = action.fcurves.new(loc_data_path, index=1, action_group=bone.name)
                fcurve_loc_z = action.fcurves.new(loc_data_path, index=2, action_group=bone.name)

                for frame in translation_frames:
                    i = frame.index
                    t = (bind_mat @ Matrix.Translation(convert_vector_space(frame.translation))).translation

                    fcurve_loc_x.keyframe_points.insert(i,t.x)
                    fcurve_loc_y.keyframe_points.insert(i,t.y)
                    fcurve_loc_z.keyframe_points.insert(i,t.z)

        arma.animation_data.action = action
        track = arma.animation_data.nla_tracks.new()
        track.strips.new(action.name, action.frame_range[0], action)
