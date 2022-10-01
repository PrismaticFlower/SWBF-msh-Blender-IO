""" Utilities for operating on Material objects. """

from typing import Dict, List
from .msh_material import *
from .msh_model import *


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


_REVERSE_RENDERTYPES_MAPPING = {val: key for (key, val) in _RENDERTYPES_MAPPING.items()}


def remove_unused_materials(materials: Dict[str, Material], 
                            models: List[Model]) -> Dict[str, Material]:
    """ Given a dictionary of materials and a list of models
        returns a dictionary containing only the materials that are used. """

    filtered_materials: Dict[str, Material] = {}

    for model in models:
        if model.geometry is None:
            continue

        for segment in model.geometry:
            if not segment.material_name:
                continue

            filtered_materials[segment.material_name] = materials[segment.material_name]

    return filtered_materials
