""" Operators for basic emulation and mapping of SWBF material system in Blender.
    Only relevant if the builtin Eevee renderer is being used! """

import bpy

from .msh_material_properties import *

from math import sqrt

from bpy.props import BoolProperty, EnumProperty, StringProperty
from bpy.types import Operator, Menu

from .option_file_parser import MungeOptions


import os


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

                        tex_name = link_node.image.filepath
                        print(tex_name)

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

    fail_silently: BoolProperty(
        name = "Fail Silently"
    )
    

    def execute(self, context):

        material = bpy.data.materials.get(self.material_name, None)

        if not material or not material.swbf_msh_mat:
            return {'CANCELLED'}

        mat_props = material.swbf_msh_mat


        texture_input_nodes = []
        surface_output_nodes = []


        diffuse_texture_path = mat_props.diffuse_map
        if diffuse_texture_path and os.path.exists(diffuse_texture_path):

            material.use_nodes = True
            material.node_tree.nodes.clear()

            bsdf = material.node_tree.nodes.new("ShaderNodeBsdfPrincipled")


            texImage = material.node_tree.nodes.new('ShaderNodeTexImage')
            texImage.image = bpy.data.images.load(diffuse_texture_path)
            texImage.image.alpha_mode = 'CHANNEL_PACKED'
            material.node_tree.links.new(bsdf.inputs['Base Color'], texImage.outputs['Color']) 

            texture_input_nodes.append(texImage)

            bsdf.inputs["Roughness"].default_value = 1.0
            bsdf.inputs["Specular"].default_value = 0.0

            if mat_props.hardedged_transparency and not mat_props.glow:
                material.blend_method = "CLIP"
                material.node_tree.links.new(bsdf.inputs['Alpha'], texImage.outputs['Alpha']) 

            material.use_backface_culling = not bool(mat_props.doublesided)

            surface_output_nodes.append(tuple(('BSDF', bsdf)))


            if mat_props.glow:

                emission = material.node_tree.nodes.new("ShaderNodeEmission")
                material.node_tree.links.new(emission.inputs['Color'], texImage.outputs['Color']) 

                emission_strength_multiplier = material.node_tree.nodes.new("ShaderNodeMath")
                emission_strength_multiplier.operation = 'MULTIPLY'
                emission_strength_multiplier.inputs[1].default_value = 32.0

                material.node_tree.links.new(emission_strength_multiplier.inputs[0], texImage.outputs['Alpha']) 

                material.node_tree.links.new(emission.inputs['Strength'], emission_strength_multiplier.outputs[0])

                surface_output_nodes.append(tuple(("Emission", emission)))

            surfaces_output = None
            if (len(surface_output_nodes) == 1):
                surfaces_output = surface_output_nodes[0][1]
            else:
                mix = material.node_tree.nodes.new("ShaderNodeMixShader")
                material.node_tree.links.new(mix.inputs[1], surface_output_nodes[0][1].outputs[0])
                material.node_tree.links.new(mix.inputs[2], surface_output_nodes[1][1].outputs[0])

                surfaces_output = mix


            if "NORMALMAP" in mat_props.rendertype and mat_props.normal_map and os.path.exists(mat_props.normal_map):
                normalMapTexImage = material.node_tree.nodes.new('ShaderNodeTexImage')
                normalMapTexImage.image = bpy.data.images.load(mat_props.normal_map)
                normalMapTexImage.image.alpha_mode = 'CHANNEL_PACKED'
                normalMapTexImage.image.colorspace_settings.name = 'Non-Color'
                texture_input_nodes.append(normalMapTexImage)

                options = MungeOptions(mat_props.normal_map + ".option")

                if options.get_bool("bumpmap"):

                    # First we must convert the RGB data to brightness
                    rgb_to_bw_node = material.node_tree.nodes.new("ShaderNodeRGBToBW")
                    material.node_tree.links.new(rgb_to_bw_node.inputs["Color"], normalMapTexImage.outputs["Color"])

                    # Now create a bump map node (perhaps we could also use this with normals and just plug color into normal input?)
                    bumpMapNode = material.node_tree.nodes.new('ShaderNodeBump')
                    bumpMapNode.inputs["Distance"].default_value = options.get_float("bumpscale", default=1.0)
                    material.node_tree.links.new(bumpMapNode.inputs["Height"], rgb_to_bw_node.outputs["Val"])

                    normalsOutputNode = bumpMapNode

                else:

                    normalMapNode = material.node_tree.nodes.new('ShaderNodeNormalMap')
                    material.node_tree.links.new(normalMapNode.inputs["Color"], normalMapTexImage.outputs["Color"])

                    normalsOutputNode = normalMapNode
                
                material.node_tree.links.new(bsdf.inputs['Normal'], normalsOutputNode.outputs["Normal"]) 



            output = material.node_tree.nodes.new("ShaderNodeOutputMaterial")
            material.node_tree.links.new(output.inputs['Surface'], surfaces_output.outputs[0]) 


            # Clear all anims in all cases
            if material.node_tree.animation_data:
                material.node_tree.animation_data.action.fcurves.clear()


            if "SCROLL" in mat_props.rendertype:
                uv_input = material.node_tree.nodes.new("ShaderNodeUVMap")

                vector_add = material.node_tree.nodes.new("ShaderNodeVectorMath")

                # Add keyframes
                scroll_per_sec_divisor = 255.0 
                frame_step = 60.0
                fps = bpy.context.scene.render.fps
                for i in range(2):
                    vector_add.inputs[1].default_value[0] = i * mat_props.scroll_speed_u * frame_step / scroll_per_sec_divisor              
                    vector_add.inputs[1].keyframe_insert("default_value", index=0, frame=i * frame_step * fps)

                    vector_add.inputs[1].default_value[1] = i * mat_props.scroll_speed_v * frame_step / scroll_per_sec_divisor               
                    vector_add.inputs[1].keyframe_insert("default_value", index=1, frame=i * frame_step * fps)


                material.node_tree.links.new(vector_add.inputs[0], uv_input.outputs[0])

                for texture_node in texture_input_nodes:
                    material.node_tree.links.new(texture_node.inputs["Vector"], vector_add.outputs[0])

            # Don't know how to set interpolation when adding keyframes
            # so we must do it after the fact
            if material.node_tree.animation_data:
                for fcurve in material.node_tree.animation_data.action.fcurves:
                    for kf in fcurve.keyframe_points.values():
                        kf.interpolation = 'LINEAR'

        '''
        else:

            # Todo: figure out some way to raise an error but continue operator execution...
            if self.fail_silently:
                return {'CANCELLED'}
            else:
                raise RuntimeError(f"Diffuse texture at path: '{diffuse_texture_path}' was not found.")
        '''

        return {'FINISHED'}

