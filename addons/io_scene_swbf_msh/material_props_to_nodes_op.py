""" Operator for creating/modifying nodes to approximate appearance of SWBF material.
    Only relevant if the builtin Eevee renderer is being used. """

import bpy
from typing import Dict
from .msh_material import *
from .msh_material_gather import *
from .msh_material_properties import *

from .msh_material_utilities import _REVERSE_RENDERTYPES_MAPPING

from math import sqrt


from bpy.props import BoolProperty, EnumProperty, StringProperty
from bpy.types import Operator, Menu






class GenerateMaterialFromSWBFProperties(bpy.types.Operator):
    
    bl_idname = "swbf_msh.generate_material"
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



    
