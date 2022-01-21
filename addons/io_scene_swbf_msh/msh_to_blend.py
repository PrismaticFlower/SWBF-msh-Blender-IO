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
from .msh_model_gather import get_is_model_hidden


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





# Create the msh hierachy.  Armatures are not created here.  Much of this could use some optimization...

# TODO: Replace with an approach informed by existing Blender addons (io_scene_obj e.g.) 
def extract_models(scene: Scene, materials_map : Dict[str, bpy.types.Material]) -> Dict[str, bpy.types.Object]:

    # This will be filled with model names -> Blender objects and returned
    model_map : Dict[str, bpy.types.Object] = {}

    sorted_models : List[Model] = sort_by_parent(scene.models)

    for model in sorted_models:
        new_obj = None


        if model.model_type == ModelType.STATIC or model.model_type == ModelType.SKIN or model.model_type == ModelType.SHADOWVOLUME:  

            new_mesh = bpy.data.meshes.new(model.name)
            verts = []
            faces = []
            offset = 0

            full_texcoords = []

            weights_offsets = {}

            face_range_to_material_index = []

            materials_to_use = []
            segment_index = 0

            if model.geometry:

                def validate_segment(segment : GeometrySegment):
                    if not segment.positions:
                        return False
                    if not segment.triangles and not segment.triangle_strips and not segment.polygons:
                        return False
                    if not segment.material_name:
                        return False
                    return True


                for seg in model.geometry:

                    if not validate_segment(seg):
                        continue

                    verts += [tuple(convert_vector_space(v)) for v in seg.positions]

                    materials_to_use.append(seg.material_name)

                    if seg.weights:
                        weights_offsets[offset] = seg.weights

                    if seg.texcoords:
                        full_texcoords += seg.texcoords
                    else:
                        full_texcoords += [(0.0,0.0) for _ in range(len(seg.positions))]

                    face_range_lower = len(faces)

                    if seg.triangles:
                        faces += [tuple([ind + offset for ind in tri]) for tri in seg.triangles]
                    elif seg.triangle_strips:
                        for strip in seg.triangle_strips:
                            for i in range(len(strip) - 2):
                                face = tuple([offset + strip[j] for j in range(i,i+3)])
                                faces.append(face)
                    elif seg.polygons:
                        faces += [tuple([ind + offset for ind in polygon]) for polygon in seg.polygons]


                    face_range_upper = len(faces)
                    face_range_to_material_index.append((face_range_lower, face_range_upper, segment_index))

                    offset += len(seg.positions)

                    segment_index += 1

            new_mesh.from_pydata(verts, [], faces)
            new_mesh.update()
            new_mesh.validate()


            # If tex coords are present, add material and UV data
            if full_texcoords:

                edit_mesh = bmesh.new()
                edit_mesh.from_mesh(new_mesh)

                uvlayer = edit_mesh.loops.layers.uv.verify()

                for edit_mesh_face in edit_mesh.faces:
                    face_index = edit_mesh_face.index
                    mesh_face = faces[face_index]

                    for frL, frU, ind in face_range_to_material_index:
                        if face_index >= frL and face_index < frU:
                            edit_mesh_face.material_index = ind

                    for i,loop in enumerate(edit_mesh_face.loops):
                        texcoord = full_texcoords[mesh_face[i]]
                        loop[uvlayer].uv = tuple([texcoord[0], texcoord[1]])

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
                            vertex_groups_indicies[index] = new_obj.vertex_groups.new(name=model_name)

                        vertex_groups_indicies[index].add([offset + i], weight.weight, 'ADD')


            '''
            Assign Material slots
            '''
            for material_name in materials_to_use:
                material = materials_map[material_name]
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

        if model.collisionprimitive is not None:
            new_obj.swbf_msh_coll_prim.prim_type = model.collisionprimitive.shape.value

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

        fill_material_props(material, new_mat.swbf_msh_mat)      

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

    if armature is not None:
        preserved_skel = armature.data.swbf_msh_skel
        for model in scene.models:
            if to_crc(model.name) in scene.skeleton or model.model_type == ModelType.BONE:
                entry = preserved_skel.add()
                entry.name = model.name


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
