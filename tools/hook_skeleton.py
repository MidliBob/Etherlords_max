#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
hook_skeleton.py — заготовка native v2: пост-масштабирование координат UI-элементов.

Идея (урок v1): не трогать rect. После применения раскладки (apply_layout 0x99fcb0)
обойти круговой список элементов и масштабировать их x/y/w/h на (W/1024, H/768).
Отрисовка и hit-test читают те же поля -> остаются согласованными, кнопки живы.

Структура списка (выведена статически из apply_flag 0x98bd70):
    mgr  = [0x82b968]
    head = [mgr]
    node = [head+8]            ; круговой: конец когда node == head
    elem = [node+0x1c]
    flags= [elem+0x14c]
    X/Y/W/H = [elem+X_OFF] ...  <-- ЗАПОЛНИТЬ из протокола deep_re (Cheat Engine)

Параметры ниже — заглушки до получения runtime-данных. Скрипт генерирует байты
трамплина и печатает их; точка вставки финализируется после шага 1 протокола.
"""
X_OFF = None   # <- offset поля X  в объекте элемента (из CE)
Y_OFF = None   # <- offset поля Y
W_OFF = None   # <- offset поля W (если масштабируется)
H_OFF = None   # <- offset поля H (если масштабируется)
BASE_W, BASE_H = 1024, 768
MGR   = 0x82b968

def asm_post_scale():
    """Псевдо->байты не генерируем вслепую: возвращаем план инструкций для ручной
    сборки в code cave, чтобы не гадать encoding до получения offsets."""
    plan = [
        f"mov  eax,[{MGR:#x}]        ; mgr",
        "mov  eax,[eax]              ; head",
        "mov  esi,[eax+8]            ; node = head->next",
        "loop:",
        "cmp  esi,eax                ; node==head -> конец",
        "je   done",
        "mov  edi,[esi+0x1c]         ; elem",
        # X' = X * W / 1024
        f"mov  ecx,[edi+{X_OFF}]      ; X",
        "imul ecx,[curW]",
        "mov  ebx,1024", "cdq", "idiv ebx",
        f"mov  [edi+{X_OFF}],eax",
        # Y' = Y * H / 768
        f"mov  ecx,[edi+{Y_OFF}]      ; Y",
        "imul ecx,[curH]",
        "mov  ebx,768", "cdq", "idiv ebx",
        f"mov  [edi+{Y_OFF}],eax",
        "mov  esi,[esi+8]             ; node = node->next",
        "jmp  loop",
        "done:",
    ]
    return plan

if __name__ == "__main__":
    if X_OFF is None or Y_OFF is None:
        print("hook_skeleton: offsets не заполнены.")
        print("Сначала выполните work/deep_re_protocol.md (шаг 1, Cheat Engine)")
        print("и пришлите: адрес инструкции-записи, её байты, offset поля X/Y,")
        print("значения регистров в момент записи.")
        print("\nПлан трамплина (будет собран после получения offsets):")
        for l in asm_post_scale():
            print("   ", l)
    else:
        print("offsets заданы — собираем Etherlords_native_v2.exe (TODO: encoding)")
