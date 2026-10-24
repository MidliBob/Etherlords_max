#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
patch_layout.py — ЭКСПЕРИМЕНТ B для Etherlords.exe (Демиурги, рус. 1.07).

Гипотеза: у UI ровно две раскладки (флаг 0 = 800x600, флаг 1 = 1024x768).
При любом другом разрешении вызов выбора раскладки ПРОПУСКАЕТСЯ, и UI остаётся
в дефолте 800x600 (это и даёт HUD, прижатый к 800x600, и серые поля).

Правка: форсировать флаг=1 (раскладка 1024x768) для ЛЮБОГО разрешения.
Три двухбайтовых замены jne -> jmp. Оригинальный файл не трогается:
пишется копия Etherlords_layout1024.exe.

Использование:
    python3 patch_layout.py Etherlords.exe            # применить -> Etherlords_layout1024.exe
    python3 patch_layout.py Etherlords.exe --check    # только проверить, что байты совпадают
"""
import hashlib, shutil, sys, os

PATCHES = [  # (file_offset, orig_bytes, new_bytes, comment)
    (0x19bd4c, bytes.fromhex("751c"), bytes.fromhex("eb00"), "jne notknown -> jmp push1   (w==1024 path)"),
    (0x19bd58, bytes.fromhex("7510"), bytes.fromhex("ebf4"), "jne notknown -> jmp push1   (w!=800 path)"),
    (0x19bd5f, bytes.fromhex("7509"), bytes.fromhex("ebed"), "jne notknown -> jmp push1   (h!=600 path)"),
]
OUT = "Etherlords_layout1024.exe"

def sha(b): return hashlib.sha256(b).hexdigest()

def main():
    src = sys.argv[1] if len(sys.argv) > 1 else "Etherlords.exe"
    check = "--check" in sys.argv
    d = bytearray(open(src, "rb").read())
    print(f"source : {src}  {len(d)} bytes  sha256={sha(d)[:16]}")
    ok = True
    for off, ob, nb, cmt in PATCHES:
        cur = bytes(d[off:off+len(ob)])
        good = (cur == ob)
        ok &= good
        print(f"  {off:#010x}: have {cur.hex(' ')}  want {ob.hex(' ')}  -> {nb.hex(' ')}  [{'OK' if good else 'MISMATCH'}]  {cmt}")
    if not ok:
        print("\nABORT: бинарь отличается от ожидаемого — патч не применяется (защита от чужого билда).")
        sys.exit(2)
    if check:
        print("\nCHECK OK: байты совпадают, патч применим.")
        return
    for off, ob, nb, cmt in PATCHES:
        d[off:off+len(nb)] = nb
    open(OUT, "wb").write(bytes(d))
    print(f"\nwrote {OUT}  {len(d)} bytes  sha256={sha(bytes(d))[:16]}")
    print("Далее: сделайте бэкап своего Etherlords.exe, положите Etherlords_layout1024.exe")
    print("рядом ПОД ИМЕНЕМ Etherlords.exe (или замените оригинал), запустите при 1600x900")
    print("и пришлите скриншоты главного меню и глобальной карты.")

if __name__ == "__main__":
    main()
