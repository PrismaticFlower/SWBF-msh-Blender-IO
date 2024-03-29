"""
Script for reading zaabin/zaa files and applying the unmunged animation
to the currently selected armature.

As regards decompress_curves, I should really make a separate AnimationSet
dataclass instead of returning a convoluted nested dict.
"""

import os
import bpy
import re

from .chunked_file_reader import Reader
from .crc import *

from .msh_model import *
from .msh_model_utilities import *
from .msh_utilities import *

from typing import List, Set, Dict, Tuple


debug = False


                                      #anims  #bones   #components #keyframes: index,value
def decompress_curves(input_file) -> Dict[int, Dict[int, List[ Dict[int,float]]]]:

    global debug

    decompressed_anims: Dict[int, Dict[int, List[ Dict[int,float]]]] = {}

    with Reader(input_file, debug=debug) as head:

        # Dont read SMNA as child, since it has a length field always set to 0...
        head.skip_until("SMNA")
        head.skip_bytes(20)
        num_anims = head.read_u16()

        if debug:
            print("\nFile contains {} animations\n".format(num_anims))

        head.skip_bytes(2)

        anim_crcs = []
        anim_metadata = {}

        head.skip_until("MINA")

        # Read metadata (crc, num frames, num bones) for each anim
        with head.read_child() as mina:

            for i in range(num_anims):

                transBitFlags = mina.read_u32()
                mina.skip_bytes(4)

                anim_crc = mina.read_u32() 
                anim_crcs.append(anim_crc)

                anim_metadata[anim_crc] = {
                    "num_frames" : mina.read_u16(),
                    "num_bones" : mina.read_u16(),
                    "transBitFlags" : transBitFlags,
                }


        head.skip_until("TNJA")

        # Read TADA offsets and quantization parameters for each rot + loc component, for each bone, for each anim
        with head.read_child() as tnja:

            for i, anim_crc in enumerate(anim_crcs):

                bone_params = {}
                bone_list = []

                for _ in range(anim_metadata[anim_crc]["num_bones"]):

                    bone_crc = tnja.read_u32()

                    bone_list.append(bone_crc)              

                    bone_params[bone_crc] = {
                        "rot_offsets" : [tnja.read_u32() for _ in range(4)], # Offsets into TADA for rotation 
                        "loc_offsets" : [tnja.read_u32() for _ in range(3)], # and translation curves
                        "qparams"     : [tnja.read_f32() for _ in range(4)], # Translation quantization parameters, 3 biases, 1 multiplier
                    }

                anim_metadata[anim_crc]["bone_params"] = bone_params
                anim_metadata[anim_crc]["bone_list"] = bone_list

        head.skip_until("TADA")

        # Decompress/dequantize frame data into discrete per-component curves
        with head.read_child() as tada:

            for anim_crc in anim_crcs:

                decompressed_anims[anim_crc] = {}

                num_frames = anim_metadata[anim_crc]["num_frames"]
                num_bones = anim_metadata[anim_crc]["num_bones"]

                transBitFlags = anim_metadata[anim_crc]["transBitFlags"]

                if debug:
                    print("\n\tAnim hash: {} Num frames: {} Num joints: {}".format(hex(anim_crc), num_frames, num_bones))

                for bone_num, bone_crc in enumerate(anim_metadata[anim_crc]["bone_list"]):

                    bone_curves = []

                    params_bone = anim_metadata[anim_crc]["bone_params"][bone_crc]
                    
                    offsets_list = params_bone["rot_offsets"] + params_bone["loc_offsets"]
                    qparams = params_bone["qparams"]

                    if debug:
                        print("\n\t\tBone #{} hash: {}".format(bone_num,hex(bone_crc)))
                        print("\n\t\tQParams: {}, {}, {}, {}".format(*qparams))
                    
                    for o, start_offset in enumerate(offsets_list):
                        
                        # Init curve dict
                        curve : Dict[int,float] = {}

                        # Init accumulator
                        accumulator = 0.0


                        # 2047 = max val of signed 12 bit int, the (overwhelmingly) common compression amount.
                        # This is used for all rotation components in the file, with no offset
                        if o < 4:
                            mult = 1 / 2047
                            bias = 0.0

                        # Translations have specific quantization parameters; biases for each component and 
                        # a single multiplier for all three
                        else:

                            mult = qparams[-1]
                            bias = qparams[o - 4]

                            if debug:
                                print("\n\t\t\tBias = {}, multiplier = {}".format(bias, mult))

                        if debug:
                            print("\n\t\t\tOffset {}: {} ({}, {} remaining)".format(o,start_offset, tada.get_current_pos(), tada.how_much_left(tada.get_current_pos())))

                        # Skip to start of compressed data for component, as specified in TNJA
                        tada.skip_bytes(start_offset)
                        

                        j = 0
                        while (j < num_frames):
                            accumulator = bias + mult * tada.read_i16()
                            curve[j if j < num_frames else num_frames] = accumulator

                            if debug:
                                print("\t\t\t\t{}: {}".format(j, accumulator))

                            j+=1

                            while (j < num_frames):

                                control = tada.read_i8()

                                # Reset the accumulator to next dequantized i16
                                if control == -0x7f:
                                    if debug:
                                        print("\t\t\t\tControl: READING NEXT FRAME")
                                    break

                                # RLE: hold current accumulator for the next u8 frames 
                                elif control == -0x80:
                                    num_skips = tada.read_u8()
                                    if debug:
                                        print("\t\t\t\tControl: HOLDING FOR {} FRAMES".format(num_skips))
                                    j += num_skips

                                # If not a special value, increment accumulator by the dequantized i8
                                # The bias is NOT applied here, only for accumulator resets
                                else:
                                    accumulator += mult * float(control) 
                                    curve[j if j < num_frames else num_frames] = accumulator
                                    if debug:
                                        print("\t\t\t\t{}: {}".format(j, accumulator))
                                    j+=1 

                        curve[num_frames - 1] = accumulator                          

                        tada.reset_pos() 

                        bone_curves.append(curve)

                    decompressed_anims[anim_crc][bone_crc] = bone_curves

    return decompressed_anims


'''
Gets the animation names from the supplied
.anims file. Handy since .zaabin files often
share a dir with a .anims file.
'''

def read_anims_file(anims_file_path):

    if not os.path.exists(anims_file_path):
        return []

    with open(anims_file_path, 'r') as file:
        anims_text = file.read()

    splits = anims_text.split('"')

    if len(splits) > 1:
        return splits[1:-1:2]

    return []



'''
Unmunge the .zaa(bin) file and apply the resulting animation
to the currently selected armature object.

Contains some bloated code for calculating the world transforms of each bone,
for now this will work ONLY if the model was directly imported from a .msh file.
'''

def extract_and_apply_munged_anim(input_file_path):

    global debug

    with open(input_file_path,"rb") as input_file:
        animation_set = decompress_curves(input_file)

    anim_names = []
    if input_file_path.endswith(".zaabin"):
        anim_names = read_anims_file(input_file_path.replace(".zaabin", ".anims"))

    arma = bpy.context.view_layer.objects.active
    if arma.type != 'ARMATURE':
        raise Exception("Select an armature to attach the imported animation to!")
    
    if arma.animation_data is not None:
        arma.animation_data_clear()
    arma.animation_data_create()



    """
    When directly imported from .msh files,
    all skeleton models are saved as emptys, since
    some are excluded from the actual armature (effectors, roots, eg...).

    bond_bind_poses contains matrices for converting the transform of 
    bones found in .msh/.zaabin files to ones that'll fit the extracted armature.
    This will be replaced with the eventual importer release.
    """

    animated_bones = set()
    for anim_crc in animation_set:
        for bone_crc in animation_set[anim_crc]:
            animated_bones.add(bone_crc)


    bpy.context.view_layer.objects.active = arma
    bpy.ops.object.mode_set(mode='EDIT')

    bone_bind_poses = {}

    for edit_bone in arma.data.edit_bones:
        if to_crc(edit_bone.name) not in animated_bones:
            continue

        curr_ancestor = edit_bone.parent
        while curr_ancestor is not None and to_crc(curr_ancestor.name) not in animated_bones:
            curr_ancestor = curr_ancestor.parent

        if curr_ancestor:
            bind_mat = curr_ancestor.matrix.inverted() @ edit_bone.matrix 
        else:
            bind_mat = arma.matrix_local @ edit_bone.matrix

        bone_bind_poses[edit_bone.name] = bind_mat.inverted()

    bpy.ops.object.mode_set(mode='OBJECT')


    if debug:
        print("Extracting {} animations from {}:".format(len(animation_set), input_file_path))

    for anim_crc in animation_set:

        found_anim = [anim_name for anim_name in anim_names if to_crc(anim_name) == anim_crc]
        if found_anim:
            anim_str = found_anim[0]
        else:
            anim_str = str(hex(anim_crc)) 

        if debug:
            print("\tExtracting anim {}:".format(anim_str))


        #if anim_str in bpy.data.actions:
        #    bpy.data.actions[anim_str].use_fake_user = False
        #    bpy.data.actions.remove(bpy.data.actions[anim_str])

        action = bpy.data.actions.new(anim_str)
        action.use_fake_user = True

        animation = animation_set[anim_crc]

        bone_crcs_list = [bone_crc_ for bone_crc_ in animation]

        for bone_crc in sorted(bone_crcs_list):

            bone_name = next((bone.name for bone in arma.pose.bones if to_crc(bone.name) == bone_crc), None)

            if bone_name is None:
                continue

            bone = arma.pose.bones[bone_name]

            bone_crc = to_crc(bone.name)

            if bone_crc not in animation:
                continue;

            bind_mat = bone_bind_poses[bone.name]
            loc_data_path = "pose.bones[\"{}\"].location".format(bone.name) 
            rot_data_path = "pose.bones[\"{}\"].rotation_quaternion".format(bone.name) 

            bone_curves = animation[bone_crc]
            num_frames = max(bone_curves[0])

            has_translation = bone_curves[4] is not None

            if debug:
                print("\t\tBone {} has {} frames: ".format(bone_name, num_frames))

            last_values = [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]

            def get_quat(index):
                nonlocal bone_curves, last_values

                q = Quaternion()
                valmap = [1,2,3,0]

                has_key = False

                for i in range(4):
                    curve = bone_curves[i]
                    if index in curve:
                        has_key = True
                        last_values[i] = curve[index]
                    q[valmap[i]] = last_values[i]

                return q if has_key else None

            def get_vec(index):
                nonlocal bone_curves, last_values
                
                v = Vector()
                has_key = False

                for i in range(4,7):
                    curve = bone_curves[i]
                    if index in curve:
                        has_key = True
                        last_values[i] = curve[index]
                    v[i - 4] = last_values[i]

                return v if has_key else None

            fcurve_rot_w = action.fcurves.new(rot_data_path, index=0, action_group=bone.name)
            fcurve_rot_x = action.fcurves.new(rot_data_path, index=1, action_group=bone.name)
            fcurve_rot_y = action.fcurves.new(rot_data_path, index=2, action_group=bone.name)
            fcurve_rot_z = action.fcurves.new(rot_data_path, index=3, action_group=bone.name)

            if has_translation:
                fcurve_loc_x = action.fcurves.new(loc_data_path, index=0, action_group=bone.name)
                fcurve_loc_y = action.fcurves.new(loc_data_path, index=1, action_group=bone.name)
                fcurve_loc_z = action.fcurves.new(loc_data_path, index=2, action_group=bone.name)

            for frame in range(num_frames):

                q = get_quat(frame)
                if q is not None:

                    if debug:
                        print("\t\t\tRot key: ({}, {})".format(frame, quat_to_str(q)))

                    # Very bloated, but works for now
                    q = (bind_mat @ convert_rotation_space(q).to_matrix().to_4x4()).to_quaternion()
                    fcurve_rot_w.keyframe_points.insert(frame,q.w)
                    fcurve_rot_x.keyframe_points.insert(frame,q.x)
                    fcurve_rot_y.keyframe_points.insert(frame,q.y)
                    fcurve_rot_z.keyframe_points.insert(frame,q.z)

                if has_translation:
                    
                    t = get_vec(frame)
                    if t is not None:

                        if debug:
                            print("\t\t\tPos key: ({}, {})".format(frame, vec_to_str(t)))

                        t = (bind_mat @ Matrix.Translation(convert_vector_space(t))).translation

                        fcurve_loc_x.keyframe_points.insert(frame,t.x)
                        fcurve_loc_y.keyframe_points.insert(frame,t.y)
                        fcurve_loc_z.keyframe_points.insert(frame,t.z)

        arma.animation_data.action = action






       








