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
Same as 'Unlit' but also enables the use of a Glow Map in the diffuse texture's alpha channel. The material will be significantly significantly brightened based on how opaque the glowmap is.

#### Materials.Flags.Per-Pixel Lighting
Calculate lighting per-pixel instead of per-vertex for diffuse lighting.

#### Materials.Flags.Specular Lighting
Use specular lighting as well as diffuse lighting. A Gloss Map in the diffuse map's and normal map's alpha channel can be used to attenuate the specular lighting's strength. (More transparent = less strong).

The Specular Colour controls the colour of the reflected specular highlights, like the diffuse map but for specular lighting and global across the material.

#### Materials.Flags.Doublesided
Disable backface culling, causing both sides of the surface to be drawn. Usually only the front facing surface is drawn.

### Materials.Data
> TODO: Write this section

### Materials.Texture Maps
> TODO: Write this section

### Materials.Rendertypes Table
| Rendertype                           | `ATRB` Data0             | `ATRB` Data1        | `ATRB` Number | `ATRB` Number Hex |
| ------------------------------------ |:------------------------:|:-------------------:|:-------------:| -----------------:|
| Normal (SWBF2)                       | Detail Map Tiling U      | Detail Map Tiling V | 00            | 00                |
| Scrolling (SWBF2)                    | Scroll Speed U           | Scroll Speed V      | 03            | 03                |
| Envmapped (SWBF2)                    | Detail Map Tiling U      | Detail Map Tiling V | 06            | 06                |
| Animated (SWBF2)                     | Animation Length         | Animation Speed     | 07            | 07                |
| Refractive (SWBF2)                   | Detail Map Tiling U      | Detail Map Tiling V | 22            | 16                |
| Normalmapped Tiled (SWBF2)           | Normal Map Tiling U      | Normal Map Tiling V | 24            | 18                |
| Blink (SWBF2)                        | Blink Minimum Brightness | Blink Speed         | 25            | 19                |
| Normalmapped Envmapped (SWBF2)       | Detail Map Tiling U      | Detail Map Tiling V | 26            | 1A                |
| Normalmapped (SWBF2)                 | Detail Map Tiling U      | Detail Map Tiling V | 27            | 1B                |
| Normalmapped Tiled Envmapped (SWBF2) | Normal Map Tiling U      | Normal Map Tiling V | 29            | 1D                |
