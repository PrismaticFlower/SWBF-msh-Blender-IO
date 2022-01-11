""" Contains functions for extracting a scene from a .msh file"""

from itertools import islice
from typing import Dict
from .msh_scene import Scene
from .msh_model import *
from .msh_material import *
from .msh_utilities import *

from .crc import *

from .chunked_file_reader import Reader



# Current model position
model_counter = 0

# Used to remap MNDX to the MODL's actual position
mndx_remap : Dict[int, int]  = {}

# How much to print
debug_level = 0


'''
Debug levels just indicate how much info should be printed.
0 = nothing
1 = just blurbs about valuable info in the chunks
2 = #1 + full chunk structure
'''
def read_scene(input_file, anim_only=False, debug=0) -> Scene:

    global debug_level
    debug_level = debug

    scene = Scene()
    scene.models = []
    scene.materials = {}

    global mndx_remap
    mndx_remap = {}

    global model_counter
    model_counter = 0

    with Reader(file=input_file, debug=debug_level>0) as head:

        head.skip_until("HEDR")

        with head.read_child() as hedr:

            while hedr.could_have_child():

                next_header = hedr.peak_next_header()

                if next_header == "MSH2":

                    with hedr.read_child() as msh2:
                        
                        if not anim_only:
                            materials_list = []

                            while (msh2.could_have_child()):

                                next_header = msh2.peak_next_header()

                                if next_header == "SINF":
                                    with msh2.read_child() as sinf:
                                        pass

                                elif next_header == "MATL":
                                    with msh2.read_child() as matl:
                                        materials_list += _read_matl_and_get_materials_list(matl)
                                        for i,mat in enumerate(materials_list):
                                            scene.materials[mat.name] = mat

                                elif next_header == "MODL":
                                    with msh2.read_child() as modl:
                                        scene.models.append(_read_modl(modl, materials_list))

                                else:
                                    msh2.skip_bytes(1)

                elif next_header == "SKL2":
                    with hedr.read_child() as skl2:
                        num_bones = skl2.read_u32()
                        scene.skeleton = [skl2.read_u32(5)[0] for i in range(num_bones)]
                    
                elif next_header == "ANM2":
                    with hedr.read_child() as anm2:
                        scene.animation = _read_anm2(anm2)

                else:
                    hedr.skip_bytes(1)

    # Print models in skeleton
    if scene.skeleton and debug_level > 0:
        print("Skeleton models: ")
        for model in scene.models:
            for i in range(len(scene.skeleton)):                
                if to_crc(model.name) == scene.skeleton[i]:
                    print("\t" + model.name)
                    if model.model_type == ModelType.SKIN:
                        scene.skeleton.pop(i)
                    break

    '''
    Iterate through every vertex weight in the scene and 
    change its index to directly reference its bone's index.  
    It will reference the MNDX of its bone's MODL by default.
    '''
    
    for model in scene.models:
        if model.geometry:
            for seg in model.geometry:
                if seg.weights:
                    for weight_set in seg.weights:
                        for vweight in weight_set:

                            if vweight.bone in mndx_remap:
                                vweight.bone = mndx_remap[vweight.bone]
                            else:
                                vweight.bone = 0

    # So in the new republic boba example, the weights aimed for bone_head instead map to sv_jettrooper...


    #for key, val in mndx_remap.items():
        #if scene.models[val].name == "bone_head" or scene.models[val].name == "sv_jettrooper":
        #print("Key: {} is mapped to val: {}".format(key, val))
        #print("Key: {}, val {} is model: {}".format(key, val, scene.models[val].name))

                    
    return scene


def _read_matl_and_get_materials_list(matl: Reader) -> List[Material]:
    materials_list: List[Material] = []

    num_mats = matl.read_u32()

    for _ in range(num_mats):
        with matl.read_child() as matd:
            materials_list.append(_read_matd(matd))

    return materials_list



def _read_matd(matd: Reader) -> Material:

    mat = Material()

    while matd.could_have_child():

        next_header = matd.peak_next_header()

        if next_header == "NAME":
            with matd.read_child() as name:
                mat.name = name.read_string()

        elif next_header == "DATA":
            with matd.read_child() as data:
                data.read_f32(4) # Diffuse Color (Seams to get ignored by modelmunge)
                mat.specular_color = data.read_f32(4)
                data.read_f32(4) # Ambient Color (Seams to get ignored by modelmunge and Zero(?))
                data.read_f32()  # Specular Exponent/Decay (Gets ignored by RedEngine in SWBFII for all known materials)    
    
        elif next_header == "ATRB":
            with matd.read_child() as atrb:
                mat.flags = MaterialFlags(atrb.read_u8())
                mat.rendertype = Rendertype(atrb.read_u8())
                mat.data = atrb.read_u8(2)

        elif next_header == "TX0D":
            with matd.read_child() as tx0d:
                mat.texture0 = tx0d.read_string()

        elif next_header == "TX1D":
            with matd.read_child() as tx1d:
                mat.texture1 = tx1d.read_string()

        elif next_header == "TX2D":
            with matd.read_child() as tx2d:
                mat.texture2 = tx2d.read_string()

        elif next_header == "TX3D":
            with matd.read_child() as tx3d:
                mat.texture3 = tx3d.read_string()

        else:
            matd.skip_bytes(1)

    return mat


def _read_modl(modl: Reader, materials_list: List[Material]) -> Model:

    model = Model()

    while modl.could_have_child():

        next_header = modl.peak_next_header()

        if next_header == "MTYP":
            with modl.read_child() as mtyp:
                model.model_type = ModelType(mtyp.read_u32())

        elif next_header == "MNDX":
            with modl.read_child() as mndx:
                index = mndx.read_u32()


                global model_counter
                #print(mndx.indent + "MNDX doesn't match counter, expected: {} found: {}".format(model_counter, index))
                #print("Model counter: {} MNDX: {}".format(model_counter, index))

                global mndx_remap
                mndx_remap[index] = model_counter

                model_counter += 1

        elif next_header == "NAME":
            with modl.read_child() as name:
                model.name = name.read_string()

        elif next_header == "PRNT":
            with modl.read_child() as prnt:
                model.parent = prnt.read_string()

        elif next_header == "FLGS":
            with modl.read_child() as flgs:
                model.hidden = flgs.read_u32()

        elif next_header == "TRAN":
            with modl.read_child() as tran:
                model.transform = _read_tran(tran)

        elif next_header == "GEOM":
            model.geometry = []
            envelope = []

            with modl.read_child() as geom:

                while geom.could_have_child():
                    next_header_geom = geom.peak_next_header()

                    if next_header_geom == "SEGM":
                        with geom.read_child() as segm:
                           model.geometry.append(_read_segm(segm, materials_list))

                    elif next_header_geom == "ENVL":
                        with geom.read_child() as envl:
                            num_indicies = envl.read_u32()
                            envelope += [envl.read_u32() for _ in range(num_indicies)]
                    
                    else:
                        geom.skip_bytes(1)

            for seg in model.geometry:
                if seg.weights and envelope:
                    for weight_set in seg.weights:
                        for vertex_weight in weight_set:
                            vertex_weight.bone = envelope[vertex_weight.bone]

        elif next_header == "SWCI":
            prim = CollisionPrimitive()
            with modl.read_child() as swci:
                prim.shape = CollisionPrimitiveShape(swci.read_u32())
                prim.radius = swci.read_f32()
                prim.height = swci.read_f32()
                prim.length = swci.read_f32()
            model.collisionprimitive = prim

        else:
            modl.skip_bytes(1)

    global debug_level
    if debug_level > 0:
        print(modl.indent + "Read model " + model.name + " of type: " + str(model.model_type)[10:])

    return model


def _read_tran(tran: Reader) -> ModelTransform:

    xform = ModelTransform()

    tran.skip_bytes(12) #ignore scale

    xform.rotation = tran.read_quat()
    xform.translation = tran.read_vec()

    global debug_level
    if debug_level > 0:
        print(tran.indent + "Rot: {} Loc: {}".format(str(xform.rotation), str(xform.translation)))

    return xform


def _read_segm(segm: Reader, materials_list: List[Material]) -> GeometrySegment:

    geometry_seg = GeometrySegment()

    while segm.could_have_child():

        next_header = segm.peak_next_header()

        if next_header == "MATI":
            with segm.read_child() as mati:
                geometry_seg.material_name = materials_list[mati.read_u32()].name

        elif next_header == "POSL":
            with segm.read_child() as posl:
                num_positions = posl.read_u32()

                for _ in range(num_positions):
                    geometry_seg.positions.append(Vector(posl.read_f32(3)))

        elif next_header == "NRML":
            with segm.read_child() as nrml:
                num_normals = nrml.read_u32()
                
                for _ in range(num_positions):
                    geometry_seg.normals.append(Vector(nrml.read_f32(3))) 

        elif next_header == "CLRL":
            geometry_seg.colors = []

            with segm.read_child() as clrl:
                num_colors = clrl.read_u32()

                for _ in range(num_colors):
                    geometry_seg.colors += unpack_color(clrl.read_u32())

        elif next_header == "UV0L":
            with segm.read_child() as uv0l:
                num_texcoords = uv0l.read_u32()

                for _ in range(num_texcoords):
                    geometry_seg.texcoords.append(Vector(uv0l.read_f32(2))) 

        elif next_header == "NDXL":
            
            with segm.read_child() as ndxl:
                pass
                '''
                num_polygons = ndxl.read_u32()

                for _ in range(num_polygons):
                    polygon = ndxl.read_u16(ndxl.read_u16())
                    geometry_seg.polygons.append(polygon)
                '''

        elif next_header == "NDXT":
            with segm.read_child() as ndxt:
                num_tris = ndxt.read_u32()

                for _ in range(num_tris):
                    geometry_seg.triangles.append(ndxt.read_u16(3))
        # 
        elif next_header == "STRP":
            strips : List[List[int]] = []

            with segm.read_child() as strp:
                num_indicies = strp.read_u32()

                num_indicies_read = 0

                curr_strip = []
                previous_flag = False

                if num_indicies > 0:
                    index, index1 = strp.read_u16(2)
                    curr_strip = [index & 0x7fff, index1 & 0x7fff]
                    num_indicies_read += 2

                for i in range(num_indicies - 2):
                    index = strp.read_u16(1)

                    if index & 0x8000 > 0:
                        index = index & 0x7fff

                        if previous_flag:
                            previous_flag = False
                            curr_strip.append(index)
                            strips.append(curr_strip[:-2])
                            curr_strip = curr_strip[-2:]
                            continue
                        else:
                            previous_flag = True

                    else:
                        previous_flag = False
                     
                    curr_strip.append(index)

            geometry_seg.triangle_strips = strips

            #if segm.read_u16 != 0: #trailing 0 bug https://schlechtwetterfront.github.io/ze_filetypes/msh.html#STRP
            #    segm.skip_bytes(-2)

        elif next_header == "WGHT":
            with segm.read_child() as wght:
                
                geometry_seg.weights = []
                num_weights = wght.read_u32()

                for _ in range(num_weights):
                    weight_set = []
                    for _ in range(4):
                        index = wght.read_u32()
                        value = wght.read_f32()

                        if value > 0.000001:
                            weight_set.append(VertexWeight(value,index))

                    geometry_seg.weights.append(weight_set)

        else:
            segm.skip_bytes(1)

    return geometry_seg



def _read_anm2(anm2: Reader) -> Animation:

    anim = Animation()

    while anm2.could_have_child():

        next_header = anm2.peak_next_header()

        if next_header == "CYCL":
            with anm2.read_child() as cycl:
                # Dont even know what CYCL's data does.  Tried playing 
                # with the values but didn't change anything in zenasset or ingame...

                '''
                num_anims = cycl.read_u32()

                for _ in range(num_anims):
                    cycl.skip_bytes(64)
                    print("CYCL play style {}".format(cycl.read_u32(4)[1]))
                '''
                pass

        elif next_header == "KFR3":
            with anm2.read_child() as kfr3:

                num_bones = kfr3.read_u32()

                bone_crcs = []

                for _ in range(num_bones):

                    bone_crc = kfr3.read_u32()
                    bone_crcs.append(bone_crc)

                    frames = ([],[])

                    frametype = kfr3.read_u32()

                    num_loc_frames = kfr3.read_u32()
                    num_rot_frames = kfr3.read_u32()

                    for i in range(num_loc_frames):
                        frames[0].append(TranslationFrame(kfr3.read_u32(), kfr3.read_vec()))

                    for i in range(num_rot_frames):
                        frames[1].append(RotationFrame(kfr3.read_u32(), kfr3.read_quat()))

                    anim.bone_frames[bone_crc] = frames


                for bone_crc in sorted(bone_crcs):

                    bone_frames = anim.bone_frames[bone_crc]

                    loc_frames = bone_frames[0]
                    rot_frames = bone_frames[1]
        else:
            anm2.skip_bytes(1)

    return anim



