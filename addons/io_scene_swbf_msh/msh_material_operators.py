""" Operators for basic emulation and mapping of SWBF material system in Blender.
    Only relevant if the builtin Eevee renderer is being used! """

import bpy

from .msh_material_properties import *

from math import sqrt

from bpy.props import BoolProperty, EnumProperty, StringProperty
from bpy.types import Operator, Menu



# FillSWBFMaterialProperties

# Iterates through all material slots of all selected
# objects and fills basic SWBF material properties
# from any Principled BSDF nodes it finds.


class FillSWBFMaterialProperties(bpy.types.Operator):
    bl_idname = "swbf_msh.fill_mat_props"
    bl_label = "Fill SWBF Material Properties"
    bl_description = ("Fill in SWBF properties of all materials used by selected objects.\n"
                "Only considers materials that use nodes.\n" 
                "Please see 'Materials > Materials Operators' in the docs for more details.")

    def execute(self, context):

        slots = sum([list(ob.material_slots) for ob in bpy.context.selected_objects if ob.type == 'MESH'],[])
        mats = [slot.material for slot in slots if (slot.material and slot.material.node_tree)]

        for mat in mats:
            try:
                for BSDF_node in [n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED']:
                    base_col = BSDF_node.inputs['Base Color'] 

                    for link in base_col.links :
                        link_node = link.from_node

                        if link_node.type != 'TEX_IMAGE':
                            continue

                        tex_name = link_node.image.name

                        i = tex_name.find(".tga")
                        
                        # Get rid of trailing number in case one is present
                        if i > 0:
                            tex_name = tex_name[0:i+4]

                        mat.swbf_msh_mat.rendertype = 'NORMAL_BF2'
                        mat.swbf_msh_mat.diffuse_map = tex_name 
                        break 
            except:
                # Many chances for null ref exceptions. None if user reads doc section...
                pass  

        return {'FINISHED'}


class VIEW3D_MT_SWBF(bpy.types.Menu):
    bl_label = "SWBF"

    def draw(self, _context):
        layout = self.layout
        layout.operator("swbf_msh.fill_mat_props", text="Fill SWBF Material Properties")


def draw_matfill_menu(self, context):
    layout = self.layout
    layout.separator()
    layout.menu("VIEW3D_MT_SWBF")




# GenerateMaterialNodesFromSWBFProperties

# Creates shader nodes to emulate SWBF material properties.
# Will probably only support for a narrow subset of properties...

class GenerateMaterialNodesFromSWBFProperties(bpy.types.Operator):
    
    bl_idname = "swbf_msh.generate_material_nodes"
    bl_label = "Generate Nodes"
    bl_description= """Generate Cycles shader nodes from SWBF material properties.

The nodes generated are meant to give one a general idea
of how the material would look ingame.  They cannot 
to provide an exact emulation"""

    
    material_name: StringProperty(
        name = "Material Name", 
        description = "Name of material whose SWBF properties the generated nodes will emulate."
    )
    

    def execute(self, context):

        material = bpy.data.materials[self.material_name]


        if material and material.swbf_msh_mat:

            material.use_nodes = True
            mat_props = material.swbf_msh_mat

            material.node_tree.nodes.clear()

            bsdf = material.node_tree.nodes.new("ShaderNodeBsdfPrincipled")

            diffuse_texture_path = mat_props.diffuse_map
            if diffuse_texture_path:
                texImage = material.node_tree.nodes.new('ShaderNodeTexImage')
                texImage.image = bpy.data.images.load(diffuse_texture_path)
                texImage.image.alpha_mode = 'CHANNEL_PACKED'
                material.node_tree.links.new(bsdf.inputs['Base Color'], texImage.outputs['Color']) 

                bsdf.inputs["Roughness"].default_value = 1.0
                bsdf.inputs["Specular"].default_value = 0.0

                if mat_props.hardedged_transparency:
                    material.blend_method = "CLIP"
                    material.node_tree.links.new(bsdf.inputs['Alpha'], texImage.outputs['Alpha']) 

                material.use_backface_culling = not bool(mat_props.doublesided)
        

            output = material.node_tree.nodes.new("ShaderNodeOutputMaterial")
            material.node_tree.links.new(output.inputs['Surface'], bsdf.outputs['BSDF']) 


        return {'FINISHED'}

