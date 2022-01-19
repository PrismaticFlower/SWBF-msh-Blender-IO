""" IntProperty needed to keep track of Collision Primitives types that are imported without indicitive names.  
    Not sure I needed a PropertyGroup/what a leaner method would be.  The prims shouldn't be renamed on import because
    they are often referenced in ODFs.

    Don't see a reason these should be exposed via a panel or need to be changed..."""

import bpy
from bpy.props import IntProperty
from bpy.types import PropertyGroup


class CollisionPrimitiveProperties(PropertyGroup):
        prim_type: IntProperty(name="Primitive Type", default=-1)


        