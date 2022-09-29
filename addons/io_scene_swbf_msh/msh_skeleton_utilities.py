""" Helpers for SWBF skeleton-armature mapping """

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



def has_preserved_skeleton(armature : bpy.types.Armature):
    return len(armature.data.swbf_msh_skel) > 0



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
            #print(f"{bone.name} is a real BONE")
            real_bones.add(bone.name)
    elif action:
        for group in armature.animation_data.action.groups:
            #print(f"{group.name} is a real BONE")
            real_bones.add(group.name)
    else:
        for bone in armature.data.bones:
            #print(f"{bone.name} is a real BONE")
            real_bones.add(bone.name)

    return real_bones





'''
Creates armature from the required nodes.  
Assumes the required_skeleton is already sorted by parent. 

Uses model_map to get the world matrix of each bone (hacky, see NOTE)
'''
def required_skeleton_to_armature(required_skeleton : List[Model], model_map : Dict[str, bpy.types.Object], msh_scene : Scene) -> bpy.types.Object:

    armature = bpy.data.armatures.new("skeleton")
    armature_obj = bpy.data.objects.new("skeleton", armature)
    armature_obj.matrix_world = Matrix.Identity(4)
    bpy.context.view_layer.active_layer_collection.collection.objects.link(armature_obj)

 
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

        # TODO: This will lead to mistranslated bones when armature is reparented!
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
    2) A node must be included in the armature if it:
        - is in SKL2 and is not the scene root
        - has model_type == BONE
        - is weighted to
        - has a parent and child that must be in the armature

This may need a lot of adjustments, don't think I can prove it's validity but it has worked very well
and handles all stock + ZETools + Pandemic XSI exporter models I've tested 
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

        # Stacked transform will be needed if we decide to include an option for excluding effectors/roots or 
        # connecting bones tip-to-tail
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

