#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
hook_skeleton.py — заготовка native v2: пост-масштабирование координат контролов.

>>> РЕАЛИЗОВАНО: сборщик v2 — tools/patch_native_v2.py (байты cave, верификация,
>>> интерпретатор-тесты T1–T4, подробности docs/08). Этот файл сохранён как
>>> дизайн-документ: карта адресов/offset'ов и план из docs/07 §6.2.

Ревизия по docs/07 («Анатомия профиля 1024x768»): CE-протокол docs/06 БОЛЬШЕ НЕ
НУЖЕН — offset'ы элементов выведены статически (docs/07, §3). Все адреса — настоящие
VA (ImageBase 0x400000; VA = file + 0x400000). В docs/02–06 использовался завышенный
базис (file + 0x800000) — см. поправку docs/07, §0.

Урок v1 (docs/05): подмена только экранных rect'ов рассинхронизирует draw/hover/click
(мёртвые кнопки). Инвариант (docs/04): клики живы только при rect == baked. Поэтому
v2 держит всех трёх потребителей согласованными одновременными правками:
  (1) форс apply_layout(1) при любом разрешении — уже делает patch_layout.py (6 байт);
  (2) подмена immediate'ов W/H внутри apply_layout на живые из объекта режима
      (трамплин v1 годится — байты в tools/patch_native.py, но ТОЛЬКО вместе с п.3);
  (3) пост-проход после apply_flag: масштабирование RECT'ов/active всех контролов
      на (W/1024, H/768) — draw и hit-test читают те же поля, расхождения нет.

Критерий приемки (docs/04, docs/06): при 1600x900 нарисованные кнопки встанут ровно
там, где до патча возникала hover-подсветка по периметру; hover и click срабатывают
в той же зоне. Повторить на 2560x1440 и 3840x2160: draw == hover == click.
"""

# --- Карта адресов (docs/07, §7). Настоящие VA; file = VA - IMAGE_BASE -------
IMAGE_BASE   = 0x400000
MODE_CHECK   = 0x59BD28   # file 0x19bd28  выбор раскладки (jne->jmp патчит patch_layout.py)
APPLY_LAYOUT = 0x59FCB0   # file 0x19fcb0  apply_layout(flag)
IMM_W1024    = 0x59FCCD   # file 0x19fccd  mov edx,0x400        (ветка flag=1)
IMM_H768     = 0x59FCD2   # file 0x19fcd2  mov [esp+0x24],0x300 (ветка flag=1)
IMM_W800     = 0x59FCDC   # file 0x19fcdc  mov edx,0x320        (ветка flag=0)
IMM_H600     = 0x59FCE1   # file 0x19fce1  mov [esp+0x24],0x258 (ветка flag=0)
APPLY_FLAG   = 0x58BD70   # file 0x18bd70  apply_flag(mgr,flag): бит профиля + relayout всех
AFTER_FLAG   = 0x59FD20   # file 0x19fd20  точка вставки пост-прохода (сразу после call 0x58bd70;
                          #                6-байтная `mov eax,[esi+0xf0]` -> jmp cave + nop)
RELAYOUT     = 0x591250   # act = record[flag]; virtual OnLayoutChange(dShX,dShY,dX,dY)
ON_LAYOUT    = 0x5912E0   # vtbl+0x5c: OffsetRect(+0x154/+0x164), visual->Offset
HIT_TEST     = 0x58FB70   # HitTest(x,y): маска +0x150 / rect +0x164,+0x154, PtInRect
SET_RECT     = 0x58F690   # set_rect(this,RECT -> [this+0x154])
MODE_OBJ     = 0x825DE8   # глобальный объект режима: ->+0x18-> {+0x14: W, +0x18: H} (live)
MGR          = 0x82B968   # глобальный менеджер контролов (круговой список)
CAVE_FILE    = 0x355656   # VA 0x755656..0x756000: ~2.4 КБ нулей внутри raw .text (исполняемый)

# --- Offset'ы CControl (docs/07, §3) — статически известны, CE не нужен ------
RECT_REL   = 0x154   # parent-relative RECT геометрии (hit-test/клиппинг); abs = SUM relative
RECT_ABS   = 0x164   # абсолютный кэш-RECT
RECT_MSK   = 0x174   # локальный RECT маски
MASK_PTR   = 0x150   # пиксельная маска hit-test (stride +0x184) — НЕ масштабируется, см. п.4
VISUAL     = 0x148   # CVisualObject: спрайт/прямоугольники отрисовки (init 0x5899b0)
RECORD0    = 0x18C   # record[0] {X,Y,sX,sY} — профиль 800x600
RECORD1    = 0x19C   # record[1] {X,Y,sX,sY} — профиль 1024x768 (X,Y = SUM ShiftX/ShiftY)
ACTIVE     = 0x1AC   # active {X,Y,sX,sY} = record[flag] (+0x1ac..+0x1bb)
PARENT     = 0x34
CHILDREN   = 0x44
NCHILDREN  = 0x48
FLAG_BITS  = 0x14C   # нижний nibble = бит профиля (1=800x600, 2=1024x768)

BASE_W, BASE_H = 1024, 768

# Обход кругового списка контролов (как в apply_flag 0x58bd70):
#     mgr  = [0x82b968]
#     head = [mgr]
#     node = [head+8]        ; круговой: конец когда node == head
#     elem = [node+0x1c]


def plan_v2():
    """План инструкций/шагов v2 (docs/07, §6.2). Encoding cave-байтов — следующий шаг;
    трамплин п.2 уже существует в байтах (tools/patch_native.py --force, секция A)."""
    return [
        "(1) Форс apply_layout(1) при любом разрешении:",
        f"      уже реализован patch_layout.py: jne->jmp @ file 0x19bd4c/0x19bd58/0x19bd5f.",
        "",
        "(2) Трамплин live W/H вместо immediate'ов 1024/768 (ветка flag=1):",
        f"      хук VA {IMM_W1024:#x} (file {IMM_W1024-IMAGE_BASE:#x}, 5 байт mov edx,0x400) -> jmp cave;",
        f"      cave: mov eax,[{MODE_OBJ:#x}]; mov eax,[eax+0x18];",
        "            mov edx,[eax+0x14]  (live W); mov ecx,[eax+0x18]  (live H);",
        f"            mov [esp+0x24],ecx; jmp {IMM_W1024+13:#x}  (за обе immediate-инструкции);",
        "      -> [screen+0xe8]=(0,0,W,H) и полосы (W-163)/(W-133) считаются от живого W.",
        "",
        f"(3) Пост-проход масштабирования: хук VA {AFTER_FLAG:#x} (file {AFTER_FLAG-IMAGE_BASE:#x})",
        "      (сразу после call apply_flag; украсть `mov eax,[esi+0xf0]`, 6 байт -> jmp+nop):",
        f"      kX = liveW/{BASE_W}, kY = liveH/{BASE_H} (live W/H из цепочки MODE_OBJ);",
        f"      обход списка [{MGR:#x}] (node=[node+8], elem=[node+0x1c], до node==head):",
        f"        RECT +{RECT_REL:#x}: L,R *= kX; T,B *= kY   (parent-relative: abs = SUM relative,",
        "                            масштабирование каждого звена согласованно по всей цепочке)",
        f"        RECT +{RECT_ABS:#x}, RECT +{RECT_MSK:#x}: так же LTRB;",
        f"        active +{ACTIVE:#x}: X *= kX, Y *= kY (sX/sY — см. caveat ниже);",
        f"        visual +{VISUAL:#x}: rect'ы спрайта (через его поля, см. 0x5899b0/0x58a5d0);",
        "        экран (esi): полосы set_rect([esi+0x10]) = (W-163,0,W,H),",
        "        set_rect([esi+0xc]) = (0,0,W-133,H) — уже от живого W после п.2.",
        "",
        "(4) Пиксельные маски (Msk) не масштабируются — два варианта (docs/07, §6.2):",
        f"      a) в хуке hit-test ({HIT_TEST:#x}) делить локальные (x-left, y-top) на (kX,kY);",
        f"      b) отключить маску у масштабированных контролов: [elem+{MASK_PTR:#x}] = 0",
        "         (hit-test откатится на rect +0x164/+0x154, потеряв пиксельную точность).",
        "",
        "CAVEAT (records): record[0/1] (+0x18c/+0x19c) — источник дельт для relayout",
        f"      ({RELAYOUT:#x}) при повторном apply_flag. Если пост-проход масштабирует active/RECT'ы,",
        "      но не records, то повторное переключение профиля собьёт позиции (дельта из",
        "      немасштабированных records). Варианты: масштабировать и records, либо гаран-",
        "      тировать однократность пост-прохода (флаг-переменная в cave/.data), либо",
        "      не трогать active/records, а масштабировать только RECT'ы и visual (минимум).",
        "",
        f"Код-кейв: file {CAVE_FILE:#x}..0x356000 (VA {CAVE_FILE+IMAGE_BASE:#x}..0x756000),",
        "      ~2.4 КБ, внутри SizeOfRawData .text — исполняемый, v1 его уже использовал.",
    ]


if __name__ == "__main__":
    print("hook_skeleton (ревизия по docs/07): offsets известны статически, CE-протокол не нужен.")
    print(f"Базис: VA = file + {IMAGE_BASE:#x}. Критерий приемки: draw == hover == click (docs/04).")
    print("\nПлан v2:")
    for line in plan_v2():
        print("   ", line)
    print("\nСТАТУС: v2 реализован — tools/patch_native_v2.py (байты cave P1/H1-H3,")
    print("        верификация capstone + интерпретатор T1-T4); детали — docs/08.")
