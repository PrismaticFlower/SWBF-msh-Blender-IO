""" Contains Blender properties and UI for .msh materials. """

import bpy
from bpy.props import StringProperty, BoolProperty, EnumProperty, FloatVectorProperty, IntProperty
from bpy.types import PropertyGroup
from .msh_material_ui_strings import *
from .msh_model import *


class SkeletonProperties(PropertyGroup):
        name: StringProperty(name="Name", default="Bone Name")



class SkeletonPropertiesPanel(bpy.types.Panel):
    """ Creates a Panel in the Object properties window """
    bl_label = "SWBF Skeleton Properties"
    bl_idname = "SKELETON_PT_swbf_msh"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "data"
    bl_options = {'DEFAULT_CLOSED'}


    @classmethod
    def poll(cls, context):
        return context.object.type == 'ARMATURE' and context.object.data.swbf_msh_skel and len(context.object.data.swbf_msh_skel) > 0


    def draw(self, context):
        if context.object is None:
            return

        layout = self.layout

        skel_props = context.object.data.swbf_msh_skel

        layout.label(text = "Bones In MSH Skeleton: ")

        for prop in skel_props:
            layout.prop(prop, "name")

        