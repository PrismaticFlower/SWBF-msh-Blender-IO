bl_info = {
    'name': 'SWBF .msh export',
    'author': 'SleepKiller',
    "version": (0, 2, 1),
    'blender': (2, 80, 0),
    'location': 'File > Import-Export',
    'description': 'Export as SWBF .msh file',
    'warning': '',
    'wiki_url': "https://github.com/SleepKiller/SWBF-msh-Blender-Export/blob/master/docs/reference_manual.md",
    'tracker_url': "https://github.com/SleepKiller/SWBF-msh-Blender-Export/issues",
    'support': 'COMMUNITY',
    'category': 'Import-Export'
}

# Taken from glTF-Blender-IO, because I do not understand Python that well
# (this is the first thing of substance I've created in it) and just wanted 
# script reloading to work.
# 
# https://github.com/KhronosGroup/glTF-Blender-IO
#
# Copyright 2018-2019 The glTF-Blender-IO authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
def reload_package(module_dict_main):
    import importlib
    from pathlib import Path

    def reload_package_recursive(current_dir, module_dict):
        for path in current_dir.iterdir():
            if "__init__" in str(path) or path.stem not in module_dict:
                continue

            if path.is_file() and path.suffix == ".py":
                importlib.reload(module_dict[path.stem])
            elif path.is_dir():
                reload_package_recursive(path, module_dict[path.stem].__dict__)

    reload_package_recursive(Path(__file__).parent, module_dict_main)


if "bpy" in locals():
    reload_package(locals())
# End of stuff taken from glTF

import bpy
from bpy_extras.io_utils import ExportHelper, ImportHelper
from bpy.props import BoolProperty, EnumProperty
from bpy.types import Operator
from .msh_scene import create_scene
from .msh_scene_save import save_scene
from .msh_scene_read import read_scene
from .msh_material_properties import *
from .msh_to_blend import *


class ExportMSH(Operator, ExportHelper):
    """ Export the current scene as a SWBF .msh file. """

    bl_idname = "swbf_msh.export"
    bl_label = "Export SWBF .msh File"
    filename_ext = ".msh"

    filter_glob: StringProperty(
        default="*.msh",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    generate_triangle_strips: BoolProperty(
        name="Generate Triangle Strips",
        description="Triangle strip generation can be slow for meshes with thousands of faces "
                    "and is off by default to enable fast mesh iteration.\n\n"
                    "In order to improve runtime performance and reduce munged model size you are "
                    "**strongly** advised to turn it on for your 'final' export!",
        default=False
    )

    export_target: EnumProperty(name="Export Target",
                                description="What to export.",
                                items=(
                                    ('SCENE', "Scene", "Export the current active scene."),
                                    ('SELECTED', "Selected", "Export the currently selected objects and their parents."),
                                    ('SELECTED_WITH_CHILDREN', "Selected with Children", "Export the currently selected objects with their children and parents.")
                                ),
                                default='SCENE')

    apply_modifiers: BoolProperty(
        name="Apply Modifiers",
        description="Whether to apply Modifiers during export or not.",
        default=True
    )

    export_with_animation: BoolProperty(
        name="Export With Animation",
        description="Includes animation data extracted from the action currently set on armature.",
        default=False
    )

    export_as_skeleton: BoolProperty(
        name="Export Objects As Skeleton",
        description="Check if you intend to export skeleton data for consumption by ZenAsset.",
        default=False
    )


    def execute(self, context):

        with open(self.filepath, 'wb') as output_file:
            save_scene(
                output_file=output_file,
                scene=create_scene(
                    generate_triangle_strips=self.generate_triangle_strips, 
                    apply_modifiers=self.apply_modifiers,
                    export_target=self.export_target,
                    skel_only=self.export_as_skeleton,
                    export_anim=self.export_with_animation
                ),
            )

        return {'FINISHED'}


# Only needed if you want to add into a dynamic menu
def menu_func_export(self, context):
    self.layout.operator(ExportMSH.bl_idname, text="SWBF msh (.msh)")





class ImportMSH(Operator, ImportHelper):
    """ Import an SWBF .msh file. """

    bl_idname = "swbf_msh.import"
    bl_label = "Import SWBF .msh File"
    filename_ext = ".msh"

    filter_glob: StringProperty(
        default="*.msh",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    def execute(self, context):
        with open(self.filepath, 'rb') as input_file:
            extract_scene(self.filepath, read_scene(input_file))
        return {'FINISHED'}

def menu_func_import(self, context):
    self.layout.operator(ImportMSH.bl_idname, text="SWBF msh (.msh)")




def register():
    bpy.utils.register_class(MaterialProperties)
    bpy.utils.register_class(MaterialPropertiesPanel)
    bpy.utils.register_class(ExportMSH)
    bpy.utils.register_class(ImportMSH)

    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
    bpy.types.Material.swbf_msh = bpy.props.PointerProperty(type=MaterialProperties)


def unregister():
    bpy.utils.unregister_class(MaterialProperties)
    bpy.utils.unregister_class(MaterialPropertiesPanel)
    bpy.utils.unregister_class(ExportMSH)
    bpy.utils.unregister_class(ImportMSH)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)


if __name__ == "__main__":
    register()
