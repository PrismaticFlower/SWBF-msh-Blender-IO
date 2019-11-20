# SWBF-msh-Blender-Export
WIP .msh (SWBF toolchain version) exporter for Blender 2.8

Currently capable of exporting the active scene without collision primitives or skinning information. 

### Installing

> TODO: Install instructions.

### Work to be done
- [x] Raise an error when a .msh segment has more than 32767 vertices.
- [x] Convert from Blender's coordinate space to .msh cooordinate space.
- [x] Add support for exporting materials. Blender's materials are all based around it's own renderers, so possibly going to need custom UI and properties in order to provide something useful for .msh files.
- [x] Add support for collision primitives. Blender doesn't seam to support having basic boxes, cylinders or spheres so it's likely some wacky rules and conventions will need to be used by the modeler. "Add a 1m mesh primitive, have "sphere/box/cylinder" in the name and control the size with the object's scale." Less intuitive than I'd like but it might be the best course of action.
- [ ] Investigate and add support for exporting bones and vertex weights.
- [ ] Investigate and add support for exporting animations.
- [ ] Investigate if anything special needs to be done for lod/lowres exporting.
- [ ] Implement .msh importing. Currently you can use the 1.2 release of [swbf-unmunge](releases/tag/v1.2.0) to save out munged models to glTF 2.0 files if you need to open a model in Blender.

### What from [glTF-Blender-IO](https://github.com/KhronosGroup/glTF-Blender-IO) was used?
The `reload_package` function from \_\_init\_\_.py. Before writing this I had barely touched Python and when I saw that glTF-Blender-IO had a function to assist script reloading "I thought that's useful, I think I kinda need that and I don't know how to write something like that myself yet.". And it was very useful, so thank you to all the glTF-Blender-IO developers and contributors.
