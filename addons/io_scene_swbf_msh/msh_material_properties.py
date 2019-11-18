""" Contains Blender properties and UI for .msh materials. """

import bpy
from bpy.props import StringProperty, BoolProperty, EnumProperty, FloatVectorProperty, IntProperty
from bpy.types import PropertyGroup
from .msh_material_ui_strings import *

UI_MATERIAL_RENDERTYPES = (
    ('NORMAL_BF2', "00 Normal (SWBF2)", UI_RENDERTYPE_NORMAL_BF2_DESC),
    ('SCROLLING_BF2', "03 Scrolling (SWBF2)", UI_RENDERTYPE_SCROLLING_BF2_DESC),
    ('ENVMAPPED_BF2', "06 Envmapped (SWBF2)", UI_RENDERTYPE_ENVMAPPED_BF2_DESC),
    ('ANIMATED_BF2', "07 Animated (SWBF2)", UI_RENDERTYPE_ANIMATED_BF2_DESC),
    ('REFRACTION_BF2', "22 Refractive (SWBF2)", UI_RENDERTYPE_REFRACTION_BF2_DESC),
    ('BLINK_BF2', "25 Blink (SWBF2)", UI_RENDERTYPE_BLINK_BF2_DESC),
    ('NORMALMAPPED_TILED_BF2', "24 Normalmapped Tiled (SWBF2)", UI_RENDERTYPE_NORMALMAPPED_TILED_BF2_DESC),
    ('NORMALMAPPED_ENVMAPPED_BF2', "26 Normalmapped Envmapped (SWBF2)", UI_RENDERTYPE_NORMALMAPPED_ENVMAPPED_BF2_DESC),
    ('NORMALMAPPED_BF2', "27 Normalmapped (SWBF2)", UI_RENDERTYPE_NORMALMAPPED_BF2_DESC),
    ('NORMALMAPPED_TILED_ENVMAPPED_BF2', "29 Normalmapped Tiled Envmapped (SWBF2)", UI_RENDERTYPE_NORMALMAPPED_TILED_ENVMAPPED_BF2_DESC))

def _make_anim_length_entry(length):
    from math import sqrt
    len_sqrt = int(sqrt(length))

    return (
        f'FRAMES_{length}', 
        f"{length} ({len_sqrt}x{len_sqrt})", 
        f"Input texture should be laid out as {len_sqrt}x{len_sqrt} frames.")

UI_MATERIAL_ANIMATION_LENGTHS = (
    ('FRAMES_1', "1 (1x1)", "Why do you have an animated texture with one frame?"),
    _make_anim_length_entry(4),
    _make_anim_length_entry(9),
    _make_anim_length_entry(16),
    _make_anim_length_entry(25),
    _make_anim_length_entry(36),
    _make_anim_length_entry(49),
    _make_anim_length_entry(64),
    _make_anim_length_entry(81),
    _make_anim_length_entry(100),
    _make_anim_length_entry(121),
    _make_anim_length_entry(144),
    _make_anim_length_entry(169),
    _make_anim_length_entry(196),
    _make_anim_length_entry(225))

class MaterialProperties(PropertyGroup):
    rendertype: EnumProperty(name="Rendertype",
                             description="Rendertype for the material.",
                             items=UI_MATERIAL_RENDERTYPES,
                             default='NORMAL_BF2')

    specular_color: FloatVectorProperty(name="Specular Colour",
                                        description="Specular colour of the material. "
                                                     "Can be used to tint specular highlights "
                                                     "or reduce their strength.",
                                        default=(1.0, 1.0, 1.0),
                                        min=0.0, max=1.0,
                                        soft_min=0.0, soft_max=1.0,
                                        subtype="COLOR")

    blended_transparency: BoolProperty(name="Blended",
                                       description="Enable blended transparency.",
                                       default=False)

    additive_transparency: BoolProperty(name="Additive",
                                        description="Enable additive transparency.",
                                        default=False)

    hardedged_transparency: BoolProperty(name="Hardedged",
                                         description="Enable hardedged (alpha cutout/clip) transparency "
                                                     "with a treshold of 0.5/0x80/128.",
                                         default=False)

    unlit: BoolProperty(name="Unlit",
                        description="Makes the material unlit/emissive.",
                        default=False)

    glow: BoolProperty(name="Glow",
                       description="Same as 'Unlit' but also enables the use of a glowmap "
                                   "in the diffuse texture's alpha channel. The material will be significantly "
                                   "significantly brightened based on how opaque the glowmap is.",
                       default=False)

    perpixel: BoolProperty(name="Per-Pixel Lighting",
                           description="Use per-pixel lighting instead of per-vertex for diffuse lighting.",
                           default=False)

    specular: BoolProperty(name="Specular Lighting",
                           description="Use specular lighting as well as diffuse lighting. A gloss map "
                                       "in the diffuse map's and normal map's alpha channel can be used "
                                       "to attenuate the specular lighting's strength. (More transparent = less strong).\n\n"
                                       "The Specular Colour controls the colour of the reflected specular highlights, "
                                       "like the diffuse map but for specular lighting and global across the material.",
                           default=False)

    doublesided: BoolProperty(name="Doublesided",
                              description="Disable backface culling, causing both sides of the surface to be drawn. "
                                          "Usually only the front facing surface is drawn.",
                              default=False)

    detail_map_tiling_u: IntProperty(name="Detail Map Tiling U",
                                     description="Tiling of the Detail Map in the U direction. (0 = no tiling).",
                                     default=0,
                                     min=0, max=255,
                                     soft_min=0, soft_max=255)

    detail_map_tiling_v: IntProperty(name="Detail Map Tiling V",
                                     description="Tiling of the Detail Map in the V direction. (0 = no tiling).",
                                     default=0,
                                     min=0, max=255,
                                     soft_min=0, soft_max=255)

    normal_map_tiling_u: IntProperty(name="Normal Map Tiling U",
                                     description="Tiling of the Normal Map in the U direction. (0 = no tiling).",
                                     default=0,
                                     min=0, max=255,
                                     soft_min=0, soft_max=255)

    normal_map_tiling_v: IntProperty(name="Normal Map Tiling V",
                                     description="Tiling of the Normal Map in the V direction. (0 = no tiling).",
                                     default=0,
                                     min=0, max=255,
                                     soft_min=0, soft_max=255)

    scroll_speed_u: IntProperty(name="Scroll Speed U",
                                description="Texture scroll speed in the U direction.",
                                default=0,
                                min=0, max=255,
                                soft_min=0, soft_max=255)

    scroll_speed_v: IntProperty(name="Scroll Speed V",
                                description="Texture scroll speed in the V direction.",
                                default=0,
                                min=0, max=255,
                                soft_min=0, soft_max=255)

    animation_length: EnumProperty(name="Animation Length",
                                   description="Number of frames in the texture animation.",
                                   items=UI_MATERIAL_ANIMATION_LENGTHS,
                                   default='FRAMES_4')

    animation_speed: IntProperty(name="Animation Speed",
                                 description="Animation speed in frames per second.",
                                 default=1,
                                 min=0, max=255,
                                 soft_min=0, soft_max=255)

    blink_min_brightness: IntProperty(name="Blink Minimum Brightness",
                                      description="Minimum brightness to blink between.",
                                      default=0,
                                      min=0, max=255,
                                      soft_min=0, soft_max=255)

    blink_speed: IntProperty(name="Blink Speed",
                             description="Speed of blinking, higher is faster.",
                             default=0,
                             min=0, max=255,
                             soft_min=0, soft_max=255)

    diffuse_map: StringProperty(name="Diffuse Map",
                                description="The basic diffuse map for the material. The alpha channel "
                                            "is either the Transparency Map, Glow Map or Gloss Map, "
                                            "depending on the selected rendertype and flags.",
                                default="white.tga")

    detail_map: StringProperty(name="Detail Map",
                               description="Detail maps allow you to add in 'detail' to the diffuse "
                                           "map at runtime. Or they can be used as fake ambient occlusion "
                                           "maps or even wacky emissive maps. See docs for more details.")

    normal_map: StringProperty(name="Normal Map",
                               description="Normal maps can provide added detail from lighting. "
                                           "If Specular is enabled the alpha channel will be "
                                           "the Gloss Map.")

    environment_map: StringProperty(name="Environment Map",
                                    description="Environment map for the material. Provides static "
                                                "reflections around the surface. Must be a cubemap.")

    distortion_map: StringProperty(name="Distortion Map",
                                   description="Distortion maps control how Refractive materials "
                                               "distort the scene behind them. Should be a normal map "
                                               "with '-forceformat v8u8' in it's '.tga.option' file.")

class MaterialPropertiesPanel(bpy.types.Panel):
    """ Creates a Panel in the Object properties window """
    bl_label = "SWBF .msh Properties"
    bl_idname = "MATERIAL_PT_swbf_msh"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "material"

    def draw(self, context):
        layout = self.layout

        material_props = context.material.swbf_msh

        layout.prop(material_props, "rendertype")
        layout.prop(material_props, "specular_color")

        if "REFRACTION" not in material_props.rendertype:
            layout.label(text="Transparency Flags: ")
            row = layout.row()
            row.prop(material_props, "blended_transparency")
            row.prop(material_props, "additive_transparency")
            row.prop(material_props, "hardedged_transparency")

            layout.label(text="Material Flags: ")
            row = layout.row()
            row.prop(material_props, "unlit")
            row.prop(material_props, "glow")
            row = layout.row()
            row.prop(material_props, "perpixel")
            row.prop(material_props, "specular")
            layout.prop(material_props, "doublesided")

            layout.label(text="Material Data: ")
            row = layout.row()

            if "SCROLLING" in material_props.rendertype:
                row.prop(material_props, "scroll_speed_u")
                row.prop(material_props, "scroll_speed_v")
            elif "ANIMATED" in material_props.rendertype:
                row.prop(material_props, "animation_length")
                row = layout.row()
                row.prop(material_props, "animation_speed")
            elif "BLINK" in material_props.rendertype:
                row.prop(material_props, "blink_min_brightness")
                row.prop(material_props, "blink_speed")
            elif "NORMALMAPPED_TILED" in material_props.rendertype:
                row.prop(material_props, "normal_map_tiling_u")
                row.prop(material_props, "normal_map_tiling_v")
            else:
                row.prop(material_props, "detail_map_tiling_u")
                row.prop(material_props, "detail_map_tiling_v")

        layout.label(text="Texture Maps: ")
        layout.prop(material_props, "diffuse_map")

        if "REFRACTION" not in material_props.rendertype:
            layout.prop(material_props, "detail_map")

        if "NORMALMAPPED" in material_props.rendertype:
            layout.prop(material_props, "normal_map")

        if "ENVMAPPED" in material_props.rendertype:
            layout.prop(material_props, "environment_map")

        if "REFRACTION" in material_props.rendertype:
            layout.prop(material_props, "distortion_map")
