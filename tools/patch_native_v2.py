#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
patch_native_v2.py — сборщик native v2 для Etherlords.exe (Демиурги, рус. 1.07).

Реализация плана docs/07 §6.2 (ревизия hook_skeleton.py). Все три потребителя
координат (draw/hover/click, docs/04) приводятся к согласованию:

  P1  форс apply_layout(1) при любом разрешении (3 x jne->jmp, как patch_layout.py);
  H1  трамплин @0x59fccd: immediate W/H=1024/768 -> живые W/H из объекта режима
      [0x825de8]->+0x18->{+0x14,+0x18}; null-guard c фолбэком 1024/768;
      -> экранные rect'ы и полосы (W-163)/(W-133) считаются от живого размера;
  H2  пост-проход @0x59fd20 (сразу после call apply_flag): обход списка контролов
      [0x82b968] (итератор 0x6c51a0, тот же, что в apply_flag) и масштабирование
      на (W/baseW, H/baseH): RECT'ы +0x154/+0x164/+0x174, active +0x1ac/+0x1b0,
      rect'ы визуала [[subnode+0x10]+0x40] и [+0x18] (те же поля, что сдвигает
      visual->Offset 0x58a5d0 — текстуры не трогаются). base = (800,600) при flag=0,
      (1024,768) иначе. При W==baseW && H==baseH проход пропускается (k=1);
  H3  mask-fix @0x58fcf6 (hit-test 0x58fb70): dx/dy в пиксельной маске делятся
      обратно в design-пространство (dx*baseW/W, dy*baseH/H) перед imul на stride
      — пиксельная точность масок сохраняется без их перерисовки.

Записи record[0/1] (+0x18c/+0x19c) и active sX/sY (+0x1b4/+0x1b8) НЕ трогаются:
это данные профилей (источник дельт relayout). Предполагается, что apply_layout
выполняется один раз за процесс (внутри CScreenManager::Init, с предшествующей
перезагрузкой Controls.reg) — см. docs/08, «Известные риски».

Статическая проверка: контрольные байты всех сайтов, аудит диффа (меняются только
ожидаемые диапазоны), полный дизассемблер cave (capstone) с проверкой целей
ветвлений. Функциональная проверка: встроенный интерпретатор подмножества i386
(декодирование capstone, семантика на Python) прогоняет ВСЕ три блока cave на
синтетических структурах — тесты T1..T4 (--no-emu отключает).

Использование:
    python3 tools/patch_native_v2.py Etherlords.exe                # -> Etherlords_native_v2.exe
    python3 tools/patch_native_v2.py Etherlords.exe --check        # только проверка применимости
    python3 tools/patch_native_v2.py Etherlords.exe --listing      # + полный листинг cave

Базис: VA = file + 0x400000 (docs/07 §0). Код-кейв: file 0x355656..0x356000
(VA 0x755656..0x756000, нули внутри raw .text — исполняемый).
"""
import argparse
import hashlib
import struct
import sys

# ------------------------------------------------------------------ константы
IMAGE_BASE = 0x400000
CAVE_FILE = 0x355656
CAVE_VA = 0x755656
CAVE_CAP = 0x356000 - CAVE_FILE          # 2474 байта

VA_MODE_OBJ = 0x825DE8                   # ->+0x18->{+0x14:W, +0x18:H} (живой режим)
VA_MGR      = 0x82B968                   # глобальный менеджер контролов
VA_ITER     = 0x6C51A0                   # итератор списка (как в apply_flag/Offset)
RET_TRAMP   = 0x59FCDA                   # возврат H1 (после immediate'ов W/H)
RET_POST    = 0x59FD26                   # возврат H2 (в apply_layout, после полосы)
RET_MASK    = 0x58FD01                   # возврат H3 (в hit-test, mov eax,[esi+0x150])

# Сайты: (имя, VA, ожидаемые байты, размер замены)
SITE_P1 = [
    ("P1a", 0x59BD4C, "751c", 2),        # jne -> jmp short (форс flag=1)
    ("P1b", 0x59BD58, "7510", 2),
    ("P1c", 0x59BD5F, "7509", 2),
]
P1_NEW = ["eb00", "ebf4", "ebed"]
SITE_H1 = ("H1", 0x59FCCD, "ba00040000", 5)          # mov edx,0x400 -> jmp trampA
SITE_H2 = ("H2", 0x59FD20, "8b86f0000000", 6)         # mov eax,[esi+0xf0] -> jmp post + nop
SITE_H3 = ("H3", 0x58FCF6, "0faf9e84010000", 7)       # imul ebx,[esi+0x184] -> jmp mask + 2*nop

# ------------------------------------------------------------- микроассемблер
REG = {'eax': 0, 'ecx': 1, 'edx': 2, 'ebx': 3, 'esp': 4, 'ebp': 5, 'esi': 6, 'edi': 7}


def _p32(v):
    return struct.pack('<I', v & 0xFFFFFFFF)


def _modrm(mod, reg, rm):
    return bytes([(mod << 6) | (reg << 3) | rm])


def _mem(regfield, base, disp):
    """ModRM(+SIB+disp) для [base+disp]; base='esp' даёт SIB."""
    b = REG[base]
    if base == 'esp':
        if -128 <= disp < 128:
            return _modrm(1, regfield, 4) + b'\x24' + bytes([disp & 0xFF])
        return _modrm(2, regfield, 4) + b'\x24' + _p32(disp)
    if disp == 0 and b != 5:
        return _modrm(0, regfield, b)
    if -128 <= disp < 128:
        return _modrm(1, regfield, b) + bytes([disp & 0xFF])
    return _modrm(2, regfield, b) + _p32(disp)


class Asm:
    """Сборщик части cave. Все переходы фиксированной длины (rel32) — размеры
    частей не зависят от раскладки, поэтому достаточно двух проходов."""

    def __init__(self, base_va):
        self.b = bytearray()
        self.base = base_va
        self.fix = []        # (pos, target) — rel32 на pos..pos+4
        self.labels = {}

    # -- служебное
    def L(self, name):
        assert name not in self.labels
        self.labels[name] = len(self.b)

    def _e(self, bs):
        self.b += bs

    def _branch(self, prefix, target):
        pos = len(self.b)
        self.b += prefix + b'\x00\x00\x00\x00'
        self.fix.append((pos + len(prefix), target))

    def resolve(self):
        for pos, target in self.fix:
            if isinstance(target, str):
                tva = self.base + self.labels[target]
            else:
                tva = target
            here = self.base + pos + 4
            self.b[pos:pos + 4] = _p32(tva - here)

    # -- инструкции (только используемые в cave)
    def pushad(self):        self._e(b'\x60')
    def popad(self):         self._e(b'\x61')
    def cdq(self):           self._e(b'\x99')
    def ret(self):           self._e(b'\xC3')
    def nop(self):           self._e(b'\x90')
    def sub_esp(self, v):    self._e(b'\x83\xEC' + bytes([v]))
    def add_esp(self, v):    self._e(b'\x83\xC4' + bytes([v]))
    def push_r(self, r):     self._e(bytes([0x50 + REG[r]]))
    def mov_r_abs32(self, r, va):
        assert r == 'eax'
        self._e(b'\xA1' + _p32(va))
    def mov_r_mem(self, r, base, disp):   self._e(b'\x8B' + _mem(REG[r], base, disp))
    def mov_mem_r(self, base, disp, r):   self._e(b'\x89' + _mem(REG[r], base, disp))
    def mov_mem_imm(self, base, disp, imm):
        self._e(b'\xC7' + _mem(0, base, disp) + _p32(imm))
    def lea_r_mem(self, r, base, disp):   self._e(b'\x8D' + _mem(REG[r], base, disp))
    def test_rr(self, a, b):              self._e(b'\x85' + _modrm(3, REG[a], REG[b]))
    def and_eax_u8(self, v):              self._e(b'\x83\xE0' + bytes([v]))
    def cmp_eax_u8(self, v):              self._e(b'\x83\xF8' + bytes([v]))
    def cmp_r_mem(self, r, base, disp):   self._e(b'\x3B' + _mem(REG[r], base, disp))
    def imul_r_mem(self, r, base, disp):  self._e(b'\x0F\xAF' + _mem(REG[r], base, disp))
    def imul_r_r_imm(self, dst, src, imm):
        self._e(b'\x69' + _modrm(3, REG[dst], REG[src]) + _p32(imm))
    def idiv_mem(self, base, disp):       self._e(b'\xF7' + _mem(7, base, disp))
    def mov_rr(self, dst, src):           self._e(b'\x8B' + _modrm(3, REG[dst], REG[src]))
    def sub_rr(self, dst, src):           self._e(b'\x2B' + _modrm(3, REG[dst], REG[src]))
    def mov_r_imm(self, r, imm):          self._e(bytes([0xB8 + REG[r]]) + _p32(imm))
    def jz(self, t):   self._branch(b'\x0F\x84', t)
    def jnz(self, t):  self._branch(b'\x0F\x85', t)
    def je(self, t):   self.jz(t)
    def jne(self, t):  self.jnz(t)
    def jmp32(self, t): self._branch(b'\xE9', t)
    def call_va(self, va):
        pos = len(self.b)
        self.b += b'\xE8' + b'\x00\x00\x00\x00'
        self.b[pos + 1:pos + 5] = _p32(va - (self.base + pos + 5))


# ------------------------------------------------------------------ части cave
def build_trampA(va, env):
    """H1: живые W/H вместо immediate 1024/768 (ветка flag=1), с null-фолбэком."""
    a = Asm(va)
    a.mov_r_abs32('eax', VA_MODE_OBJ)   # mov eax,[0x825de8]
    a.test_rr('eax', 'eax')
    a.jz('fb')
    a.mov_r_mem('eax', 'eax', 0x18)     # mov eax,[eax+0x18]
    a.test_rr('eax', 'eax')
    a.jz('fb')
    a.mov_r_mem('edx', 'eax', 0x14)     # W
    a.mov_r_mem('ecx', 'eax', 0x18)     # H
    a.mov_mem_r('esp', 0x24, 'ecx')     # mov [esp+0x24],ecx (слот H, как оригинал)
    a.jmp32(RET_TRAMP)
    a.L('fb')                           # фолбэк: оригинальные immediate
    a.mov_r_imm('edx', 0x400)           # mov edx,1024
    a.mov_mem_imm('esp', 0x24, 0x300)   # mov [esp+0x24],768
    a.jmp32(RET_TRAMP)
    a.resolve()
    return bytes(a.b)


def build_post(va, env):
    """H2: пост-проход масштабирования контролов после apply_flag.
    Кадр (sub esp,48): W=0,H=4,baseW=8,baseH=12,slot1=16,head=20,elem=24,
    ohead=28,slot2=32,S=36,slot3=40. Внутри pushad/popad — регистры apply_layout
    (esi=screen, ebx=flag, edi/ebp) сохраняются; в конце выполняется украденная
    инструкция mov eax,[esi+0xf0]."""
    SR = env['scale_rect']
    a = Asm(va)
    a.pushad()
    a.sub_esp(48)
    a.mov_r_mem('eax', 'esi', 0xf0); a.mov_mem_r('esp', 0, 'eax')    # W = screen.right
    a.mov_r_mem('eax', 'esi', 0xf4); a.mov_mem_r('esp', 4, 'eax')    # H = screen.bottom
    a.test_rr('ebx', 'ebx'); a.jnz('base1024')                       # flag (ebx жив)
    a.mov_mem_imm('esp', 8, 800); a.mov_mem_imm('esp', 12, 600)
    a.jmp32('basedone')
    a.L('base1024')
    a.mov_mem_imm('esp', 8, 1024); a.mov_mem_imm('esp', 12, 768)
    a.L('basedone')
    a.mov_r_mem('eax', 'esp', 0); a.cmp_r_mem('eax', 'esp', 8); a.jne('work')
    a.mov_r_mem('eax', 'esp', 4); a.cmp_r_mem('eax', 'esp', 12); a.je('fin')  # k==1: пропуск
    a.L('work')
    # обход списка контролов — паттерн один в один как в apply_flag (0x58bd70)
    a.mov_r_abs32('eax', VA_MGR)
    a.mov_r_mem('eax', 'eax', 0)                       # head = [mgr]
    a.mov_mem_r('esp', 20, 'eax')
    a.mov_r_mem('eax', 'eax', 8)                       # node = [head+8]
    a.mov_mem_r('esp', 16, 'eax')
    a.cmp_r_mem('eax', 'esp', 20); a.je('fin')
    a.L('outer')
    a.mov_r_mem('eax', 'esp', 16)
    a.mov_r_mem('eax', 'eax', 0x1c)                    # elem = [node+0x1c]
    a.mov_mem_r('esp', 24, 'eax')
    a.lea_r_mem('ecx', 'eax', 0x154); a.call_va(SR)    # RECT геометрии
    a.mov_r_mem('eax', 'esp', 24)
    a.lea_r_mem('ecx', 'eax', 0x164); a.call_va(SR)    # RECT абсолютный кэш
    a.mov_r_mem('eax', 'esp', 24)
    a.lea_r_mem('ecx', 'eax', 0x174); a.call_va(SR)    # RECT маски
    # active X,Y (+0x1ac/+0x1b0); sX/sY (+0x1b4/8) не трогаем
    a.mov_r_mem('eax', 'esp', 24)
    a.lea_r_mem('ecx', 'eax', 0x1ac)
    a.mov_r_mem('eax', 'ecx', 0)
    a.imul_r_mem('eax', 'esp', 0); a.cdq(); a.idiv_mem('esp', 8)
    a.mov_mem_r('ecx', 0, 'eax')
    a.mov_r_mem('eax', 'ecx', 4)
    a.imul_r_mem('eax', 'esp', 4); a.cdq(); a.idiv_mem('esp', 12)
    a.mov_mem_r('ecx', 4, 'eax')
    # визуал: v=[elem+0x148]; обход как в Offset (0x58a5d0)
    a.mov_r_mem('eax', 'esp', 24)
    a.mov_r_mem('eax', 'eax', 0x148)
    a.test_rr('eax', 'eax'); a.jz('next')
    a.mov_r_mem('eax', 'eax', 0)                       # ohead = [v]
    a.mov_mem_r('esp', 28, 'eax')
    a.mov_r_mem('eax', 'eax', 8)                       # onode = [ohead+8]
    a.mov_mem_r('esp', 32, 'eax')
    a.cmp_r_mem('eax', 'esp', 28); a.je('next')
    a.L('vouter')
    a.mov_r_mem('eax', 'esp', 32)
    a.mov_r_mem('eax', 'eax', 0x14)                    # sh = [onode+0x14]
    a.mov_r_mem('eax', 'eax', 0)                       # S = [sh]
    a.mov_mem_r('esp', 36, 'eax')
    a.mov_r_mem('eax', 'eax', 8)                       # snode = [S+8]
    a.mov_mem_r('esp', 40, 'eax')
    a.cmp_r_mem('eax', 'esp', 36); a.je('vnext')
    a.L('vinner')
    a.mov_r_mem('eax', 'esp', 40)
    a.mov_r_mem('eax', 'eax', 0x10)                    # obj = [snode+0x10]
    a.lea_r_mem('ecx', 'eax', 0x40); a.call_va(SR)     # экран. rect (сдвигается Offset'ом)
    a.mov_r_mem('eax', 'esp', 40)
    a.mov_r_mem('eax', 'eax', 0x10)
    a.lea_r_mem('ecx', 'eax', 0x18); a.call_va(SR)     # второй rect (тоже сдвигается)
    a.lea_r_mem('eax', 'esp', 40); a.push_r('eax')
    a.call_va(VA_ITER); a.add_esp(4)
    a.mov_r_mem('eax', 'esp', 40); a.cmp_r_mem('eax', 'esp', 36); a.jne('vinner')
    a.L('vnext')
    a.lea_r_mem('eax', 'esp', 32); a.push_r('eax')
    a.call_va(VA_ITER); a.add_esp(4)
    a.mov_r_mem('eax', 'esp', 32); a.cmp_r_mem('eax', 'esp', 28); a.jne('vouter')
    a.L('next')
    a.lea_r_mem('eax', 'esp', 16); a.push_r('eax')
    a.call_va(VA_ITER); a.add_esp(4)
    a.mov_r_mem('eax', 'esp', 16); a.cmp_r_mem('eax', 'esp', 20); a.jne('outer')
    a.L('fin')
    a.add_esp(48)
    a.popad()
    a.mov_r_mem('eax', 'esi', 0xf0)                    # украденная инструкция
    a.jmp32(RET_POST)
    a.resolve()
    return bytes(a.b)


def build_scale_rect(va, env):
    """scale_rect(ecx=&RECT): L,R *= W/baseW; T,B *= H/baseH (idiv, trunc).
    Кадр вызывающего (post_scale): W=[esp+4+0], H=[esp+4+4], baseW=[esp+4+8],
    baseH=[esp+4+12] (+4 — адрес возврата). Портит только eax/edx."""
    a = Asm(va)
    for off, wslot, bslot in ((0x0, 0, 8), (0x8, 0, 8), (0x4, 4, 12), (0xC, 4, 12)):
        a.mov_r_mem('eax', 'ecx', off)
        a.imul_r_mem('eax', 'esp', wslot + 4)
        a.cdq()
        a.idiv_mem('esp', bslot + 4)
        a.mov_mem_r('ecx', off, 'eax')
    a.ret()
    a.resolve()
    return bytes(a.b)


def build_mask(va, env):
    """H3: hit-test с маской — dx/dy из native обратно в design-пространство.
    Вход (как в оригинальной точке 0x58fcf6): ebx=dy_native, edi=x, eax=absL,
    esi=elem; ebp/остальное не трогаем. Воспроизводит украденные
    `mov ecx,edi; sub ecx,eax` и `imul ebx,[esi+0x184]`."""
    a = Asm(va)
    a.mov_rr('ecx', 'edi')
    a.sub_rr('ecx', 'eax')                       # dx_native
    a.mov_r_abs32('eax', VA_MODE_OBJ)
    a.test_rr('eax', 'eax'); a.jz('raw')
    a.mov_r_mem('eax', 'eax', 0x18)
    a.test_rr('eax', 'eax'); a.jz('raw')
    a.sub_esp(8)
    a.mov_r_mem('edx', 'eax', 0x14); a.mov_mem_r('esp', 0, 'edx')    # W
    a.mov_r_mem('edx', 'eax', 0x18); a.mov_mem_r('esp', 4, 'edx')    # H
    a.mov_r_mem('eax', 'esi', 0x14c)             # бит профиля (нижний nibble)
    a.and_eax_u8(0x0F)
    a.cmp_eax_u8(1); a.je('b800')                # бит 1 = профиль 800x600
    a.imul_r_r_imm('ecx', 'ecx', 1024)
    a.imul_r_r_imm('ebx', 'ebx', 768)
    a.jmp32('div')
    a.L('b800')
    a.imul_r_r_imm('ecx', 'ecx', 800)
    a.imul_r_r_imm('ebx', 'ebx', 600)
    a.L('div')
    a.mov_rr('eax', 'ecx'); a.cdq(); a.idiv_mem('esp', 0); a.mov_rr('ecx', 'eax')
    a.mov_rr('eax', 'ebx'); a.cdq(); a.idiv_mem('esp', 4); a.mov_rr('ebx', 'eax')
    a.add_esp(8)
    a.L('raw')
    a.imul_r_mem('ebx', 'esi', 0x184)            # украденная инструкция (stride)
    a.jmp32(RET_MASK)
    a.resolve()
    return bytes(a.b)


# ------------------------------------------------------------------- раскладка
def layout_parts():
    """Двухпроходная раскладка: размеры не зависят от адресов (все переходы rel32)."""
    env0 = {'scale_rect': CAVE_VA}
    sizes = {
        'trampA':     len(build_trampA(CAVE_VA, env0)),
        'post_scale': len(build_post(CAVE_VA, env0)),
        'scale_rect': len(build_scale_rect(CAVE_VA, env0)),
        'maskfix':    len(build_mask(CAVE_VA, env0)),
    }
    off = 0
    va = {}
    for name in ('trampA', 'post_scale', 'scale_rect', 'maskfix'):
        off = (off + 15) & ~15
        va[name] = CAVE_VA + off
        off += sizes[name]
    assert off <= CAVE_CAP, f"cave overflow: {off} > {CAVE_CAP}"
    env = dict(va)
    parts = {
        'trampA':     build_trampA(va['trampA'], env),
        'post_scale': build_post(va['post_scale'], env),
        'scale_rect': build_scale_rect(va['scale_rect'], env),
        'maskfix':    build_mask(va['maskfix'], env),
    }
    for name, blob in parts.items():          # размеры совпали с первым проходом?
        assert len(blob) == sizes[name], name
    return parts, va, sizes


def build_cave_blob(parts, va):
    used_end = max(va[n] + len(parts[n]) for n in parts) - CAVE_VA
    blob = bytearray(used_end)
    for name, b in parts.items():
        blob[va[name] - CAVE_VA: va[name] - CAVE_VA + len(b)] = b
    return bytes(blob)


# --------------------------------------------------------------- сборка патча
def va2file(va):
    return va - IMAGE_BASE     # для .text (RVA == file offset у данного билда)


def check_sites(d, verbose=True):
    ok = True
    for name, va, want, _sz in SITE_P1 + [SITE_H1, SITE_H2, SITE_H3]:
        off = va2file(va)
        cur = d[off:off + len(bytes.fromhex(want))].hex()
        good = cur == want
        ok &= good
        if verbose:
            print(f"  {name:4s} file {off:#08x}: have {cur}  want {want}  [{'OK' if good else 'MISMATCH'}]")
    cave = d[CAVE_FILE:CAVE_FILE + CAVE_CAP]
    zeros = all(b == 0 for b in cave)
    if verbose:
        print(f"  cave file {CAVE_FILE:#x}..{CAVE_FILE+CAVE_CAP:#x}: "
              f"{'пусто (OK)' if zeros else 'НЕ ПУСТО — будет перезаписан'}")
    return ok


def make_patched(d, parts, va):
    img = bytearray(d)
    # P1: форс flag=1
    for (name, va_s, _want, _sz), new in zip(SITE_P1, P1_NEW):
        img[va2file(va_s):va2file(va_s) + 2] = bytes.fromhex(new)
    # H1/H2/H3: jmp в cave (+ nop-хвосты)
    for (name, site_va, _want, size), part in ((SITE_H1, 'trampA'), (SITE_H2, 'post_scale'),
                                               (SITE_H3, 'maskfix')):
        rel = va[part] - (site_va + 5)
        rep = b'\xE9' + _p32(rel) + b'\x90' * (size - 5)
        img[va2file(site_va):va2file(site_va) + size] = rep
    # cave
    blob = build_cave_blob(parts, va)
    img[CAVE_FILE:CAVE_FILE + len(blob)] = blob
    return bytes(img), blob


def audit_diff(orig, patched):
    """Меняться должны только: 3 сайта P1, H1/H2/H3 и занятая часть cave."""
    allowed = set()
    for _n, va_s, _w, sz in SITE_P1 + [SITE_H1, SITE_H2, SITE_H3]:
        allowed.update(range(va2file(va_s), va2file(va_s) + sz))
    allowed.update(range(CAVE_FILE, CAVE_FILE + CAVE_CAP))
    changed = {i for i in range(len(orig)) if orig[i] != patched[i]}
    extra = changed - allowed
    assert not extra, f"неожиданные изменения: {sorted(extra)[:16]}"
    for _n, va_s, _w, sz in SITE_P1 + [SITE_H1, SITE_H2, SITE_H3]:
        site = set(range(va2file(va_s), va2file(va_s) + sz))
        assert site & changed, f"сайт {va_s:#x} не изменён"
    return len(changed)


# -------------------------------------------------------- capstone-верификация
def verify_disasm(parts, va, listing=False):
    from capstone import Cs, CS_ARCH_X86, CS_MODE_32
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    allowed = {RET_TRAMP, RET_POST, RET_MASK, VA_ITER} | set(va.values())
    n_ins = 0
    for name, blob in parts.items():
        base = va[name]
        allowed.update(range(base, base + len(blob)))
        dec = 0
        lines = []
        for ins in md.disasm(blob, base):
            dec += ins.size
            n_ins += 1
            lines.append("  %#010x  %-24s  %s %s" % (ins.address, ins.bytes.hex(' '),
                                                     ins.mnemonic, ins.op_str))
            if ins.mnemonic in ('jmp', 'call', 'jz', 'jnz', 'je', 'jne') and ins.op_str.startswith('0x'):
                tgt = int(ins.op_str, 16)
                assert tgt in allowed, f"{name}: цель ветвления {tgt:#x} вне разрешённого набора"
        assert dec == len(blob), f"{name}: {dec}/{len(blob)} байт не декодируются"
        if listing:
            print(f"\n; ---- {name} @ VA {base:#x} ({len(blob)} байт) ----")
            print("\n".join(lines))
    return n_ins


# ------------------------------------------- интерпретатор i386-подмножества
def _s32(v):
    v &= 0xFFFFFFFF
    return v - 0x100000000 if v & 0x80000000 else v


class Mem:
    """Плоская память из регионов (образ exe + BSS + heap + stack)."""

    def __init__(self):
        self.regions = []

    def map(self, base, data):
        self.regions.append((base, bytearray(data)))

    def _find(self, addr, n):
        for base, buf in self.regions:
            if base <= addr and addr + n <= base + len(buf):
                return buf, addr - base
        raise AssertionError(f"mem: адрес {addr:#x}+{n} вне регионов")

    def rb(self, addr, n):
        buf, off = self._find(addr, n)
        return bytes(buf[off:off + n])

    def wb(self, addr, data):
        buf, off = self._find(addr, len(data))
        buf[off:off + len(data)] = data

    def r32(self, addr):
        return struct.unpack('<I', self.rb(addr, 4))[0]

    def w32(self, addr, v):
        self.wb(addr, _p32(v))


class Mini386:
    """Интерпретатор подмножества i386, достаточного для cave: mov/lea/push/pop,
    add/sub/and/test/cmp, imul/idiv/cdq, call/ret/jmp/jz/jnz, pushad/popad/nop.
    Декодирование — capstone (detail). Флаги: только ZF (потребляют jz/jnz)."""

    ORDER = ['eax', 'ecx', 'edx', 'ebx', 'esp', 'ebp', 'esi', 'edi']

    def __init__(self, mem):
        self.m = mem
        self.r = {n: 0 for n in self.ORDER}
        self.eip = 0
        self.zf = 0
        from capstone import Cs, CS_ARCH_X86, CS_MODE_32
        self.md = Cs(CS_ARCH_X86, CS_MODE_32)
        self.md.detail = True
        self.steps = 0
        from capstone import x86 as cx86
        self.cx = cx86

    # -- доступ к операндам
    def _ea(self, op):
        m = op.mem
        assert m.index == 0 and m.scale == 1, "index/scale не ожидаются"
        base = 0 if m.base == 0 else self.r[self.md.reg_name(m.base)]
        return (base + m.disp) & 0xFFFFFFFF

    def _get(self, op):
        t = op.type
        if t == self.cx.X86_OP_IMM:
            return op.imm & 0xFFFFFFFF
        if t == self.cx.X86_OP_REG:
            return self.r[self.md.reg_name(op.reg)]
        if t == self.cx.X86_OP_MEM:
            assert op.size in (0, 4), f"не-dword обращение ({op.size})"
            return self.m.r32(self._ea(op))
        raise AssertionError(f"неизвестный тип операнда {t}")

    def _set(self, op, v):
        v &= 0xFFFFFFFF
        t = op.type
        if t == self.cx.X86_OP_REG:
            self.r[self.md.reg_name(op.reg)] = v
        elif t == self.cx.X86_OP_MEM:
            self.m.w32(self._ea(op), v)
        else:
            raise AssertionError("imm как приёмник")

    def _push(self, v):
        self.r['esp'] = (self.r['esp'] - 4) & 0xFFFFFFFF
        self.m.w32(self.r['esp'], v)

    def _pop(self):
        v = self.m.r32(self.r['esp'])
        self.r['esp'] = (self.r['esp'] + 4) & 0xFFFFFFFF
        return v

    def run(self, start, stop, budget=200000):
        self.eip = start
        while self.eip != stop:
            assert self.steps < budget, f"бюджет исчерпан (eip={self.eip:#x}) — зацикливание?"
            self.steps += 1
            code = self.m.rb(self.eip, 16)
            ins = next(self.md.disasm(code, self.eip), None)
            assert ins is not None, f"не декодируется @ {self.eip:#x}"
            self._exec(ins)
        return self.steps

    def _exec(self, ins):
        m, ops = ins.mnemonic, ins.operands
        nxt = ins.address + ins.size
        if m == 'nop':
            self.eip = nxt
        elif m == 'mov':
            self._set(ops[0], self._get(ops[1])); self.eip = nxt
        elif m == 'lea':
            self._set(ops[0], self._ea(ops[1])); self.eip = nxt
        elif m == 'push':
            self._push(self._get(ops[0])); self.eip = nxt
        elif m == 'add' or m == 'sub':
            a, b = self._get(ops[0]), self._get(ops[1])
            self._set(ops[0], a + b if m == 'add' else a - b); self.eip = nxt
        elif m == 'and':
            self._set(ops[0], self._get(ops[0]) & self._get(ops[1])); self.eip = nxt
        elif m == 'test':
            self.zf = 1 if (self._get(ops[0]) & self._get(ops[1])) == 0 else 0; self.eip = nxt
        elif m == 'cmp':
            self.zf = 1 if self._get(ops[0]) == self._get(ops[1]) else 0; self.eip = nxt
        elif m == 'imul':
            if len(ops) == 2:
                v = _s32(self._get(ops[0])) * _s32(self._get(ops[1]))
            else:
                v = _s32(self._get(ops[1])) * _s32(self._get(ops[2]))
            self._set(ops[0], v); self.eip = nxt
        elif m == 'cdq':
            self.r['edx'] = 0xFFFFFFFF if self.r['eax'] & 0x80000000 else 0; self.eip = nxt
        elif m == 'idiv':
            div = _s32(self._get(ops[0]))
            assert div != 0, "деление на ноль"
            num = (_s32(self.r['edx']) << 32) | self.r['eax']
            q = abs(num) // abs(div)
            if (num < 0) != (div < 0):
                q = -q
            assert -0x80000000 <= q <= 0x7FFFFFFF, f"idiv overflow: {q}"
            self.r['eax'] = q & 0xFFFFFFFF
            self.r['edx'] = (abs(num) % abs(div) * (1 if num < 0 else -1 if num >= 0 else 0)) & 0xFFFFFFFF if num >= 0 else (-(abs(num) % abs(div))) & 0xFFFFFFFF
            self.eip = nxt
        elif m == 'call':
            self._push(nxt); self.eip = self._get(ops[0])
        elif m == 'ret':
            self.eip = self._pop()
        elif m == 'jmp':
            self.eip = self._get(ops[0])
        elif m in ('jz', 'je'):
            self.eip = self._get(ops[0]) if self.zf else nxt
        elif m in ('jnz', 'jne'):
            self.eip = self._get(ops[0]) if not self.zf else nxt
        elif m == 'pushal':
            esp0 = self.r['esp']
            for n in self.ORDER:
                self._push(esp0 if n == 'esp' else self.r[n])
            self.eip = nxt
        elif m == 'popal':
            for n in reversed(self.ORDER):
                v = self._pop()
                if n != 'esp':
                    self.r[n] = v
            self.eip = nxt
        else:
            raise AssertionError(f"неподдерживаемая инструкция: {m} {ins.op_str} @ {ins.address:#x}")


# ------------------------------------------------- функциональные тесты cave
def emu_tests(patched_img, va):
    """Прогон байтов cave на интерпретаторе с синтетическими структурами.
    Итератор 0x6c51a0 в ТЕСТОВОМ образе заменяется заглушкой `slot=[slot+8]`:
    настоящий итератор обходит древовидную структуру, которую синтетика не
    воспроизводит; протокол вызова (push &slot / call / add esp,4) и обработка
    слота — те же, что в apply_flag, их тест и покрывает."""
    HEAP, STACK = 0x2000000, 0x1000000
    ITER_STUB = bytes.fromhex("8b542404" "8b02" "8b4008" "8902" "c3")  # slot=[slot+8]

    def new_cpu():
        mem = Mem()
        img = bytearray(patched_img[:0x417000])            # .text/.rdata/.data (file==RVA)
        img[va2file(VA_ITER):va2file(VA_ITER) + len(ITER_STUB)] = ITER_STUB
        mem.map(IMAGE_BASE, bytes(img))
        mem.map(0x400000 + 0x417000, bytes(0x43C000 - 0x417000))   # BSS-хвост .data
        mem.map(HEAP, bytes(0x20000))
        mem.map(STACK, bytes(0x20000))
        cpu = Mini386(mem)
        cpu.r['esp'] = STACK + 0x10000
        return cpu

    ok = True

    def chk(name, got, want):
        nonlocal ok
        good = got == want
        ok &= good
        print(f"  [{'OK ' if good else 'FAIL'}] {name}: got {got}, want {want}")

    def setup_mode(mem, w=1600, h=900, present=True):
        mo, md_ = HEAP, HEAP + 0x100
        if present:
            mem.w32(mo + 0x18, md_)
            mem.w32(md_ + 0x14, w)
            mem.w32(md_ + 0x18, h)
            mem.w32(VA_MODE_OBJ, mo)
        else:
            mem.w32(VA_MODE_OBJ, 0)

    # --- T1: трамплин H1 (живые W/H + фолбэк при null)
    print("test T1: trampA (live W/H + fallback)")
    cpu = new_cpu()
    setup_mode(cpu.m)
    cpu.r['esp'] = esp0 = STACK + 0x10000
    cpu.run(va['trampA'], RET_TRAMP)
    chk("edx=W", cpu.r['edx'], 1600)
    chk("[esp+0x24]=H", cpu.m.r32(esp0 + 0x24), 900)
    cpu = new_cpu()
    setup_mode(cpu.m, present=False)
    cpu.run(va['trampA'], RET_TRAMP)
    chk("fallback edx=1024", cpu.r['edx'], 1024)
    chk("fallback H=768", cpu.m.r32(cpu.r['esp'] + 0x24), 768)

    # --- T2: mask-fix H3 (профиль 1024 и 800; сохранность ebp)
    print("test T2: maskfix (dx/dy -> design)")
    for nib, want_dx, want_dy in ((2, 192, 85), (1, 150, 66)):
        cpu = new_cpu()
        setup_mode(cpu.m)
        elem = HEAP + 0x1000
        cpu.m.w32(elem + 0x14c, 0x00200000 | nib)
        cpu.m.w32(elem + 0x184, 20)                  # stride
        cpu.r.update(ebx=100, edi=500, eax=200, esi=elem, ebp=0xDEAD)
        cpu.run(va['maskfix'], RET_MASK)
        chk(f"nib={nib} dx_design", cpu.r['ecx'], want_dx)         # (500-200)*baseW/1600
        chk(f"nib={nib} dy_design*stride", cpu.r['ebx'], want_dy * 20)  # 100*baseH/900*20
        chk(f"nib={nib} ebp preserved", cpu.r['ebp'], 0xDEAD)

    # --- T3: пост-проход H2 (список 2 контрола, визуал, records не тронуты)
    print("test T3: post_scale (обход, RECT'ы, active, визуал)")
    cpu = new_cpu()
    m = cpu.m
    H = HEAP
    sc = H + 0x2000                                  # screen manager
    m.w32(sc + 0xe8, 0); m.w32(sc + 0xec, 0)
    m.w32(sc + 0xf0, 1600); m.w32(sc + 0xf4, 900)    # живые W/H (после H1)
    mgr, head, n1, n2 = H + 0x3000, H + 0x3040, H + 0x3080, H + 0x30C0
    e1, e2 = H + 0x4000, H + 0x5000
    v, oh, on1, sh, s, sn1, obj = (H + 0x6000 + i * 0x40 for i in range(7))
    m.w32(VA_MGR, mgr); m.w32(mgr, head)
    m.w32(head + 8, n1)
    m.w32(n1 + 8, n2); m.w32(n1 + 0x1c, e1)
    m.w32(n2 + 8, head); m.w32(n2 + 0x1c, e2)
    for off, vals in ((0x154, (100, 50, 300, 150)), (0x164, (100, 50, 300, 150)),
                      (0x174, (0, 0, 64, 64)), (0x18c, (0, 0, 7, 8)),
                      (0x19c, (10, 20, 30, 40)), (0x1ac, (10, 20, 30, 40))):
        for i, val in enumerate(vals):
            m.w32(e1 + off + 4 * i, val)
    m.w32(e1 + 0x14c, 2)
    m.w32(e1 + 0x148, v)
    m.w32(v, oh); m.w32(oh + 8, on1); m.w32(on1 + 8, oh)
    m.w32(on1 + 0x14, sh); m.w32(sh, s)
    m.w32(s + 8, sn1); m.w32(sn1 + 8, s); m.w32(sn1 + 0x10, obj)
    for i, val in enumerate((10, 10, 110, 60)):
        m.w32(obj + 0x18 + 4 * i, val)
        m.w32(obj + 0x40 + 4 * i, val)
    for i in range(4):
        m.w32(obj + 0x30 + 4 * i, 999)               # source-rect: НЕ трогать
    for off, vals in ((0x154, (0, 0, 10, 10)), (0x164, (0, 0, 0, 0)),
                      (0x174, (0, 0, 0, 0)), (0x1ac, (0, 0, 0, 0))):
        for i, val in enumerate(vals):
            m.w32(e2 + off + 4 * i, val)
    m.w32(e2 + 0x148, 0)

    def rd(addr, n=4):
        return [m.r32(addr + 4 * i) for i in range(n)]

    esp0 = STACK + 0x10000
    cpu.r.update(esi=sc, ebx=1, edi=0xABCD, ebp=0xBEEF, esp=esp0)
    steps = cpu.run(va['post_scale'], RET_POST)
    chk("eax (stolen mov)", cpu.r['eax'], 1600)
    chk("esp balance", cpu.r['esp'], esp0)
    chk("edi preserved", cpu.r['edi'], 0xABCD)
    chk("ebp preserved", cpu.r['ebp'], 0xBEEF)
    chk("ebx preserved", cpu.r['ebx'], 1)
    chk("esi preserved", cpu.r['esi'], sc)
    chk("e1 rect154", rd(e1 + 0x154), [156, 58, 468, 175])
    chk("e1 rect164", rd(e1 + 0x164), [156, 58, 468, 175])
    chk("e1 rect174", rd(e1 + 0x174), [0, 0, 100, 75])
    chk("e1 active X,Y,sX,sY", rd(e1 + 0x1ac), [15, 23, 30, 40])
    chk("e1 record1 intact", rd(e1 + 0x19c), [10, 20, 30, 40])
    chk("e1 record0 intact", rd(e1 + 0x18c), [0, 0, 7, 8])
    chk("obj+0x18 scaled", rd(obj + 0x18), [15, 11, 171, 70])
    chk("obj+0x40 scaled", rd(obj + 0x40), [15, 11, 171, 70])
    chk("obj+0x30 untouched", rd(obj + 0x30), [999, 999, 999, 999])
    chk("e2 rect154", rd(e2 + 0x154), [0, 0, 15, 11])
    chk("list intact (n2.next)", rd(n2 + 8, 1), [head])
    print(f"  (T3 выполнен за {steps} шагов)")

    # --- T4: identity (W,H == base) -> проход пропускается (на состоянии T3)
    print("test T4: post_scale identity-skip @1024x768")
    m.w32(sc + 0xf0, 1024); m.w32(sc + 0xf4, 768)     # экран как для base-профиля
    cpu.r.update(eax=0, ebx=1, ecx=0, edx=0, esi=sc, edi=0, ebp=0, esp=STACK + 0x10000)
    cpu.run(va['post_scale'], RET_POST)
    chk("e1 rect154 untouched (still scaled)", rd(e1 + 0x154), [156, 58, 468, 175])
    chk("obj+0x40 untouched", rd(obj + 0x40), [15, 11, 171, 70])
    chk("eax=1024", cpu.r['eax'], 1024)

    return ok


# ----------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description="native v2 patcher (docs/07 §6.2, docs/08)")
    ap.add_argument("src", nargs="?", default="Etherlords.exe")
    ap.add_argument("--out", default="Etherlords_native_v2.exe")
    ap.add_argument("--check", action="store_true", help="только проверка применимости")
    ap.add_argument("--listing", action="store_true", help="печатать дизассемблер cave")
    ap.add_argument("--no-emu", action="store_true", help="пропустить функциональные тесты")
    args = ap.parse_args()

    d = open(args.src, "rb").read()
    print(f"source : {args.src}  {len(d)} bytes  sha256={hashlib.sha256(d).hexdigest()[:16]}")

    print("\n[1/4] контрольные байты сайтов:")
    if not check_sites(d):
        print("\nABORT: бинарь отличается от анализируемого билда (docs/07).")
        sys.exit(2)

    print("\n[2/4] сборка cave:")
    parts, va, sizes = layout_parts()
    for name in ('trampA', 'post_scale', 'scale_rect', 'maskfix'):
        print(f"  {name:11s} VA {va[name]:#010x}  file {va2file(va[name]):#08x}  {sizes[name]:4d} байт")
    blob = build_cave_blob(parts, va)
    print(f"  итого занято {len(blob)} из {CAVE_CAP} байт cave")
    n_ins = verify_disasm(parts, va, listing=args.listing)
    print(f"  capstone: {n_ins} инструкций, все ветвления в разрешённом наборе, байт без остатка")

    print("\n[3/4] образ + аудит диффа:")
    img, _ = make_patched(d, parts, va)
    n_changed = audit_diff(d, img)
    print(f"  изменено байт: {n_changed} (только сайты P1/H1/H2/H3 + cave)")

    if args.check:
        print("\nCHECK OK: патч применим.")
        return

    if not args.no_emu:
        print("\n[4/4] интерпретатор: функциональные тесты cave (T1..T4)")
        if not emu_tests(img, va):
            print("\nABORT: тесты провалены — файл НЕ записан.")
            sys.exit(3)
    else:
        print("\n[4/4] Unicorn-тесты пропущены (--no-emu)")

    open(args.out, "wb").write(img)
    print(f"\nwrote {args.out}  {len(img)} bytes  sha256={hashlib.sha256(img).hexdigest()[:16]}")
    print("Далее: бэкап своего Etherlords.exe, положить результат под его именем,")
    print("выставить VideoResolution (1600x900 / 2560x1440) и пройти критерий приемки")
    print("(docs/04): нарисованные кнопки там, где раньше была hover-подсветка;")
    print("hover и click срабатывают в той же зоне. Откат при проблеме — бэкап")
    print("или безопасный базис tools/patch_layout.py.")


if __name__ == "__main__":
    main()
