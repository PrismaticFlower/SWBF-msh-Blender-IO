""" Gathers the Blender objects from the current scene and returns them as a list of
    Model objects. """

import bpy
import math
from enum import Enum
from typing import List, Set, Dict, Tuple
from itertools import zip_longest
from .msh_model import *
from .msh_model_utilities import *
from .msh_utilities import *
from .msh_skeleton_utilities import *

SKIPPED_OBJECT_TYPES = {"LATTICE", "CAMERA", "LIGHT", "SPEAKER", "LIGHT_PROBE"}
MESH_OBJECT_TYPES = {"MESH", "CURVE", "SURFACE", "META", "FONT", "GPENCIL"}
MAX_MSH_VERTEX_COUNT = 32767

def gather_models(apply_modifiers: bool, export_target: str, skeleton_only: bool) -> Tuple[List[Model], bpy.types.Object]:
    """ Gathers the Blender objects from the current scene and returns them as a list of
        Model objects. """

    depsgraph = bpy.context.evaluated_depsgraph_get()
    parents = create_parents_set()

    models_list: List[Model] = []

    # Composite bones are bones which have geometry.  
    # If a child object has the same name, it will take said child's geometry.

    # Pure bones are just bones and after all objects are explored the only
    # entries remaining in this dict will be bones without geometry.  
    pure_bones_from_armature = {}
    armature_found = None

    # Non-bone objects that will be exported
    blender_objects_to_export = []

    # This must be seperate from the list above,
    # since exported objects will contain Blender objects as well as bones
    # Here we just keep track of all names, regardless of origin
    exported_object_names: Set[str] = set() 

    # Me must keep track of hidden objects separately because
    # evaluated_get clears hidden status
    blender_objects_to_hide: Set[str] = set()

    # Armature must be processed before everything else!

    # In this loop we also build a set of names of all objects
    # that will be exported.  This is necessary so we can prune vertex
    # groups that do not reference exported objects in the main 
    # model building loop below this one.
    for uneval_obj in select_objects(export_target):

        if get_is_model_hidden(uneval_obj):
            blender_objects_to_hide.add(uneval_obj.name)

        if uneval_obj.type == "ARMATURE" and not armature_found:
            # Keep track of the armature, we don't want to process > 1!
            armature_found = uneval_obj.evaluated_get(depsgraph) if apply_modifiers else uneval_obj
            # Get all bones in a separate list.  While we iterate through
            # objects we removed bones with geometry from this dict.  After iteration
            # is done, we add the remaining bones to the models from exported
            # scene objects.
            pure_bones_from_armature = expand_armature(armature_found)
            # All bones to set
            exported_object_names.update(pure_bones_from_armature.keys())
        
        elif not (uneval_obj.type in SKIPPED_OBJECT_TYPES and uneval_obj.name not in parents):
            exported_object_names.add(uneval_obj.name)
            blender_objects_to_export.append(uneval_obj)
        
        else:
            pass

    for uneval_obj in blender_objects_to_export:

        obj = uneval_obj.evaluated_get(depsgraph) if apply_modifiers else uneval_obj

        check_for_bad_lod_suffix(obj)

        # Test for a mesh object that should be a BONE on export.
        # If so, we inject geometry into the BONE while not modifying it's transform/name
        # and remove it from the set of BONES without geometry (pure).
        if obj.name in pure_bones_from_armature:
            model = pure_bones_from_armature.pop(obj.name)
        else:
            model = Model()
            model.name = obj.name
            model.model_type = ModelType.NULL if skeleton_only else get_model_type(obj, armature_found)

            transform = obj.matrix_local

            if obj.parent_bone:
                model.parent = obj.parent_bone

                # matrix_local, when called on an armature child also parented to a bone, appears to be broken.
                # At the very least, the results contradict the docs...  
                armature_relative_transform = obj.parent.matrix_world.inverted() @ obj.matrix_world
                transform = obj.parent.data.bones[obj.parent_bone].matrix_local.inverted() @ armature_relative_transform 

            else:
                if obj.parent is not None:
                    if obj.parent.type == "ARMATURE":
                        model.parent = obj.parent.parent.name if obj.parent.parent else ""
                        transform = obj.parent.matrix_local @ transform
                    else:
                        model.parent = obj.parent.name

            local_translation, local_rotation, _ = transform.decompose()
            model.transform.rotation = convert_rotation_space(local_rotation)  
            model.transform.translation = convert_vector_space(local_translation)

        if obj.type in MESH_OBJECT_TYPES and not skeleton_only:

            # Vertex groups are often used for purposes other than skinning.
            # Here we gather all vgroups and select the ones that reference
            # objects included in the export.
            valid_vgroup_indices : Set[int] = set()
            if model.model_type == ModelType.SKIN:
                valid_vgroups = [group for group in obj.vertex_groups if group.name in exported_object_names]
                valid_vgroup_indices = { group.index for group in valid_vgroups }
                model.bone_map = [ group.name for group in valid_vgroups ]

            mesh = obj.to_mesh()
            model.geometry = create_mesh_geometry(mesh, valid_vgroup_indices)

            obj.to_mesh_clear()

            _, _, world_scale = obj.matrix_world.decompose()
            world_scale = convert_scale_space(world_scale)
            scale_segments(world_scale, model.geometry)
                
            for segment in model.geometry:
                if len(segment.positions) > MAX_MSH_VERTEX_COUNT:
                    raise RuntimeError(f"Object '{obj.name}' has resulted in a .msh geometry segment that has "
                                       f"more than {MAX_MSH_VERTEX_COUNT} vertices! Split the object's mesh up "
                                       f"and try again!")

        if get_is_collision_primitive(obj):
            model.collisionprimitive = get_collision_primitive(obj)

        model.hidden = model.name in blender_objects_to_hide

        models_list.append(model)

    # We removed all composite bones after looking through the objects,
    # so the bones left are all pure and we add them all here.
    return (models_list + list(pure_bones_from_armature.values()), armature_found)



def create_parents_set() -> Set[str]:
    """ Creates a set with the names of the Blender objects from the current scene
        that have at least one child. """
        
    parents = set()

    for obj in bpy.context.scene.objects:
        if obj.parent is not None:
            parents.add(obj.parent.name)

    return parents

def create_mesh_geometry(mesh: bpy.types.Mesh, valid_vgroup_indices: Set[int]) -> List[GeometrySegment]:
    """ Creates a list of GeometrySegment objects from a Blender mesh.
        Does NOT create triangle strips in the GeometrySegment however. """

    # We have to do this for all meshes to account for sharp edges
    mesh.calc_normals_split()

    mesh.validate_material_indices()
    mesh.calc_loop_triangles()

    material_count = max(len(mesh.materials), 1)

    segments: List[GeometrySegment] = [GeometrySegment() for i in range(material_count)]
    vertex_cache = [dict() for i in range(material_count)]
    vertex_remap: List[Dict[Tuple[int, int], int]] = [dict() for i in range(material_count)]
    polygons: List[Set[int]] = [set() for i in range(material_count)]

    if mesh.color_attributes.active_color is not None:
        for segment in segments:
            segment.colors = []

    if valid_vgroup_indices:
        for segment in segments:
            segment.weights = []

    for segment, material in zip(segments, mesh.materials):
        segment.material_name = material.name

    def add_vertex(material_index: int, vertex_index: int, loop_index: int) -> int:
        nonlocal segments, vertex_remap

        vertex_cache_miss_index = -1
        segment = segments[material_index]
        cache = vertex_cache[material_index]
        remap = vertex_remap[material_index]

        # always use loop normals since we always calculate a custom split set        
        vertex_normal = Vector( mesh.loops[loop_index].normal )

        def get_cache_vertex():
            yield mesh.vertices[vertex_index].co.x
            yield mesh.vertices[vertex_index].co.y
            yield mesh.vertices[vertex_index].co.z

            yield vertex_normal.x
            yield vertex_normal.y
            yield vertex_normal.z

            if mesh.uv_layers.active is not None:
                yield mesh.uv_layers.active.data[loop_index].uv.x
                yield mesh.uv_layers.active.data[loop_index].uv.y

            if segment.colors is not None:
                data_type = mesh.color_attributes.active_color.data_type
                if data_type == "FLOAT_COLOR" or data_type == "BYTE_COLOR":
                    for v in mesh.color_attributes.active_color.data[vertex_index].color:
                        yield v

            if segment.weights is not None:
                for v in mesh.vertices[vertex_index].groups:
                    if v.group in valid_vgroup_indices:                    
                        yield v.group
                        yield v.weight

        vertex_cache_entry = tuple(get_cache_vertex())
        cached_vertex_index = cache.get(vertex_cache_entry, vertex_cache_miss_index)

        if cached_vertex_index != vertex_cache_miss_index:
            remap[(vertex_index, loop_index)] = cached_vertex_index

            return cached_vertex_index

        new_index: int = len(segment.positions)
        cache[vertex_cache_entry] = new_index
        remap[(vertex_index, loop_index)] = new_index

        segment.positions.append(convert_vector_space(mesh.vertices[vertex_index].co))
        segment.normals.append(convert_vector_space(vertex_normal))

        if mesh.uv_layers.active is None:
            segment.texcoords.append(Vector((0.0, 0.0)))
        else:
            segment.texcoords.append(mesh.uv_layers.active.data[loop_index].uv.copy())

        if segment.colors is not None:
            data_type = mesh.color_attributes.active_color.data_type
            if data_type == "FLOAT_COLOR" or data_type == "BYTE_COLOR":
                segment.colors.append(list(mesh.color_attributes.active_color.data[vertex_index].color))

        if segment.weights is not None:
            groups = mesh.vertices[vertex_index].groups
            segment.weights.append([VertexWeight(v.weight, v.group) for v in groups if v.group in valid_vgroup_indices])

        return new_index

    for tri in mesh.loop_triangles:
        polygons[tri.material_index].add(tri.polygon_index)
        segments[tri.material_index].triangles.append([
            add_vertex(tri.material_index, tri.vertices[0], tri.loops[0]),
            add_vertex(tri.material_index, tri.vertices[1], tri.loops[1]),
            add_vertex(tri.material_index, tri.vertices[2], tri.loops[2])])

    for segment, remap, polys in zip(segments, vertex_remap, polygons):
        for poly_index in polys:
            poly = mesh.polygons[poly_index]

            segment.polygons.append([remap[(v, l)] for v, l in zip(poly.vertices, poly.loop_indices)])

    return segments

def get_model_type(obj: bpy.types.Object, armature_found: bpy.types.Object) -> ModelType:
    """ Get the ModelType for a Blender object. """

    if obj.type in MESH_OBJECT_TYPES:
        # Objects can have vgroups for non-skinning purposes.
        # If we can find one vgroup that shares a name with a bone in the 
        # armature, we know the vgroup is for weighting purposes and thus
        # the object is a skin.  Otherwise, interpret it as a static mesh.

        # We must also check that an armature included in the export
        # and that it is the same one this potential skin is weighting to.
        # If we failed to do this, a user could export a selected object
        # that is a skin, but the weight data in the export would reference
        # nonexistent models!
        if (obj.vertex_groups and armature_found and 
            obj.parent and obj.parent.name == armature_found.name):
            
            for vgroup in obj.vertex_groups:
                if vgroup.name in armature_found.data.bones:
                    return ModelType.SKIN

            return ModelType.STATIC
        
        else:
            return ModelType.STATIC

    return ModelType.NULL

def get_is_model_hidden(obj: bpy.types.Object) -> bool:
    """ Gets if a Blender object should be marked as hidden in the .msh file. """

    if obj.hide_get():
        return True

    name = obj.name.lower()

    if name.startswith("c_"):
        return True
    if name.startswith("sv_"):
        return True
    if name.startswith("p_"):
        return True
    if name.startswith("collision"):
        return True

    if obj.type not in MESH_OBJECT_TYPES:
        return True

    if name.endswith("_lod2"):
        return True
    if name.endswith("_lod3"):
        return True
    if name.endswith("_lowrez"):
        return True
    if name.endswith("_lowres"):
        return True

    return False

def get_is_collision_primitive(obj: bpy.types.Object) -> bool:
    """ Gets if a Blender object represents a collision primitive. """

    name = obj.name.lower()

    return name.startswith("p_")

def get_collision_primitive(obj: bpy.types.Object) -> CollisionPrimitive:
    """ Gets the CollisionPrimitive of an object or raises an error if
        it can't. """

    primitive = CollisionPrimitive()
    primitive.shape = get_collision_primitive_shape(obj)

    if primitive.shape == CollisionPrimitiveShape.SPHERE:
        # Tolerate a 5% difference to account for icospheres with 2 subdivisions.
        if not (math.isclose(obj.dimensions[0], obj.dimensions[1], rel_tol=0.05) and
                math.isclose(obj.dimensions[0], obj.dimensions[2], rel_tol=0.05)):
            raise RuntimeError(f"Object '{obj.name}' is being used as a sphere collision "
                               f"primitive but it's dimensions are not uniform!")

        primitive.radius = max(obj.dimensions[0], obj.dimensions[1], obj.dimensions[2]) * 0.5
    elif primitive.shape == CollisionPrimitiveShape.CYLINDER:
        primitive.radius = max(obj.dimensions[0], obj.dimensions[1]) * 0.5
        primitive.height = obj.dimensions[2]
    elif primitive.shape == CollisionPrimitiveShape.BOX:
        primitive.radius = obj.dimensions[0] * 0.5
        primitive.height = obj.dimensions[2] * 0.5
        primitive.length = obj.dimensions[1] * 0.5

    return primitive




def get_collision_primitive_shape(obj: bpy.types.Object) -> CollisionPrimitiveShape:
    """ Gets the CollisionPrimitiveShape of an object or raises an error if
        it can't. """

    # arc170 fighter has examples of box colliders without proper naming
    # and cis_hover_aat has a cylinder which is named p_vehiclesphere.
    # To export these properly we must check the collision_prim property
    # that was assigned on import BEFORE looking at the name.
    prim_type = obj.swbf_msh_coll_prim.prim_type
    if prim_type in [item.value for item in CollisionPrimitiveShape]:
        return CollisionPrimitiveShape(prim_type)

    name = obj.name.lower()

    if "sphere" in name or "sphr" in name or "spr" in name:
        return CollisionPrimitiveShape.SPHERE
    if "cylinder" in name or "cyln" in name or "cyl" in name:
        return CollisionPrimitiveShape.CYLINDER
    if "box" in name or "cube" in name or "cuboid" in name:
        return CollisionPrimitiveShape.BOX

    raise RuntimeError(f"Object '{obj.name}' has no primitive type specified in it's name!")


def check_for_bad_lod_suffix(obj: bpy.types.Object):
    """ Checks if the object has an LOD suffix that is known to be ignored by  """

    name = obj.name.lower()
    failure_message = f"Object '{obj.name}' has unknown LOD suffix at the end of it's name!"

    if name.endswith("_lod1"):
        raise RuntimeError(failure_message)
    
    for i in range(4, 10):
        if name.endswith(f"_lod{i}"):
            raise RuntimeError(failure_message)

def select_objects(export_target: str) -> List[bpy.types.Object]:
    """ Returns a list of objects to export. """

    if export_target == "SCENE" or not export_target in {"SELECTED", "SELECTED_WITH_CHILDREN"}:
        return list(bpy.context.scene.objects)

    objects = list(bpy.context.selected_objects)
    added = {obj.name for obj in objects}

    if export_target == "SELECTED_WITH_CHILDREN":
        children = []

        def add_children(parent):
            nonlocal children
            nonlocal added

            for obj in bpy.context.scene.objects:
                if obj.parent == parent and obj.name not in added:
                    children.append(obj)
                    added.add(obj.name)

                    add_children(obj)

        
        for obj in objects:
            add_children(obj)

        objects = objects + children

    parents = []

    for obj in objects:
        parent = obj.parent

        while parent is not None:
            if parent.name not in added:
                parents.append(parent)
                added.add(parent.name)

            parent = parent.parent

    return objects + parents









def expand_armature(armature: bpy.types.Object) -> Dict[str, Model]:

    proper_BONES = get_real_BONES(armature)

    bones: Dict[str, Model] = {}

    for bone in armature.data.bones:
        model = Model()

        transform = bone.matrix_local

        if bone.parent:
            transform = bone.parent.matrix_local.inverted() @ transform
            model.parent = bone.parent.name
        # If the bone has no parent_bone:
        #   set model parent to SKIN object if there is one
        #   set model parent to armature parent if there is one
        else:

            bone_world_matrix = get_bone_world_matrix(armature, bone.name)
            parent_obj = None

            for child_obj in armature.original.children:
                if child_obj.vertex_groups and not get_is_model_hidden(child_obj) and not child_obj.parent_bone:
                    #model.parent = child_obj.name
                    parent_obj = child_obj
                    break

            if parent_obj:
                transform = parent_obj.matrix_world.inverted() @ bone_world_matrix
                model.parent = parent_obj.name
            elif not parent_obj and armature.parent:
                transform = armature.parent.matrix_world.inverted() @ bone_world_matrix 
                model.parent = armature.parent.name
            else:
                transform = bone_world_matrix
                model.parent = ""



        local_translation, local_rotation, _ = transform.decompose()

        model.model_type = ModelType.BONE if bone.name in proper_BONES else ModelType.NULL
        model.name = bone.name
        model.hidden = True
        model.transform.rotation = convert_rotation_space(local_rotation)
        model.transform.translation = convert_vector_space(local_translation)

        bones[bone.name] = model

    return bones
