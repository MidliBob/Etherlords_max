#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""disasm.py — хелпер capstone-листингов по VA для Etherlords.exe (билд 409d3e08…).

    python3 work/disasm.py 0x58f690 [кол-во]

Пути выводятся от расположения скрипта (запуск из любого каталога).
Кэш work/insns.pkl и игровой бинарник в репозитории НЕ лежат (исключены в 0.0.6 —
work/README.md): кэш опционален (без него — прямой capstone), exe ищется по порядку:
  1. reference/Etherlords.exe            (в корне репозитория, игнорируется git'ом)
  2. ../Etherlords_max/reference/Etherlords.exe  (старый относительный путь автора)
  3. $EL_EXE                             (env: /путь/к/вашему/Etherlords.exe)
Достать кэш/эталон из истории git:
  git checkout cabb35c -- work/insns.pkl reference/Etherlords.exe
  git restore --staged work/insns.pkl reference/Etherlords.exe
"""
import os
import pickle
import sys

import capstone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

PKL = os.path.join(HERE, 'insns.pkl')
EXE_CANDIDATES = [
    os.path.join(ROOT, 'reference', 'Etherlords.exe'),
    os.path.join(os.path.dirname(ROOT), 'Etherlords_max', 'reference', 'Etherlords.exe'),
    os.environ.get('EL_EXE') or '',
]

byaddr = {}
if os.path.exists(PKL):
    insns = pickle.load(open(PKL, 'rb'))
    byaddr = {a: (a, s, mn, op, bb) for a, s, mn, op, bb in insns}

data = None
for c in EXE_CANDIDATES:
    if c and os.path.exists(c):
        data = open(c, 'rb').read()
        break

if not byaddr and data is None:
    sys.exit('disasm.py: нет ни кэша work/insns.pkl, ни Etherlords.exe.\n'
             '  exe: положите свою копию в reference/Etherlords.exe или\n'
             '       задайте EL_EXE=/путь/к/Etherlords.exe (билд 409d3e08…);\n'
             '  кэш: git checkout cabb35c -- work/insns.pkl (лежит в истории).')

BASE = 0x400000
TEXT_FILE = 0x1000
TEXT_VA = 0x401000
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)


def dis(va, n=150):
    if va in byaddr:
        out = []
        a = va
        for i in range(n):
            t = byaddr.get(a)
            if not t:
                break
            a2, s, mn, op, bb = t
            out.append(f'{a2:#010x}  {bb.hex(" "):<26} {mn} {op}')
            a = a2 + s
            if mn == 'ret':
                break
        return '\n'.join(out)
    if data is None:
        return (f'{va:#x}: в кэше нет, а exe для прямого capstone не найден '
                f'(см. подсказку в шапке disasm.py)')
    off = TEXT_FILE + (va - TEXT_VA)
    code = data[off:off + 4 * n]
    out = []
    for i in md.disasm(code, va):
        out.append(f'{i.address:#010x}  {i.bytes.hex(" "):<26} {i.mnemonic} {i.op_str}')
        if i.mnemonic == 'ret':
            break
    return '\n'.join(out)


if __name__ == '__main__':
    va = int(sys.argv[1], 16)
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 150
    print(dis(va, n))
