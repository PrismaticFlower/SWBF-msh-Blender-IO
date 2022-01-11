""" For finding textures and assigning material properties from entries in a Material """

import bpy
from typing import Dict
from .msh_material import *
from .msh_material_gather import *
from .msh_material_properties import *

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

    return ""



def fill_material_props(material : Material, material_properties):
    """ Fills MaterialProperties from Material instance """

    if material_properties is None or material is None:
        return

    material_properties.specular_color = (material.specular_color[0], material.specular_color[1], material.specular_color[2])
    material_properties.diffuse_map = material.texture0
    
    _fill_material_props_rendertype(material, material_properties)
    _fill_material_props_flags(material, material_properties)
    _fill_material_props_data(material, material_properties)
    
    _fill_normal_map_or_distortion_map_texture(material, material_properties)
    _fill_detail_texture(material, material_properties)
    _fill_envmap_texture(material, material_properties)



def _fill_material_props_rendertype(material, material_properties):

    _REVERSE_RENDERTYPES_MAPPING = {
        Rendertype.NORMAL : "NORMAL_BF2",
        Rendertype.SCROLLING : "SCROLLING_BF2",
        Rendertype.ENVMAPPED : "ENVMAPPED_BF2",
        Rendertype.ANIMATED : "ANIMATED_BF2",
        Rendertype.REFRACTION : "REFRACTION_BF2",
        Rendertype.BLINK : "BLINK_BF2",
        Rendertype.NORMALMAPPED_TILED : "NORMALMAPPED_TILED_BF2",
        Rendertype.NORMALMAPPED_ENVMAPPED : "NORMALMAPPED_ENVMAPPED_BF2",
        Rendertype.NORMALMAPPED : "NORMALMAPPED_BF2",
        Rendertype.NORMALMAPPED_TILED_ENVMAP : "NORMALMAPPED_TILED_ENVMAPPED_BF2"}

    material_properties.rendertype = _REVERSE_RENDERTYPES_MAPPING[material.rendertype]



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
    if material.rendertype == Rendertype.SCROLLING:
        material_properties.scroll_speed_u = material.data[0]
        material_properties.scroll_speed_v = material.data[1]
    
    elif material.rendertype == Rendertype.BLINK:
        material_properties.blink_min_brightness = material.data[0]
        material_properties.blink_speed = material.data[1]
    
    elif material.rendertype == Rendertype.NORMALMAPPED_TILED_ENVMAP or material.rendertype == Rendertype.NORMALMAPPED_TILED:
        material_properties.normal_map_tiling_u = material.data[0]
        material_properties.normal_map_tiling_v = material.data[1]
    
    elif material.rendertype == Rendertype.REFRACTION:
        pass
    
    elif material.rendertype == Rendertype.ANIMATED:

        anim_length_index = int(sqrt(length)) - 1
        if animation_length_index < 0:
            animation_length_index = 0
        elif animation_length_index > len(UI_MATERIAL_ANIMATION_LENGTHS):
            animation_length_index = len(UI_MATERIAL_ANIMATION_LENGTHS) - 1

        material_properties.animation_length = UI_MATERIAL_ANIMATION_LENGTHS[animation_length_index]
        material_properties.animation_speed = material.data[1]
    
    else:
        material_properties.detail_map_tiling_u = material.data[0]
        material_properties.detail_map_tiling_v = material.data[1]


def _fill_normal_map_or_distortion_map_texture(material, material_properties):
    if material.rendertype == Rendertype.REFRACTION:
        material_properties.distortion_map = material.texture1
    elif material.rendertype.value > 24:
        material_properties.normal_map = material.texture1


def _fill_detail_texture(material, material_properties):
    if material.rendertype != Rendertype.REFRACTION:
        material_properties.detail_map = material.texture2


def _fill_envmap_texture(material, material_properties):
    if material.rendertype != Rendertype.ENVMAPPED:
        material_properties.environment_map = material.texture3
