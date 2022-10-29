"""
Reader class for both zaabin, zaa, and msh files.
"""

import io
import struct
import os

from mathutils import Vector, Quaternion


class Reader:
    def __init__(self, file, parent=None, indent=0, debug=False):
        self.file = file
        self.size: int = 0
        self.size_pos = None
        self.parent = parent
        self.indent = "  " * indent #for print debugging, should be stored as str so msh_scene_read can access it
        self.debug = debug


    def __enter__(self):
        self.size_pos = self.file.tell()

        if self.parent is not None:
            self.header = self.read_bytes(4).decode("utf-8")
        else:
            self.header = "File"

        if self.parent is not None:
            self.size = self.read_u32()
        else:
            self.size = os.path.getsize(self.file.name) - 8
        
        # No padding to multiples of 4.  Files exported from XSI via zetools do not align by 4!
        self.end_pos = self.size_pos + self.size + 8

        if self.debug:
            print("{}Begin {} of Size {} at pos {}:".format(self.indent, self.header, self.size, self.size_pos))

        return self


    def __exit__(self, exc_type, exc_value, traceback):
        if self.size > self.MAX_SIZE:
            raise OverflowError(f"File overflowed max size. size = {self.size} MAX_SIZE = {self.MAX_SIZE}")

        if self.debug:
            print("{}End {} at pos: {}".format(self.indent, self.header, self.end_pos))

        self.file.seek(self.end_pos)



    def read_bytes(self,num_bytes):
        return self.file.read(num_bytes)


    def read_string(self):
        last_byte = self.read_bytes(1)
        result = b''
        while last_byte[0] != 0x0:
            result += last_byte
            last_byte = self.read_bytes(1)

        return result.decode("utf-8")

    def read_i8(self, num=1):
        buf = self.read_bytes(num)
        result = struct.unpack(f"<{num}b", buf)
        return result[0] if num == 1 else result

    def read_u8(self, num=1):
        buf = self.read_bytes(num)
        result = struct.unpack(f"<{num}B", buf)
        return result[0] if num == 1 else result

    def read_i16(self, num=1):
        buf = self.read_bytes(num * 2)
        result = struct.unpack(f"<{num}h", buf)
        return result[0] if num == 1 else result

    def read_u16(self, num=1):
        buf = self.read_bytes(num * 2)
        result = struct.unpack(f"<{num}H", buf)
        return result[0] if num == 1 else result

    def read_i32(self, num=1):
        buf = self.read_bytes(num * 4)
        result = struct.unpack(f"<{num}i", buf)
        return result[0] if num == 1 else result

    def read_u32(self, num=1):
        buf = self.read_bytes(num * 4) 
        result = struct.unpack(f"<{num}I", buf)
        return result[0] if num == 1 else result

    def read_f32(self, num=1):
        buf = self.read_bytes(num * 4)
        result = struct.unpack(f"<{num}f", buf)
        return result[0] if num == 1 else result


    def read_quat(self):
        rot = self.read_f32(4)
        return Quaternion((rot[3], rot[0], rot[1], rot[2]))

    def read_vec(self):
        return Vector(self.read_f32(3))


    def read_child(self):
        child = Reader(self.file, parent=self, indent=int(len(self.indent) / 2) + 1, debug=self.debug)
        return child


    def skip_bytes(self,num):
        self.file.seek(num,1)


    def peak_next_header(self):

        buf = self.read_bytes(4);
        self.file.seek(-4,1)

        try:
            result = buf.decode("utf-8")
            return result
        except:
            return ""

    def get_current_pos(self):
        return self.file.tell()

    def reset_pos(self):
        self.file.seek(self.size_pos - self.file.tell() + 8, 1)

    def how_much_left(self, pos):
        return self.end_pos - pos

    def bytes_remaining(self):
        return self.end_pos - self.file.tell()

    def skip_until(self, header):
        while (self.could_have_child() and header not in self.peak_next_header()):
            self.skip_bytes(1)


    def could_have_child(self):
    	return self.end_pos - self.file.tell() >= 8


    MAX_SIZE: int = 2147483647 - 8
