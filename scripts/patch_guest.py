#!/usr/bin/env python3
"""Make Android 8.1 bionic avoid a syscall the iOS runtime does not implement.

The stock Twoyi runtime implements the syscall ABI used by Android 13. Android
8.1's bionic calls sched_get_priority_max (arm64 syscall 125), which the runtime
does not provide, so boot dies with NEO_ABI_MISSING. Rewrite the wrapper to
return 99 directly instead of issuing svc #0.

Usage: patch_guest.py PATH/TO/libc.so
"""
import pathlib
import struct
import sys

libc = pathlib.Path(sys.argv[1])
data = bytearray(libc.read_bytes())


def movz(reg, imm):
    return struct.pack('<I', 0xD2800000 | (imm << 5) | reg)


SVC = struct.pack('<I', 0xD4000001)
needle = movz(8, 125)  # mov x8, #125 (sched_get_priority_max)
i = data.find(needle)
if i < 0:
    sys.exit('sched_get_priority_max wrapper not found')
if data[i + 4:i + 8] != SVC:
    sys.exit('unexpected wrapper layout after mov x8,#125')

data[i + 4:i + 8] = movz(0, 99)  # mov x0, #99; rest of wrapper returns it
libc.write_bytes(data)
print(f'patched {libc} at 0x{i:x}: svc -> mov x0,#99')
