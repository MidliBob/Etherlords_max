#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dump_blocks.py — генератор blocks/*.asm/*.hex для Etherlords.exe (Демиурги, рус. 1.07).

Исправляет ошибку прошлой версии: блоки 03..05 нарезались по "file-смещениям",
равным VA из листингов со сдвинутым базисом (см. docs/07, раздел 0), и оказывались
пустыми (offset за EOF). Здесь блоки задаются НАСТОЯЩИМИ VA, file-смещение
вычисляется через таблицу секций PE (для данного билда .text/.rdata/.data:
VA = file + 0x400000, ImageBase = 0x400000).

Запуск:
    python3 tools/dump_blocks.py [путь/к/Etherlords.exe] [каталог_вывода]
По умолчанию: Etherlords.exe рядом с tools/, вывод в ../blocks.

Требуется: pip install pefile capstone
"""
import hashlib
import os
import sys

import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

# (имя, va_start, va_end, назначение) — настоящие VA (ImageBase 0x400000)
BLOCKS = [
    ("01_parse_video_resolution", 0x42db8f, 0x42dbd6,
     "Чтение VideoResolution из settings.ini -> atoi -> [esi+0x28]/[esi+0x2c]. Белый список отсутствует."),
    ("02_mode_check_layout", 0x59bd28, 0x59bd90,
     "Выбор раскладки: ==1024x768 -> apply_layout(1); ==800x600 -> apply_layout(0); иначе ПРОПУСК."),
    ("03_apply_layout", 0x59fcb0, 0x59fda0,
     "apply_layout(flag): W,H=(800,600)|(1024,768) immediate; [screen+0xe8]=(0,0,W,H); set_rect subscreens; apply_flag(mgr,flag); полосы (W-163) и (W-133)."),
    ("04_set_rect", 0x58f690, 0x58f6b3,
     "set_rect(this,RECT): копирует RECT в [this+0x154]."),
    ("05_apply_flag", 0x58bd70, 0x58be08,
     "apply_flag(mgr,flag): flag->бит (0->1,1->2,2->4,3->8) в нижний nibble [elem+0x14c]; обход кругового списка [mgr]->head,[node+8],elem=[node+0x1c]; relayout(elem,flag)."),
    ("06_aspect_4_3", 0x446f28, 0x446f60,
     "push 0x3faaaaab (4/3) -> аргумент построения матрицы/вьюпорта."),
    ("07_aspect_3_4", 0x452b20, 0x452b60,
     "mov eax,0x3f400000 (3/4) -> поле проекции [esi+0x20]."),
    ("08_push800x600_a", 0x59ab28, 0x59ab50,
     "Дефолт SetRect(&[esi+0xe8],0,0,800,600) сайт #1."),
    ("09_push800x600_b", 0x59bd00, 0x59bd28,
     "Дефолт SetRect(0,0,800,600) + set_rect([esi+8]) сайт #2 (перед mode_check)."),
    ("10_relayout_elem", 0x591250, 0x5912de,
     "relayout(elem,flag): act{+0x1ac..0x1bb} = record[flag]{+0x18c+flag*16}; virtual OnLayoutChange(vtbl+0x5c)(dShX,dShY,dX,dY)."),
    ("11_on_layout_change", 0x5912e0, 0x591339,
     "OnLayoutChange: OffsetRect(+0x154,dShX,dShY); если +0x164 непуст OffsetRect(+0x164,dX,dY); visual(+0x148): 0x58a5d0(dX,dY)."),
    ("12_set_shift", 0x591170, 0x591190,
     "SetShift(elem,flag,sx,sy): record[flag].sX(+8)=sx, .sY(+12)=sy. Из лоадера: SetShift(1,ShiftX,ShiftY)."),
    ("13_apply_shift", 0x591190, 0x5911f0,
     "ApplyShift(elem): rec1.X+=rec1.sX; rec1.Y+=rec1.sY; детям OffsetRecord(child,1,sX,sY)."),
    ("14_offset_record", 0x5911f0, 0x591250,
     "OffsetRecord(elem,flag,dx,dy): record[flag].X+=dx,.Y+=dy; рекурсия в детей (+0x44/+0x48)."),
    ("15_loader_geometry", 0x58c41d, 0x58c4c9,
     "Лоадер Controls.reg: Left/Top/Width/Height -> SetRect(elem+0x154,{L,T,L+W,T+H}); 0x590e90 переводит в parent-relative."),
    ("16_loader_shiftxy", 0x58c905, 0x58c944,
     "Лоадер Controls.reg: ShiftX/ShiftY -> SetShift(elem,1,ShiftX,ShiftY) = record[1].sX/sY."),
    ("17_hittest", 0x58fb70, 0x58fd44,
     "HitTest(x,y): рекурсия детей; маска +0x150 (stride +0x184, rect +0x174, цепочка родителей +0x34->+0x154/0x158, PtInRect+бит маски); иначе rect +0x164/+0x154 + PtInRect."),
    ("18_ctor_zero_records", 0x58f261, 0x58f2b0,
     "Базовый контор контрола: зануляет record[0..1] (+0x18c..0x1ab) и act (+0x1ac..0x1bb). Размер Panel=0x1d0: место ровно под ДВЕ записи."),
    ("19_apply_shifts_pass", 0x58ca30, 0x58ca88,
     "Пост-проход загрузки: ApplyShift(0x591190) для каждого элемента плоского списка менеджера."),
    ("20_live_viewport", 0x5a0070, 0x5a0175,
     "Создание viewport'а ЖИВЫМ размером: RECT{0,0,realW,realH} из [0x825de8]->+0x18->{+0x14,+0x18} (0x5a00fd). Потребитель — миникарта/hover-поверхности."),
    ("21_screen_init_defaults", 0x59bc9e, 0x59bd28,
     "CScreenManager::Init: set_rect(0,0,800,600) для subscreens +0xb4/+0xb8/+0xc0 и [0x82bc58]; загрузка Controls.reg (0x58be10) и CutParts.reg (0x58ca90); ApplyShifts (0x58ca30)."),
]


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    exe = sys.argv[1] if len(sys.argv) > 1 else os.path.join(here, "..", "reference", "Etherlords.exe")
    outdir = sys.argv[2] if len(sys.argv) > 2 else os.path.join(here, "..", "blocks")
    pe = pefile.PE(exe, fast_load=True)
    data = open(exe, "rb").read()
    base = pe.OPTIONAL_HEADER.ImageBase
    md = Cs(CS_ARCH_X86, CS_MODE_32)

    def va2off(va):
        rva = va - base
        for s in pe.sections:
            if s.VirtualAddress <= rva < s.VirtualAddress + max(s.Misc_VirtualSize, s.SizeOfRawData):
                return s.PointerToRawData + (rva - s.VirtualAddress)
        return None

    os.makedirs(outdir, exist_ok=True)
    print("| # | блок | file range | va range | bytes | sha256[:16] | назначение |")
    print("|---|---|---|---|---|---|---|")
    for i, (name, va0, va1, note) in enumerate(BLOCKS):
        f0, f1 = va2off(va0), va2off(va1)
        if f0 is None or f1 is None:
            print("!! %s: VA вне секций" % name)
            continue
        blob = data[f0:f1]
        sha = hashlib.sha256(blob).hexdigest()[:16]
        lines = ["; %s" % name,
                 "; file %#x..%#x  va %#x..%#x" % (f0, f1, va0, va1),
                 "; %s" % note]
        for ins in md.disasm(blob, va0):
            o = f0 + (ins.address - va0)
            raw = data[o:o + ins.size]
            lines.append("  %#010x  %-16s  %s %s" % (ins.address, raw.hex(" "), ins.mnemonic, ins.op_str))
        with open(os.path.join(outdir, name + ".asm"), "w", encoding="utf-8") as fh:
            fh.write("\n".join(lines) + "\n")
        with open(os.path.join(outdir, name + ".hex"), "w", encoding="utf-8") as fh:
            fh.write(blob.hex() + "\n")
        print("| %d | %s | %#x..%#x | %#x..%#x | %d | %s | %s |"
              % (i + 1, name, f0, f1, va0, va1, len(blob), sha, note))


if __name__ == "__main__":
    main()
