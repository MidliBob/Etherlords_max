#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
patch_native_v3.py — сборщик native v3 для Etherlords.exe (Демиурги, рус. 1.07).

Наследует v2 (docs/08) и чинит два класса регрессий, найденных полевой приемкой
(docs/09): съехавший интерфейс меню сохранения/загрузки и глобальной карты +
«hover правее нарисованной кнопки» колеса команд.

Причина (docs/09 §2): пост-проход v2 масштабирует только те контролы, которые
уже лежат в списке менеджера [0x82b968] на момент apply_layout (т.е. созданные
при Init). Контролы, создаваемые лениво позже (кнопки колеса/скроллы adv-экрана,
клоны диалогов, списки сохранений — «FindControl-or-create» и new в коде экранов),
остаются в design-координатах, тогда как цепочка родителей уже масштабирована:
draw идёт по абсолютным design-rect'ам визуала, а hit-test суммирует
parent-relative rect'ы масштабированной цепочки → hover/click уезжают вправо-вниз
от нарисованного. Плюс экранные классы рисуют часть элементов от design-констант
(глобалы блока 0x8295xx меню сохранений, хардкод-рамка CSelectMission).

Новые хуки v3:
  H4  AddControl @0x58bbc0 (единственная точка регистрации контрола в менеджере,
      вызывается из ctor'а 0x58f2f2): масштабирование нового контрола в момент
      создания (scale_one), с маркером «уже масштабирован» в nibble [+0x14c];
      гейт — пост-проход уже отработал (маркер у головы списка) и W/H != base;
  H2' пост-проход v2 + маркер: пропускает помеченные контролы (идемпотентность),
      ставит маркер помасштабированным (та же процедура scale_one);
  H5  design-константы меню сохранений/загрузки (блок 0x8295xx: 62 dword'а —
      rect'ы/пары xy; ось field0/2 = X, field1/3 = Y): пересчёт из запечённых
      design-значений на живые W/H при входе в CSaveScreen::Draw (0x53f830) и в
      row-layout (0x53ec30) — идемпотентно (пишется из констант, не накопительно);
      0x8295a8/ac (пиксельный размер превью) НЕ масштабируются;
  H6  хардкод-рамка CSelectMission::Draw (0x5461bc, ветка flag==1): rect
      (158,111,866,661) -> масштабированный; source-rect текстуры (225,45,235,55)
      не трогается.

Маркер: bits 2..3 nibble [+0x14c]: (nibble & 0xC) == 0x4 => «масштабирован mod'ом».
ctor пишет nibble=0xF (0x58f2cf), apply_flag — 1/2, поэтому 0x4..0x7 в ванильной
игре не возникают; бит 0x8 не используем (входит в 0xF ctor'а).

Сборка/проверка как в v2: контрольные байты сайтов, capstone-аудит cave, аудит
диффа, интерпретатор i386 (тесты T1..T8 — 67 проверок в сборке с логгером;
с 0.0.8 прогоняются для ЛЮБОЙ сборки — логгер-стабы в тестах не исполняются).

БЫСТРЫЙ ЗАПУСК (0.0.9): положите этот скрипт в папку игры и запустите (двойной
клик или `python patch_native_v3.py`) — найдёт Etherlords.exe рядом (или в CWD),
создаст рядом Etherlords_native_v6dbg.exe; игру запускайте этим файлом
(переименований не нужно, оригинал не трогается). Нужны Python 3.8+ и capstone.
На Windows при запуске без аргументов окно не закроется сразу (пауза).

    python3 tools/patch_native_v3.py Etherlords.exe               # -> Etherlords_native_v6dbg.exe (с логгером)
    python3 tools/patch_native_v3.py Etherlords.exe --no-logger   # -> Etherlords_native_v6.exe (чистый release)

0.0.8: логгер H8/H9 (set_rect/OnLayoutChange -> el_evt.log) ВКЛЮЧЁН ПО УМОЛЧАНИЮ
В КАЖДОЙ СБОРКЕ — в репозитории нет исходного бинарника (0.0.6), полевой лог
основной канал данных. Лог усекается на первом событии сессии (CREATE_ALWAYS)
и ограничен DBG_CAP=20000 рекордов (~880 КБ); состояние — проверенно свободные
dword'ы .data 0x830040/0x830044 (НЕ 0x829764/68 из docs/09 §3 — они заняты
игрой, см. доп. 0.0.8). --no-logger = чистый release, байты идентичны v6 из
0.0.6 (sha256 5ad61f0e…). H10 (evt_hit) по-прежнему не включён — не влезает
в cave (доп. 0.0.6).

0.0.11: debug-сборка ДОПОЛНИТЕЛЬНО хукает H11 — hover-сайт CButtonList::Draw
0x57CFEE: рекорд kind=3 (56 Б: cursor [screen+0xe0/e4], rect array[i]+0x14,
i, флаги) для диагностики колеса (docs/09, доп. 0.0.11); dedup по смене i.

0.0.13: H12 (сайт 0x50F5B4) поставлен по статической гипотезе и НЕ СРАБОТАЛ
в поле (kind4=0): это обработчик КЛИКА, hover живёт в другом	mouse-виртуале.

0.0.14: H12 снят; вместо него H13 — vtable-интерпозиция ВСЕХ мышиных
виртуалов класса колеса (vtable 0x75AC20, слоты 3,7,9,0xA..0xD,0x12 — все
тела в wheel-регионе 0x50e4c1..0x510295): в debug-сборке слоты в файле
перенаправляются на трамплины в НОВОЙ PE-секции .ellog (RVA 0x43B000,
добавляется только в debug; release байт-в-байт прежний 5ad61f0e…); общий
стаб пишет kind=4 (44 Б): slot, this, vtable, caller-ret, args стека
(x,y,…), active [+0x1ac/+0x1b0], sector0 L [+0x208] — и уходит в оригинал
слота. Один сеанс показывает, КАКОЙ слот = hover и в каких пространствах
курсор/active/сектора (docs/09, доп. 0.0.14). Debug: cave 2283/2474 +
.ellog 272/4096, capstone 620, тесты T1–T10 (96 проверок), sha256
6477c5930fe722cf… (файл 4 317 184 Б = +4 КБ секции).
"""
import argparse
import hashlib
import os
import struct
import sys

# ------------------------------------------------------------------ константы
IMAGE_BASE = 0x400000
CAVE_FILE = 0x355656
CAVE_VA = 0x755656
CAVE_CAP = 0x356000 - CAVE_FILE          # 2474 байта

VA_MODE_OBJ = 0x825DE8                   # ->+0x18->{+0x14:W, +0x18:H} (живой режим)
VA_MGR      = 0x82B968                   # глобальный менеджер контролов
VA_SCREEN   = 0x82722C                   # screen manager ([+0x188] = flag профиля)
VA_ITER     = 0x6C51A0                   # итератор списка (как в apply_flag/Offset)
RET_TRAMP   = 0x59FCDA                   # возврат H1
RET_POST    = 0x59FD26                   # возврат H2
RET_MASK    = 0x58FD01                   # возврат H3
RET_ADD     = 0x58BBC5                   # возврат H4 (после украденных 5 байт)
RET_DRAW    = 0x53F839                   # возврат H5a (после call 0x5905d0)
RET_ROWL    = 0x53EC37                   # возврат H5b
RET_SEL1    = 0x5461C4                   # возврат H6 (gate=false: mov 2..4 оригинала)
RET_SEL2    = 0x5461DC                   # возврат H6 (gate=true: после rect'ов)
VA_DRAWBASE = 0x5905D0                   # базовый Draw (украденный call из H5a)

VTBL_BUTTONLIST = 0x75D498               # CButtonList: спрайт-массив rect'ов
MARK_MASK   = 0x0C

# логгер событий set_rect / OnLayoutChange (H8/H9) — ПО УМОЛЧАНИЮ В КАЖДОЙ
# СБОРКЕ (0.0.8): в репозитории больше нет исходного бинарника (0.0.6), полевой
# el_evt.log — основной канал данных для итераций. Чистый release: --no-logger.
# H10 (evt_hit, логгер hit-test-масок) удалён в 0.0.6: с ним cave переполнялся
# (2507 > 2474); возврат — только вместе с расширением cave (новая PE-секция).
# См. docs/09, доп. 0.0.6 и 0.0.8.
DEBUG = True
SITE_H8 = ("H8", 0x58F690, "8b4424048b10", 6)    # set_rect prologue
SITE_H9 = ("H9", 0x5912E0, "8b44240853", 5)      # OnLayoutChange prologue
# H11 (0.0.11): hover-сайт CButtonList::Draw — пишется [esi+0x28c]=edi при попадании
# PtInRect(array[i]+0x14, cursor[screen+0xe0/e4]); лог kind=3 (cursor+rect+i+флаги).
SITE_H11 = ("H11", 0x57CFEE, "89be8c020000", 6)
RET_H11 = 0x57CFF4
# H13 (0.0.14): vtable-интерпозиция мышиных виртуалов колеса. Класс колеса —
# vtable 0x75AC20 (в логах vt=?75ac20); его mouse-виртуалы — функции wheel-
# региона 0x50e4c1..0x510295 (H12-сайт 0x50f5b4 сидел в слоте 7 = обработчик
# КЛИКА, hover живёт в другом слоте). В debug-сборке слоты перенаправляются
# на трамплины в НОВОЙ PE-секции .ellog (RVA 0x43b000, только debug): общий
# стаб пишет kind=4 (slot, this, vt, caller, args0..2, active, sector0) и
# уходит в оригинал. Рекорд приходит на КАЖДЫЙ mouse-event колеса — видно,
# какой слот = hover.
VTBL_WHEEL = 0x75AC20
WHEEL_SLOTS = (3, 7, 9, 0x0A, 0x0B, 0x0C, 0x0D, 0x12)
WHEEL_ORIG = {3: 0x510100, 7: 0x50F530, 9: 0x50F740, 0x0A: 0x50FDB0,
              0x0B: 0x50FB70, 0x0C: 0x50FED0, 0x0D: 0x50FDD0, 0x12: 0x50F310}
EXTRA_RVA = 0x43B000       # RVA новой секции .ellog (= SizeOfImage оригинала)
EXTRA_VA = 0x400000 + EXTRA_RVA
EXTRA_CAP = 0x1000
RET_OLC = 0x5912E5
RET_SETRECT = 0x58F696
IAT_CREATEFILEA = 0x756270
IAT_CLOSEHANDLE = 0x7560D0
IAT_WRITEFILE   = 0x75617C
# Состояние логгера: два dword'а в нулевом (виртуальном) хвосте .data (секция
# R+W; .text не записываем). Свободность ПРОВЕРЕНА: во всём бинарнике нет ни
# одной 4-байтовой ссылки на 0x830040/0x830044 (pattern-scan). ВНИМАНИЕ:
# 0x829764/0x829768 из docs/09 §3 (v4→v5, «xref'ов нет») ЗАНЯТЫ — их пишет
# сама игра (mov [0x829764],0xa1 @0x54191e, mov [0x829768],edx @0x541bfc,
# mov ebx,0x829768 @0x5428de — блок констант экрана сохранений). Отгруженная
# v5dbg их фактически не использовала (в её cave нет ссылок), но повторно
# брать их нельзя.
VA_LOG_FLAG   = 0x830040   # 0 = первое событие сессии: CREATE_ALWAYS (усечь лог), далее 1
VA_LOG_COUNT  = 0x830044   # счётчик рекордов сессии
VA_LOG_LASTI  = 0x830048   # H11: последний залогированный hover-индекс (dedup)
DBG_CAP       = 20000      # лимит рекордов на сессию (44 Б * 20000 ≈ 880 КБ)
MARK_SCALED = 0x04                       # (nibble & MARK_MASK) == MARK_SCALED
TOOL_REV = "0.0.14"                      # ревизия сборщика: печатается в баннере и
                                         # читается tools/elfolder_check.py в папке игры

# Сайты: (имя, VA, ожидаемые байты, размер замены)
SITE_P1 = [
    ("P1a", 0x59BD4C, "751c", 2),        # jne -> jmp short (форс flag=1)
    ("P1b", 0x59BD58, "7510", 2),
    ("P1c", 0x59BD5F, "7509", 2),
]
P1_NEW = ["eb00", "ebf4", "ebed"]
SITE_H1 = ("H1", 0x59FCCD, "ba00040000", 5)          # mov edx,0x400 -> jmp trampA
SITE_H2 = ("H2", 0x59FD20, "8b86f0000000", 6)        # mov eax,[esi+0xf0] -> jmp post
SITE_H3 = ("H3", 0x58FCF6, "0faf9e84010000", 7)      # imul ebx,[esi+0x184] -> jmp mask
SITE_H4 = ("H4", 0x58BBC0, "568b742408", 5)          # push esi; mov esi,[esp+8]
SITE_H5A = ("H5a", 0x53F830, "56578bf1e8", 5)        # push esi; push edi; mov esi,ecx; call..
SITE_H5B = ("H5b", 0x53EC30, "6aff685180", 5)        # push -1; push 0x728051
SITE_H6 = ("H6", 0x5461BC, "c74424149e", 5)          # mov dword [esp+0x14],0x9e
# H7 (scale-aware set_rect) УДАЛЁН в v5: полевые кадры v4 показали, что вызовы
# set_rect в меню/adv получают УЖЕ native-rect'ы (центровка текстов, перестановка
# колеса) -> домножение на k давало двойной масштаб (съехавшие тексты главного
# меню, уход hover колеса). Анализ wheels-рассогласования перенесён в debug-лог
# (--debug, H8/H9). См. docs/09 §4 (v4 post-mortem).

ALL_SITES = lambda: SITE_P1 + [SITE_H1, SITE_H2, SITE_H3, SITE_H4, SITE_H5A,
                               SITE_H5B, SITE_H6] + ([SITE_H8, SITE_H9, SITE_H11] if DEBUG else [])


# design-константы блока меню сохранений (addr, value, axis): axis 0=X(kx), 1=Y(ky).
# Извлечены из setter'а 0x53db8c..0x53de78 (имmediates). Пары/четвёрки трактуются
# по осям позиционно: field0/field2 — X, field1/field3 — Y (LTRB и xywh одинаково).
SAVE_CONSTS = (
    # v5: оставлена только доказанная и безопасная пара — прибавка к active
    # (спрайт-якорь в CSaveScreen::Draw 0x53f8bd/bf). Колонки 0x829610..64c
    # исключены: rowlayout строит из них только шапку, а тексты строк берут
    # координаты из кэша CTextArray (design, Init) — масштабирование колонок
    # ломало отрисовку строк (v4: « smear »). См. docs/09 §3.1.
    (0x829550, 693, 0), (0x829554, 448, 1),
)
# хардкод-рамка CSelectMission (rect диалога, design 1024x768)
SEL_FRAME = (158, 111, 866, 661)

# ------------------------------------------------------------- микроассемблер
REG = {'eax': 0, 'ecx': 1, 'edx': 2, 'ebx': 3, 'esp': 4, 'ebp': 5, 'esi': 6, 'edi': 7}


def _p32(v):
    return struct.pack('<I', v & 0xFFFFFFFF)


def _modrm(mod, reg, rm):
    return bytes([(mod << 6) | (reg << 3) | rm])


def _mem(regfield, base, disp):
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
    """Сборщик cave. Все переходы rel32 фиксированной длины."""

    def __init__(self, base_va):
        self.b = bytearray()
        self.base = base_va
        self.fix = []
        self.labels = {}

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
            tva = self.base + self.labels[target] if isinstance(target, str) else target
            here = self.base + pos + 4
            self.b[pos:pos + 4] = _p32(tva - here)

    # -- инструкции
    def pushad(self):        self._e(b'\x60')
    def popad(self):         self._e(b'\x61')
    def cdq(self):           self._e(b'\x99')
    def ret(self):           self._e(b'\xC3')
    def nop(self):           self._e(b'\x90')
    def sub_esp(self, v):
        if v <= 127:
            self._e(b'\x83\xEC' + bytes([v]))
        else:
            self._e(b'\x81\xEC' + _p32(v))
    def add_esp(self, v):
        if v <= 127:
            self._e(b'\x83\xC4' + bytes([v]))
        else:
            self._e(b'\x81\xC4' + _p32(v))
    def push_r(self, r):     self._e(bytes([0x50 + REG[r]]))
    def pop_r(self, r):      self._e(bytes([0x58 + REG[r]]))
    def mov_r_abs32(self, r, va):
        # moffs/dispp: 8B /r mod=00 rm=101 (disp32) — верно для всех GPR
        self._e(b'\x8B' + _modrm(0, REG[r], 5) + _p32(va))
    def mov_r_mem(self, r, base, disp):   self._e(b'\x8B' + _mem(REG[r], base, disp))
    def mov_mem_r(self, base, disp, r):   self._e(b'\x89' + _mem(REG[r], base, disp))
    def mov_mem_imm(self, base, disp, imm):
        self._e(b'\xC7' + _mem(0, base, disp) + _p32(imm))
    def lea_r_mem(self, r, base, disp):   self._e(b'\x8D' + _mem(REG[r], base, disp))
    def test_rr(self, a, b):              self._e(b'\x85' + _modrm(3, REG[a], REG[b]))
    def and_eax_u8(self, v):              self._e(b'\x83\xE0' + bytes([v]))
    def and_eax_imm32(self, v):           self._e(b'\x25' + _p32(v))
    def or_eax_u8(self, v):               self._e(b'\x83\xC8' + bytes([v]))
    def cmp_eax_u8(self, v):              self._e(b'\x83\xF8' + bytes([v]))
    def cmp_eax_imm32(self, v):           self._e(b'\x3D' + _p32(v))
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
    def jae(self, t):  self._branch(b'\x0F\x83', t)
    def jbe(self, t):  self._branch(b'\x0F\x86', t)
    def inc_abs32(self, va):           self._e(b'\xFF\x05' + _p32(va))
    def cmp_abs32_imm(self, va, imm):  self._e(b'\x81\x3D' + _p32(va) + _p32(imm))
    def jmp32(self, t): self._branch(b'\xE9', t)
    def call_va(self, va):
        pos = len(self.b)
        self.b += b'\xE8' + b'\x00\x00\x00\x00'
        self.b[pos + 1:pos + 5] = _p32(va - (self.base + pos + 5))

    def add_eax_u8(self, v):                self._e(b'\x83\xC0' + bytes([v]))
    def add_rr(self, dst, src):             self._e(b'\x03' + _modrm(3, REG[dst], REG[src]))
    def cmp_rr(self, dst, src):             self._e(b'\x3B' + _modrm(3, REG[dst], REG[src]))
    def add_eax_imm32(self, v):             self._e(b'\x05' + _p32(v))
    def push_imm(self, v):                  self._e(b'\x68' + _p32(v))
    def push_mem(self, va):                   self._e(b'\xFF\x35' + _p32(va))
    def mov_mem_abs(self, r, va):             self._e(b'\x89' + _modrm(0, REG[r], 5) + _p32(va))
    def call_iat(self, va):                   self._e(b'\xFF\x15' + _p32(va))
    def raw(self, bs):                          self._e(bs)
    def mov_mem_imm8(self, base, disp, imm):
        self._e(b'\xC6' + _mem(0, base, disp) + bytes([imm & 0xFF]))


# ------------------------------------------------------------------ части cave
def build_post_done(va, env):
    """post_done() -> eax: 1, если пост-проход уже отработал (первый элемент
    списка менеджера помечен маркером). Безопасно на пустом/неинициализированном
    списке: null/empty-проверки на каждом шаге (крах v3 на старте: H4 вызывается
    на первом же контроле загрузки Controls.reg, когда список ещё пуст).
    Портит только eax; ecx/edx сохраняются."""
    a = Asm(va)
    a.push_r('ecx')
    a.push_r('edx')
    a.mov_r_abs32('edx', VA_MGR)
    a.test_rr('edx', 'edx'); a.jz('no')
    a.mov_r_mem('edx', 'edx', 0)                 # head
    a.test_rr('edx', 'edx'); a.jz('no')
    a.mov_r_mem('ecx', 'edx', 8)                 # первый node
    a.cmp_rr('ecx', 'edx'); a.je('no')           # пустой список (node == head)
    a.mov_r_mem('ecx', 'ecx', 0x1c)              # первый elem
    a.test_rr('ecx', 'ecx'); a.jz('no')
    a.mov_r_mem('eax', 'ecx', 0x14c)
    a.and_eax_u8(0x0F)
    a.and_eax_u8(0x0C)
    a.cmp_eax_u8(MARK_SCALED)
    a.jne('no')
    a.mov_r_imm('eax', 1)
    a.jmp32('out')
    a.L('no')
    a.mov_r_imm('eax', 0)
    a.L('out')
    a.pop_r('edx')
    a.pop_r('ecx')
    a.ret()
    a.resolve()
    return bytes(a.b)


def build_trampA(va, env):
    """H1: живые W/H вместо immediate 1024/768 (ветка flag=1), с null-фолбэком."""
    a = Asm(va)
    a.mov_r_abs32('eax', VA_MODE_OBJ)
    a.test_rr('eax', 'eax')
    a.jz('fb')
    a.mov_r_mem('eax', 'eax', 0x18)
    a.test_rr('eax', 'eax')
    a.jz('fb')
    a.mov_r_mem('edx', 'eax', 0x14)
    a.mov_r_mem('ecx', 'eax', 0x18)
    a.mov_mem_r('esp', 0x24, 'ecx')
    a.jmp32(RET_TRAMP)
    a.L('fb')
    a.mov_r_imm('edx', 0x400)
    a.mov_mem_imm('esp', 0x24, 0x300)
    a.jmp32(RET_TRAMP)
    a.resolve()
    return bytes(a.b)


def build_scale_rect(va, env):
    """scale_rect(ecx=&RECT): L,R *= W/baseW; T,B *= H/baseH.
    Кадр вызывающего: W=[esp+4+0], H=[esp+4+4], baseW=[esp+4+8], baseH=[esp+4+12].
    Портит только eax/edx."""
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


def build_scale_one(va, env):
    """scale_one(eax=elem, edx=force): масштабирование одного контрола (поля те же,
    что в пост-проходе v2) с маркер-протоколом:
      * (nibble[+0x14c] & 0xC) == 0x4 -> уже масштабирован, выход;
      * edx==0: гейт «пост-проход отработал» = маркер у головы списка [0x82b968]
        (edx==1 — форс из пост-прохода, гейт не нужен);
      * живой режим [0x825de8]; base = (800,600) при flag==0, иначе (1024,768);
      * k==1 -> только маркер;
      * scale: +0x154/+0x164/+0x174, active +0x1ac/+0x1b0, визуал (+0x40/+0x18);
      * ставит маркер (nibble & ~0xC | 0x4).
    Кадр (sub esp,40): W=0,H=4,bW=8,bH=12,elem=16,S=20,ohead=24,onode=28,snode=32.
    Портит eax/ecx/edx."""
    SR = env['scale_rect']
    a = Asm(va)
    a.sub_esp(40)
    a.mov_mem_r('esp', 16, 'eax')
    a.mov_r_mem('eax', 'eax', 0x14c)             # маркер: уже масштабирован?
    a.and_eax_u8(0x0F)
    a.and_eax_u8(0x0C)
    a.cmp_eax_u8(MARK_SCALED)
    a.je('out')
    a.test_rr('edx', 'edx')
    a.jnz('gate_ok')                             # force: гейт не нужен
    a.call_va(env['post_done'])
    a.test_rr('eax', 'eax')
    a.jz('out')
    a.L('gate_ok')
    a.mov_r_abs32('eax', VA_MODE_OBJ)            # живой режим
    a.test_rr('eax', 'eax'); a.jz('out')
    a.mov_r_mem('eax', 'eax', 0x18)
    a.test_rr('eax', 'eax'); a.jz('out')
    a.mov_r_mem('ecx', 'eax', 0x14); a.mov_mem_r('esp', 0, 'ecx')    # W
    a.mov_r_mem('ecx', 'eax', 0x18); a.mov_mem_r('esp', 4, 'ecx')    # H
    a.mov_r_abs32('eax', VA_SCREEN)              # base по флагу профиля
    a.test_rr('eax', 'eax'); a.jz('out')
    a.mov_r_mem('ecx', 'eax', 0x188)
    a.test_rr('ecx', 'ecx')
    a.jnz('base1024')
    a.mov_mem_imm('esp', 8, 800); a.mov_mem_imm('esp', 12, 600)
    a.jmp32('basedone')
    a.L('base1024')
    a.mov_mem_imm('esp', 8, 1024); a.mov_mem_imm('esp', 12, 768)
    a.L('basedone')
    a.mov_r_mem('eax', 'esp', 0); a.cmp_r_mem('eax', 'esp', 8); a.jne('work')
    a.mov_r_mem('eax', 'esp', 4); a.cmp_r_mem('eax', 'esp', 12); a.jne('work')
    a.jmp32('mark')                              # k==1: только маркер
    a.L('work')
    a.mov_r_mem('eax', 'esp', 16)
    a.lea_r_mem('ecx', 'eax', 0x154); a.call_va(SR)
    a.mov_r_mem('eax', 'esp', 16)
    a.lea_r_mem('ecx', 'eax', 0x164); a.call_va(SR)
    a.mov_r_mem('eax', 'esp', 16)
    a.lea_r_mem('ecx', 'eax', 0x174); a.call_va(SR)
    a.mov_r_mem('eax', 'esp', 16)                # active X,Y
    a.lea_r_mem('ecx', 'eax', 0x1ac)
    a.mov_r_mem('eax', 'ecx', 0)
    a.imul_r_mem('eax', 'esp', 0); a.cdq(); a.idiv_mem('esp', 8)
    a.mov_mem_r('ecx', 0, 'eax')
    a.mov_r_mem('eax', 'ecx', 4)
    a.imul_r_mem('eax', 'esp', 4); a.cdq(); a.idiv_mem('esp', 12)
    a.mov_mem_r('ecx', 4, 'eax')
    a.mov_r_mem('eax', 'esp', 16)                # визуал: обход как в 0x58a5d0
    a.mov_r_mem('eax', 'eax', 0x148)
    a.test_rr('eax', 'eax'); a.jz('blist')
    a.mov_r_mem('eax', 'eax', 0)                 # ohead
    a.mov_mem_r('esp', 24, 'eax')
    a.mov_r_mem('eax', 'eax', 8)                 # onode
    a.mov_mem_r('esp', 28, 'eax')
    a.cmp_r_mem('eax', 'esp', 24); a.je('mark')
    a.L('vouter')
    a.mov_r_mem('eax', 'esp', 28)
    a.mov_r_mem('eax', 'eax', 0x14)              # sh
    a.mov_r_mem('eax', 'eax', 0)                 # S
    a.mov_mem_r('esp', 20, 'eax')
    a.mov_r_mem('eax', 'esp', 20)
    a.mov_r_mem('eax', 'eax', 8)                 # snode = [S+8]
    a.mov_mem_r('esp', 32, 'eax')
    a.cmp_r_mem('eax', 'esp', 20); a.je('vnext')
    a.L('vinner')
    a.mov_r_mem('eax', 'esp', 32)
    a.mov_r_mem('eax', 'eax', 0x10)              # obj
    a.lea_r_mem('ecx', 'eax', 0x40); a.call_va(SR)
    a.mov_r_mem('eax', 'esp', 32)
    a.mov_r_mem('eax', 'eax', 0x10)
    a.lea_r_mem('ecx', 'eax', 0x18); a.call_va(SR)
    a.lea_r_mem('eax', 'esp', 32)
    a.push_r('eax')
    a.call_va(VA_ITER); a.add_esp(4)
    a.mov_r_mem('eax', 'esp', 32)
    a.cmp_r_mem('eax', 'esp', 20)
    a.jne('vinner')
    a.L('vnext')
    a.lea_r_mem('eax', 'esp', 28)
    a.push_r('eax')
    a.call_va(VA_ITER); a.add_esp(4)
    a.mov_r_mem('eax', 'esp', 28)
    a.cmp_r_mem('eax', 'esp', 24)
    a.jne('vouter')
    a.L('blist')
    # CButtonList: собственный массив спрайтов [elem+0x1c0], шаг 0x34, rect +0x14
    a.mov_r_mem('eax', 'esp', 16)
    a.mov_r_mem('eax', 'eax', 0)                 # vtable
    a.cmp_eax_imm32(VTBL_BUTTONLIST)
    a.jne('mark')
    a.mov_r_mem('ebx', 'esp', 16)
    a.mov_r_mem('edx', 'ebx', 0x1c4)             # count
    a.test_rr('edx', 'edx'); a.jz('mark')
    a.mov_r_mem('ebx', 'ebx', 0x1c0)             # base массива
    a.mov_mem_r('esp', 36, 'edx')                # i = count
    a.L('sloop')
    a.mov_r_mem('eax', 'esp', 36)
    a.add_eax_u8(0xFF)                           # i -= 1
    a.mov_mem_r('esp', 36, 'eax')
    a.imul_r_r_imm('eax', 'eax', 0x34)
    a.add_rr('eax', 'ebx')
    a.lea_r_mem('ecx', 'eax', 0x14)              # rect спрайта
    a.call_va(SR)
    a.mov_r_mem('eax', 'esp', 36)
    a.test_rr('eax', 'eax')
    a.jnz('sloop')
    a.L('mark')
    a.mov_r_mem('eax', 'esp', 16)
    a.mov_r_mem('eax', 'eax', 0x14c)
    a.and_eax_imm32(0xFFFFFFF3)                  # & ~0xC
    a.or_eax_u8(MARK_SCALED)
    a.mov_r_mem('ecx', 'esp', 16)
    a.mov_mem_r('ecx', 0x14c, 'eax')
    a.L('out')
    a.add_esp(40)
    a.ret()
    a.resolve()
    return bytes(a.b)


def build_post(va, env):
    """H2': пост-проход после apply_flag: обход списка [0x82b968] и scale_one(force=1)
    для каждого контрола (маркер делает проход идемпотентным). Кадр (sub esp,16):
    head=0,node=4,elem=8. Внутри pushad/popad; в конце украденный mov eax,[esi+0xf0]."""
    SO = env['scale_one']
    SR = env['scale_rect']
    a = Asm(va)
    a.pushad()
    a.sub_esp(16)
    a.mov_r_abs32('eax', VA_MGR)
    a.mov_r_mem('eax', 'eax', 0)                       # head = [mgr]
    a.mov_mem_r('esp', 0, 'eax')
    a.mov_r_mem('eax', 'eax', 8)                       # node = [head+8]
    a.mov_mem_r('esp', 4, 'eax')
    a.cmp_r_mem('eax', 'esp', 0); a.je('fin')
    a.L('outer')
    a.mov_r_mem('eax', 'esp', 4)
    a.mov_r_mem('eax', 'eax', 0x1c)                    # elem = [node+0x1c]
    a.mov_mem_r('esp', 8, 'eax')
    a.mov_r_imm('edx', 1)                              # force: без гейта головы
    a.call_va(SO)
    a.lea_r_mem('eax', 'esp', 4)
    a.push_r('eax')
    a.call_va(VA_ITER); a.add_esp(4)
    a.mov_r_mem('eax', 'esp', 4)
    a.cmp_r_mem('eax', 'esp', 0); a.jne('outer')
    # v6: abs-rect'а adv-панели/колеса (fn 0x5036xx: design-глобалы 0x827e70/80 ->
    # parent-relative +0x154, визуал не двигается -> hover уезжал от нарисованного
    # колеса). Boot-setter 0x501b10/0x501b40, рантайм-writer'ов нет (el_evt.log).
    a.mov_r_abs32('eax', VA_MODE_OBJ)
    a.test_rr('eax', 'eax'); a.jz('fin')
    a.mov_r_mem('eax', 'eax', 0x18)
    a.test_rr('eax', 'eax'); a.jz('fin')
    a.mov_r_mem('ecx', 'eax', 0x14); a.mov_mem_r('esp', 0, 'ecx')
    a.mov_r_mem('ecx', 'eax', 0x18); a.mov_mem_r('esp', 4, 'ecx')
    a.test_rr('ebx', 'ebx'); a.jnz('b1024')
    a.mov_mem_imm('esp', 8, 800); a.mov_mem_imm('esp', 12, 600)
    a.jmp32('bdone')
    a.L('b1024')
    a.mov_mem_imm('esp', 8, 1024); a.mov_mem_imm('esp', 12, 768)
    a.L('bdone')
    a.mov_r_mem('eax', 'esp', 0); a.cmp_r_mem('eax', 'esp', 8); a.jne('gscale')
    a.mov_r_mem('eax', 'esp', 4); a.cmp_r_mem('eax', 'esp', 12); a.je('fin')
    a.L('gscale')
    a.mov_r_imm('ecx', 0x827E70); a.call_va(SR)
    a.mov_r_imm('ecx', 0x827E80); a.call_va(SR)
    a.L('fin')
    a.add_esp(16)
    a.popad()
    a.mov_r_mem('eax', 'esi', 0xf0)                    # украденная инструкция
    a.jmp32(RET_POST)
    a.resolve()
    return bytes(a.b)


def build_mask(va, env):
    """H3: mask-fix hit-test (как в v2)."""
    a = Asm(va)
    a.mov_rr('ecx', 'edi')
    a.sub_rr('ecx', 'eax')
    a.mov_r_abs32('eax', VA_MODE_OBJ)
    a.test_rr('eax', 'eax'); a.jz('raw')
    a.mov_r_mem('eax', 'eax', 0x18)
    a.test_rr('eax', 'eax'); a.jz('raw')
    a.sub_esp(8)
    a.mov_r_mem('edx', 'eax', 0x14); a.mov_mem_r('esp', 0, 'edx')
    a.mov_r_mem('edx', 'eax', 0x18); a.mov_mem_r('esp', 4, 'edx')
    a.mov_r_mem('eax', 'esi', 0x14c)
    a.and_eax_u8(0x0F)
    a.cmp_eax_u8(1); a.je('b800')
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
    a.imul_r_mem('ebx', 'esi', 0x184)
    a.jmp32(RET_MASK)
    a.resolve()
    return bytes(a.b)


def build_addstub(va, env):
    """H4: пролог AddControl 0x58bbc0 (push esi; mov esi,[esp+8]): масштабировать
    новый контрол в момент регистрации. [esp+4]=elem на входе. pushad/popad —
    контекст ctor'а целый; затем украденные 5 байт и jmp RET_ADD."""
    SO = env['scale_one']
    a = Asm(va)
    a.pushad()
    a.mov_r_mem('eax', 'esp', 0x24)              # elem = [esp+0x24] после pushad
    a.mov_r_imm('edx', 0)                        # гейт головы обязателен
    a.call_va(SO)
    a.popad()
    a.push_r('esi')                              # украденные: push esi
    a.mov_r_mem('esi', 'esp', 8)                 #         ; mov esi,[esp+8]
    a.jmp32(RET_ADD)
    a.resolve()
    return bytes(a.b)


def build_savefix(va, env):
    """fix_save_consts: идемпотентный пересчёт design-констант блока 0x8295xx
    (таблица SAVE_CONSTS лежит в cave следом, part 'savefix_tbl': тройки
    (addr, design, axis)) в native по осям: X *= W/1024, Y *= H/768.
    Гейт: flag==1 ([0x82722c]+0x188), маркер головы списка (пост-проход был),
    (W,H) != (1024,768). Кадр (sub esp,20): W=0,H=4,i=8,addr=12,den=16.
    Портит eax/ecx/edx (ebx/esi/edi/ebp не трогает)."""
    a = Asm(va)
    a.sub_esp(20)
    a.mov_r_abs32('eax', VA_SCREEN)
    a.test_rr('eax', 'eax'); a.jz('out')
    a.mov_r_mem('ecx', 'eax', 0x188)
    a.test_rr('ecx', 'ecx'); a.jz('out')
    a.call_va(env['post_done'])
    a.test_rr('eax', 'eax'); a.jz('out')
    a.mov_r_abs32('eax', VA_MODE_OBJ)
    a.test_rr('eax', 'eax'); a.jz('out')
    a.mov_r_mem('eax', 'eax', 0x18)
    a.test_rr('eax', 'eax'); a.jz('out')
    a.mov_r_mem('ecx', 'eax', 0x14); a.mov_mem_r('esp', 0, 'ecx')
    a.mov_r_mem('ecx', 'eax', 0x18); a.mov_mem_r('esp', 4, 'ecx')
    a.mov_r_mem('eax', 'esp', 0)
    a.cmp_eax_imm32(1024); a.jne('go')
    a.mov_r_mem('eax', 'esp', 4)
    a.cmp_eax_imm32(768); a.je('out')
    a.L('go')
    a.mov_mem_imm('esp', 8, 0)                   # i = 0
    a.L('loop')
    a.mov_r_mem('eax', 'esp', 8)
    a.imul_r_r_imm('eax', 'eax', 12)
    a.add_eax_imm32(env['savefix_tbl'])
    a.mov_mem_r('esp', 12, 'eax')                # addr-ptr = tbl + i*12
    a.mov_r_mem('ecx', 'eax', 4)                 # design
    a.mov_r_mem('edx', 'eax', 8)                 # axis
    a.test_rr('edx', 'edx'); a.jnz('axis_y')
    a.imul_r_mem('ecx', 'esp', 0)                # design * W
    a.mov_rr('eax', 'ecx')
    a.cdq()
    a.mov_mem_imm('esp', 16, 1024)
    a.idiv_mem('esp', 16)
    a.jmp32('store')
    a.L('axis_y')
    a.imul_r_mem('ecx', 'esp', 4)                # design * H
    a.mov_rr('eax', 'ecx')
    a.cdq()
    a.mov_mem_imm('esp', 16, 768)
    a.idiv_mem('esp', 16)
    a.L('store')
    a.mov_r_mem('edx', 'esp', 12)
    a.mov_r_mem('edx', 'edx', 0)                 # addr
    a.mov_mem_r('edx', 0, 'eax')                 # [addr] = scaled
    a.mov_r_mem('eax', 'esp', 8)
    a.add_eax_u8(1)
    a.mov_mem_r('esp', 8, 'eax')
    a.cmp_eax_u8(len(SAVE_CONSTS))
    a.jne('loop')
    a.L('out')
    a.add_esp(20)
    a.ret()
    a.resolve()
    return bytes(a.b)


def build_savefix_tbl(va, env):
    return b''.join(_p32(addr) + _p32(val) + _p32(axis)
                    for addr, val, axis in SAVE_CONSTS)


def build_drawstub(va, env):
    """H5a: пролог CSaveScreen::Draw 0x53f830 (push esi; push edi; mov esi,ecx;
    call 0x5905d0[опкод украден]): fix_save_consts, затем базовый Draw и jmp
    RET_DRAW."""
    SF = env['savefix']
    a = Asm(va)
    a.push_r('esi')
    a.push_r('edi')
    a.mov_rr('esi', 'ecx')
    a.pushad()
    a.call_va(SF)
    a.popad()
    a.call_va(VA_DRAWBASE)
    a.jmp32(RET_DRAW)
    a.resolve()
    return bytes(a.b)


def build_rowlstub(va, env):
    """H5b: пролог row-layout 0x53ec30 (push -1; push 0x728051): fix_save_consts
    перед украденными push'ами."""
    SF = env['savefix']
    a = Asm(va)
    a.pushad()
    a.call_va(SF)
    a.popad()
    a.push_imm(0xFFFFFFFF)
    a.push_imm(0x728051)
    a.jmp32(RET_ROWL)
    a.resolve()
    return bytes(a.b)


def build_selstub(va, env):
    """H6: сайт 0x5461bc (mov dword [esp+0x14],0x9e — хардкод рамки диалога
    CSelectMission, ветка flag==1). gate=true: пишем масштабированный rect в слоты
    [esp+0x14..0x23] и jmp RET_SEL2; gate=false: пишем design mov#1 и jmp RET_SEL1
    (оригинальные mov 2..4). eax/ecx/edx/ebx сохраняются."""
    a = Asm(va)
    a.push_r('eax')
    a.push_r('ecx')
    a.push_r('edx')
    a.push_r('ebx')
    a.mov_r_abs32('eax', VA_SCREEN)
    a.test_rr('eax', 'eax'); a.jz('nogate')
    a.mov_r_mem('ecx', 'eax', 0x188)
    a.test_rr('ecx', 'ecx'); a.jz('nogate')
    a.call_va(env['post_done'])
    a.test_rr('eax', 'eax'); a.jz('nogate')
    a.mov_r_abs32('eax', VA_MODE_OBJ)
    a.test_rr('eax', 'eax'); a.jz('nogate')
    a.mov_r_mem('eax', 'eax', 0x18)
    a.test_rr('eax', 'eax'); a.jz('nogate')
    a.mov_r_mem('ebx', 'eax', 0x14)              # W
    a.mov_r_mem('ecx', 'eax', 0x18)              # H
    a.sub_esp(16)                                # W=0,H=4,d1=8,d2=12 (esp=F)
    a.mov_mem_r('esp', 0, 'ebx')
    a.mov_mem_r('esp', 4, 'ecx')
    a.mov_mem_imm('esp', 8, 1024)
    a.mov_mem_imm('esp', 12, 768)
    a.mov_r_mem('eax', 'esp', 0)
    a.cmp_eax_imm32(1024); a.jne('go')
    a.mov_r_mem('eax', 'esp', 4)
    a.cmp_eax_imm32(768); a.je('kip')
    a.L('go')
    # слоты оригинального rect: E+0x14 = [F+0x34] (4 push + sub 16 = 0x20; E=F+0x20)
    for i, (design, axis) in enumerate(zip(SEL_FRAME, (0, 1, 0, 1))):
        a.mov_r_imm('eax', design)
        a.imul_r_mem('eax', 'esp', 0 if axis == 0 else 4)
        a.cdq()
        a.idiv_mem('esp', 8 if axis == 0 else 12)
        a.mov_mem_r('esp', 0x34 + 4 * i, 'eax')
    a.L('outpop')
    a.add_esp(16)
    a.pop_r('ebx')
    a.pop_r('edx')
    a.pop_r('ecx')
    a.pop_r('eax')
    a.jmp32(RET_SEL2)
    a.L('kip')
    a.add_esp(16)
    a.jmp32('nogate')
    a.L('nogate')
    a.pop_r('ebx')
    a.pop_r('edx')
    a.pop_r('ecx')
    a.pop_r('eax')
    a.mov_mem_imm('esp', 0x14, 0x9E)             # оригинал mov #1 (design)
    a.jmp32(RET_SEL1)
    a.resolve()
    return bytes(a.b)

# ----------------------------------------------- debug-логгер (--debug, v5dbg)
# Бинарный лог событий перестановок: рекорд 11 dword (44 байта):
#   [0] kind (1=set_rect, 2=OnLayoutChange)
#   [1] this (контрол)
#   [2] vtable контрола
#   [3] return address вызывающего (код-сайт перестановки)
#   [4] marker byte [this+0x14c] & 0xFF
#   [5..8] rect[4] (kind=1) или dShX,dShY,dX,dY (kind=2)
#   [9] 0
# Файл el_evt.log пишется в рабочем каталоге игры (CreateFileA FILE_APPEND_DATA).
def build_evt_str(va, env):
    return b"el_evt.log\x00"


def build_evt_write(va, env):
    """evt_write(eax=name_z, edx=buf, ecx=len): пишет один рекорд в el_evt.log.

    CreateFileA(FILE_APPEND_DATA) -> WriteFile -> CloseHandle на каждый вызов,
    без кэша handle (его негде безопасно хранить, кроме проверенных dword'ов
    ниже). Относительный путь = cwd игры (тот же, где HallOfFame.hl).

    Состояние логгера (0.0.8) — dword'ы VA_LOG_FLAG/VA_LOG_COUNT в нулевом
    хвосте .data (загрузчик зануляет их на старте процесса):
      * первое событие сессии (flag==0): CREATE_ALWAYS — старый el_evt.log
        УСекается, лог всегда соответствует последнему запуску; flag:=1;
      * последующие: OPEN_ALWAYS (append);
      * после DBG_CAP рекордов записи прекращаются (защита от безлимита).
    Портит eax/ecx/edx/ebx (esi/edi сохраняет); вызывается под pushad стабов.
    Ошибка CreateFileA (нет прав на cwd) -> тихий выход, без краша."""
    a = Asm(va)
    a.push_r('ebx')
    a.inc_abs32(VA_LOG_COUNT)                      # счётчик рекордов сессии
    a.cmp_abs32_imm(VA_LOG_COUNT, DBG_CAP)
    a.jbe('cap_ok')
    a.pop_r('ebx')                                 # лимит: больше не пишем
    a.ret()
    a.L('cap_ok')
    a.mov_r_abs32('ebx', VA_LOG_FLAG)              # 0 = первое событие сессии
    a.push_r('esi')
    a.push_r('edi')
    a.mov_rr('esi', 'edx')                         # buf
    a.mov_rr('edi', 'ecx')                         # len
    a.mov_r_imm('edx', 4)                          # OPEN_ALWAYS (append)
    a.test_rr('ebx', 'ebx')
    a.jnz('have_disp')
    a.mov_r_imm('edx', 2)                          # CREATE_ALWAYS: усекаем старый лог
    a.mov_r_imm('ebx', 1)
    a.mov_mem_abs('ebx', VA_LOG_FLAG)              # [flag] = 1
    a.L('have_disp')
    a.mov_rr('ebx', 'eax')                         # name
    a.push_imm(0)                                # hTemplateFile
    a.push_imm(0x00000080)                       # dwFlagsAndAttributes
    a.push_r('edx')                              # dwCreationDisposition
    a.push_imm(0)                                # lpSecurityAttributes
    a.push_imm(7)                                # share R|W|D
    a.push_imm(0x00000004)                       # FILE_APPEND_DATA
    a.push_r('ebx')
    a.call_iat(IAT_CREATEFILEA)
    a.mov_r_imm('edx', 0xFFFFFFFF)
    a.cmp_rr('eax', 'edx'); a.je('out')
    a.mov_rr('ebx', 'eax')                       # handle
    a.sub_esp(8)
    a.push_imm(0)                                # lpOverlapped
    a.lea_r_mem('eax', 'esp', 4)                 # &written
    a.push_r('eax')
    a.push_r('edi')                              # len
    a.push_r('esi')                              # buf
    a.push_r('ebx')                              # h
    a.call_iat(IAT_WRITEFILE)
    a.push_r('ebx')
    a.call_iat(IAT_CLOSEHANDLE)
    a.add_esp(8)
    a.L('out')
    a.pop_r('edi')
    a.pop_r('esi')
    a.pop_r('ebx')
    a.ret()
    a.resolve()
    return bytes(a.b)


def build_evt_setrect(va, env):
    """H8: пролог set_rect 0x58f690 (6 байт): лог + украденные mov eax,[esp+4];
    mov edx,[eax]; jmp 0x58f696. this=ecx, rect*=[esp+4], ret=[esp]."""
    W = env['evt_write']
    a = Asm(va)
    a.push_r('ecx')                              # сохранить this над pushad
    a.pushad()
    a.sub_esp(48)
    a.mov_mem_imm('esp', 0, 1)                   # kind
    a.mov_r_mem('eax', 'esp', 0x50)              # this (push ecx slot)
    a.mov_mem_r('esp', 4, 'eax')
    a.mov_r_mem('eax', 'eax', 0)                 # vtable
    a.mov_mem_r('esp', 8, 'eax')
    a.mov_r_mem('eax', 'esp', 0x54)              # ret addr (E)
    a.mov_mem_r('esp', 12, 'eax')
    a.mov_r_mem('eax', 'esp', 0x50)
    a.mov_r_mem('eax', 'eax', 0x14c)
    a.and_eax_u8(0xFF)
    a.mov_mem_r('esp', 16, 'eax')
    a.mov_r_mem('eax', 'esp', 0x58)              # rect* (E+4)
    for j in range(4):
        a.mov_r_mem('edx', 'eax', 4 * j)
        a.mov_mem_r('esp', 20 + 4 * j, 'edx')
    a.mov_mem_imm('esp', 36, 0)
    a.mov_r_imm('eax', env['evt_str'])
    a.lea_r_mem('edx', 'esp', 0)
    a.mov_r_imm('ecx', 44)
    a.call_va(W)
    a.add_esp(48)
    a.L('skip')
    a.popad()
    a.pop_r('ecx')
    a.mov_r_mem('eax', 'esp', 4)                 # украденные
    a.mov_r_mem('edx', 'eax', 0)
    a.jmp32(RET_SETRECT)
    a.resolve()
    return bytes(a.b)


def build_evt_hover(va, env):
    """H11 (0.0.11): сайт hover-попадания CButtonList::Draw 0x57CFEE (6 байт:
    mov [esi+0x28c], edi — пишется индекс кнопки при PtInRect(array[i]+0x14,
    cursor), где cursor = [screen+0xe0]/[screen+0xe4] один раз на Draw).
    Лог kind=3 (56 Б, свой stride): this, vtable, i, cursor(x,y), rect
    array[i]+0x14 (LTRB), флаги [+0x14c]. Dedup: пишем только при смене i
    (свой dword VA_LOG_LASTI) — иначе hover каждый кадр съел бы DBG_CAP.
    Украденные байты + jmp 0x57CFF4. Регистры — под pushad."""
    W = env['evt_write']
    a = Asm(va)
    a.pushad()
    a.mov_r_abs32('eax', VA_LOG_LASTI)
    a.lea_r_mem('ecx', 'edi', 1)       # 0.0.12: храним i+1 (0 = «ещё не было»),
    a.cmp_rr('eax', 'ecx')             # иначе dedup съедал первый hover кнопки i=0
    a.je('skip')                       # тот же индекс — не логируем повторно
    a.mov_mem_abs('ecx', VA_LOG_LASTI)
    a.sub_esp(56)
    a.mov_r_imm('eax', 3);              a.mov_mem_r('esp', 0, 'eax')
    a.mov_mem_r('esp', 4, 'esi')
    a.mov_r_mem('eax', 'esi', 0);       a.mov_mem_r('esp', 8, 'eax')
    a.mov_r_imm('eax', 0x57CFEE);       a.mov_mem_r('esp', 12, 'eax')
    a.mov_mem_r('esp', 16, 'edi')
    a.mov_r_mem('eax', 'esp', 0x88);    a.mov_mem_r('esp', 20, 'eax')  # cursor X = frame[0x30]
    a.mov_r_mem('eax', 'esp', 0x8C);    a.mov_mem_r('esp', 24, 'eax')  # cursor Y = frame[0x34]
    a.mov_r_mem('eax', 'esi', 0x1c0)
    a.add_rr('eax', 'ebx')
    a.add_eax_imm32(0x14)               # rect = array + i*0x34 + 0x14
    a.mov_r_mem('ecx', 'eax', 0);       a.mov_mem_r('esp', 28, 'ecx')
    a.mov_r_mem('ecx', 'eax', 4);       a.mov_mem_r('esp', 32, 'ecx')
    a.mov_r_mem('ecx', 'eax', 8);       a.mov_mem_r('esp', 36, 'ecx')
    a.mov_r_mem('ecx', 'eax', 0xc);     a.mov_mem_r('esp', 40, 'ecx')
    a.mov_r_mem('ecx', 'esi', 0x14c);   a.mov_mem_r('esp', 44, 'ecx')
    a.mov_r_imm('eax', env['evt_str'])
    a.lea_r_mem('edx', 'esp', 0)
    a.mov_r_imm('ecx', 56)
    a.call_va(W)
    a.add_esp(56)
    a.L('skip')
    a.popad()
    a.mov_mem_r('esi', 0x28c, 'edi')    # украденные байты сайта
    a.jmp32(RET_H11)
    a.resolve()
    return bytes(a.b)


def build_evt_olc(va, env):
    """H9: пролог OnLayoutChange 0x5912e0 (5 байт: mov eax,[esp+8]; push ebx):
    лог (dShX,dShY,dX,dY) + украденные + jmp 0x5912e5."""
    W = env['evt_write']
    a = Asm(va)
    a.push_r('ecx')
    a.pushad()
    a.sub_esp(48)
    a.mov_mem_imm('esp', 0, 2)                   # kind
    a.mov_r_mem('eax', 'esp', 0x50)              # this
    a.mov_mem_r('esp', 4, 'eax')
    a.mov_r_mem('eax', 'eax', 0)
    a.mov_mem_r('esp', 8, 'eax')
    a.mov_r_mem('eax', 'esp', 0x54)              # ret addr
    a.mov_mem_r('esp', 12, 'eax')
    a.mov_r_mem('eax', 'esp', 0x50)
    a.mov_r_mem('eax', 'eax', 0x14c)
    a.and_eax_u8(0xFF)
    a.mov_mem_r('esp', 16, 'eax')
    for j in range(4):
        a.mov_r_mem('edx', 'esp', 0x58 + 4 * j)  # args E+4..E+0x10
        a.mov_mem_r('esp', 20 + 4 * j, 'edx')
    a.mov_mem_imm('esp', 36, 0)
    a.mov_r_imm('eax', env['evt_str'])
    a.lea_r_mem('edx', 'esp', 0)
    a.mov_r_imm('ecx', 44)
    a.call_va(W)
    a.add_esp(48)
    a.L('skip')
    a.popad()
    a.pop_r('ecx')
    a.mov_r_mem('eax', 'esp', 8)                 # украденные
    a.push_r('ebx')
    a.jmp32(RET_OLC)
    a.resolve()
    return bytes(a.b)


def build_wtramp(va, env):
    """Трамплины слотов: push slot; jmp wstub. 7 байт на слот, порядок WHEEL_SLOTS."""
    a = Asm(va)
    for slot in WHEEL_SLOTS:
        a.raw(b'\x6a' + bytes([slot]))          # push imm8 slot
        a.jmp32(env['wstub'])
    a.resolve()
    return bytes(a.b)


def build_wstub(va, env):
    """Общий стаб H13: thiscall (ecx=this, args x,y в стеке). Пишет kind=4
    (44 Б): this, vt, caller-ret, mark=slot, d0..d2 = args стека, d3/d4 =
    active [+0x1ac/+0x1b0], pad = sector0 L [+0x208]; затем хвостовой переход
    в оригинал слота через wtab[slot] (eax-трамплин, регистры из pushad)."""
    W = env['evt_write']
    a = Asm(va)
    a.pushad()
    a.sub_esp(44)
    a.mov_mem_imm('esp', 0, 4)                            # kind
    # pushad-кадр: [esp1+24] = сохранённый ecx (this); esp2 = esp1 − 44
    a.mov_r_mem('eax', 'esp', 68);  a.mov_mem_r('esp', 4, 'eax')    # this (сохранённый ecx)
    a.mov_r_mem('eax', 'eax', 0);   a.mov_mem_r('esp', 8, 'eax')    # vtable
    a.mov_r_mem('eax', 'esp', 80);  a.mov_mem_r('esp', 12, 'eax')   # caller ret
    a.mov_r_mem('eax', 'esp', 76);  a.mov_mem_r('esp', 16, 'eax')   # slot
    a.mov_r_mem('eax', 'esp', 84);  a.mov_mem_r('esp', 20, 'eax')   # arg0 (x?)
    a.mov_r_mem('eax', 'esp', 88);  a.mov_mem_r('esp', 24, 'eax')   # arg1 (y?)
    a.mov_r_mem('eax', 'esp', 92);  a.mov_mem_r('esp', 28, 'eax')   # arg2
    a.mov_r_mem('eax', 'esp', 68)
    a.mov_r_mem('ecx', 'eax', 0x1ac); a.mov_mem_r('esp', 32, 'ecx')  # active X
    a.mov_r_mem('ecx', 'eax', 0x1b0); a.mov_mem_r('esp', 36, 'ecx')  # active Y
    a.mov_r_mem('ecx', 'eax', 0x208); a.mov_mem_r('esp', 40, 'ecx')  # sector0 L
    a.mov_r_imm('eax', env['evt_str'])
    a.lea_r_mem('edx', 'esp', 0)
    a.mov_r_imm('ecx', 44)
    a.call_va(W)
    a.add_esp(44)
    a.mov_r_mem('eax', 'esp', 32)                          # slot (из pushad-кадра)
    a.raw(b'\x8b\x04\x85' + _p32(env['wtab']))          # mov eax,[wtab+eax*4]
    a.raw(b'\x89\x44\x24\x1c')                          # mov [esp+28],eax (слот сохран. eax в pushad)
    a.popad()
    a.raw(b'\xff\xe0')                                   # jmp eax (оригинал слота)
    a.resolve()
    return bytes(a.b)


def build_wtab(va, env):
    """Таблица оригиналов: wtab[slot*4] = адрес исходной виртуальной функции."""
    blob = bytearray(max(WHEEL_SLOTS) * 4 + 4)
    for slot in WHEEL_SLOTS:
        blob[slot * 4:slot * 4 + 4] = _p32(WHEEL_ORIG[slot])
    return bytes(blob)


# ------------------------------------------------------------------- раскладка
def extra_order():
    return ('wtramp', 'wstub', 'wtab')


def part_order():
    return (('trampA', 'post_scale', 'scale_rect', 'scale_one', 'post_done',
             'maskfix', 'add_stub', 'savefix', 'savefix_tbl', 'draw_stub',
             'rowl_stub', 'sel_stub')
            + (('evt_write', 'evt_setrect', 'evt_olc', 'evt_hover',
                 'evt_str') if DEBUG else ()))


DATA_PARTS = {'savefix_tbl', 'evt_str', 'wtab'}


def layout_parts():
    env0 = {'scale_rect': CAVE_VA, 'scale_one': CAVE_VA, 'savefix': CAVE_VA,
            'savefix_tbl': CAVE_VA, 'post_done': CAVE_VA, 'evt_write': CAVE_VA,
            'evt_str': CAVE_VA}
    builders = {
        'trampA': build_trampA, 'post_scale': build_post, 'post_done': build_post_done,
        'scale_rect': build_scale_rect, 'scale_one': build_scale_one,
        'maskfix': build_mask, 'add_stub': build_addstub,
        'savefix': build_savefix, 'savefix_tbl': build_savefix_tbl,
        'draw_stub': build_drawstub, 'rowl_stub': build_rowlstub,
        'sel_stub': build_selstub,
        'evt_write': build_evt_write, 'evt_setrect': build_evt_setrect,
        'evt_olc': build_evt_olc, 'evt_hover': build_evt_hover,
        'evt_str': build_evt_str,
    } if DEBUG else {
        'trampA': build_trampA, 'post_scale': build_post, 'post_done': build_post_done,
        'scale_rect': build_scale_rect, 'scale_one': build_scale_one,
        'maskfix': build_mask, 'add_stub': build_addstub,
        'savefix': build_savefix, 'savefix_tbl': build_savefix_tbl,
        'draw_stub': build_drawstub, 'rowl_stub': build_rowlstub,
        'sel_stub': build_selstub,
    }
    order = part_order()
    sizes = {n: len(builders[n](CAVE_VA, env0)) for n in order}
    off = 0
    va = {}
    for name in order:
        # 0.0.13: debug-раскладка выравнивается по 4 (x86 не требует 16) —
        # экономия ~80 байт cave под H12; release остаётся при 16, чтобы
        # release-бинар был байт-в-байт прежним (sha256 5ad61f0e…).
        al = 3 if DEBUG else 15
        off = (off + al) & ~al
        va[name] = CAVE_VA + off
        off += sizes[name]
    assert off <= CAVE_CAP, f"cave overflow: {off} > {CAVE_CAP}"
    env = dict(va)
    parts = {n: builders[n](va[n], env) for n in order}
    for name in order:
        assert len(parts[name]) == sizes[name], name
    return parts, va, sizes


def layout_extra(va_main):
    """Раскладка H13-блока в новой секции .ellog (только debug-сборки)."""
    builders = {'wtramp': build_wtramp, 'wstub': build_wstub, 'wtab': build_wtab}
    env0 = {'wstub': EXTRA_VA, 'wtab': EXTRA_VA, 'evt_write': EXTRA_VA,
            'evt_str': EXTRA_VA}
    sizes = {n: len(builders[n](EXTRA_VA, env0)) for n in extra_order()}
    off = 0
    xva = {}
    for name in extra_order():
        off = (off + 3) & ~3
        xva[name] = EXTRA_VA + off
        off += sizes[name]
    assert off <= EXTRA_CAP, f".ellog overflow: {off} > {EXTRA_CAP}"
    env = dict(xva)
    env['evt_write'] = va_main['evt_write']
    env['evt_str'] = va_main['evt_str']
    xparts = {n: builders[n](xva[n], env) for n in extra_order()}
    for name in extra_order():
        assert len(xparts[name]) == sizes[name], name
    return xparts, xva, sizes


def build_cave_blob(parts, va):
    used_end = max(va[n] + len(parts[n]) for n in parts) - CAVE_VA
    blob = bytearray(used_end)
    for name, b in parts.items():
        blob[va[name] - CAVE_VA: va[name] - CAVE_VA + len(b)] = b
    return bytes(blob)


# --------------------------------------------------------------- сборка патча
def va2file(va):
    return va - IMAGE_BASE


def check_sites(d, verbose=True):
    ok = True
    for name, va, want, _sz in ALL_SITES():
        off = va2file(va)
        cur = d[off:off + len(bytes.fromhex(want))].hex()
        good = cur == want
        ok &= good
        if verbose:
            print(f"  {name:4s} file {off:#08x}: have {cur}  want {want}  "
                  f"[{'OK' if good else 'MISMATCH'}]")
    for slot in WHEEL_SLOTS:
        off = VTBL_WHEEL - IMAGE_BASE + 4 * slot
        cur = struct.unpack_from('<I', d, off)[0]
        good = cur == WHEEL_ORIG[slot]
        ok &= good
        if verbose:
            print(f"  vtbl[{slot:#04x}] file {off:#08x}: have {cur:#010x}  "
                  f"want {WHEEL_ORIG[slot]:#010x}  [{'OK' if good else 'MISMATCH'}]")
    cave = d[CAVE_FILE:CAVE_FILE + CAVE_CAP]
    zeros = all(b == 0 for b in cave)
    if verbose:
        print(f"  cave file {CAVE_FILE:#x}..{CAVE_FILE+CAVE_CAP:#x}: "
              f"{'пусто (OK)' if zeros else 'НЕ ПУСТО — будет перезаписан'}")
    return ok


def make_patched(d, parts, va, extra=None):
    img = bytearray(d)
    for (name, va_s, _want, _sz), new in zip(SITE_P1, P1_NEW):
        img[va2file(va_s):va2file(va_s) + 2] = bytes.fromhex(new)
    pairs = ((SITE_H1, 'trampA'), (SITE_H2, 'post_scale'), (SITE_H3, 'maskfix'),
             (SITE_H4, 'add_stub'), (SITE_H5A, 'draw_stub'), (SITE_H5B, 'rowl_stub'),
             (SITE_H6, 'sel_stub'))
    if DEBUG:
        pairs += ((SITE_H8, 'evt_setrect'), (SITE_H9, 'evt_olc'),
                  (SITE_H11, 'evt_hover'))
    for (name, site_va, _want, size), part in pairs:
        rel = va[part] - (site_va + 5)
        rep = b'\xE9' + _p32(rel) + b'\x90' * (size - 5)
        img[va2file(site_va):va2file(site_va) + size] = rep
    blob = build_cave_blob(parts, va)
    img[CAVE_FILE:CAVE_FILE + len(blob)] = blob
    if extra is not None:
        xparts, xva = extra
        e_lf = struct.unpack_from('<I', img, 0x3C)[0]
        nsec = struct.unpack_from('<H', img, e_lf + 6)[0]
        sopt = struct.unpack_from('<H', img, e_lf + 20)[0]
        sect_off = e_lf + 24 + sopt
        size_img = struct.unpack_from('<I', img, e_lf + 24 + 0x38)[0]
        assert nsec == 5 and size_img == EXTRA_RVA, \
            f"PE-магия не совпадает с ожиданием (nsec={nsec}, SizeOfImage={size_img:#x})"
        raw_off = (len(img) + 0x1FF) & ~0x1FF
        img.extend(b'\x00' * (raw_off + EXTRA_CAP - len(img)))
        xblob = bytearray(EXTRA_CAP)
        for n in extra_order():
            o = xva[n] - EXTRA_VA
            xblob[o:o + len(xparts[n])] = xparts[n]
        img[raw_off:raw_off + EXTRA_CAP] = xblob
        hdr = struct.pack('<8sIIIIIIHHI', b'.ellog\x00\x00', EXTRA_CAP, EXTRA_RVA,
                          EXTRA_CAP, raw_off, 0, 0, 0, 0, 0x60000020)
        img[sect_off + 5 * 40:sect_off + 6 * 40] = hdr
        struct.pack_into('<H', img, e_lf + 6, 6)
        struct.pack_into('<I', img, e_lf + 24 + 0x38, size_img + EXTRA_CAP)
        for idx, slot in enumerate(WHEEL_SLOTS):
            struct.pack_into('<I', img, VTBL_WHEEL - IMAGE_BASE + 4 * slot,
                             xva['wtramp'] + idx * 7)
    return bytes(img), blob


def audit_diff(orig, patched, debug=False):
    allowed = set()
    for _n, va_s, _w, sz in ALL_SITES():
        allowed.update(range(va2file(va_s), va2file(va_s) + sz))
    allowed.update(range(CAVE_FILE, CAVE_FILE + CAVE_CAP))
    if debug:
        e_lf = struct.unpack_from('<I', orig, 0x3C)[0]
        sopt = struct.unpack_from('<H', orig, e_lf + 20)[0]
        sect_off = e_lf + 24 + sopt
        allowed.update(range(e_lf + 6, e_lf + 8))                 # NumberOfSections
        allowed.update(range(e_lf + 24 + 0x38, e_lf + 24 + 0x3C))  # SizeOfImage
        allowed.update(range(sect_off + 5 * 40, sect_off + 6 * 40))  # новый заголовок
        for slot in WHEEL_SLOTS:                                   # vtable-слоты
            allowed.update(range(VTBL_WHEEL - IMAGE_BASE + 4 * slot,
                                 VTBL_WHEEL - IMAGE_BASE + 4 * slot + 4))
    changed = {i for i in range(len(orig)) if orig[i] != patched[i]}
    extra = changed - allowed
    assert not extra, f"неожиданные изменения: {sorted(extra)[:16]}"
    for _n, va_s, _w, sz in ALL_SITES():
        site = set(range(va2file(va_s), va2file(va_s) + sz))
        assert site & changed, f"сайт {va_s:#x} не изменён"
    return len(changed)


# -------------------------------------------------------- capstone-верификация
def verify_disasm(parts, va, listing=False, extra=None):
    from capstone import Cs, CS_ARCH_X86, CS_MODE_32
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    allowed = {RET_TRAMP, RET_POST, RET_MASK, RET_ADD, RET_DRAW, RET_ROWL,
               RET_SEL1, RET_SEL2, RET_SETRECT, RET_OLC, RET_H11,
               VA_ITER, VA_DRAWBASE} | set(va.values())
    xparts, xva = (extra or ({}, {}))
    allowed |= set(xva.values())
    n_ins = 0
    for name in list(part_order()) + ([n for n in extra_order()] if extra else []):
        blob = (parts if name in parts else xparts)[name]
        base = (va if name in va else xva)[name]
        allowed.update(range(base, base + len(blob)))
        if name in DATA_PARTS:
            if listing:
                print(f"\n; ---- {name} @ VA {base:#x} ({len(blob)} байт, данные) ----")
            continue
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
    ORDER = ['eax', 'ecx', 'edx', 'ebx', 'esp', 'ebp', 'esi', 'edi']

    def __init__(self, mem):
        self.m = mem
        self.r = {n: 0 for n in self.ORDER}
        self.eip = 0
        self.zf = 0
        self.cf = 0
        from capstone import Cs, CS_ARCH_X86, CS_MODE_32
        self.md = Cs(CS_ARCH_X86, CS_MODE_32)
        self.md.detail = True
        self.steps = 0
        from capstone import x86 as cx86
        self.cx = cx86

    def _ea(self, op):
        m = op.mem
        base = 0 if m.base == 0 else self.r[self.md.reg_name(m.base)]
        idx = 0 if m.index == 0 else self.r[self.md.reg_name(m.index)] * m.scale
        return (base + idx + m.disp) & 0xFFFFFFFF

    def _get(self, op):
        t = op.type
        if t == self.cx.X86_OP_IMM:
            return op.imm & 0xFFFFFFFF
        if t == self.cx.X86_OP_REG:
            return self.r[self.md.reg_name(op.reg)]
        if t == self.cx.X86_OP_MEM:
            assert op.size in (0, 4)
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

    def run(self, start, stop, budget=400000):
        self.eip = start
        while self.eip != stop:
            assert self.steps < budget, f"бюджет исчерпан (eip={self.eip:#x})"
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
        elif m == 'pop':
            self._set(ops[0], self._pop()); self.eip = nxt
        elif m == 'add' or m == 'sub':
            a, b = self._get(ops[0]), self._get(ops[1])
            self._set(ops[0], a + b if m == 'add' else a - b); self.eip = nxt
        elif m == 'and':
            self._set(ops[0], self._get(ops[0]) & self._get(ops[1])); self.eip = nxt
        elif m == 'or':
            self._set(ops[0], self._get(ops[0]) | self._get(ops[1])); self.eip = nxt
        elif m == 'test':
            self.zf = 1 if (self._get(ops[0]) & self._get(ops[1])) == 0 else 0; self.eip = nxt
        elif m == 'cmp':
            a, b = self._get(ops[0]) & 0xFFFFFFFF, self._get(ops[1]) & 0xFFFFFFFF
            self.zf = 1 if a == b else 0
            self.cf = 1 if a < b else 0           # unsigned (для jbe/jae теста T8)
            self.eip = nxt
        elif m == 'inc':
            self._set(ops[0], self._get(ops[0]) + 1); self.eip = nxt
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
            assert div != 0
            num = (_s32(self.r['edx']) << 32) | self.r['eax']
            q = abs(num) // abs(div)
            if (num < 0) != (div < 0):
                q = -q
            assert -0x80000000 <= q <= 0x7FFFFFFF
            rem = abs(num) % abs(div)
            if (num < 0):
                rem = -rem
            self.r['eax'] = q & 0xFFFFFFFF
            self.r['edx'] = rem & 0xFFFFFFFF
            self.eip = nxt
        elif m == 'call':
            self._push(nxt); self.eip = self._get(ops[0])
        elif m == 'ret':
            self.eip = self._pop()
            if len(ops):                          # ret N
                self.r['esp'] = (self.r['esp'] + self._get(ops[0])) & 0xFFFFFFFF
        elif m == 'jmp':
            self.eip = self._get(ops[0])
        elif m in ('jz', 'je'):
            self.eip = self._get(ops[0]) if self.zf else nxt
        elif m in ('jnz', 'jne'):
            self.eip = self._get(ops[0]) if not self.zf else nxt
        elif m in ('jbe', 'jna'):
            self.eip = self._get(ops[0]) if (self.cf or self.zf) else nxt
        elif m in ('jae', 'jnb', 'jnc'):
            self.eip = self._get(ops[0]) if not self.cf else nxt
        elif m in ('jb', 'jnae', 'jc'):
            self.eip = self._get(ops[0]) if self.cf else nxt
        elif m in ('ja', 'jnbe'):
            self.eip = self._get(ops[0]) if not (self.cf or self.zf) else nxt
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
def emu_tests(patched_img, va, extra=None):
    """T1..T7 на интерпретаторе. Итератор 0x6c51a0 в тестовом образе — заглушка
    `slot=[slot+8]` (протокол вызова тот же, что в apply_flag)."""
    HEAP, STACK = 0x2000000, 0x1000000
    ITER_STUB = bytes.fromhex("8b542404" "8b02" "8b4008" "8902" "c3")

    def new_cpu():
        mem = Mem()
        img = bytearray(patched_img[:0x417000])
        img[va2file(VA_ITER):va2file(VA_ITER) + len(ITER_STUB)] = ITER_STUB
        mem.map(IMAGE_BASE, bytes(img))
        if len(patched_img) > 0x41D000:      # секция .ellog (debug-сборки)
            mem.map(EXTRA_VA, bytes(patched_img[0x41D000:0x41D000 + EXTRA_CAP]))
        mem.map(0x400000 + 0x417000, bytes(0x43C000 - 0x417000))
        mem.map(HEAP, bytes(0x40000))
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

    def setup_gate(mem, marked=True, flag=1, empty=False):
        """screen flag + список менеджера: sentinel head -> node(n1) -> elem e0
        (маркер у e0); empty=True — пустой список (node == head)."""
        mem.w32(VA_SCREEN, VA_SCREEN)            # указатель на сам себя (тест)
        mem.w32(VA_SCREEN + 0x188, flag)
        mgr, head, n1, e0 = HEAP + 0x3000, HEAP + 0x3040, HEAP + 0x3080, HEAP + 0x3100
        mem.w32(VA_MGR, mgr)
        mem.w32(mgr, head)
        mem.w32(head + 8, head if empty else n1)
        mem.w32(head + 0x1c, 0)                  # у sentinel'а elem = 0
        mem.w32(n1 + 8, head)
        mem.w32(n1 + 0x1c, e0)
        mem.w32(e0 + 0x14c, 0x200000 | (0x6 if marked else 0x2))

    # --- T1: trampA
    print("test T1: trampA (live W/H + fallback)")
    cpu = new_cpu(); setup_mode(cpu.m)
    esp0 = STACK + 0x10000
    cpu.run(va['trampA'], RET_TRAMP)
    chk("edx=W", cpu.r['edx'], 1600)
    chk("[esp+0x24]=H", cpu.m.r32(esp0 + 0x24), 900)
    cpu = new_cpu(); setup_mode(cpu.m, present=False)
    cpu.run(va['trampA'], RET_TRAMP)
    chk("fallback edx=1024", cpu.r['edx'], 1024)

    # --- T2: maskfix
    print("test T2: maskfix (dx/dy -> design)")
    for nib, want_dx, want_dy in ((2, 192, 85), (1, 150, 66)):
        cpu = new_cpu(); setup_mode(cpu.m)
        elem = HEAP + 0x1000
        cpu.m.w32(elem + 0x14c, 0x00200000 | nib)
        cpu.m.w32(elem + 0x184, 20)
        cpu.r.update(ebx=100, edi=500, eax=200, esi=elem, ebp=0xDEAD)
        cpu.run(va['maskfix'], RET_MASK)
        chk(f"nib={nib} dx_design", cpu.r['ecx'], want_dx)
        chk(f"nib={nib} dy_design*stride", cpu.r['ebx'], want_dy * 20)
        chk(f"nib={nib} ebp preserved", cpu.r['ebp'], 0xDEAD)

    # --- T3: post_scale (force, маркеры ставятся)
    print("test T3: post_scale (обход, RECT'ы, актив, визуал, маркеры)")
    cpu = new_cpu(); m = cpu.m
    setup_mode(m)
    H = HEAP
    sc = H + 0x2000
    m.w32(sc + 0xe8, 0); m.w32(sc + 0xec, 0)
    m.w32(sc + 0xf0, 1600); m.w32(sc + 0xf4, 900)
    mgr, head, n1, n2 = H + 0x3000, H + 0x3040, H + 0x3080, H + 0x30C0
    e1, e2 = H + 0x4000, H + 0x5000
    m.w32(VA_MGR, mgr); m.w32(mgr, head)
    m.w32(head + 8, n1)
    m.w32(n1 + 8, n2); m.w32(n1 + 0x1c, e1)
    m.w32(n2 + 8, head); m.w32(n2 + 0x1c, e2)
    v, oh, on1, sh, s, sn1, obj = (H + 0x6000 + i * 0x40 for i in range(7))
    for off, vals in ((0x154, (100, 50, 300, 150)), (0x164, (100, 50, 300, 150)),
                      (0x174, (0, 0, 64, 64)), (0x18c, (0, 0, 7, 8)),
                      (0x19c, (10, 20, 30, 40)), (0x1ac, (10, 20, 30, 40))):
        for i, val in enumerate(vals):
            m.w32(e1 + off + 4 * i, val)
    m.w32(VA_SCREEN, VA_SCREEN)
    m.w32(VA_SCREEN + 0x188, 1)
    m.w32(e1 + 0x14c, 2)                          # unmarked, profile 1024
    m.w32(e1 + 0x148, v)
    m.w32(v, oh); m.w32(oh + 8, on1); m.w32(on1 + 8, oh)
    m.w32(on1 + 0x14, sh); m.w32(sh, s)
    m.w32(s + 8, sn1); m.w32(sn1 + 8, s); m.w32(sn1 + 0x10, obj)
    for i, val in enumerate((10, 10, 110, 60)):
        m.w32(obj + 0x18 + 4 * i, val)
        m.w32(obj + 0x40 + 4 * i, val)
    for i in range(4):
        m.w32(obj + 0x30 + 4 * i, 999)
    for off, vals in ((0x154, (0, 0, 10, 10)), (0x164, (0, 0, 0, 0)),
                      (0x174, (0, 0, 0, 0)), (0x1ac, (0, 0, 0, 0))):
        for i, val in enumerate(vals):
            m.w32(e2 + off + 4 * i, val)
    m.w32(e2 + 0x14c, 2)
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
    chk("e1 rect154", rd(e1 + 0x154), [156, 58, 468, 175])
    chk("e1 rect174", rd(e1 + 0x174), [0, 0, 100, 75])
    chk("e1 active X,Y", rd(e1 + 0x1ac, 2), [15, 23])
    chk("e1 record1 intact", rd(e1 + 0x19c), [10, 20, 30, 40])
    chk("obj+0x40 scaled", rd(obj + 0x40), [15, 11, 171, 70])
    chk("obj+0x30 untouched", rd(obj + 0x30), [999, 999, 999, 999])
    chk("e1 marker set", rd(e1 + 0x14c, 1)[0] & 0xC, MARK_SCALED)
    chk("e2 marker set", rd(e2 + 0x14c, 1)[0] & 0xC, MARK_SCALED)
    print(f"  (T3 выполнен за {steps} шагов)")

    # --- T3b: v6 — глобалы adv-панели 0x827e70/80 масштабируются пост-проходом
    print("test T3b: post_scale масштабирует 0x827e70/0x827e80 (колесо)")
    for i, v in enumerate((628, 172, 733, 442)):
        m.w32(0x827E70 + 4 * i, v)
    for i, v in enumerate((852, 181, 957, 613)):
        m.w32(0x827E80 + 4 * i, v)
    m.w32(sc + 0xf0, 1600); m.w32(sc + 0xf4, 900)
    # контролы уже помечены после T3 -> пост-проход их не трогает, глобалы да
    cpu.r.update(eax=0, ebx=1, ecx=0, edx=0, esi=sc, edi=0, ebp=0, esp=STACK + 0x10000)
    cpu.run(va['post_scale'], RET_POST)
    chk("e1 rect154 not re-scaled", rd(e1 + 0x154), [156, 58, 468, 175])
    chk("0x827e70 scaled", rd(0x827E70), [981, 201, 1145, 517])
    chk("0x827e80 scaled", rd(0x827E80), [1331, 212, 1495, 718])

    # --- T4: identity (k==1) — rect'ы не трогаются, маркер ставится
    print("test T4: post_scale identity-skip @1024x768")
    m.w32(e1 + 0x14c, 2); m.w32(e2 + 0x14c, 2)    # снять маркеры
    setup_mode(m, w=1024, h=768)
    cpu.r.update(eax=0, ebx=1, ecx=0, edx=0, esi=sc, edi=0, ebp=0, esp=STACK + 0x10000)
    cpu.run(va['post_scale'], RET_POST)
    chk("e1 rect154 untouched", rd(e1 + 0x154), [156, 58, 468, 175])
    chk("obj+0x40 untouched", rd(obj + 0x40), [15, 11, 171, 70])
    chk("e1 marker set (k==1)", rd(e1 + 0x14c, 1)[0] & 0xC, MARK_SCALED)
    # повторный проход при native W/H: маркер -> идемпотентность
    setup_mode(m, w=1600, h=900)
    cpu.r.update(eax=0, ebx=1, ecx=0, edx=0, esi=sc, edi=0, ebp=0, esp=STACK + 0x10000)
    cpu.run(va['post_scale'], RET_POST)
    chk("e1 rect154 no double-scale", rd(e1 + 0x154), [156, 58, 468, 175])

    # --- T5: H4 add_stub — новый контрол масштабируется при регистрации
    print("test T5: add_stub (scale-on-create + гейт головы)")
    cpu = new_cpu(); m = cpu.m
    setup_mode(m); setup_gate(m, marked=True)
    ne = HEAP + 0x8000
    for off, vals in ((0x154, (200, 100, 400, 200)), (0x164, (200, 100, 400, 200)),
                      (0x174, (0, 0, 32, 32)), (0x1ac, (200, 100, 0, 0))):
        for i, val in enumerate(vals):
            m.w32(ne + off + 4 * i, val)
    m.w32(ne + 0x14c, 0xF05FFFFF)                 # nibble=0xF как после ctor
    m.w32(ne + 0x148, 0)
    esp0 = STACK + 0x10000
    m.w32(esp0 + 4, ne)                           # аргумент AddControl
    cpu.r.update(ecx=HEAP + 0x3000, esi=0x1111, esp=esp0)
    cpu.run(va['add_stub'], RET_ADD)
    chk("new rect154 scaled", rd(ne + 0x154), [312, 117, 625, 234])
    chk("new rect174 scaled", rd(ne + 0x174), [0, 0, 50, 37])
    chk("new active scaled", rd(ne + 0x1ac, 2), [312, 117])
    chk("marker set", rd(ne + 0x14c, 1)[0] & 0xC, MARK_SCALED)
    chk("esi = elem (stolen)", cpu.r['esi'], ne)
    chk("esp = entry-4 (stolen push)", cpu.r['esp'], esp0 - 4)
    # гейт: голова не помечена (пост-проход ещё не было) -> не трогать
    cpu = new_cpu(); m = cpu.m
    setup_mode(m); setup_gate(m, marked=False)
    ne = HEAP + 0x8000
    for i, val in enumerate((200, 100, 400, 200)):
        m.w32(ne + 0x154 + 4 * i, val)
    m.w32(ne + 0x14c, 0xF05FFFFF)
    m.w32(ne + 0x148, 0)
    m.w32(esp0 + 4, ne)
    cpu.r.update(ecx=HEAP + 0x3000, esi=0x1111, esp=esp0)
    cpu.run(va['add_stub'], RET_ADD)
    chk("gate closed: rect untouched", rd(ne + 0x154), [200, 100, 400, 200])
    chk("gate closed: no marker", rd(ne + 0x14c, 1)[0] & 0xC, 0xC)  # nibble 0xF as-is

    # --- T6: H5b rowl_stub — пересчёт констант блока 0x8295xx
    print("test T6: savefix (design-константы -> native)")
    cpu = new_cpu(); m = cpu.m
    setup_mode(m); setup_gate(m, marked=True)
    esp0 = STACK + 0x10000
    cpu.r.update(ecx=HEAP + 0x9000, esp=esp0, ebx=0xBBBB, ebp=0xEEEE)
    cpu.run(va['rowl_stub'], RET_ROWL)
    chk("0x829550 = 693*1600/1024", m.r32(0x829550), 693 * 1600 // 1024)
    chk("0x829554 = 448*900/768", m.r32(0x829554), 448 * 900 // 768)
    chk("0x8295a8 untouched (px size)", m.r32(0x8295a8), 0)   # в образе .data=0
    chk("esp = entry-8 (stolen pushes)", cpu.r['esp'], esp0 - 8)
    chk("ebx preserved", cpu.r['ebx'], 0xBBBB)

    # --- T5c: AddControl при ПУСТОМ списке менеджера (старт игры) — без краха
    print("test T5c: add_stub @ пустой список (null/empty-safe гейт)")
    cpu = new_cpu(); m = cpu.m
    setup_mode(m); setup_gate(m, marked=True, empty=True)
    ne = HEAP + 0x8800
    for i, val in enumerate((200, 100, 400, 200)):
        m.w32(ne + 0x154 + 4 * i, val)
    m.w32(ne + 0x14c, 0xF05FFFFF)
    m.w32(ne + 0x148, 0)
    esp0 = STACK + 0x10000
    m.w32(esp0 + 4, ne)
    cpu.r.update(ecx=HEAP + 0x3000, esi=0x3333, esp=esp0)
    cpu.run(va['add_stub'], RET_ADD)             # не должно упасть на [0+0x14c]
    chk("empty list: rect untouched", rd(ne + 0x154), [200, 100, 400, 200])
    chk("empty list: esp = entry-4", cpu.r['esp'], esp0 - 4)
    # mgr вовсе ещё не создан ([0x82b968]==0)
    cpu = new_cpu(); m = cpu.m
    setup_mode(m)
    m.w32(VA_MGR, 0)
    for i, val in enumerate((200, 100, 400, 200)):
        m.w32(ne + 0x154 + 4 * i, val)
    m.w32(ne + 0x14c, 0xF05FFFFF)
    m.w32(esp0 + 4, ne)
    cpu.r.update(ecx=0, esi=0x3333, esp=esp0)
    cpu.run(va['add_stub'], RET_ADD)
    chk("mgr=null: rect untouched", rd(ne + 0x154), [200, 100, 400, 200])

    # --- T6b: scale_one масштабирует спрайт-rect'ы CButtonList (колесо команд)
    print("test T6b: scale_one + CButtonList sprite rects")
    cpu = new_cpu(); m = cpu.m
    setup_mode(m); setup_gate(m, marked=True)
    bl = HEAP + 0xA000
    arr = HEAP + 0xA400
    m.w32(bl + 0x0, 0x75D498)                    # vtable CButtonList
    m.w32(bl + 0x14c, 0xF05FFFFF)
    m.w32(bl + 0x1c0, arr)
    m.w32(bl + 0x1c4, 2)
    for i, rect in enumerate(((640, 600, 720, 660), (720, 600, 800, 660))):
        for j, v in enumerate(rect):
            m.w32(arr + i * 0x34 + 0x14 + 4 * j, v)
        m.w32(arr + i * 0x34 + 0x28, 0x7777)     # texture ptr: не трогать
    m.w32(bl + 0x154, 0)                         # rect'ы контрола тоже
    m.w32(bl + 0x148, 0)
    esp0 = STACK + 0x10000
    m.w32(esp0 + 4, bl)
    cpu.r.update(ecx=HEAP + 0x3000, esi=0x2222, esp=esp0)
    cpu.run(va['add_stub'], RET_ADD)
    chk("sprite0 rect scaled", rd(arr + 0x14), [1000, 703, 1125, 773])
    chk("sprite1 rect scaled", rd(arr + 0x34 + 0x14), [1125, 703, 1250, 773])
    chk("sprite0 texture intact", rd(arr + 0x28, 1), [0x7777])
    chk("bl marker set", rd(bl + 0x14c, 1)[0] & 0xC, MARK_SCALED)

    # --- T7: H6 sel_stub — рамка CSelectMission
    print("test T7: sel_stub (рамка диалога: gate on/off)")
    cpu = new_cpu(); m = cpu.m
    setup_mode(m); setup_gate(m, marked=True)
    esp0 = STACK + 0x10000
    cpu.r.update(eax=0xA1, ecx=0xC2, edx=0xD3, ebx=0xB4, esp=esp0)
    cpu.run(va['sel_stub'], RET_SEL2)
    chk("rect L", m.r32(esp0 + 0x14), 158 * 1600 // 1024)
    chk("rect T", m.r32(esp0 + 0x18), 111 * 900 // 768)
    chk("rect R", m.r32(esp0 + 0x1c), 866 * 1600 // 1024)
    chk("rect B", m.r32(esp0 + 0x20), 661 * 900 // 768)
    chk("regs preserved", (cpu.r['eax'], cpu.r['ecx'], cpu.r['edx'], cpu.r['ebx']),
        (0xA1, 0xC2, 0xD3, 0xB4))
    chk("esp balance", cpu.r['esp'], esp0)
    cpu = new_cpu(); m = cpu.m
    setup_mode(m, w=1024, h=768); setup_gate(m, marked=True)
    cpu.r.update(eax=0xA1, ecx=0xC2, edx=0xD3, ebx=0xB4, esp=esp0)
    cpu.run(va['sel_stub'], RET_SEL1)
    chk("gate off: design L", m.r32(esp0 + 0x14), 0x9E)
    chk("gate off: esp balance", cpu.r['esp'], esp0)

    # --- T8: evt_write логгера (0.0.8) — CreateFileA/WriteFile/CloseHandle
    # эмулируются stdcall-заглушками; проверяются: усечение лога на первом
    # событии сессии (CREATE_ALWAYS), append после (OPEN_ALWAYS), лимит
    # DBG_CAP (ранний выход без CreateFileA), баланс esp, esi/edi целы.
    if 'evt_write' not in va:
        print("test T8: пропущен (release-сборка без логгера)")
    else:
        print("test T8: evt_write (truncate-per-session + cap DBG_CAP)")
        STUBS = HEAP + 0x30000
        SLOT_DISP, SLOT_LEN = HEAP + 0x31000, HEAP + 0x31004
        NAME, BUF = HEAP + 0x31100, HEAP + 0x31200
        STOP = STACK                                  # сентинел ret-адреса
        stub_cfa = (b"\x8b\x44\x24\x14" + b"\xa3" + _p32(SLOT_DISP)
                    + b"\xb8\x34\x12\x00\x00" + b"\xc2\x1c\x00")   # [esp+0x14]=disp->slot; eax=0x1234; ret 28
        stub_wf = (b"\x8b\x44\x24\x0c" + b"\xa3" + _p32(SLOT_LEN)
                   + b"\xb8\x01\x00\x00\x00" + b"\xc2\x14\x00")    # nBytes->slot; eax=1; ret 20
        stub_ch = b"\xb8\x01\x00\x00\x00" + b"\xc2\x04\x00"        # eax=1; ret 4

        def run_evt(cpu, m, esp0):
            m.w32(IAT_CREATEFILEA, STUBS)
            m.w32(IAT_WRITEFILE, STUBS + 32)
            m.w32(IAT_CLOSEHANDLE, STUBS + 64)
            cpu.r.update(eax=NAME, edx=BUF, ecx=44,
                         esi=0xE5E5, edi=0xD7D7, esp=esp0)
            m.w32(esp0, STOP)
            cpu.run(va['evt_write'], STOP)

        cpu = new_cpu(); m = cpu.m
        m.wb(STUBS, stub_cfa.ljust(32, b'\x90'))
        m.wb(STUBS + 32, stub_wf.ljust(32, b'\x90'))
        m.wb(STUBS + 64, stub_ch.ljust(16, b'\x90'))
        m.wb(NAME, b"el_evt.log\x00")
        m.wb(BUF, b'\xAB' * 44)
        m.w32(VA_LOG_FLAG, 0); m.w32(VA_LOG_COUNT, 0)
        esp0 = STACK + 0x10000
        run_evt(cpu, m, esp0)
        chk("T8.1 esp balance (ret)", cpu.r['esp'], esp0 + 4)
        chk("T8.1 flag:=1 (сессия начата)", m.r32(VA_LOG_FLAG), 1)
        chk("T8.1 count=1", m.r32(VA_LOG_COUNT), 1)
        chk("T8.1 disposition=CREATE_ALWAYS(2)", m.r32(SLOT_DISP), 2)
        chk("T8.1 WriteFile len=44", m.r32(SLOT_LEN), 44)
        chk("T8.1 esi/edi preserved", (cpu.r['esi'], cpu.r['edi']), (0xE5E5, 0xD7D7))
        m.w32(SLOT_DISP, 0xDEAD)
        run_evt(cpu, m, esp0)
        chk("T8.2 disposition=OPEN_ALWAYS(4)", m.r32(SLOT_DISP), 4)
        chk("T8.2 count=2", m.r32(VA_LOG_COUNT), 2)
        m.w32(VA_LOG_COUNT, DBG_CAP)
        m.w32(SLOT_DISP, 0xBEEF)
        run_evt(cpu, m, esp0)
        chk("T8.3 cap: CreateFileA не вызван", m.r32(SLOT_DISP), 0xBEEF)
        chk("T8.3 cap: count=DBG_CAP+1", m.r32(VA_LOG_COUNT), DBG_CAP + 1)
        chk("T8.3 cap: esp balance", cpu.r['esp'], esp0 + 4)

    # --- T9: evt_hover (H11) — рекорд kind=3: cursor+rect+i+флаги, dedup по i
    if 'evt_hover' not in va:
        print("test T9: пропущен (release-сборка без логгера)")
    else:
        print("test T9: evt_hover (hover-сайт CButtonList: cursor+rect, dedup)")
        STUBS = HEAP + 0x30000
        SLOT_DISP, SLOT_LEN = HEAP + 0x31000, HEAP + 0x31004
        stub_cfa = (b"\x8b\x44\x24\x14" + b"\xa3" + _p32(SLOT_DISP)
                    + b"\xb8\x34\x12\x00\x00" + b"\xc2\x1c\x00")
        stub_wf = (b"\x8b\x44\x24\x0c" + b"\xa3" + _p32(SLOT_LEN)
                   + b"\xb8\x01\x00\x00\x00" + b"\xc2\x14\x00")
        stub_ch = b"\xb8\x01\x00\x00\x00" + b"\xc2\x04\x00"
        cpu = new_cpu(); m = cpu.m
        m.wb(STUBS, stub_cfa.ljust(32, b'\x90'))
        m.wb(STUBS + 32, stub_wf.ljust(32, b'\x90'))
        m.wb(STUBS + 64, stub_ch.ljust(16, b'\x90'))
        m.w32(IAT_CREATEFILEA, STUBS)
        m.w32(IAT_WRITEFILE, STUBS + 32)
        m.w32(IAT_CLOSEHANDLE, STUBS + 64)
        ctrl, arr = HEAP + 0x5000, HEAP + 0x6000
        m.w32(ctrl + 0x0, 0x75D498)                 # vtable CButtonList
        m.w32(ctrl + 0x1c0, arr)
        for j, v in enumerate((100, 50, 200, 130)):
            m.w32(arr + 0x14 + 4 * j, v)            # rect кнопки i=0
        for j, v in enumerate((1200, 700, 1300, 780)):
            m.w32(arr + 0x34 + 0x14 + 4 * j, v)     # rect кнопки i=1
        m.w32(ctrl + 0x14c, 0xF05FFFF6)
        m.w32(ctrl + 0x28c, 0xFFFFFFFF)
        m.w32(VA_LOG_LASTI, 0)
        m.w32(VA_LOG_FLAG, 1); m.w32(VA_LOG_COUNT, 0)
        esp0 = STACK + 0x10000
        m.w32(esp0 + 0x30, 1550)                    # cursor X (frame[0x30])
        m.w32(esp0 + 0x34, 810)                     # cursor Y
        # первый hover кнопки i=0 (0.0.12: dedup не должен его съесть)
        cpu.r.update(esi=ctrl, edi=0, ebx=0x00, eax=0x99, ecx=0x77, edx=0x55, esp=esp0)
        cpu.run(va['evt_hover'], RET_H11)
        b = esp0 - 88                               # рекорд на стеке
        chk("T9 i=0: kind=3", m.r32(b + 0), 3)
        chk("T9 i=0: this", m.r32(b + 4), ctrl)
        chk("T9 i=0: vtable", m.r32(b + 8), 0x75D498)
        chk("T9 i=0: ret-маркер сайта", m.r32(b + 12), 0x57CFEE)
        chk("T9 i=0: i", m.r32(b + 16), 0)
        chk("T9 i=0: cursor=(1550,810)", (m.r32(b + 20), m.r32(b + 24)), (1550, 810))
        chk("T9 i=0: rect array[0]+0x14", [m.r32(b + 28 + 4 * j) for j in range(4)],
            [100, 50, 200, 130])
        chk("T9 i=0: флаги [+0x14c]", m.r32(b + 44), 0xF05FFFF6)
        chk("T9 i=0: stolen [esi+0x28c]=i", m.r32(ctrl + 0x28c), 0)
        chk("T9 i=0: WriteFile len=56", m.r32(SLOT_LEN), 56)
        chk("T9 i=0: regs preserved", (cpu.r['esi'], cpu.r['edi'], cpu.r['ebx']),
            (ctrl, 0, 0x00))
        chk("T9 i=0: esp balance", cpu.r['esp'], esp0)
        # dedup: тот же i повторно — записи нет
        m.w32(SLOT_LEN, 0)
        cpu.r.update(esi=ctrl, edi=0, ebx=0x00, eax=0x99, ecx=0x77, edx=0x55, esp=esp0)
        cpu.run(va['evt_hover'], RET_H11)
        chk("T9 dedup: повторный i=0 не пишется", m.r32(SLOT_LEN), 0)
        chk("T9 dedup: esp balance", cpu.r['esp'], esp0)
        # другой индекс — пишется снова
        cpu.r.update(esi=ctrl, edi=1, ebx=0x34, eax=0x99, ecx=0x77, edx=0x55, esp=esp0)
        cpu.run(va['evt_hover'], RET_H11)
        chk("T9 смена i: пишется", m.r32(SLOT_LEN), 56)
        chk("T9 смена i: i=1", m.r32(b + 16), 1)
        chk("T9 смена i: rect array[1]+0x14", [m.r32(b + 28 + 4 * j) for j in range(4)],
            [1200, 700, 1300, 780])

    # --- T10: H13 vtable-стаб (kind=4: slot/this/args/active/sector0 + хвост в оригинал)
    if not extra:
        print("test T10: пропущен (release-сборка без .ellog)")
    else:
        print("test T10: evt_wheel-stub H13 (vtable-интерпозиция, kind=4)")
        xva = extra[1]
        STUBS = HEAP + 0x30000
        SLOT_DISP, SLOT_LEN = HEAP + 0x31000, HEAP + 0x31004
        stub_cfa = (b"\x8b\x44\x24\x14" + b"\xa3" + _p32(SLOT_DISP)
                    + b"\xb8\x34\x12\x00\x00" + b"\xc2\x1c\x00")
        stub_wf = (b"\x8b\x44\x24\x0c" + b"\xa3" + _p32(SLOT_LEN)
                   + b"\xb8\x01\x00\x00\x00" + b"\xc2\x14\x00")
        stub_ch = b"\xb8\x01\x00\x00\x00" + b"\xc2\x04\x00"
        cpu = new_cpu(); m = cpu.m
        m.wb(STUBS, stub_cfa.ljust(32, b'\x90'))
        m.wb(STUBS + 32, stub_wf.ljust(32, b'\x90'))
        m.wb(STUBS + 64, stub_ch.ljust(16, b'\x90'))
        m.w32(IAT_CREATEFILEA, STUBS)
        m.w32(IAT_WRITEFILE, STUBS + 32)
        m.w32(IAT_CLOSEHANDLE, STUBS + 64)
        STOP = STACK
        scr = HEAP + 0x7000
        m.w32(scr + 0x0, VTBL_WHEEL)
        m.w32(scr + 0x1ac, 300); m.w32(scr + 0x1b0, 190)
        m.w32(scr + 0x208, 100)
        slot = 7
        m.w32(xva['wtab'] + slot * 4, STOP)      # «оригинал» слота = сентинел
        m.w32(VA_LOG_FLAG, 1); m.w32(VA_LOG_COUNT, 0)
        esp0 = STACK + 0x10000
        m.w32(esp0, 0xC0FFEE)                    # caller ret
        m.w32(esp0 + 4, 1550)                    # arg0 (x?)
        m.w32(esp0 + 8, 823)                     # arg1 (y?)
        m.w32(esp0 + 12, 9)                      # arg2
        idx = WHEEL_SLOTS.index(slot)
        cpu.r.update(ecx=scr, eax=0x99, edx=0x55, ebx=0x11, esp=esp0)
        cpu.run(xva['wtramp'] + idx * 7, STOP)
        b = esp0 - 80
        chk("T10 kind=4", m.r32(b + 0), 4)
        chk("T10 this", m.r32(b + 4), scr)
        chk("T10 vtable", m.r32(b + 8), VTBL_WHEEL)
        chk("T10 caller ret", m.r32(b + 12), 0xC0FFEE)
        chk("T10 mark=slot", m.r32(b + 16), 7)
        chk("T10 args (1550,823,9)", (m.r32(b + 20), m.r32(b + 24), m.r32(b + 28)),
            (1550, 823, 9))
        chk("T10 active=(300,190)", (m.r32(b + 32), m.r32(b + 36)), (300, 190))
        chk("T10 sector0L", m.r32(b + 40), 100)
        chk("T10 WriteFile len=44", m.r32(SLOT_LEN), 44)
        chk("T10 eax=оригинал слота", cpu.r['eax'], STOP)
        chk("T10 esp=entry-4 (slot оставлен)", cpu.r['esp'], esp0 - 4)
        chk("T10 ecx(this) сохранён", cpu.r['ecx'], scr)

    return ok


# ----------------------------------------------------------------------- main
def _pause_win():
    """Двойной клик на Windows: не закрывать окно сразу (виден результат/ошибка)."""
    if sys.platform == "win32":
        try:
            input("\nНажмите Enter, чтобы закрыть окно...")
        except (EOFError, OSError):
            pass


def _resolve_src(arg):
    """(src, from_default). Без аргумента ищем Etherlords.exe в CWD, затем рядом
    со скриптом — сценарий 0.0.9: скрипт кладётся в папку игры и запускается
    (двойным кликом или `python patch_native_v3.py`)."""
    if arg:
        return arg, False
    here = os.path.dirname(os.path.abspath(__file__))
    for c in ("Etherlords.exe", os.path.join(here, "Etherlords.exe")):
        if os.path.isfile(c):
            return c, True
    return "Etherlords.exe", True


def main():
    ap = argparse.ArgumentParser(description="native v3..v6 patcher (docs/09)")
    ap.add_argument("src", nargs="?", default=None,
                    help="путь к Etherlords.exe (по умолчанию: ищется в CWD или рядом со скриптом)")
    ap.add_argument("--out", default=None)
    ap.add_argument("--check", action="store_true", help="только проверка применимости")
    ap.add_argument("--listing", action="store_true", help="печатать дизассемблер cave")
    ap.add_argument("--no-emu", action="store_true", help="пропустить функциональные тесты")
    ap.add_argument("--debug", action="store_true",
                    help="(устарел, no-op) логгер H8/H9 с 0.0.8 включён в каждой сборке")
    ap.add_argument("--no-logger", action="store_true",
                    help="чистый release без логгера H8/H9 -> Etherlords_native_v6.exe")
    args = ap.parse_args()
    global DEBUG
    DEBUG = not args.no_logger

    src, from_default = _resolve_src(args.src)
    if not os.path.isfile(src):
        print("Etherlords.exe НЕ НАЙДЕН.")
        print("Быстрый запуск: положите patch_native_v3.py в папку игры (рядом с")
        print("Etherlords.exe) и запустите его; либо укажите путь явно:")
        print("    python3 patch_native_v3.py /путь/к/Etherlords.exe")
        sys.exit(2)

    if args.out is None:
        name = "Etherlords_native_v6dbg.exe" if DEBUG else "Etherlords_native_v6.exe"
        # быстрый запуск (src найден автоматически): сборка — рядом с игрой;
        # явный путь src: как раньше, в каталог запуска (или --out).
        args.out = os.path.join(os.path.dirname(os.path.abspath(src)), name) if from_default else name
    d = open(src, "rb").read()
    print(f"tool   : patch_native_v3.py rev {TOOL_REV}")
    print(f"source : {src}  {len(d)} bytes  sha256={hashlib.sha256(d).hexdigest()[:16]}")

    print("\n[1/4] контрольные байты сайтов:")
    if not check_sites(d):
        print("\nABORT: бинарь отличается от анализируемого билда (docs/07/09).")
        sys.exit(2)

    print("\n[2/4] сборка cave:")
    parts, va, sizes = layout_parts()
    for name in part_order():
        print(f"  {name:11s} VA {va[name]:#010x}  file {va2file(va[name]):#08x}  {sizes[name]:4d} байт")
    blob = build_cave_blob(parts, va)
    print(f"  итого занято {len(blob)} из {CAVE_CAP} байт cave")
    extra = None
    if DEBUG:
        xparts, xva, xsizes = layout_extra(va)
        for name in extra_order():
            print(f"  {name:11s} VA {xva[name]:#010x}  (.ellog)  {xsizes[name]:4d} байт")
        extra = (xparts, xva)
        print(f"  секция .ellog: {sum(xsizes.values())} из {EXTRA_CAP} байт "
              f"(только debug; release без секции)")
    n_ins = verify_disasm(parts, va, listing=args.listing, extra=extra)
    print(f"  capstone: {n_ins} инструкций, все ветвления в разрешённом наборе, байт без остатка")

    print("\n[3/4] образ + аудит диффа:")
    img, _ = make_patched(d, parts, va, extra)
    n_changed = audit_diff(d, img, debug=DEBUG)
    print(f"  изменено байт: {n_changed} (сайты P1/H1..H6 + cave"
          + (", .ellog, vtable)" if DEBUG else ")"))

    if args.check:
        print("\nCHECK OK: патч применим.")
        return

    if not args.no_emu:
        print("\n[4/4] интерпретатор: функциональные тесты cave (T1..T10)")
        print("      (логгер-стабы H8/H9 в тестах не исполняются напрямую — IAT эмулируется заглушками)")
        if not emu_tests(img, va, extra):
            print("\nABORT: тесты провалены — файл НЕ записан.")
            sys.exit(3)
    else:
        print("\n[4/4] эмуляция пропущена (--no-emu)")

    open(args.out, "wb").write(img)
    print(f"\nwrote {args.out}  {len(img)} bytes  sha256={hashlib.sha256(img).hexdigest()[:16]}")
    if from_default:
        print(f"Запускайте игру через {os.path.basename(args.out)} (из папки игры).")
        print("Оригинальный Etherlords.exe не тронут — он же откат; переименований не нужно.")
        print("После запуска в папке игры появится el_evt.log (последний сеанс) —")
        print("при проблемах с UI пришлите его (разбор: tools/decode_evtlog.py).")
    else:
        print("Приёмка (docs/09 §5): главное меню, меню сохранения/загрузки, глобальная")
        print("карта (колесо команд: hover/click секторов и центра), бой. Откат — бэкап.")


if __name__ == "__main__":
    try:
        main()
    finally:
        if len(sys.argv) == 1:       # двойной клик / запуск без аргументов
            _pause_win()
