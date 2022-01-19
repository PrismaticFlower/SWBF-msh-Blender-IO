""" UI strings that are too long to have in msh_materials_properties.py """


UI_RENDERTYPE_UNSUPPORTED_BF2_DESC = \
    "Unsupported rendertype.  The raw values of the material "\
    "are fully accessible, but their purpose is unknown.  "

UI_RENDERTYPE_DETAIL_MAP_DESC = \
    "Can optionally have a Detail Map."

UI_RENDERTYPE_DETAIL_MAP_TILING_DESC = \
    "Tiling for the detail map can specified " \
    "with Detail Map Tiling U and Detail Map Tiling V."

UI_RENDERTYPE_ENV_MAP_DESC = \
    "Uses an Environment Map to show reflections on the model. " \
    "Useful for anything you want to look reflective or metallic." \
    "\n\n" \
    "The reflections from the Environment Map are affected by " \
    "Specular Colour. And if Specular Material Flag is checked then " \
    "reflections will be affected by the Gloss Map."

UI_RENDERTYPE_NORMAL_MAP_DESC = \
    "Enables the use of a Normal Map with the material."

UI_RENDERTYPE_NORMAL_MAP_TILING_DESC = \
    "Tiling for the normal map can be controlled with Normal Map " \
    "Tiling U and Normal Map Tiling V."

UI_RENDERTYPE_NORMAL_PER_PIXEL_DESC = \
    "This rendertype also enables per-pixel lighting."

UI_RENDERTYPE_NORMAL_BF2_DESC = f"""\
Basic material.

{UI_RENDERTYPE_DETAIL_MAP_DESC} {UI_RENDERTYPE_DETAIL_MAP_TILING_DESC}
"""

UI_RENDERTYPE_SCROLLING_BF2_DESC = f"""\
Like Normal except the textures have scrolling. Useful for water, monitors with scrolling content, interlaced holograms, etc.

Scroll speed and direction is specified with Scroll Speed U and Scroll Speed V.

{UI_RENDERTYPE_DETAIL_MAP_DESC} The Detail Map will not be affected by scrolling.
"""

UI_RENDERTYPE_ENVMAPPED_BF2_DESC = f"""\
{UI_RENDERTYPE_ENV_MAP_DESC}

{UI_RENDERTYPE_DETAIL_MAP_DESC} {UI_RENDERTYPE_DETAIL_MAP_TILING_DESC}
"""

UI_RENDERTYPE_ANIMATED_BF2_DESC = f"""\
Use an animated texture. The animation's frames should be packed into NxN squares where N is the square root of the number of frames in the animation. So a 25 frame animation should be packed into 5x5 squares in the Diffuse Map.

Set frame count with Animation Length and frame rate with Animation Speed.

{UI_RENDERTYPE_DETAIL_MAP_DESC} The Detail Map will not be subject to animation.
"""

UI_RENDERTYPE_REFRACTION_BF2_DESC = f"""\
Distorts/refracts the scene behind the material. 

The Diffuse Map's alpha channel controls the visibility of the scene while the Distortion Map controls the distortion.

When distortion is not needed but transparency is the Normal rendertype should be used as this one comes at a performance cost.
"""

UI_RENDERTYPE_BLINK_BF2_DESC = f"""\
Oscillates the diffuse strength of the material between full strength and a supplied strength.

Blink Minimum Brightness sets the strength of the material's diffuse at the bottom of the "blink". Blink Speed sets the speed of the blinking.

{UI_RENDERTYPE_DETAIL_MAP_DESC}
"""

UI_RENDERTYPE_NORMALMAPPED_BF2_DESC = f"""\
{UI_RENDERTYPE_NORMAL_MAP_DESC}

{UI_RENDERTYPE_DETAIL_MAP_DESC} {UI_RENDERTYPE_DETAIL_MAP_TILING_DESC}

{UI_RENDERTYPE_NORMAL_PER_PIXEL_DESC}
"""

UI_RENDERTYPE_NORMALMAPPED_TILED_BF2_DESC = f"""\
{UI_RENDERTYPE_NORMAL_MAP_DESC} {UI_RENDERTYPE_NORMAL_MAP_TILING_DESC}

{UI_RENDERTYPE_DETAIL_MAP_DESC}

{UI_RENDERTYPE_NORMAL_PER_PIXEL_DESC}
"""

UI_RENDERTYPE_NORMALMAPPED_ENVMAPPED_BF2_DESC = f"""\
{UI_RENDERTYPE_NORMAL_MAP_DESC}

{UI_RENDERTYPE_ENV_MAP_DESC}

{UI_RENDERTYPE_DETAIL_MAP_DESC} {UI_RENDERTYPE_DETAIL_MAP_TILING_DESC}

{UI_RENDERTYPE_NORMAL_PER_PIXEL_DESC}
"""

UI_RENDERTYPE_NORMALMAPPED_TILED_ENVMAPPED_BF2_DESC = f"""\
{UI_RENDERTYPE_NORMAL_MAP_DESC} {UI_RENDERTYPE_NORMAL_MAP_TILING_DESC}

{UI_RENDERTYPE_ENV_MAP_DESC}

{UI_RENDERTYPE_DETAIL_MAP_DESC}

{UI_RENDERTYPE_NORMAL_PER_PIXEL_DESC}
"""