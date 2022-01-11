""" Gathers the Blender objects from the current scene and returns them as a list of
    Model objects. """

import bpy
import bmesh
import math
from enum import Enum
from typing import List, Set, Dict, Tuple
from itertools import zip_longest
from .msh_scene import Scene
from .msh_material_to_blend import *
from .msh_model import *
from .msh_model_utilities import *
from .msh_utilities import *
from .msh_model_gather import *
from .msh_skeleton_properties import *
from .crc import *

import os

# Extracts and applies anims in the scene to the currently selected armature
def extract_and_apply_anim(filename : str, scene : Scene):

    arma = bpy.context.view_layer.objects.active

    if arma.type != 'ARMATURE':
        raise Exception("Select an armature to attach the imported animation to!")

    if scene.animation is None:
        raise Exception("No animation found in msh file!")
    
    else:
        head, tail = os.path.split(filename)
        anim_name = tail.split(".")[0]
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






'''
Creates armature from the required nodes.  
Assumes the required_skeleton is already sorted by parent. 

Uses model_map to get the world matrix of each bone (hacky, see NOTE)
'''
def required_skeleton_to_armature(required_skeleton : List[Model], model_map : Dict[str, bpy.types.Object], msh_scene : Scene) -> bpy.types.Object:

    armature = bpy.data.armatures.new("skeleton")
    armature_obj = bpy.data.objects.new("skeleton", armature)
    bpy.context.view_layer.active_layer_collection.collection.objects.link(armature_obj)


    preserved = armature_obj.data.swbf_msh_skel
    for model in required_skeleton:
        if to_crc(model.name) in msh_scene.skeleton:
            entry = preserved.add()
            entry.name = model.name

    
    bones_set = set([model.name for model in required_skeleton])

    armature_obj.select_set(True)
    bpy.context.view_layer.objects.active = armature_obj
    bpy.ops.object.mode_set(mode='EDIT')

    for bone in required_skeleton:

        edit_bone = armature.edit_bones.new(bone.name)

        if bone.parent and bone.parent in bones_set:
            edit_bone.parent = armature.edit_bones[bone.parent]

        '''
        NOTE: I recall there being some rare issue with the get_world_matrix utility func.
        Never bothered to figure it out and referencing the bone object's world mat always works.
        Bone objects will be deleted later.
        '''
        bone_obj = model_map[bone.name]

        edit_bone.matrix = bone_obj.matrix_world
        edit_bone.tail = bone_obj.matrix_world @ Vector((0.0,1.0,0.0))

        bone_children = [b for b in get_model_children(bone, required_skeleton)]
        
        '''
        Perhaps we'll add an option for importing bones tip-to-tail, but that would 
        require preserving their original transforms as changing the tail position
        changes the bones' transform...
        '''
        tail_pos = Vector()
        if bone_children:
            for bone_child in bone_children:
                tail_pos += bone_obj.matrix_world.translation
            tail_pos = tail_pos / len(bone_children) 
            edit_bone.length = .5 #(tail_pos - edit_bone.head).magnitude
        else:
            bone_length = .5# edit_bone.parent.length if edit_bone.parent is not None else .5
            edit_bone.tail = bone_obj.matrix_world @ Vector((0.0,bone_length,0.0))

    bpy.ops.object.mode_set(mode='OBJECT')
    armature_obj.select_set(True)
    bpy.context.view_layer.update() 

    return armature_obj




'''
Ok, so this method is crucial.  What this does is: 
    1) Find all nodes that are weighted to by skinned segments.
    2) A node must be included in the armature if:
        - It is in SKL2 and is not the scene root
        - It is weighted to
        - It has a parent and child that must be in the armature
'''
def extract_required_skeleton(scene: Scene) -> List[Model]:

    # Will map Model names to Models in scene, for convenience
    model_dict : Dict[str, Model] = {}

    '''
    Will contain hashes of all models that definitely need to be in the skeleton/armature.
    We initialize it with the contents of SKL2 i.e. the nodes that are animated.
    For now this includes the scene root, but that'll be excluded later.
    '''
    skeleton_hashes = set(scene.skeleton)

    '''
    We also need to add all nodes that are weighted to.  These are not necessarily in
    SKL2, as SKL2 seems to only reference nodes that are keyframed.
    However, sometimes SKL2 is not included when it should be, but it can be mostly recovered
    by checking which models are BONEs.
    '''
    for model in scene.models:
        model_dict[model.name] = model

        #if to_crc(model.name) in scene.skeleton:
        print("Skel model {} of type {} has parent {}".format(model.name, model.model_type, model.parent))

        if model.model_type == ModelType.BONE:
            skeleton_hashes.add(to_crc(model.name))    

        elif model.geometry:
            for seg in model.geometry:
                if seg.weights:
                    for weight_set in seg.weights:
                        for weight in weight_set:
                            model_weighted_to = scene.models[weight.bone]

                            if to_crc(model_weighted_to.name) not in skeleton_hashes:
                                skeleton_hashes.add(to_crc(model_weighted_to.name))

    # The result of this function (to be sorted by parent)
    required_skeleton_models = []

    # Set of nodes to be included in required skeleton/were visited
    visited_nodes = set()

    '''
    Here we add all skeleton nodes (except root) and any necessary ancestors to the armature.
        - e.g. in bone_x/eff_x/eff_y, the effectors do not have to be in armature, as they are not ancestors of a bone
        - but  in bone_x/eff_x/eff_y/bone_y, they do.
    '''
    for bone in sort_by_parent(scene.models):

        # make sure we exclude the scene root and any nodes irrelevant to the armature
        if not bone.parent or to_crc(bone.name) not in skeleton_hashes:
            continue

        potential_bones = [bone]
        visited_nodes.add(bone.name)

        # Stacked transform will be needed if we decide to include an option for excluding effectors/roots
        #stacked_transform = model_transform_to_matrix(bone.transform)
        
        curr_ancestor = model_dict[bone.parent]

        while True:

            # If we hit a non-skin scene root, that means we just add the bone we started with, no ancestors.
            if not curr_ancestor.parent and curr_ancestor.model_type != ModelType.SKIN:
                required_skeleton_models.append(bone)
                visited_nodes.add(bone.name)
                break 

            # If we encounter another bone, a skin, or a previously visited object, we need to add the bone and its 
            # ancestors.
            elif to_crc(curr_ancestor.name) in scene.skeleton or curr_ancestor.model_type == ModelType.SKIN or curr_ancestor.name in visited_nodes:
                for potential_bone in potential_bones:
                    required_skeleton_models.append(potential_bone)
                    visited_nodes.add(potential_bone.name)
                break

            # Add ancestor to potential bones, update next ancestor
            else:
                if curr_ancestor.name not in visited_nodes:
                    potential_bones.insert(0, curr_ancestor)
                curr_ancestor = model_dict[curr_ancestor.parent]
                
                #stacked_transform = model_transform_to_matrix(curr_ancestor.transform) @ stacked_transform

    return required_skeleton_models              





# Create the msh hierachy.  Armatures are not created here.
def extract_models(scene: Scene, materials_map : Dict[str, bpy.types.Material]) -> Dict[str, bpy.types.Object]:

    # This will be filled with model names -> Blender objects and returned
    model_map : Dict[str, bpy.types.Object] = {}

    sorted_models : List[Model] = sort_by_parent(scene.models)

    for model in sorted_models:
        new_obj = None

        if model.model_type == ModelType.STATIC or model.model_type == ModelType.SKIN:  

            new_mesh = bpy.data.meshes.new(model.name)
            verts = []
            faces = []
            offset = 0

            mat_name = ""

            full_texcoords = []

            weights_offsets = {}

            if model.geometry:
                for i,seg in enumerate(model.geometry):

                    if i == 0:
                        mat_name = seg.material_name

                    verts += [tuple(convert_vector_space(v)) for v in seg.positions]

                    if seg.weights:
                        weights_offsets[offset] = seg.weights

                    if seg.texcoords is not None:
                        full_texcoords += seg.texcoords
                    else:
                        full_texcoords += [(0.0,0.0) for _ in range(len(seg.positions))]

                    if seg.triangles:
                        faces += [tuple([ind + offset for ind in tri]) for tri in seg.triangles]
                    else:
                        for strip in seg.triangle_strips:
                            for i in range(len(strip) - 2):
                                face = tuple([offset + strip[j] for j in range(i,i+3)])
                                faces.append(face)

                    offset += len(seg.positions)

            new_mesh.from_pydata(verts, [], faces)
            new_mesh.update()
            new_mesh.validate()

            
            if full_texcoords:

                edit_mesh = bmesh.new()
                edit_mesh.from_mesh(new_mesh)

                uvlayer = edit_mesh.loops.layers.uv.verify()

                for edit_mesh_face in edit_mesh.faces:
                    mesh_face = faces[edit_mesh_face.index]

                    for i,loop in enumerate(edit_mesh_face.loops):

                        texcoord = full_texcoords[mesh_face[i]]
                        loop[uvlayer].uv = tuple([texcoord.x, texcoord.y])

                edit_mesh.to_mesh(new_mesh)
                edit_mesh.free() 
            
            new_obj = bpy.data.objects.new(new_mesh.name, new_mesh)


            vertex_groups_indicies = {}

            for offset in weights_offsets:
                for i, weight_set in enumerate(weights_offsets[offset]):
                    for weight in weight_set:
                        index = weight.bone

                        if index not in vertex_groups_indicies:
                            model_name = scene.models[index].name
                            #print("Adding new vertex group with index {}  and model name {}".format(index, model_name))
                            vertex_groups_indicies[index] = new_obj.vertex_groups.new(name=model_name)

                        vertex_groups_indicies[index].add([offset + i], weight.weight, 'ADD')

            '''
            Assign Materials - will do per segment later...
            '''
            if mat_name:
                material = materials_map[mat_name]

                if new_obj.data.materials:
                    new_obj.data.materials[0] = material
                else:
                    new_obj.data.materials.append(material)
        
        else:

            new_obj = bpy.data.objects.new(model.name, None)
            new_obj.empty_display_size = 1
            new_obj.empty_display_type = 'PLAIN_AXES' 


        model_map[model.name] = new_obj

        if model.parent:
            new_obj.parent = model_map[model.parent]

        new_obj.location = convert_vector_space(model.transform.translation)
        new_obj.rotation_mode = "QUATERNION"
        new_obj.rotation_quaternion = convert_rotation_space(model.transform.rotation)

        bpy.context.collection.objects.link(new_obj)


    return model_map


# TODO: Add to custom material info struct, maybe some material conversion/import?
def extract_materials(folder_path: str, scene: Scene) -> Dict[str, bpy.types.Material]:

    extracted_materials : Dict[str, bpy.types.Material] = {}

    for material_name, material in scene.materials.items():

        new_mat = bpy.data.materials.new(name=material_name)
        new_mat.use_nodes = True
        bsdf = new_mat.node_tree.nodes["Principled BSDF"]

        diffuse_texture_path = find_texture_path(folder_path, material.texture0)

        if diffuse_texture_path:
            texImage = new_mat.node_tree.nodes.new('ShaderNodeTexImage')
            texImage.image = bpy.data.images.load(diffuse_texture_path)
            new_mat.node_tree.links.new(bsdf.inputs['Base Color'], texImage.outputs['Color'])  

        fill_material_props(material, new_mat.swbf_msh)      

        extracted_materials[material_name] = new_mat

    return extracted_materials



def extract_scene(filepath: str, scene: Scene):

    folder = os.path.join(os.path.dirname(filepath),"")

    # material_map mapes Material names to Blender materials
    material_map = extract_materials(folder, scene)

    # model_map maps Model names to Blender objects.
    model_map = extract_models(scene, material_map)


    # skel contains all models needed in an armature
    skel = extract_required_skeleton(scene)

    # Create the armature if skel is non-empty
    armature = None if not skel else required_skeleton_to_armature(skel, model_map, scene)


    '''
    If an armature was created, we need to do a few extra 
    things to ensure the import makes sense in Blender.  It can
    get a bit messy, as XSI + SWBF have very loose requirements  
    when it comes to skin-skeleton parentage.

    If not, we're good.
    '''
    if armature is not None:

        has_skin = False

        # Handle armature related parenting
        for curr_model in scene.models:

            curr_obj = model_map[curr_model.name]
            
            # Parent all skins to armature
            if curr_model.model_type == ModelType.SKIN:

                has_skin = True

                curr_obj.parent = armature
                curr_obj.parent_type = 'ARMATURE'

            # Parent the object to a bone if necessary
            else:
                if curr_model.parent in armature.data.bones and curr_model.name not in armature.data.bones:
                    # Not sure what the different mats do, but saving the worldmat and 
                    # applying it after clearing the other mats yields correct results...
                    worldmat = curr_obj.matrix_world

                    curr_obj.parent = armature
                    curr_obj.parent_type = 'BONE'
                    curr_obj.parent_bone = curr_model.parent
                    # ''
                    curr_obj.matrix_basis = Matrix()
                    curr_obj.matrix_parent_inverse = Matrix()
                    curr_obj.matrix_world = worldmat

        '''
        Sometimes skins are parented to other skins.  We need to find the skin highest in the hierarchy and
        parent all skins to its parent (armature_reparent_obj).

        If not skin exists, we just reparent the armature to the parent of the highest node in the skeleton
        '''
        armature_reparent_obj = None
        if has_skin:
            for model in sort_by_parent(scene.models):
                if model.model_type == ModelType.SKIN:
                    armature_reparent_obj = None if not model.parent else model_map[model.parent]
        else:
            skeleton_parent_name = skel[0].parent
            for model in scene.models:
                if model.name == skeleton_parent_name:
                    armature_reparent_obj = None if not skeleton_parent_name else model_map[skeleton_parent_name]

        # Now we reparent the armature to the node (armature_reparent_obj) we just found
        if armature_reparent_obj is not None and armature.name != armature_reparent_obj.name:
            armature.parent = armature_reparent_obj


        # If an bone exists in the armature, delete its 
        # object counterpart (as created in extract_models)
        for bone in skel:
            model_to_remove = model_map[bone.name]
            if model_to_remove:
                bpy.data.objects.remove(model_to_remove, do_unlink=True)
                model_map.pop(bone.name)
    

    # Lastly, hide all that is hidden in the msh scene
    for model in scene.models:
        if model.name in model_map:
            obj = model_map[model.name]
            if get_is_model_hidden(obj) and len(obj.children) == 0:
                obj.hide_set(True)
