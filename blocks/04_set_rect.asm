; 04_set_rect
; file 0x18f690..0x18f6b3  va 0x58f690..0x58f6b3
; set_rect(this,RECT): копирует RECT в [this+0x154].
  0x0058f690  8b 44 24 04       mov eax, dword ptr [esp + 4]
  0x0058f694  8b 10             mov edx, dword ptr [eax]
  0x0058f696  81 c1 54 01 00 00  add ecx, 0x154
  0x0058f69c  89 11             mov dword ptr [ecx], edx
  0x0058f69e  8b 50 04          mov edx, dword ptr [eax + 4]
  0x0058f6a1  89 51 04          mov dword ptr [ecx + 4], edx
  0x0058f6a4  8b 50 08          mov edx, dword ptr [eax + 8]
  0x0058f6a7  89 51 08          mov dword ptr [ecx + 8], edx
  0x0058f6aa  8b 40 0c          mov eax, dword ptr [eax + 0xc]
  0x0058f6ad  89 41 0c          mov dword ptr [ecx + 0xc], eax
  0x0058f6b0  c2 04 00          ret 4
