""" Contains Blender properties and UI for .msh materials. """

import bpy
from bpy.props import StringProperty, BoolProperty, EnumProperty, FloatVectorProperty, IntProperty
from bpy.types import PropertyGroup
from .msh_material_ui_strings import *
from .msh_model import *


class SkeletonProperties(PropertyGroup):
        name: StringProperty(name="Name", default="Bone Name")
        parent: StringProperty(name="Parent", default="Bone Parent")
        loc: FloatVectorProperty(name="Local Position", default=(0.0, 0.0, 0.0), subtype="XYZ", size=3)
        rot: FloatVectorProperty(name="Local Rotation", default=(0.0, 0.0, 0.0, 0.0), subtype="QUATERNION", size=4)





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
        return context.object.type == 'ARMATURE'


    def draw(self, context):
        if context.object is None:
            return

        layout = self.layout

        skel_props = context.object.data.swbf_msh_skel

        for prop in skel_props:
            layout.prop(prop, "name")
            layout.prop(prop, "parent")
            layout.prop(prop, "loc")
            layout.prop(prop, "rot")


            '''
            layout.prop(skel_props, "name")
            layout.prop(skel_props, "parent")
            layout.prop(skel_props, "loc")
            layout.prop(skel_props, "rot")
            '''


        #self.layout.label(text=context.object.swbf_msh_skel.yolo[1])
        