## Collision Primitives
Collision primitives are the game's (according to the docs) lightweight method of adding collision to an 
object and are preferred to collision meshes where reasonable.

> TODO: Finish writing this section.

## Materials
Since Blender's sophisticated materials are a poor fit for what .msh files can represent the addon defines
custom properties for representing .msh materials. It then exposes these through a UI panel under Blender's
Material context.

![.msh Material Panel](images/materials.png)

> TODO: Explain why some .msh rendertypes were left out of the addon. (The short answer is they're either redundant or outright unused.)

> TODO: Document what rendertypes/flags are multipass and cause the model to be drawn more than once. And explain the implications of that.

### Materials.Rendertype
Rendertypes in .msh materials confer unique information about how the material. Such as
if the materials textures scroll or if the material has an environment map.

> One could argue that "rendertype" should be stylized as "render type". I thought about that and decided I'd rather spend time writing the addon than thinking about that.

#### Materials.Rendertype.Normal (SWBF2)
Basic material.

Can optionally have a Detail Map. Tiling for the detail map can specified with Detail Map Tiling U and Detail Map Tiling V.

#### Materials.Rendertype.Scrolling (SWBF2)
Like Normal except the textures have scrolling. Useful for water, monitors with scrolling content, interlaced holograms, etc.

Scroll speed and direction is specified with Scroll Speed U and Scroll Speed V.

Can optionally have a Detail Map. The Detail Map will not be affected by scrolling.

#### Materials.Rendertype.Envmapped (SWBF2)
Uses an Environment Map to show reflections on the model. Useful for anything you want to look reflective or 
metallic.

The reflections from the Environment Map are affected by Specular Colour. And if Specular Material Flag is checked then reflections will be affected by the Gloss Map.

Can optionally have a Detail Map. Tiling for the detail map can specified with Detail Map Tiling U and Detail Map Tiling V.

#### Materials.Rendertype.Animated (SWBF2)
Use an animated texture. The animation's frames should be packed into NxN squares where N is the square root of the number of frames in the animation. So a 25 frame animation should be packed into 5x5 squares in the Diffuse Map.

Set frame count with Animation Length and frame rate with Animation Speed.

Can optionally have a Detail Map. The Detail Map will not be subject to animation.

#### Materials.Rendertype.Refraction (SWBF2)
Distorts/refracts the scene behind the material. 

The Diffuse Map's alpha channel controls the visibility of the scene while the Distortion Map controls the distortion.

When distortion is not needed but transparency is the Normal rendertype should be used as this one comes at a performance cost.

The Material Flags are not exposed by the addon for this rendertype as most are unsupported by it. The Blended Transparency flag is supported and **required** but is set automatically by the addon.

#### Materials.Rendertype.Blink (SWBF2)
Oscillates the diffuse strength of the material between full strength and a supplied strength.

Blink Minimum Brightness sets the strength of the material's diffuse at the bottom of the "blink". Blink Speed sets the speed of the blinking.

Can optionally have a Detail Map.

#### Materials.Rendertype.Normalmapped (SWBF2)
Enables the use of a Normal Map with the material.

Can optionally have a Detail Map. Tiling for the detail map can specified with Detail Map Tiling U and Detail Map Tiling V.

This rendertype also enables per-pixel lighting. 

#### Materials.Rendertype.Normalmapped Tiled (SWBF2)
Enables the use of a Normal Map with the material. Tiling for the normal map can be controlled with Normal Map Tiling U and Normal Map Tiling V.

Can optionally have a Detail Map.

This rendertype also enables per-pixel lighting.

#### Materials.Rendertype.Normalmapped Envmapped (SWBF2)
Enables the use of a Normal Map with the material.

Uses an Environment Map to show reflections on the model. Useful for anything you want to look reflective or 
metallic.

The reflections from the Environment Map are affected by Specular Colour. And if Specular Material Flag is checked then reflections will be affected by the Gloss Map.

Can optionally have a Detail Map. Tiling for the detail map can specified with Detail Map Tiling U and Detail Map Tiling V.

This rendertype also enables per-pixel lighting.

#### Materials.Rendertype.Normalmapped Envmapped (SWBF2)
Enables the use of a Normal Map with the material. Tiling for the normal map can be controlled with Normal Map Tiling U and Normal Map Tiling V

Uses an Environment Map to show reflections on the model. Useful for anything you want to look reflective or 
metallic.

The reflections from the Environment Map are affected by Specular Colour. And if Specular Material Flag is checked then reflections will be affected by the Gloss Map.

Can optionally have a Detail Map.

This rendertype also enables per-pixel lighting.

### Materials.Transparency Flags

> TODO: Improve this section.

#### Materials.Transparency Flags.Blended
Regular alpha blended transparency.

#### Materials.Transparency Flags.Additive
Additive transparency, objects behind the material will appear brighter because the material will be "added" on top of the scene.

> TODO: Explain the difference between Blended + Additive vs just Additive

#### Materials.Transparency Flags.Hardedged
Hardedged/alpha cutout/clip transparency. Any point on the material with an alpha value below the threshold of 0.5/0x80/128 will be discarded. Useful for leaves, flowers, wire fences and all sorts.

### Materials.Flags

#### Materials.Flags.Unlit
Makes the material unlit/emissive. Useful for anything that is meant to be giving light but not reflecting any/much.

#### Materials.Flags.Glow
Same as 'Unlit' but also enables the use of a Glow Map in the diffuse texture's alpha channel. The material will be significantly significantly brightened based on how opaque the Glow Map is.

Note that despite the name this doesn't automatically create "glowing" materials. What it does do is let you brighten a material enough so that it'll pass the game's bloom threshold (which is set by the map) and then the bloom effect will cause it to "glow".

#### Materials.Flags.Per-Pixel Lighting
Calculate lighting per-pixel instead of per-vertex for diffuse lighting.

#### Materials.Flags.Specular Lighting
Use specular lighting as well as diffuse lighting. A Gloss Map in the diffuse map's and normal map's alpha channel can be used to attenuate the specular lighting's strength. (More transparent = less strong).

The Specular Colour controls the colour of the reflected specular highlights, like the diffuse map but for specular lighting and global across the material.

#### Materials.Flags.Doublesided
Disable backface culling, causing both sides of the surface to be drawn. Usually only the front facing surface is drawn.

### Materials.Data

#### Materials.Data.Detail Map Tiling U
Tiling of the Detail Map in the U direction. A value of 0 is valid and means no tiling.

#### Materials.Data.Detail Map Tiling V
Tiling of the Detail Map in the V direction. A value of 0 is valid and means no tiling.

#### Materials.Data.Normal Map Tiling U
Tiling of the Normal Map in the U direction. A value of 0 is valid and means no tiling.

#### Materials.Data.Normal Map Tiling V
Tiling of the Normal Map in the V direction. A value of 0 is valid and means no tiling.

#### Materials.Data.Scroll Speed U
Texture scroll speed in the U direction.

#### Materials.Data.Scroll Speed V
Texture scroll speed in the V direction.

#### Materials.Data.Animation Length
Number of frames in the texture animation.

Valid Values

|     |     |     |     |     |     |     |     |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 1   | 4   | 9   | 16  | 25  | 36  | 49  | 64  |
| 81  | 100 | 121 | 144 | 169 | 196 | 225 |     |

#### Materials.Data.Animation Speed
Animation speed in frames per second.

#### Materials.Data.Blink Minimum Brightness
Sets the strength of the material's diffuse at the bottom of the "blink".

#### Materials.Data.Blink Speed
Speed of blinking, higher is faster.

### Materials.Texture Maps

#### Materials.Texture Maps.Diffuse Map
The basic diffuse map for the material. The alpha channel is either the Transparency Map, Glow Map or Gloss Map, depending on the selected rendertype and flags.

#### Materials.Texture Maps.Detail Map
Detail maps allow you to add in 'detail' to the Diffuse Map at runtime. 

Or they can be used as fake ambient occlusion maps or even wacky emissive maps.

See Appendix Detail Map Blending for a rundown of the details of how they're blended in
with the Diffuse Map.

#### Materials.Texture Maps.Normal Map
Normal maps can provide added detail from lighting. They work much the same way as in any other game/application that uses Tangent Space Normal Maps. See Appendix Normal Map Example if you require a rundown of Normal Maps.

If Specular is enabled the alpha channel will be the Gloss Map.

#### Materials.Texture Maps.Environment Map
Environment map for the material. Used to provide static reflections for the model. Must be a cubemap, see Appendix Cubemap Layout.

#### Materials.Texture Maps.Distortion Map
Distortion maps control how Refractive materials distort the scene behind them. Should be a Normal Map with '-forceformat v8u8' in it's '.tga.option' file. See Appendix .tga.option Files.

## Appendices

### Appendix Detail Map Blending

> TODO: Write this section (with pretty pictures).

### Appendix Normal Map Example

> TODO: Write this section (with pretty pictures).

### Appendix Cubemap Layout

> TODO: Write this section (with layout reference).

### Appendix .msh.option Files

> TODO: Should this section exist?

> TODO: Write this section.

### Appendix .tga.option Files

> TODO: Write this section.

### Appendix Rendertypes Table
| Rendertype                           | `ATRB` Data0             | `ATRB` Data1        | `ATRB` Number | `ATRB` Number Hex | `TX0D`      | `TX1D`         | `TX2D`     | `TX3D`          |
| ------------------------------------ |:------------------------:|:-------------------:|:-------------:|:-----------------:|:-----------:|:--------------:|:----------:| ---------------:|
| Normal (SWBF2)                       | Detail Map Tiling U      | Detail Map Tiling V | 00            | 00                | Diffuse Map |                | Detail Map |                 |
| Scrolling (SWBF2)                    | Scroll Speed U           | Scroll Speed V      | 03            | 03                | Diffuse Map |                | Detail Map |                 |
| Envmapped (SWBF2)                    | Detail Map Tiling U      | Detail Map Tiling V | 06            | 06                | Diffuse Map |                | Detail Map | Environment Map |
| Animated (SWBF2)                     | Animation Length         | Animation Speed     | 07            | 07                | Diffuse Map |                | Detail Map |                 |
| Refractive (SWBF2)                   | Detail Map Tiling U      | Detail Map Tiling V | 22            | 16                | Diffuse Map | Distortion Map |            |                 |
| Normalmapped Tiled (SWBF2)           | Normal Map Tiling U      | Normal Map Tiling V | 24            | 18                | Diffuse Map | Normal Map     | Detail Map |                 |
| Blink (SWBF2)                        | Blink Minimum Brightness | Blink Speed         | 25            | 19                | Diffuse Map |                | Detail Map |                 |
| Normalmapped Envmapped (SWBF2)       | Detail Map Tiling U      | Detail Map Tiling V | 26            | 1A                | Diffuse Map | Normal Map     | Detail Map | Environment Map |
| Normalmapped (SWBF2)                 | Detail Map Tiling U      | Detail Map Tiling V | 27            | 1B                | Diffuse Map | Normal Map     | Detail Map |                 |
| Normalmapped Tiled Envmapped (SWBF2) | Normal Map Tiling U      | Normal Map Tiling V | 29            | 1D                | Diffuse Map | Normal Map     | Detail Map | Environment Map |

