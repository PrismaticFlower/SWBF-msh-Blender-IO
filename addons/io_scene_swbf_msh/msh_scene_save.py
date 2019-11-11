""" Contains functions for saving a Scene to a .msh file.  """

from itertools import islice
from .msh_scene import Scene, create_scene_aabb
from .msh_model import *
from .msh_writer import Writer
from .msh_utilities import *

def save_scene(output_file, scene: Scene):
    """ Saves scene to the supplied file. """

    with Writer(file=output_file, chunk_id="HEDR") as hedr:
        with hedr.create_child("MSH2") as msh2:

            with msh2.create_child("SINF") as sinf:
                _write_sinf(sinf, scene)

            with msh2.create_child("MATL") as matl:
                _write_matl(matl, scene)

            for index, model in enumerate(scene.models):
                with msh2.create_child("MODL") as modl:
                    _write_modl(modl, model, index)

        with hedr.create_child("CL1L"):
            pass

def _write_sinf(sinf: Writer, scene: Scene):
    with sinf.create_child("NAME") as name:
        name.write_string(scene.name)

    with sinf.create_child("FRAM") as fram:
        fram.write_i32(0, 1)
        fram.write_f32(29.97003)

    with sinf.create_child("BBOX") as bbox:
        aabb = create_scene_aabb(scene)

        bbox_position = div_vec(add_vec(aabb.min_, aabb.max_), Vector((2.0, 2.0, 2.0)))
        bbox_size = div_vec(sub_vec(aabb.max_, aabb.min_), Vector((2.0, 2.0, 2.0)))
        bbox_length = bbox_size.length

        bbox.write_f32(0.0, 0.0, 0.0, 1.0)
        bbox.write_f32(bbox_position.x, bbox_position.y, bbox_position.z)
        bbox.write_f32(bbox_size.x, bbox_size.y, bbox_size.z, bbox_length)

def _write_matl(matl: Writer, scene: Scene):
    # TODO: Material support.

    matl.write_u32(1) # Material count.

    with matl.create_child("MATD") as matd:
        with matd.create_child("NAME") as name:
            name.write_string(f"{scene.name}Material") # TODO: Proper name with material support.

        with matd.create_child("DATA") as data:
            data.write_f32(1.0, 1.0, 1.0, 1.0) # Diffuse Color (Seams to get ignored by modelmunge)
            data.write_f32(1.0, 1.0, 1.0, 1.0) # Specular Color
            data.write_f32(0.0, 0.0, 0.0, 1.0) # Ambient Color (Seams to get ignored by modelmunge and Zero(?))
            data.write_f32(50.0) # Specular Exponent/Decay (Gets ignored by RedEngine in SWBFII for all known materials)

        with matd.create_child("ATRB") as atrb:
            atrb.write_u8(0) # Material Flags
            atrb.write_u8(0) # Rendertype
            atrb.write_u8(0, 0) # Rendertype Params (Scroll rate, animation divisors, etc)

        with matd.create_child("TX0D") as tx0d:
            tx0d.write_string("null_detailmap.tga")

def _write_modl(modl: Writer, model: Model, index: int):
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
                    _write_segm(segm, segment)

    # TODO: Collision Primitive

def _write_tran(tran: Writer, transform: ModelTransform):
    tran.write_f32(1.0, 1.0, 1.0) # Scale, ignored by modelmunge
    tran.write_f32(transform.rotation.x, transform.rotation.y, transform.rotation.z, transform.rotation.w)
    tran.write_f32(transform.translation.x, transform.translation.y, transform.translation.z)

def _write_segm(segm: Writer, segment: GeometrySegment):

    with segm.create_child("MATI") as mati:
        mati.write_u32(0)

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
