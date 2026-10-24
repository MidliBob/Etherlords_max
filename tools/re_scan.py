#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
re_scan.py — стартовый сканер для поиска «точек правки» под native hi-res / widescreen
в 32-битном Win32 PE старой игры (целевой кейс: Etherlords II / Демиурги).

Ищет (без запуска игры и без дизассемблера уровня IDA):
  1. Строки настроек: VideoResolution, settings.ini, "%dx%d" и готовые "WxH".
  2. Кросс-ссылки (xref) на эти строки -> место, где разрешение читается/валидируется.
  3. Таблицы/пары констант разрешений (640x480, 800x600, 1024x768, 1280x1024 ...).
  4. Float-константы соотношения сторон (4/3, 3/4) -> проекционная матрица.
  5. Графический API: импорт ddraw/d3d8/d3dim + строки LoadLibrary + имена функций
     (SetDisplayMode, EnumDisplayModes, CreateDevice, IDirectDraw7::SetDisplayMode ...).
  6. Для каждой находки: файловое смещение для hex-правки + окно дизассемблирования.

Использование:
    python3 re_scan.py Etherlords.exe [--base 0x400000] [--window 24]

Не модифицирует файл. Только читает и печатает отчёт.
"""
import argparse, json, re, struct, sys
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

RES_PAIRS = [(640,480),(800,600),(1024,768),(1152,864),(1280,720),(1280,800),
             (1280,960),(1280,1024),(1366,768),(1440,900),(1600,900),(1600,1200),
             (1680,1050),(1920,1080),(1920,1200),(2560,1440),(3840,2160)]
ASPECT_FLOATS = {4.0/3.0:"4/3 (aspect)", 3.0/4.0:"3/4 (inv aspect)",
                 16.0/9.0:"16/9", 9.0/16.0:"9/16", 5.0/4.0:"5/4", 4.0/5.0:"4/5"}
CFG_STRINGS = [b"VideoResolution", b"settings.ini", b"Settings.ini", b"SETTINGS.INI",
               b"%dx%d", b"%d x %d", b"%i x %i", b"Resolution", b"ScreenWidth",
               b"ScreenHeight", b"Fullscreen", b"FullScreen", b"windowed"]
GFX_DLLS    = [b"ddraw.dll", b"d3d8.dll", b"d3dim.dll", b"d3d9.dll", b"D3D8.DLL", b"DDRAW.DLL"]
GFX_APIS    = [b"SetDisplayMode", b"EnumDisplayModes", b"CreateDevice", b"Reset",
               b"SetViewport", b"SetTransform", b"DirectDrawCreate", b"Direct3DCreate8",
               b"Direct3DCreate9", b"GetDeviceCaps", b"SetRenderTarget", b"Clear",
               b"BeginScene", b"EndScene", b"Present", b"SetBackBuffer", b"Flip"]


def f32(x):  # float -> little-endian bytes
    return struct.pack("<f", x)


def build_rva_map(pe):
    """RVA -> (section, file_offset_delta)"""
    m = []
    for s in pe.sections:
        m.append((s.VirtualAddress, s.VirtualAddress + max(s.Misc_VirtualSize, s.SizeOfRawData),
                  s.PointerToRawData, s.Name.rstrip(b"\x00").decode("latin1")))
    return m


def rva_to_off(pe, rva, rmap):
    for va, va_end, raw, name in rmap:
        if va <= rva < va_end:
            return raw + (rva - va), name
    return None, None


def find_all(data, needle, start=0):
    out, i = [], data.find(needle, start)
    while i != -1:
        out.append(i)
        i = data.find(needle, i + 1)
    return out


def disasm_window(pe, data, off, base, n_back=8, n_fwd=16, rmap=None):
    """Дизассемблировать небольшой кусок кода вокруг файлового смещения."""
    lines = []
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    # вернёмся назад на n_back инструкций грубо: начнём с off-24 и пропустим до off
    start = max(0, off - 24)
    chunk = data[start:start + 24 + n_fwd * 6]
    try:
        insns = list(md.disasm(chunk, base + start))
    except Exception:
        return ["  <disasm error>"]
    seen_off = False
    for ins in insns:
        fo = start + (ins.address - (base + start))
        mark = ">>" if fo <= off < fo + len(ins.bytes) else "  "
        if fo + len(ins.bytes) > off:
            seen_off = True
        lines.append(f"{mark} {ins.address:#010x}  {ins.mnemonic:8s} {ins.op_str}")
        if seen_off and len([l for l in lines if l.startswith('>>')]) >= 1 and len(lines) > n_fwd:
            break
    return lines[: n_back + n_fwd + 4]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("exe")
    ap.add_argument("--base", type=lambda x: int(x, 0), default=None)
    ap.add_argument("--window", type=int, default=16)
    a = ap.parse_args()

    pe = pefile.PE(a.exe, fast_load=True)
    pe.parse_data_directories(directories=[pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_IMPORT"]])
    data = open(a.exe, "rb").read()
    base = a.base or pe.OPTIONAL_HEADER.ImageBase
    rmap = build_rva_map(pe)
    rep = {"file": a.exe, "image_base": hex(base), "sections": [],
           "strings": [], "xrefs": [], "res_tables": [], "aspect": [], "gfx": []}
    for s in pe.sections:
        rep["sections"].append({"name": s.Name.rstrip(b"\x00").decode("latin1"),
                                "vaddr": hex(s.VirtualAddress),
                                "vsize": s.Misc_VirtualSize,
                                "raw": s.SizeOfRawData,
                                "entropy": round(s.get_entropy(), 3)})

    # ---- 1. строки конфигурации ----
    for needle in CFG_STRINGS + [f"{w}x{h}".encode() for w, h in RES_PAIRS]:
        for off in find_all(data, needle):
            rep["strings"].append({"off": off, "str": needle.decode("latin1", "replace")})

    # ---- 2. xref на строки: ищем RVA строки как imm32 в коде ----
    text = [s for s in pe.sections if s.Name.rstrip(b"\x00") in (b".text", b".code")] or pe.sections[:1]
    for entry in rep["strings"]:
        rva = None
        for va, va_end, raw, name in rmap:
            if raw <= entry["off"] < raw + 0x1000000:
                # approx: only for offsets inside a section
                if raw <= entry["off"]:
                    rva = va + (entry["off"] - raw)
                    break
        if rva is None:
            continue
        pat = struct.pack("<I", base + rva)
        for off in find_all(data, pat):
            rep["xrefs"].append({"str": entry["str"], "str_off": entry["off"],
                                 "xref_off": off, "rva": hex(rva)})

    # ---- 3. таблицы/пары разрешений: ищем imm32 w,h идущие рядом ----
    for w, h in RES_PAIRS:
        pat = struct.pack("<II", w, h)
        for off in find_all(data, pat):
            rep["res_tables"].append({"wh": f"{w}x{h}", "off": off, "kind": "adjacent_u32_pair"})
        # пары push imm32 w ; push imm32 h (6A/68 opcode)
        for m in re.finditer(re.escape(b"\x68" + struct.pack("<I", w)) +
                             re.escape(b"\x68" + struct.pack("<I", h)), data):
            rep["res_tables"].append({"wh": f"{w}x{h}", "off": m.start(), "kind": "push_push"})
        for m in re.finditer(re.escape(b"\x68" + struct.pack("<I", h)) +
                             re.escape(b"\x68" + struct.pack("<I", w)), data):
            rep["res_tables"].append({"wh": f"{w}x{h}", "off": m.start(), "kind": "push_push_rev"})

    # ---- 4. float соотношения сторон ----
    for val, label in ASPECT_FLOATS.items():
        for off in find_all(data, f32(val)):
            rep["aspect"].append({"value": round(val, 6), "label": label, "off": off})
    # double-варианты
    for val, label in ASPECT_FLOATS.items():
        for off in find_all(data, struct.pack("<d", val)):
            rep["aspect"].append({"value": round(val, 6), "label": label + " (double)", "off": off})

    # ---- 5. графический API ----
    have_import = {}
    for e in (getattr(pe, "DIRECTORY_ENTRY_IMPORT", None) or []):
        dll = e.dll.decode("latin1", "replace")
        names = [(i.name.decode("latin1", "replace") if i.name else f"ord{i.ordinal}") for i in e.imports]
        if re.search(r"(?i)ddraw|d3d|d3dim|d3dx", dll):
            have_import[dll] = names
    rep["gfx"].append({"imports": have_import})
    for needle in GFX_DLLS + GFX_APIS:
        offs = find_all(data, needle)
        if offs:
            rep["gfx"].append({"needle": needle.decode("latin1"), "offs": offs[:8]})

    print(json.dumps(rep, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
