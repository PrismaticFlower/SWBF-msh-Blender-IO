""" Gathers the Blender objects from the current scene and returns them as a list of
    Model objects. """

import bpy
import bmesh
import math
from enum import Enum
from typing import List, Set, Dict, Tuple
from itertools import zip_longest
from .msh_scene import Scene
from .msh_model import *
from .msh_model_utilities import *
from .msh_utilities import *
from .msh_model_gather import *



def extract_models(models, materials_map):

    model_map = {}

    for model in sort_by_parent(models):

        if model.model_type != ModelType.STATIC:
            new_obj = bpy.data.objects.new(model.name, None)
            new_obj.empty_display_size = 1
            new_obj.empty_display_type = 'PLAIN_AXES' 

        else:  
            new_mesh = bpy.data.meshes.new(model.name)
            verts = []
            faces = []
            offset = 0

            mat_name = ""

            for i,seg in enumerate(model.geometry):

                if i == 0:
                    mat_name = seg.material_name

                verts += [tuple(convert_vector_space(v)) for v in seg.positions]
                faces += [tuple([ind + offset for ind in tri]) for tri in seg.triangles]

                offset += len(seg.positions)

            new_mesh.from_pydata(verts, [], faces)
            new_mesh.update()
            new_mesh.validate()

            
            edit_mesh = bmesh.new()
            edit_mesh.from_mesh(new_mesh)

            uvlayer = edit_mesh.loops.layers.uv.verify()

            for edit_mesh_face in edit_mesh.faces:
                mesh_face = faces[edit_mesh_face.index]

                for i,loop in enumerate(edit_mesh_face.loops):
                    texcoord = seg.texcoords[mesh_face[i]]
                    loop[uvlayer].uv = tuple([texcoord.x, texcoord.y])

            edit_mesh.to_mesh(new_mesh)
            edit_mesh.free()  
                  

            new_obj = bpy.data.objects.new(new_mesh.name, new_mesh)

            '''
            Assign Materials - will do per segment later...
            '''

            if mat_name:
                material = materials_map[mat_name]

                if new_obj.data.materials:
                    new_obj.data.materials[0] = material
                else:
                    new_obj.data.materials.append(material)



        model_map[model.name] = new_obj

        if model.parent:
            new_obj.parent = model_map[model.parent]

        new_obj.location = convert_vector_space(model.transform.translation)
        new_obj.rotation_mode = "QUATERNION"
        new_obj.rotation_quaternion = convert_rotation_space(model.transform.rotation)

        bpy.context.collection.objects.link(new_obj)



def extract_materials(scene: Scene) -> Dict[str,bpy.types.Material]:

    extracted_materials = {}

    for material_name in scene.materials.keys():

        new_mat = bpy.data.materials.new(name=material_name)
        new_mat.use_nodes = True
        bsdf = new_mat.node_tree.nodes["Principled BSDF"]
        texImage = new_mat.node_tree.nodes.new('ShaderNodeTexImage')
        texImage.image = bpy.data.images.load("/Users/will/Desktop/grad.png")
        new_mat.node_tree.links.new(bsdf.inputs['Base Color'], texImage.outputs['Color'])

        extracted_materials[material_name] = new_mat

    return extracted_materials



def extract_scene(scene: Scene):

    matmap = extract_materials(scene)
    extract_models(scene.models, matmap)





