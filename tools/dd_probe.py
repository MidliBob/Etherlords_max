#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""dd_probe.py — точечный дизассемблер + поиск vtable-вызовов DirectDraw для Etherlords.exe"""
import sys, struct, json
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

EXE = sys.argv[1] if len(sys.argv) > 1 else "Etherlords.exe"
pe = pefile.PE(EXE, fast_load=True)
data = open(EXE, "rb").read()
BASE = pe.OPTIONAL_HEADER.ImageBase
secs = [(s.VirtualAddress, s.Misc_VirtualSize, s.PointerToRawData, s.SizeOfRawData,
         s.Name.rstrip(b"\x00").decode("latin1")) for s in pe.sections]

def off2va(off):
    for va, vs, raw, rs, nm in secs:
        if raw <= off < raw + rs:
            return BASE + va + (off - raw), nm
    return None, None

def va2off(va):
    rva = va - BASE
    for va_, vs, raw, rs, nm in secs:
        if va_ <= rva < va_ + max(vs, rs):
            return raw + (rva - va_), nm
    return None, None

MD = Cs(CS_ARCH_X86, CS_MODE_32)

def dis(off, n=40, back=0):
    va, nm = off2va(off)
    start = off - back
    chunk = data[start:start + n * 7]
    out = []
    for ins in MD.disasm(chunk, BASE + (start - off) + va):
        fo = start + (ins.address - (BASE + (start - off) + va))
        out.append((fo, ins.address, f"{ins.mnemonic} {ins.op_str}"))
        if len(out) >= n:
            break
    return out, nm

def show(title, off, n=40, back=0):
    ins, nm = dis(off, n, back)
    print(f"\n===== {title}  (file {off:#010x}, sect {nm}) =====")
    for fo, va, txt in ins:
        mark = ">>" if fo == off else "  "
        print(f"{mark} {va:#010x} [{fo:#010x}] {txt}")

# ---- 1. окна вокруг xref'ов VideoResolution / %dx%d / FullScreen ----
TARGETS = {
    "VideoResolution#1": 0x2db9d, "VideoResolution#2": 0x2e436,
    "VideoResolution#3": 0x2ed3a, "VideoResolution#4": 0x2f731,
    "pctdx%d#1": 0x2e418, "pctdx%d#2": 0x2f70f,
    "FullScreen#1": 0x2dc0b, "FullScreen#2": 0x2e480,
}
for t, o in TARGETS.items():
    show(t, o, n=34, back=14)

# ---- 2. vtable-вызовы DirectDraw (IDirectDraw7) ----
VT = {0x18: "CreateSurface(6)", 0x20: "EnumDisplayModes(8)", 0x30: "GetDisplayMode(12)",
      0x50: "SetCooperativeLevel(20)", 0x54: "SetDisplayMode(21)", 0x58: "WaitForVerticalBlank(22)"}
REGCODE = {0x50: "eax", 0x51: "ecx", 0x52: "edx", 0x53: "ebx", 0x55: "ebp", 0x56: "esi", 0x57: "edi"}
print("\n\n########## DirectDraw vtable calls ##########")
for disp, name in VT.items():
    for rc, rn in REGCODE.items():
        pat = bytes([0xFF, rc, disp])
        i = data.find(pat)
        cnt = 0
        while i != -1 and cnt < 12:
            va, nm = off2va(i)
            if nm == ".text":
                print(f"  {name:26s} call [{rn}+{disp:#x}]  file={i:#010x} va={va:#010x}")
                cnt += 1
            i = data.find(pat, i + 1)
