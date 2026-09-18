"""Read the writable filesystem location from an ESP32 merged image."""

import struct


def find_vfs_partition(firmware):
    with open(firmware, "rb") as stream:
        stream.seek(0x8000)
        table = stream.read(0x1000)
    for position in range(0, len(table), 32):
        entry = table[position:position + 32]
        if len(entry) != 32:
            break
        magic, kind, subtype, offset, size, label, _flags = struct.unpack(
            "<HBBLL16sL", entry)
        if magic == 0x50AA and kind == 1 and label.rstrip(b"\0") == b"vfs":
            if subtype != 0x81:
                raise RuntimeError("The firmware vfs partition is not FAT")
            return offset, size
    raise RuntimeError("No FAT vfs partition found in %s" % firmware)
