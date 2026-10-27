#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""evt2txt.py — расшифровка el_evt.log в ТЕКСТ для пересылки (0.0.11).

Чат/почта нередко не принимают бинарный .log (или .txt с бинарным содержимым):
этот скрипт превращает лог debug-сборки в человекочитаемый .txt, который
можно прикрепить куда угодно.

Быстрый запуск: положите скрипт в папку игры (рядом с el_evt.log) и запустите
(двойной клик или `python evt2txt.py`) — рядом с логом появится
`el_evt_decoded.txt`. Либо: `python evt2txt.py /путь/к/el_evt.log [out.txt]`.

Только стандартная библиотека (Python 3.8+); формат рекордов — как у
tools/decode_evtlog.py (kind 1/2 = 44 Б, kind 3 = 56 Б).
"""
import os
import struct
import sys

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
STRIPS = {0x59FD55: 'right-strip', 0x59FD8C: 'game-area', 0x59FD95: 'screen'}


def s32(v):
    return v - 0x100000000 if v >= 0x80000000 else v


def iter_records(data):
    off = 0
    while off + 44 <= len(data):
        kind = struct.unpack_from('<I', data, off)[0]
        if kind == 3 and off + 56 <= len(data):
            yield struct.unpack_from('<14I', data, off)
            off += 56
        else:
            yield struct.unpack_from('<11I', data, off)
            off += 44


def name(vt):
    return VT.get(vt, f'?{vt:#x}')


def main():
    if len(sys.argv) > 1:
        src = sys.argv[1]
    else:
        here = os.path.dirname(os.path.abspath(__file__))
        src = next((c for c in ('el_evt.log', os.path.join(here, 'el_evt.log'))
                    if os.path.isfile(c)), 'el_evt.log')
    if not os.path.isfile(src):
        print("el_evt.log НЕ НАЙДЕН: положите скрипт в папку игры (рядом с логом)")
        print("или укажите путь: python evt2txt.py /путь/к/el_evt.log [out.txt]")
        return 2
    out = sys.argv[2] if len(sys.argv) > 2 else \
        os.path.join(os.path.dirname(os.path.abspath(src)), 'el_evt_decoded.txt')

    data = open(src, 'rb').read()
    recs = list(iter_records(data))
    lines = []
    res = None
    kinds = {}
    for i, r in enumerate(recs):
        k = r[0]
        kinds[k] = kinds.get(k, 0) + 1
        this, vt, ret, mark = r[1], r[2], r[3], r[4]
        nm = name(vt)
        if k == 1:
            d = tuple(map(s32, r[5:9]))
            if ret in STRIPS and res is None:
                res = (d[2], d[3])
            lines.append(f"{i:6d} set_rect  this={this:#010x} vt={nm:22s} "
                         f"ret={ret:#010x} mark={mark:#010x} rect={d}")
        elif k == 2:
            d = tuple(map(s32, r[5:9]))
            lines.append(f"{i:6d} OnLayout  this={this:#010x} vt={nm:22s} "
                         f"ret={ret:#010x} mark={mark:#010x} d={d}")
        elif k == 3:
            i_btn, cx, cy = r[4], r[5], r[6]
            rect = tuple(map(s32, r[7:11]))
            lines.append(f"{i:6d} hover     this={this:#010x} vt={nm:22s} i={i_btn} "
                         f"cursor=({cx},{cy}) rect={rect} flags={r[11]:#010x}")
        elif k == 4:
            cx, cy, ax, ay = r[5], r[6], r[7], r[8]
            sl, st = s32(r[9]), s32(r[10])
            lines.append(f"{i:6d} wheelin   this={this:#010x} cursor=({cx},{cy}) "
                         f"active=({ax},{ay}) sector0=({sl},{st})")
        else:
            lines.append(f"{i:6d} kind={k}  this={this:#010x} vt={nm:22s} ret={ret:#010x}")
    head = [f"# source : {src} ({len(data)} bytes)",
            f"# records: {len(recs)}  " +
            ", ".join(f"kind{k}={n}" for k, n in sorted(kinds.items())),
            f"# session resolution: {res[0]}x{res[1]}" if res else
            "# session resolution: unknown (нет полос apply_layout)"]
    open(out, 'w', encoding='utf-8').write("\n".join(head + lines) + "\n")
    print("\n".join(head))
    print(f"# wrote {out} ({len(head) + len(lines)} строк)")
    print("Прикрепляйте этот .txt — он чисто текстовый.")
    return 0


if __name__ == '__main__':
    code = main()
    if len(sys.argv) == 1 and sys.platform == 'win32':
        try:
            input("\nНажмите Enter, чтобы закрыть окно...")
        except (EOFError, OSError):
            pass
    sys.exit(code)
