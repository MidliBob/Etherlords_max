#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""decode_evtlog.py — разбор бинарного лога el_evt.log debug-сборок (v5dbg;
с 0.0.8 логгер H8/H9 встроен в КАЖДУЮ сборку по умолчанию — v6dbg).
С 0.0.11 также kind=3 (H11: hover-сайт CButtonList, рекорд 56 Б).

Использование:  python3 tools/decode_evtlog.py el_evt.log [filter_vtable_hex]
Расширение файла произвольное (пересылать лог можно как el_evt.log.txt).
"""
import struct, sys

VT = {
    0x75a8c0: 'CAdvScreen', 0x75b954: 'CScenarioList', 0x75b9cc: 'CPlayerList',
    0x75c04c: 'CSelectMission', 0x75bde4: 'CSaveScreen', 0x75d7bc: 'CMyScrollBar',
    0x75d794: 'CScroller', 0x75d924: 'CTextArray', 0x75d498: 'CButtonList',
    0x75aa40: 'CMiniMap', 0x75a9b4: 'CInfoFrame', 0x75d434: 'CCommonText',
    0x75a82c: 'CAutoButton', 0x75d224: 'CMessageButton', 0x75d328: 'CMultyMessageButton',
    0x75b82c: 'CLoadGameScreen', 0x75b8b4: 'CMainMenu', 0x75bd4c: 'CNewGameScreen',
    0x75da0c: 'CSelectCreateLoadScreen', 0x75d3b8: 'CCamera', 0x75d66c: 'CEasyList',
    0x75d5dc: 'CLevelList', 0x75a93c: 'CPanelFader', 0x75aba0: 'CFadingButton',
}


def iter_records(data):
    """Рекорды переменной длины: kind=3 -> 56 байт, иначе 44."""
    off = 0
    while off + 44 <= len(data):
        kind = struct.unpack_from('<I', data, off)[0]
        if kind in (3, 5) and off + 56 <= len(data):
            yield struct.unpack_from('<14I', data, off)
            off += 56
        elif kind == 7 and off + 60 <= len(data):
            yield struct.unpack_from('<15I', data, off)
            off += 60
        else:
            yield struct.unpack_from('<11I', data, off)
            off += 44


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else 'el_evt.log'
    flt = int(sys.argv[2], 16) if len(sys.argv) > 2 else None
    data = open(path, 'rb').read()
    recs = list(iter_records(data))
    print(f"{path}: {len(recs)} records ({len(data)} bytes)")
    for i, r in enumerate(recs):
        k, this, vt, ret, mark = r[0], r[1], r[2], r[3], r[4]
        if flt and vt != flt:
            continue
        name = VT.get(vt, f'?{vt:#x}')
        if k == 1:
            d0, d1, d2, d3 = r[5:9]
            print(f"{i:6d} set_rect  this={this:#010x} vt={name:22s} ret={ret:#010x} "
                  f"mark={mark:#04x} rect=({d0},{d1},{d2},{d3})")
        elif k == 2:
            d0, d1, d2, d3 = r[5:9]
            print(f"{i:6d} OnLayout  this={this:#010x} vt={name:22s} ret={ret:#010x} "
                  f"mark={mark:#04x} d=({d0},{d1},{d2},{d3})")
        elif k == 3:
            i_btn, cx, cy, L, T, R, B, flags = r[4], r[5], r[6], r[7], r[8], r[9], r[10], r[11]
            print(f"{i:6d} hover     this={this:#010x} vt={name:22s} i={i_btn} "
                  f"cursor=({cx},{cy}) rect=({L},{T},{R},{B}) flags={flags:#010x}")
        elif k == 4:
            slot, a0, a1, a2, ax, ay, sec = r[4], r[5], r[6], r[7], r[8], r[9], r[10]
            print(f"{i:6d} wheelin   this={this:#010x} vt={name:22s} slot={slot} "
                  f"ret={ret:#010x} args=({a0},{a1},{a2}) active=({ax},{ay}) sector0L={sec}")
        elif k == 5:
            code, a2, a3, cx, cy, ax, ay, sec = r[5], r[6], r[7], r[8], r[9], r[10], r[11], r[12]
            print(f"{i:6d} msgevt    this={this:#010x} vt={name:22s} code={code:#x} "
                  f"args=({a2},{a3}) cursor=({cx},{cy}) active=({ax},{ay}) sector0L={sec}")
        elif k == 6:
            code, a2, a3, cx, cy = r[5], r[6], r[7], r[8], r[9]
            print(f"{i:6d} msgrcv    this={this:#010x} vt={name:22s} code={code:#x} "
                  f"args=({a2},{a3}) cursor=({cx},{cy})")
        elif k == 7:
            x, y = r[5], r[6]
            r154 = tuple(v - 0x100000000 if v >= 0x80000000 else v for v in r[7:11])
            r164 = tuple(v - 0x100000000 if v >= 0x80000000 else v for v in r[11:15])
            print(f"{i:6d} hittest   this={this:#010x} vt={name:22s} xy=({x},{y}) "
                  f"r154={r154} r164={r164}")
        else:
            print(f"{i:6d} kind={k}  this={this:#010x} vt={name:22s} ret={ret:#010x} raw={r[5:]}")


if __name__ == '__main__':
    main()
