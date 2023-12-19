""" Converts msh meshes to Blender counterparts """


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


def validate_segment_geometry(segment : GeometrySegment):
    if not segment.positions:
        return False
    if not segment.triangles and not segment.triangle_strips and not segment.polygons:
        return False
    if not segment.material_name:
        return False
    if not segment.normals:
        return False
    return True


def get_shadow_geometry(model: Model):
    for segment in model.geometry:
        if segment.shadow_geometry is not None:
            return segment.shadow_geometry
    return None



# SHDW mesh info is of a different form from
# normal segment geometry
def model_to_shadow_mesh(model: Model, shadow_geometry : ShadowGeometry):
    blender_mesh = bpy.data.meshes.new(model.name)

    # As is the case with normal geometry processing,
    # these will contain flattened lists
    vertex_positions = [convert_vector_space(position) for position in shadow_geometry.positions]
    
    # Vertices
    blender_mesh.vertices.add(len(vertex_positions))
    blender_mesh.vertices.foreach_set("co", [component for vertex_position in vertex_positions for component in vertex_position])


    def faces_from_half_edges(half_edges : List[Tuple[int,int,int,int]]) -> List[List[int]]:
        faces = []
        visited_edges = [False] * len(half_edges)
        
        for i in range(len(half_edges)):

            if visited_edges[i]:
                continue

            curr_edge = half_edges[i]

            curr_index = curr_edge[0]
            starting_index = curr_index

            face_length = 0
            face_temp = [0] * 5

            while True:
                
                if face_length + 1> len(face_temp):
                    face_temp.append(curr_index)
                else:    
                    face_temp[face_length] = curr_index

                face_length += 1

                curr_edge = half_edges[curr_edge[1]]
                curr_index = curr_edge[0]
                
                if (curr_index == starting_index):
                    break

            #print(f"Added a face of length: {face_length}")
            faces.append(face_temp[0:face_length])

        return faces

    polygons = faces_from_half_edges(shadow_geometry.edges)

    # LOOPS 
    flat_indices = [index for polygon in polygons for index in polygon]
    blender_mesh.loops.add(len(flat_indices))

    # Position indices
    blender_mesh.loops.foreach_set("vertex_index", flat_indices)



    # POLYGONS/FACES
    blender_mesh.polygons.add(len(polygons))

    # Indices of starting loop for each polygon
    polygon_loop_start_indices = [0] * len(polygons)
    current_polygon_start_index = 0

    # Number of loops in this polygon.  Polygon i will use
    # loops from polygon_loop_start_indices[i] to 
    # polygon_loop_start_indices[i] + polygon_loop_totals[i]
    polygon_loop_totals = [0] * len(polygons)

    for i,polygon in enumerate(polygons):
        polygon_loop_start_indices[i] = current_polygon_start_index

        current_polygon_length = len(polygon)
        current_polygon_start_index += current_polygon_length

        polygon_loop_totals[i] = current_polygon_length

    blender_mesh.polygons.foreach_set("loop_start", polygon_loop_start_indices)
    blender_mesh.polygons.foreach_set("loop_total", polygon_loop_totals)

    blender_mesh.validate(clean_customdata=False) 
    blender_mesh.update()

    #sv_name = model.name if model.name.startswith("sv_") else "sv_" + model.name

    blender_mesh_object = bpy.data.objects.new(model.name, blender_mesh)

    return blender_mesh_object


def model_to_mesh(model: Model, scene: Scene, materials_map : Dict[str, bpy.types.Material]) -> bpy.types.Object:

    blender_mesh = bpy.data.meshes.new(model.name)

    # Per vertex data which will eventually be remapped to loops
    vertex_positions = []
    vertex_uvs = []
    vertex_normals = []
    vertex_colors = []

    # Keeps track of which vertices each group of weights affects
    # i.e. maps offset of vertices -> weights that affect them
    vertex_weights_offsets = {}

    # Since polygons in a msh segment index into the segment's verts,
    # we must keep an offset to index them into the verts of the whole mesh
    polygon_index_offset = 0

    # List of tuples of face indices
    polygons = []

    # Each polygon has an index into the mesh's material list
    current_material_index = 0
    polygon_material_indices = []


    if model.geometry:
        geometry_has_colors = any(segment.colors for segment in model.geometry)

        for segment in model.geometry:

            if not validate_segment_geometry(segment):
                continue

            blender_mesh.materials.append(materials_map[segment.material_name])

            vertex_positions += [tuple(convert_vector_space(p)) for p in segment.positions]

            if segment.texcoords:
                vertex_uvs += [tuple(texcoord) for texcoord in segment.texcoords]
            else:
                vertex_uvs += [(0.0,0.0) for _ in range(len(segment.positions))]

            if segment.normals:
                vertex_normals += [tuple(convert_vector_space(n)) for n in segment.normals]

            if segment.colors:
                vertex_colors.extend(segment.colors)
            elif geometry_has_colors:
                [vertex_colors.extend([0.0, 0.0, 0.0, 1.0]) for _ in range(len(segment.positions))]
            
            if segment.weights:
                vertex_weights_offsets[polygon_index_offset] = segment.weights


            segment_polygons = []

            if segment.triangles:
                segment_polygons = [tuple([ind + polygon_index_offset for ind in tri]) for tri in segment.triangles]
            elif segment.triangle_strips:
                winding = [0,1,2]
                rwinding = [1,0,2]
                for strip in segment.triangle_strips:
                    for i in range(len(strip) - 2):
                        strip_tri = tuple([polygon_index_offset + strip[i+j] for j in (winding if i % 2 == 0 else rwinding)])
                        segment_polygons.append(strip_tri)
            elif segment.polygons:
                segment_polygons = [tuple([ind + polygon_index_offset for ind in polygon]) for polygon in segment.polygons]

            polygon_index_offset += len(segment.positions)

            polygons += segment_polygons

            polygon_material_indices += [current_material_index for _ in segment_polygons]
            current_material_index += 1

        '''
        Start building the blender mesh
        '''

        # VERTICES

        # This is all we have to do for vertices, other attributes are done per-loop
        blender_mesh.vertices.add(len(vertex_positions))
        blender_mesh.vertices.foreach_set("co", [component for vertex_position in vertex_positions for component in vertex_position])

        # LOOPS 
        
        flat_indices = [index for polygon in polygons for index in polygon]

        blender_mesh.loops.add(len(flat_indices))

        # Position indices
        blender_mesh.loops.foreach_set("vertex_index", flat_indices)

        # Normals
        blender_mesh.create_normals_split()
        blender_mesh.loops.foreach_set("normal", [component for i in flat_indices for component in vertex_normals[i]])

        # UVs
        blender_mesh.uv_layers.new(do_init=False)
        blender_mesh.uv_layers[0].data.foreach_set("uv", [component for i in flat_indices for component in vertex_uvs[i]])

        # Colors
        if geometry_has_colors:
            blender_mesh.color_attributes.new("COLOR0", "FLOAT_COLOR", "POINT")
            blender_mesh.color_attributes[0].data.foreach_set("color", vertex_colors)


        # POLYGONS/FACES
        blender_mesh.polygons.add(len(polygons))

        # Indices of starting loop for each polygon
        polygon_loop_start_indices = [0] * len(polygons)
        current_polygon_start_index = 0

        # Number of loops in this polygon.  Polygon i will use
        # loops from polygon_loop_start_indices[i] to 
        # polygon_loop_start_indices[i] + polygon_loop_totals[i]
        polygon_loop_totals = [0] * len(polygons)

        for i,polygon in enumerate(polygons):
            polygon_loop_start_indices[i] = current_polygon_start_index

            current_polygon_length = len(polygon)
            current_polygon_start_index += current_polygon_length

            polygon_loop_totals[i] = current_polygon_length

        blender_mesh.polygons.foreach_set("loop_start", polygon_loop_start_indices)
        blender_mesh.polygons.foreach_set("loop_total", polygon_loop_totals)
        blender_mesh.polygons.foreach_set("material_index", polygon_material_indices)
        blender_mesh.polygons.foreach_set("use_smooth", [True for _ in polygons])

        blender_mesh.validate(clean_customdata=False) 
        blender_mesh.update()


        # Reset custom normals after calling update/validate
        reset_normals = [0.0] * (len(blender_mesh.loops) * 3)
        blender_mesh.loops.foreach_get("normal", reset_normals)
        blender_mesh.normals_split_custom_set(tuple(zip(*(iter(reset_normals),) * 3)))
        blender_mesh.use_auto_smooth = True


    blender_mesh_object = bpy.data.objects.new(model.name, blender_mesh)


    # VERTEX GROUPS

    vertex_groups_indicies = {}

    for offset in vertex_weights_offsets:
        for i, weight_set in enumerate(vertex_weights_offsets[offset]):
            for weight in weight_set:
                index = weight.bone

                if index not in vertex_groups_indicies:
                    model_name = scene.models[index].name
                    vertex_groups_indicies[index] = blender_mesh_object.vertex_groups.new(name=model_name)

                vertex_groups_indicies[index].add([offset + i], weight.weight, 'ADD')


    return blender_mesh_object





def model_to_mesh_object(model: Model, scene : Scene, materials_map : Dict[str, bpy.types.Material]) -> bpy.types.Object:
    
    shadow_geometry = get_shadow_geometry(model)
    if shadow_geometry is not None:
        return model_to_shadow_mesh(model, shadow_geometry)
    else:
        return model_to_mesh(model, scene, materials_map)


