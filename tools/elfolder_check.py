#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""elfolder_check.py — самодиагностика папки игры (0.0.12).

Отвечает на вопросы «какой скрипт? какой exe? какой лог?» одним запуском:
положите в папку игры и запустите (двойной клик или `python elfolder_check.py`) —
рядом появится CHECK.txt, его содержимое можно копировать прямо в чат.

Проверяет: ревизию patch_native_v3.py (TOOL_REV/H11/dedup/H12), наличие evt2txt.py,
sha256 Etherlords.exe, ЧТО реально внутри Etherlords_native_v6dbg.exe (сайты
P1/H8/H11/H12 побайтово + sha-таблица версий), состояние el_evt.log (размер, время,
число рекордов по kind, наличие hover) и согласованность времён exe/лога.
Только стандартная библиотека.
"""
import hashlib
import os
import re
import struct
import sys
import time

EXPECT_ORIG = "409d3e08"          # sha256[:8] анализируемого билда (рус. 1.07)
V6DBG_SHA = {                     # sha256[:8] -> что это за сборка
    "5ad61f0e": "RELEASE (--no-logger): логгера НЕТ совсем — для диагностики не годится",
    "74b8106f": "v6dbg 0.0.8–0.0.10: логгер H8/H9, но БЕЗ H11 (hover не пишется)",
    "c0dcbd4e": "v6dbg 0.0.11: H11 есть, но dedup съедал первый hover i=0",
    "7fc13634": "v6dbg 0.0.12: H11 + фикс dedup, но БЕЗ H12 (если hover колеса живёт в adv-хендлере, пар колеса в логе не будет)",
    "24e0c3f8": "v6dbg 0.0.13: H12 стоял в обработчике КЛИКА (hover не писал) — устарел",
    "6477c593": "v6dbg 0.0.14: H13 vtable-интерпозиция мышиных слотов колеса (.ellog) — ТО, ЧТО НУЖНО",
}


def s32(v):
    return v - 0x100000000 if v >= 0x80000000 else v


def find_dir():
    if len(sys.argv) > 1:
        return sys.argv[1]
    for c in (os.getcwd(), os.path.dirname(os.path.abspath(__file__))):
        if os.path.isfile(os.path.join(c, "Etherlords.exe")) or \
           os.path.isfile(os.path.join(c, "el_evt.log")):
            return c
    return os.getcwd()


def log_stats(path):
    d = open(path, 'rb').read()
    kinds = {}
    off = 0
    while off + 44 <= len(d):
        k = struct.unpack_from('<I', d, off)[0]
        if k == 3 and off + 56 <= len(d):
            off += 56
        else:
            off += 44
        kinds[k] = kinds.get(k, 0) + 1
    return len(d), kinds


def main():
    d = find_dir()
    out = []
    out.append(f"== elfolder_check (папка: {d}) ==")

    # 1) скрипты
    sp = os.path.join(d, "patch_native_v3.py")
    if os.path.isfile(sp):
        src = open(sp, encoding="utf-8", errors="replace").read()
        rev = re.search(r'TOOL_REV\s*=\s*"([^"]+)"', src)
        out.append(f"patch_native_v3.py: есть; rev={rev.group(1) if rev else 'НЕТ (старее 0.0.12)'}; "
                   f"H11={'есть' if 'SITE_H11' in src else 'НЕТ'}; "
                   f"dedup-fix={'есть' if 'храним i+1' in src else 'НЕТ'}")
    else:
        out.append("patch_native_v3.py: НЕТ в папке (скопировать из tools/ репозитория)")
    out.append("evt2txt.py: " + ("есть" if os.path.isfile(os.path.join(d, "evt2txt.py"))
                                 else "НЕТ (скопировать из tools/)"))

    # 2) оригинал
    op = os.path.join(d, "Etherlords.exe")
    if os.path.isfile(op):
        h = hashlib.sha256(open(op, 'rb').read()).hexdigest()
        out.append(f"Etherlords.exe: sha256={h[:16]}… " +
                   ("OK (анализируемый билд)" if h.startswith(EXPECT_ORIG)
                    else "ДРУГОЙ БИЛД — патчер откажется собирать"))
    else:
        out.append("Etherlords.exe: НЕТ в папке")

    # 3) что внутри v6dbg
    vp = os.path.join(d, "Etherlords_native_v6dbg.exe")
    if os.path.isfile(vp):
        img = open(vp, 'rb').read()
        h = hashlib.sha256(img).hexdigest()
        p1 = img[0x19bd4c:0x19bd4e] == b"\xeb\x00"
        h8 = img[0x18f690] == 0xE9
        h11 = img[0x17cfee] == 0xE9
        h12 = img[0x10f5b4] == 0xE9
        import struct as _st
        h13 = 0x83B000 <= _st.unpack_from('<I', img, 0x35ac20 + 4 * 7)[0] < 0x83C000
        verdict = V6DBG_SHA.get(h[:8], "неизвестная сборка (пересобрать из текущего скрипта)")
        out.append(f"Etherlords_native_v6dbg.exe: sha256={h[:16]}… -> {verdict}")
        out.append(f"  сайты: P1(форс раскладки)={'OK' if p1 else 'НЕТ'}, "
                   f"H8(логгер set_rect)={'есть' if h8 else 'НЕТ'}, "
                   f"H11(hover-логгер)={'есть' if h11 else 'НЕТ'}, "
                   f"H13(vtable-слоты колеса)={'есть' if h13 else 'НЕТ'}")
        mtime_exe = os.path.getmtime(vp)
    else:
        out.append("Etherlords_native_v6dbg.exe: НЕТ (запустить patch_native_v3.py в папке)")
        mtime_exe = None

    # 4) лог
    lp = os.path.join(d, "el_evt.log")
    if os.path.isfile(lp):
        size, kinds = log_stats(lp)
        mt = os.path.getmtime(lp)
        out.append(f"el_evt.log: {size} байт, изменён {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(mt))}, "
                   f"рекорды: " + ", ".join(f"kind{k}={n}" for k, n in sorted(kinds.items())) +
                   f", hover(kind3)={kinds.get(3, 0)}, wheelin(kind4)={kinds.get(4, 0)}")
        if mtime_exe is not None:
            if mt < mtime_exe:
                out.append("  ВНИМАНИЕ: лог СТАРЕЕ exe v6dbg — сеанс новой сборки не писал лог "
                           "(запускали не v6dbg? игра не стартовала?)")
            elif kinds.get(3, 0) == 0 and h11:
                out.append("  ВНИМАНИЕ: лог новее exe с H11, но hover-записей нет: "
                           "курсора не было на кнопках CButtonList (колесо!) или hover не сработал")
            elif kinds.get(3, 0) == 0:
                out.append("  сборка без H11: hover-записей быть не может (см. вердикт выше)")
        if kinds.get(3, 0):
            out.append("  hover-записи ЕСТЬ — присылайте el_evt_decoded.txt (evt2txt.py)")
    else:
        out.append("el_evt.log: НЕТ (сборка с логгером ещё не запускалась из этой папки)")

    txt = "\n".join(out)
    print(txt)
    cp = os.path.join(d, "CHECK.txt")
    open(cp, "w", encoding="utf-8").write(txt + "\n")
    print(f"\n[записано в {cp} — можно копировать содержимое прямо в чат]")
    return 0


if __name__ == '__main__':
    code = main()
    if len(sys.argv) == 1 and sys.platform == 'win32':
        try:
            input("\nНажмите Enter, чтобы закрыть окно...")
        except (EOFError, OSError):
            pass
    sys.exit(code)
