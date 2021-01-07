
import io
import struct
import os

class ZAAReader:
    def __init__(self, file, parent=None, indent=0):
        self.file = file
        self.size: int = 0
        self.size_pos = None
        self.parent = parent
        self.indent = "  " * indent #for print debugging


    def __enter__(self):
        self.size_pos = self.file.tell()

        if self.parent is not None:
            self.header = self.read_bytes(4).decode("utf-8")
        else:
            self.header = "HEAD"

        if self.parent is not None:
            self.size = self.read_u32()
        else:
            self.size = os.path.getsize(self.file.name) - 8

        padding_length = 4 - (self.size % 4) if self.size % 4 > 0 else 0
        self.end_pos = self.size_pos + padding_length + self.size + 8

        if self.parent is not None:
            print(self.indent + "Begin " + self.header + ", Size: " + str(self.size) + ", Pos: " + str(self.size_pos))
        else:
            print(self.indent + "Begin head, Size: " + str(self.size) + ", Pos: " + str(self.size_pos))


        return self


    def __exit__(self, exc_type, exc_value, traceback):
        if self.size > self.MAX_SIZE:
            raise OverflowError(f".msh file overflowed max size. size = {self.size} MAX_SIZE = {self.MAX_SIZE}")

        print(self.indent + "End   " + self.header)
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



    def read_child(self):
        child = ZAAReader(self.file, parent=self, indent=int(len(self.indent) / 2) + 1)
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

    def skip_until(self, header):
        while (self.could_have_child() and header not in self.peak_next_header()):
            self.skip_bytes(1)


    def could_have_child(self):
    	return self.end_pos - self.file.tell() >= 8


    MAX_SIZE: int = 2147483647 - 8
