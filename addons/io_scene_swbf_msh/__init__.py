bl_info = {
    'name': 'SWBF .msh Import-Export',
    'author': 'Will Snyder, SleepKiller',
    "version": (1, 2, 1),
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
from bpy.props import BoolProperty, EnumProperty, CollectionProperty
from bpy.types import Operator, Menu
from .msh_scene_utilities import create_scene, set_scene_animation
from .msh_scene_save import save_scene
from .msh_scene_read import read_scene
from .msh_material_properties import *
from .msh_skeleton_properties import *
from .msh_collision_prim_properties import *
from .msh_material_operators import *
from .msh_scene_to_blend import *
from .msh_anim_to_blend import *
from .zaa_to_blend import *


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


    animation_export: EnumProperty(name="Export Animation(s)",
                                description="If/how animation data should be exported.",
                                items=(
                                    ('NONE', "None", "Do not include animation data in the export."),
                                    ('ACTIVE', "Active", "Export animation extracted from the scene's Armature's active Action."),
                                    ('BATCH', "Batch", "Export a separate animation file for each Action in the scene.")
                                ),
                                default='NONE')


    def execute(self, context):

        if 'SELECTED' in self.export_target and len(bpy.context.selected_objects) == 0:
            raise Exception("{} was chosen, but you have not selected any objects. "
                            " Don't forget to unhide all the objects you wish to select!".format(self.export_target))


        scene, armature_obj = create_scene(
                                generate_triangle_strips=self.generate_triangle_strips,
                                apply_modifiers=self.apply_modifiers,
                                export_target=self.export_target,
                                skel_only=self.animation_export != 'NONE') # Exclude geometry data (except root stuff) if we're doing anims

        if self.animation_export != 'NONE' and not armature_obj:
            raise Exception("Could not find an armature object from which to export animations!")


        def write_scene_to_file(filepath : str, scene_to_write : Scene):
            with open(filepath, 'wb') as output_file:
                save_scene(output_file=output_file, scene=scene_to_write)

        if self.animation_export == 'ACTIVE':
            set_scene_animation(scene, armature_obj)
            write_scene_to_file(self.filepath, scene)

        elif self.animation_export == 'BATCH':
            export_dir = self.filepath if os.path.isdir(self.filepath) else os.path.dirname(self.filepath)

            for action in bpy.data.actions:
                anim_save_path = os.path.join(export_dir, action.name + ".msh")
                armature_obj.animation_data.action = action
                set_scene_animation(scene, armature_obj)
                write_scene_to_file(anim_save_path, scene)
        else:
            write_scene_to_file(self.filepath, scene)

        return {'FINISHED'}


# Only needed if you want to add into a dynamic menu
def menu_func_export(self, context):
    self.layout.operator(ExportMSH.bl_idname, text="SWBF msh (.msh)")



class ImportMSH(Operator, ImportHelper):
    """ Import SWBF .msh file(s). """

    bl_idname = "swbf_msh.import"
    bl_label = "Import SWBF .msh File(s)"
    filename_ext = ".msh"

    files: CollectionProperty(
            name="File Path(s)",
            type=bpy.types.OperatorFileListElement,
            )

    filter_glob: StringProperty(
        default="*.msh;*.zaa;*.zaabin",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    animation_only: BoolProperty(
        name="Import Animation(s)",
        description="Import one or more animations from the selected files and append each as a new Action to currently selected Armature.",
        default=False
    )


    def execute(self, context):
        dirname = os.path.dirname(self.filepath)
        for file in self.files:
            filepath = os.path.join(dirname, file.name)
            if filepath.endswith(".zaabin") or filepath.endswith(".zaa"):
                extract_and_apply_munged_anim(filepath)
            else:
                with open(filepath, 'rb') as input_file:
                    scene = read_scene(input_file, self.animation_only)

                if not self.animation_only:
                    extract_scene(filepath, scene)
                else:
                    extract_and_apply_anim(filepath, scene)

        return {'FINISHED'}

def menu_func_import(self, context):
    self.layout.operator(ImportMSH.bl_idname, text="SWBF msh (.msh)")




def register():
    bpy.utils.register_class(CollisionPrimitiveProperties)

    bpy.utils.register_class(MaterialProperties)
    bpy.utils.register_class(MaterialPropertiesPanel)

    bpy.utils.register_class(SkeletonProperties)
    bpy.utils.register_class(SkeletonPropertiesPanel)

    bpy.utils.register_class(ExportMSH)
    bpy.utils.register_class(ImportMSH)

    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)

    bpy.types.Object.swbf_msh_coll_prim = bpy.props.PointerProperty(type=CollisionPrimitiveProperties)
    bpy.types.Material.swbf_msh_mat = bpy.props.PointerProperty(type=MaterialProperties)
    bpy.types.Armature.swbf_msh_skel = bpy.props.CollectionProperty(type=SkeletonProperties)

    bpy.utils.register_class(FillSWBFMaterialProperties)
    bpy.utils.register_class(VIEW3D_MT_SWBF)
    bpy.types.VIEW3D_MT_object_context_menu.append(draw_matfill_menu)

    bpy.utils.register_class(GenerateMaterialNodesFromSWBFProperties)



def unregister():
    bpy.utils.unregister_class(CollisionPrimitiveProperties)

    bpy.utils.unregister_class(MaterialProperties)
    bpy.utils.unregister_class(MaterialPropertiesPanel)

    bpy.utils.unregister_class(SkeletonProperties)
    bpy.utils.unregister_class(SkeletonPropertiesPanel)

    bpy.utils.unregister_class(ExportMSH)
    bpy.utils.unregister_class(ImportMSH)

    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)

    bpy.utils.unregister_class(FillSWBFMaterialProperties)

    bpy.utils.unregister_class(VIEW3D_MT_SWBF)
    bpy.types.VIEW3D_MT_object_context_menu.remove(draw_matfill_menu)

    bpy.utils.unregister_class(GenerateMaterialNodesFromSWBFProperties)



if __name__ == "__main__":
    register()
