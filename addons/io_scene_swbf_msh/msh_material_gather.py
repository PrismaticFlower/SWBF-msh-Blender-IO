""" Gathers the Blender materials and returns them as a dictionary of
    strings and Material objects. """

import bpy
from typing import Dict
from .msh_material import *

def gather_materials() -> Dict[str, Material]:
    """ Gathers the Blender materials and returns them as
        a dictionary of strings and Material objects. """

    materials: Dict[str, Material] = {}

    for blender_material in bpy.data.materials:
        materials[blender_material.name] = read_material(blender_material)

    return materials

def read_material(blender_material: bpy.types.Material) -> Material:
    """ Reads a the swbf_msh properties from a Blender material and
        returns a Material object. """

    result = Material()

    if blender_material.swbf_msh is None:
        return result

    props = blender_material.swbf_msh

    result.specular_color = props.specular_color.copy()
    result.rendertype = _read_material_props_rendertype(props)
    result.flags = _read_material_props_flags(props)
    result.data = _read_material_props_data(props)
    result.texture0 = props.diffuse_map
    result.texture1 = _read_normal_map_or_distortion_map_texture(props)
    result.texture2 = _read_detail_texture(props)
    result.texture3 = _read_envmap_texture(props)

    return result

_RENDERTYPES_MAPPING = {
    "NORMAL_BF2": Rendertype.NORMAL,
    "SCROLLING_BF2": Rendertype.SCROLLING,
    "ENVMAPPED_BF2": Rendertype.ENVMAPPED,
    "ANIMATED_BF2": Rendertype.ANIMATED,
    "REFRACTION_BF2": Rendertype.REFRACTION,
    "BLINK_BF2": Rendertype.BLINK,
    "NORMALMAPPED_TILED_BF2": Rendertype.NORMALMAPPED_TILED,
    "NORMALMAPPED_ENVMAPPED_BF2": Rendertype.NORMALMAPPED_ENVMAPPED,
    "NORMALMAPPED_BF2": Rendertype.NORMALMAPPED,
    "NORMALMAPPED_TILED_ENVMAPPED_BF2": Rendertype.NORMALMAPPED_TILED_ENVMAP}

def _read_material_props_rendertype(props) -> Rendertype:
    return _RENDERTYPES_MAPPING[props.rendertype]

def _read_material_props_flags(props) -> MaterialFlags:
    flags = MaterialFlags.NONE

    if props.blended_transparency:
        flags |= MaterialFlags.BLENDED_TRANSPARENCY
    if props.additive_transparency:
        flags |= MaterialFlags.ADDITIVE_TRANSPARENCY
    if props.hardedged_transparency:
        flags |= MaterialFlags.HARDEDGED_TRANSPARENCY
    if props.unlit:
        flags |= MaterialFlags.UNLIT
    if props.glow:
        flags |= MaterialFlags.GLOW
    if props.perpixel:
        flags |= MaterialFlags.PERPIXEL
    if props.specular:
        flags |= MaterialFlags.SPECULAR
    if props.doublesided:
        flags |= MaterialFlags.DOUBLESIDED

    return flags

def _read_material_props_data(props) -> Tuple[int, int]:
    if "SCROLLING" in props.rendertype:
        return (props.scroll_speed_u, props.scroll_speed_v)
    if "BLINK" in props.rendertype:
        return (props.blink_min_brightness, props.blink_speed)
    if "NORMALMAPPED_TILED" in props.rendertype:
        return (props.normal_map_tiling_u, props.normal_map_tiling_v)
    if "REFRACTION" in props.rendertype:
        return (0, 0)
    if "ANIMATED" in props.rendertype:
        return (int(str(props.animation_length).split("_")[1]), props.animation_speed)

    return (props.detail_map_tiling_u, props.detail_map_tiling_v)

def _read_normal_map_or_distortion_map_texture(props) -> str:
    if "REFRACTION" in props.rendertype:
        return props.distortion_map
    if "NORMALMAPPED" in props.rendertype:
        return props.normal_map

    return ""

def _read_detail_texture(props) -> str:
    if "REFRACTION" in props.rendertype:
        return ""

    return props.detail_map

def _read_envmap_texture(props) -> str:
    if "ENVMAPPED" not in props.rendertype:
        return ""

    return props.environment_map
