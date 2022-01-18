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

    # Placeholders to avoid crashes/import-export inconsistencies
    OTHER_1 = 1
    OTHER_2 = 2
    OTHER_4 = 4
    OTHER_5 = 5
    OTHER_8 = 8
    OTHER_9 = 9
    OTHER_10 = 10
    OTHER_11 = 11
    OTHER_12 = 12
    OTHER_13 = 13
    OTHER_14 = 14
    OTHER_15 = 15
    OTHER_16 = 16
    OTHER_17 = 17
    OTHER_18 = 18
    OTHER_19 = 19
    OTHER_20 = 20
    OTHER_21 = 21
    OTHER_23 = 23
    OTHER_28 = 28
    OTHER_30 = 30
    OTHER_31 = 31


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
    """ Data class representing a .msh material."""

    name: str = ""

    specular_color: Color = Color((1.0, 1.0, 1.0))
    rendertype: Rendertype = Rendertype.NORMAL
    flags: MaterialFlags = MaterialFlags.NONE
    data: Tuple[int, int] = (0, 0)

    texture0: str = "white.tga"
    texture1: str = ""
    texture2: str = ""
    texture3: str = ""
