# SWBF-msh-Blender-Export
WIP .msh (SWBF toolchain version) exporter for Blender 2.8

Currently capable of exporting the active scene without any materials or skinning information. 

### Behaviour to be aware of

#### For UV layers and vertex colors layers it is the active layer that is exported.
Unlikely to come up since if you're working on a model for SWBF you're unlikely to have multiple layers to start 
with but 

#### If a scene has multiple "roots" they will be reparented to a new "root" added during export.
This is to make sure the .msh file only has one root in it. Any object that doesn't have a parent is considered a root.
There is no need to explicitly make sure your scene only has one root as a result of this, it is fine to let the exporter
add one and perform the reparenting.

#### Object scales are applied during export.
Despite `.msh` files have a field in their transform section for scale it seams to get ignored by modelmunge. 
As a result there is no point in even trying to export the scale. Instead it is applied to a the vertex coordinates during export.
The way it is applied is very basic but it should give the expected result for most use cases. Currently only the scale component of 
the transform hierarchy is applied but it'd probably be better to transform the coordinates in world space and then transform them 
back into local space using only translation and rotation.

#### Object types with no possible representation in .msh files are not exported unless they have children.
Currently the exporter considers the following object types fall in this category. As I am unfamilar with Blender it is 
possible that more object types should be added.

- Lattices
- Cameras
- Lights
- Light Probes
- Speakers

If an object has children it is always exported as an empty.

#### Objects whose name starts with "sv_", "p_" or "collision" will be marked as hidden in the .msh file.
This should be consistent with other .msh exporters. As far as I know the only special thing about collision meshes or
"sv_" meshes is their name and the fact they're hidden. As such you should be able to just make a mesh and give it the right
name to get a shadow volume or or collision mesh. (Collision primitives are still preferred from the game's standpoint, 
but those aren't supported yet.)

The check for if a name begins with "sv_", "p_" or "collision" is case-insensitive. So you should be able to do 
"Collision-sv-mesh" if you prefer it to "collision-sv-mesh".

#### For completeness poloygons (`NDXL` chunks), triangles (`NDXT`) and triangle strips (`STRP`) are all saved. 
This should hopefully give the .msh files the greatest chance of being opened by the various tools out there.

Saving polygons also will make any hypothetical importer work better, since quads and ngons could be restored on import.

The triangle strips are generated using a brute-force method that seams to give decent results.

#### Delta transforms are combined with regular transforms on export.
Unsurprisingly Blender's delta transforms have no meaningful representation in .msh files. 
So they are combined with the regular transform during export.

### Work to be done
- [ ] Raise an error when a .msh segment has more than 32767 vertices.
- [ ] Convert from Blender's coordinate space to .msh cooordinate space.
- [ ] Add support for exporting materials. Blender's materials are all based around it's own renderers, so possibly going to need custom UI and properties in order to provide something useful for .msh files.
- [ ] Add support for collision primitives. Blender doesn't seam to support having basic boxes, cylinders or spheres so it's likely some wacky rules and conventions will need to be used by the modeler. "Add a 1m mesh primitive, have "sphere/box/cylinder" in the name and control the size with the object's scale." Less intuitive than I'd like but it might be the best course of action.
- [ ] Investigate and add support for exporting bones and vertex weights.
- [ ] Investigate and add support for exporting animations.
- [ ] Investigate if anything special needs to be done for lod/lowres exporting.
- [ ] Implement .msh importing. Currently you can use the 1.2 release of [swbf-unmunge](releases/tag/v1.2.0) to save out munged models to glTF 2.0 files if you need to open a model in Blender.

### What from [glTF-Blender-IO](https://github.com/KhronosGroup/glTF-Blender-IO) was used?
The `reload_package` function from \_\_init\_\_.py. Before writing this I had barely touched Python and when I saw that glTF-Blender-IO had a function to assist script reloading "I thought that's useful, I think I kinda need that and I don't know how to write something like that myself yet.". And it was very useful, so thank you to all the glTF-Blender-IO developers and contributors.
