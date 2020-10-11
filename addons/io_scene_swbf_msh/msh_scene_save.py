""" Contains functions for saving a Scene to a .msh file.  """

from itertools import islice
from typing import Dict
from .msh_scene import Scene, create_scene_aabb
from .msh_model import *
from .msh_material import *
from .msh_writer import Writer
from .msh_utilities import *

from .crc import *

def save_scene(output_file, scene: Scene):
    """ Saves scene to the supplied file. """

    with Writer(file=output_file, chunk_id="HEDR") as hedr:
        with hedr.create_child("MSH2") as msh2:

            with msh2.create_child("SINF") as sinf:
                _write_sinf(sinf, scene)

            material_index: Dict[str, int] = {}

            with msh2.create_child("MATL") as matl:
                material_index = _write_matl_and_get_material_index(matl, scene)

            for index, model in enumerate(scene.models):
                with msh2.create_child("MODL") as modl:
                    _write_modl(modl, model, index, material_index)

        with hedr.create_child("ANM2") as anm2: #simple for now
            for anim in scene.anims:
                _write_anm2(anm2, anim)

        with hedr.create_child("CL1L"):
            pass

def _write_sinf(sinf: Writer, scene: Scene):
    with sinf.create_child("NAME") as name:
        name.write_string(scene.name)

    with sinf.create_child("FRAM") as fram:
        fram.write_i32(0, 20) #test values
        fram.write_f32(10.0) #test values

    with sinf.create_child("BBOX") as bbox:
        aabb = create_scene_aabb(scene)

        bbox_position = div_vec(add_vec(aabb.min_, aabb.max_), Vector((2.0, 2.0, 2.0)))
        bbox_size = div_vec(sub_vec(aabb.max_, aabb.min_), Vector((2.0, 2.0, 2.0)))
        bbox_length = bbox_size.length

        bbox.write_f32(0.0, 0.0, 0.0, 1.0)
        bbox.write_f32(bbox_position.x, bbox_position.y, bbox_position.z)
        bbox.write_f32(bbox_size.x, bbox_size.y, bbox_size.z, bbox_length)

def _write_matl_and_get_material_index(matl: Writer, scene: Scene):
    material_index: Dict[str, int] = {}

    if len(scene.materials) > 0:
        matl.write_u32(len(scene.materials)) # Material count.

        for index, name_material in enumerate(scene.materials.items()):
            with matl.create_child("MATD") as matd:
                material_index[name_material[0]] = index
                _write_matd(matd, name_material[0], name_material[1])
    else:
        matl.write_u32(1) # Material count.

        default_material_name = f"{scene.name}Material"
        material_index[default_material_name] = 0

        with matl.create_child("MATD") as matd:
            _write_matd(matd, default_material_name, Material())

    return material_index

def _write_matd(matd: Writer, material_name: str, material: Material):
    with matd.create_child("NAME") as name:
        name.write_string(material_name)
    with matd.create_child("DATA") as data:
        data.write_f32(1.0, 1.0, 1.0, 1.0) # Diffuse Color (Seams to get ignored by modelmunge)
        data.write_f32(material.specular_color[0], material.specular_color[1],
                       material.specular_color[2], 1.0)
        data.write_f32(0.0, 0.0, 0.0, 1.0) # Ambient Color (Seams to get ignored by modelmunge and Zero(?))
        data.write_f32(50.0) # Specular Exponent/Decay (Gets ignored by RedEngine in SWBFII for all known materials)    
    with matd.create_child("ATRB") as atrb:
        atrb.write_u8(material.flags.value)
        atrb.write_u8(material.rendertype.value)
        atrb.write_u8(material.data[0], material.data[1])

    with matd.create_child("TX0D") as tx0d:
        tx0d.write_string(material.texture0)
    if material.texture1 or material.texture2 or material.texture3:
        with matd.create_child("TX1D") as tx1d:
            tx1d.write_string(material.texture1)

        if material.texture2 or material.texture3:
            with matd.create_child("TX2D") as tx2d:
                tx2d.write_string(material.texture2)

        if material.texture3:
            with matd.create_child("TX3D") as tx3d:
                tx3d.write_string(material.texture3)

def _write_modl(modl: Writer, model: Model, index: int, material_index: Dict[str, int]):
    with modl.create_child("MTYP") as mtyp:
        mtyp.write_u32(model.model_type.value)

    with modl.create_child("MNDX") as mndx:
        mndx.write_u32(index)

    with modl.create_child("NAME") as name:
        name.write_string(model.name)

    if model.parent:
        with modl.create_child("PRNT") as prnt:
            prnt.write_string(model.parent)

    if model.hidden:
        with modl.create_child("FLGS") as flgs:
            flgs.write_u32(1)

    with modl.create_child("TRAN") as tran:
        _write_tran(tran, model.transform)

    if model.geometry is not None:
        with modl.create_child("GEOM") as geom:
            for segment in model.geometry:
                with geom.create_child("SEGM") as segm:
                    _write_segm(segm, segment, material_index)

    if model.collisionprimitive is not None:
        with modl.create_child("SWCI") as swci:
            swci.write_u32(model.collisionprimitive.shape.value)
            swci.write_f32(model.collisionprimitive.radius)
            swci.write_f32(model.collisionprimitive.height)
            swci.write_f32(model.collisionprimitive.length)

def _write_tran(tran: Writer, transform: ModelTransform):
    tran.write_f32(1.0, 1.0, 1.0) # Scale, ignored by modelmunge
    tran.write_f32(transform.rotation.x, transform.rotation.y, transform.rotation.z, transform.rotation.w)
    tran.write_f32(transform.translation.x, transform.translation.y, transform.translation.z)

def _write_segm(segm: Writer, segment: GeometrySegment, material_index: Dict[str, int]):

    with segm.create_child("MATI") as mati:
        mati.write_u32(material_index.get(segment.material_name, 0))

    with segm.create_child("POSL") as posl:
        posl.write_u32(len(segment.positions))

        for position in segment.positions:
            posl.write_f32(position.x, position.y, position.z)

    with segm.create_child("NRML") as nrml:
        nrml.write_u32(len(segment.normals))

        for normal in segment.normals:
            nrml.write_f32(normal.x, normal.y, normal.z)

    if segment.colors is not None:
        with segm.create_child("CLRL") as clrl:
            clrl.write_u32(len(segment.colors))

            for color in segment.colors:
                clrl.write_u32(pack_color(color))

    with segm.create_child("UV0L") as uv0l:
        uv0l.write_u32(len(segment.texcoords))

        for texcoord in segment.texcoords:
            uv0l.write_f32(texcoord.x, texcoord.y)

    with segm.create_child("NDXL") as ndxl:
        ndxl.write_u32(len(segment.polygons))

        for polygon in segment.polygons:
            ndxl.write_u16(len(polygon))

            for index in polygon:
                ndxl.write_u16(index)

    with segm.create_child("NDXT") as ndxt:
        ndxt.write_u32(len(segment.triangles))

        for triangle in segment.triangles:
            ndxt.write_u16(triangle[0], triangle[1], triangle[2])

    with segm.create_child("STRP") as strp:
        strp.write_u32(sum(len(strip) for strip in segment.triangle_strips))

        for strip in segment.triangle_strips:
            strp.write_u16(strip[0] | 0x8000, strip[1] | 0x8000)

            for index in islice(strip, 2, len(strip)):
                strp.write_u16(index)


def _write_anm2(anm2: Writer, anim: Animation):

    with anm2.create_child("CYCL") as cycl:
        
        cycl.write_u32(1)
        cycl.write_string(anim.name)
        
        for _ in range(64 - (len(anim.name) + 1)):
            cycl.write_u8(0)
        
        cycl.write_f32(10.0) #test framerate
        cycl.write_u32(0) #what does play style refer to?
        cycl.write_u32(0, 20) #first frame indices


    with anm2.create_child("KFR3") as kfr3:
        
        kfr3.write_u32(len(anim.bone_transforms.keys()))

        for boneName in anim.bone_transforms.keys():
            kfr3.write_u32(crc(boneName))
            kfr3.write_u32(0) #what is keyframe type?

            kfr3.write_u32(21, 21) #basic testing

            print(boneName)

            for i, xform in enumerate(anim.bone_transforms[boneName]):
                kfr3.write_u32(i)
                kfr3.write_f32(xform.translation.x, xform.translation.y, xform.translation.z)

                print(xform.translation)

            for i, xform in enumerate(anim.bone_transforms[boneName]):
                kfr3.write_u32(i)
                kfr3.write_f32(xform.rotation.x, xform.rotation.y, xform.rotation.z, xform.rotation.w)









