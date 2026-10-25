; 12_set_shift
; file 0x191170..0x191190  va 0x591170..0x591190
; SetShift(elem,flag,sx,sy): record[flag].sX(+8)=sx, .sY(+12)=sy. Из лоадера: SetShift(1,ShiftX,ShiftY).
  0x00591170  8b 44 24 04       mov eax, dword ptr [esp + 4]
  0x00591174  8b 54 24 08       mov edx, dword ptr [esp + 8]
  0x00591178  c1 e0 04          shl eax, 4
  0x0059117b  89 94 08 94 01 00 00  mov dword ptr [eax + ecx + 0x194], edx
  0x00591182  8b 54 24 0c       mov edx, dword ptr [esp + 0xc]
  0x00591186  89 94 08 98 01 00 00  mov dword ptr [eax + ecx + 0x198], edx
  0x0059118d  c2 0c 00          ret 0xc
