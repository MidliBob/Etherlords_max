#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
patch_native.py — v1 (РЕГРЕССИЯ). Не применять для игры; оставлен как разбор ошибки.

!!! ВНИМАНИЕ: v1 ДАЁТ РЕГРЕССИЮ (мёртвые кнопки): подмена экранных rect'ов (секция A)
!!! БЕЗ масштабирования координат элементов рассинхронизирует draw/hover/click.
!!! См. docs/04_hit_test_model.md и docs/05_native_v1_regression.md;
!!! ревизия плана v2 — docs/07 §6 и tools/hook_skeleton.py.

Адреса — настоящие VA (ImageBase 0x400000; VA = file + 0x400000, см. docs/07 §0).
До ревизии файл был записан в старом базисе (file + 0x800000) и содержал
незакрытый docstring (SyntaxError — скрипт не запускался вовсе). File-оффсеты
и результирующие байты от смены базиса НЕ изменились.

Секция A (трамплин live W/H) пригодится для v2 — но ТОЛЬКО вместе с пост-проходом
масштабирования RECT'ов контролов (см. hook_skeleton.py, план п.2+п.3).

Запуск без ключей печатает предупреждение и выходит. Пересобрать регрессионный
бинар (например, для сравнения байтов):
    python3 tools/patch_native.py --force
"""
import struct
import sys

if "--force" not in sys.argv:
    print(__doc__)
    print("Сборка v1 заблокирована (регрессия, docs/05). Безопасный базис — tools/patch_layout.py.")
    print("Для пересборки эталонного v1-бинара: --force")
    sys.exit(2)

SRC = "Etherlords.exe"
DST = "Etherlords_native.exe"
data = bytearray(open(SRC, "rb").read())
VA2F = lambda va: va - 0x400000   # настоящий базис: VA = file + 0x400000
CAVE = 0x755656                   # file 0x355656: нули в raw .text


def put(va, bs):
    f = VA2F(va)
    data[f:f + len(bs)] = bs


# --- B: неизвестное разрешение -> форсируем раскладку flag=1 (jmp на push 1 @0x59bd4e) ---
put(0x0059BD4C, b"\xeb\x00")   # jne bd6a -> jmp bd4e  (w==1024, h!=768)
put(0x0059BD58, b"\xeb\xf4")   # jne bd6a -> jmp bd4e  (w!=800)
put(0x0059BD5F, b"\xeb\xed")   # jne bd6a -> jmp bd4e  (w==800, h!=600)

# --- A: трамплин: реальные W/H из цепочки режима вместо 1024/768 ---
t  = b"\xa1\xe8\x5d\x82\x00"   # mov eax,[0x825de8]
t += b"\x8b\x40\x18"           # mov eax,[eax+0x18]
t += b"\x8b\x50\x14"           # mov edx,[eax+0x14]   (W)
t += b"\x8b\x48\x18"           # mov ecx,[eax+0x18]   (H)
t += b"\x89\x4c\x24\x24"       # mov [esp+0x24],ecx
t += b"\xe9" + struct.pack("<i", 0x0059FCDA - (CAVE + len(t) + 5))
put(CAVE, t)

# --- хук ветки flag==1 (mov edx,0x400) на трамплин ---
site = 0x0059FCCD
put(site, b"\xe9" + struct.pack("<i", CAVE - (site + 5)))

open(DST, "wb").write(bytes(data))
print("wrote", DST, len(data))
