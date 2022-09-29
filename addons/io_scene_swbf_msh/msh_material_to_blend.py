""" For finding textures and assigning MaterialProperties from entries in a Material """

import bpy
from typing import Dict
from .msh_material import *
from .msh_material_gather import *
from .msh_material_properties import *
from .msh_material_operators import *

from .msh_material_utilities import _REVERSE_RENDERTYPES_MAPPING

from math import sqrt

import os



def find_texture_path(folder_path : str, name : str) -> str:

    if not folder_path or not name:
        return ""

    possible_paths = [
        os.path.join(folder_path, name),
        os.path.join(folder_path, "PC", name),
        os.path.join(folder_path, "pc", name),
        os.path.join(folder_path, ".." , name),
    ]  

    for possible_path in possible_paths:
        if os.path.exists(possible_path):
            return possible_path

    return name



def swbf_material_to_blend(material_name : str, material : Material, folder_path : str) -> bpy.types.Material:

    new_mat = bpy.data.materials.new(name=material_name)
    
    fill_material_props(material, new_mat.swbf_msh_mat, folder_path)
    
    bpy.ops.swbf_msh.generate_material_nodes('EXEC_DEFAULT', material_name=new_mat.name, fail_silently=True) 

    return new_mat    



def fill_material_props(material, material_properties, folder_path):
    """ Fills MaterialProperties from Material instance """

    if material_properties is None or material is None:
        return

    material_properties.rendertype_value = material.rendertype.value

    material_properties.specular_color = (material.specular_color[0], material.specular_color[1], material.specular_color[2])
    
    _fill_material_props_rendertype(material, material_properties)
    _fill_material_props_flags(material, material_properties)
    _fill_material_props_data(material, material_properties)
    _fill_material_props_texture_maps(material, material_properties, folder_path)



def _fill_material_props_rendertype(material, material_properties):
    if material.rendertype in _REVERSE_RENDERTYPES_MAPPING:
        material_properties.rendertype = _REVERSE_RENDERTYPES_MAPPING[material.rendertype]
    else:
        material_properties.rendertype = "UNSUPPORTED"


def _fill_material_props_flags(material, material_properties):
    if material.rendertype == Rendertype.REFRACTION:
        material_properties.blended_transparency = True
        return

    flags = material.flags

    material_properties.blended_transparency = bool(flags & MaterialFlags.BLENDED_TRANSPARENCY)
    material_properties.additive_transparency = bool(flags & MaterialFlags.ADDITIVE_TRANSPARENCY)
    material_properties.hardedged_transparency = bool(flags & MaterialFlags.HARDEDGED_TRANSPARENCY)
    material_properties.unlit = bool(flags & MaterialFlags.UNLIT)
    material_properties.glow = bool(flags & MaterialFlags.GLOW)
    material_properties.perpixel = bool(flags & MaterialFlags.PERPIXEL)
    material_properties.specular = bool(flags & MaterialFlags.SPECULAR)
    material_properties.doublesided = bool(flags & MaterialFlags.DOUBLESIDED)


def _fill_material_props_data(material, material_properties):

    material_properties.data_value_0 = material.data[0]
    material_properties.data_value_1 = material.data[1]

    material_properties.scroll_speed_u = material.data[0]
    material_properties.scroll_speed_v = material.data[1]

    material_properties.blink_min_brightness = material.data[0]
    material_properties.blink_speed = material.data[1]

    material_properties.normal_map_tiling_u = material.data[0]
    material_properties.normal_map_tiling_v = material.data[1]

    anim_length_index = int(sqrt(material.data[0]))
    if anim_length_index < 0:
        anim_length_index = 0
    elif anim_length_index > len(UI_MATERIAL_ANIMATION_LENGTHS):
        anim_length_index = len(UI_MATERIAL_ANIMATION_LENGTHS) - 1

    material_properties.animation_length = UI_MATERIAL_ANIMATION_LENGTHS[anim_length_index][0]
    material_properties.animation_speed = material.data[1]

    material_properties.detail_map_tiling_u = material.data[0]
    material_properties.detail_map_tiling_v = material.data[1]


def _fill_material_props_texture_maps(material, material_properties, folder_path):

    t0path = find_texture_path(folder_path, material.texture0)        
    t1path = find_texture_path(folder_path, material.texture1)        
    t2path = find_texture_path(folder_path, material.texture2)        
    t3path = find_texture_path(folder_path, material.texture3)        

    material_properties.texture_0 = t0path
    material_properties.texture_1 = t1path
    material_properties.texture_2 = t2path
    material_properties.texture_3 = t3path

    material_properties.diffuse_map = t0path
    material_properties.distortion_map = t1path
    material_properties.normal_map = t1path
    material_properties.detail_map = t2path
    material_properties.environment_map = t3path


