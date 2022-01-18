""" Keeps track of exact skeleton when imported.  Possibly needed for exporting skeleton-compatible animations.  Will
    probably be needed (with a matrix property) if we:
        - add tip-to-tail adjustment and/or omit roots/effectors for imported skeletons to keep track of the original bone transforms
        - add some sort of basepose-adjustment animation import option for already imported skeletons

    I guess this might not need a panel, but I included it because the docs might need to reference it and 
    people may want to exclude certain bones without deleting keyframes.
"""

import bpy
from bpy.props import StringProperty
from bpy.types import PropertyGroup


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

        