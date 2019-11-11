
import io
import struct

class Writer:
    def __init__(self, file, chunk_id: str, parent=None):
        self.file = file
        self.size: int = 0
        self.size_pos = None
        self.parent = parent

        self.file.write(bytes(chunk_id[0:4], "ascii"))

    def __enter__(self):
        self.size_pos = self.file.tell()
        self.file.write(struct.pack(f"<I", 0))

        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self.size > self.MAX_SIZE:
            raise OverflowError(f".msh file overflowed max size. size = {self.size} MAX_SIZE = {self.MAX_SIZE}")

        if (self.size % 4) > 0:
            padding = 4 - (self.size % 4)
            self.write_bytes(bytes([0 for i in range(padding)]))

        head_pos = self.file.tell()
        self.file.seek(self.size_pos)
        self.file.write(struct.pack(f"<I", self.size))
        self.file.seek(head_pos)

        if self.parent is not None:
            self.parent.size += self.size

    def write_bytes(self, packed_bytes):
        self.size += len(packed_bytes)
        self.file.write(packed_bytes)

    def write_string(self, string: str):
        self.write_bytes(bytes(string, "utf-8"))
        self.write_bytes(b'\0')

    def write_i8(self, *ints):
        self.write_bytes(struct.pack(f"<{len(ints)}b", *ints))

    def write_u8(self, *ints):
        self.write_bytes(struct.pack(f"<{len(ints)}B", *ints))

    def write_i16(self, *ints):
        self.write_bytes(struct.pack(f"<{len(ints)}h", *ints))

    def write_u16(self, *ints):
        self.write_bytes(struct.pack(f"<{len(ints)}H", *ints))

    def write_i32(self, *ints):
        self.write_bytes(struct.pack(f"<{len(ints)}i", *ints))

    def write_u32(self, *ints):
        self.write_bytes(struct.pack(f"<{len(ints)}I", *ints))

    def write_f32(self, *floats):
        self.write_bytes(struct.pack(f"<{len(floats)}f", *floats))

    def create_child(self, child_id: str):
        child = Writer(self.file, chunk_id=child_id, parent=self)
        self.size += 8

        return child

    MAX_SIZE: int = 2147483647 - 8
