#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""decode_evtlog.py — разбор бинарного лога el_evt.log debug-сборок (v5dbg;
с 0.0.8 логгер H8/H9 встроен в КАЖДУЮ сборку по умолчанию — v6dbg).

Рекорд 44 байта: kind, this, vtable, ret, mark, d0..d4, pad.
kind 1 = set_rect(this, {d0..d3}), kind 2 = OnLayoutChange(this, dShX,dShY,dX,dY).
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

def main():
    path = sys.argv[1] if len(sys.argv) > 1 else 'el_evt.log'
    flt = int(sys.argv[2], 16) if len(sys.argv) > 2 else None
    data = open(path, 'rb').read()
    n = len(data) // 44
    print(f"{path}: {n} records ({len(data)} bytes)")
    for i in range(n):
        k, this, vt, ret, mark, d0, d1, d2, d3, d4, pad = struct.unpack_from('<11I', data, i * 44)
        if flt and vt != flt:
            continue
        name = VT.get(vt, f'?{vt:#x}')
        if k == 1:
            print(f"{i:6d} set_rect  this={this:#010x} vt={name:22s} ret={ret:#010x} "
                  f"mark={mark:#04x} rect=({d0},{d1},{d2},{d3})")
        else:
            print(f"{i:6d} OnLayout  this={this:#010x} vt={name:22s} ret={ret:#010x} "
                  f"mark={mark:#04x} d=({d0},{d1},{d2},{d3})")

if __name__ == '__main__':
    main()
