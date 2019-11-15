""" Utilities for operating on Material objects. """

from typing import Dict, List
from .msh_material import *
from .msh_model import *

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
