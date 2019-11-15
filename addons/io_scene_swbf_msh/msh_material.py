""" Contains Material and dependent types for representing materials easilly
    saved to a .msh file. """

from dataclasses import dataclass
from typing import Tuple
from enum import Enum, Flag
from mathutils import Color

class Rendertype(Enum):
    # TODO: Add SWBF1 rendertypes.
    NORMAL = 0
    SCROLLING = 3
    ENVMAPPED = 6
    ANIMATED = 7
    REFRACTION = 22
    BLINK = 25
    NORMALMAPPED_TILED = 24
    NORMALMAPPED_ENVMAPPED = 26
    NORMALMAPPED = 27
    NORMALMAPPED_TILED_ENVMAP = 29

class MaterialFlags(Flag):
    NONE = 0
    UNLIT = 1
    GLOW = 2
    BLENDED_TRANSPARENCY = 4
    DOUBLESIDED = 8
    HARDEDGED_TRANSPARENCY = 16
    PERPIXEL = 32
    ADDITIVE_TRANSPARENCY = 64
    SPECULAR = 128

@dataclass
class Material:
    """ Data class representing a .msh material.
        Intended to be stored in a dictionary so name is missing. """

    specular_color: Color = Color((1.0, 1.0, 1.0))
    rendertype: Rendertype = Rendertype.NORMAL
    flags: MaterialFlags = MaterialFlags.NONE
    data: Tuple[int, int] = (0, 0)

    texture0: str = "white.tga"
    texture1: str = ""
    texture2: str = ""
    texture3: str = ""
