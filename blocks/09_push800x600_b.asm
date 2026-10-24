; 09_push800x600_b
; file 0x19bd00..0x19bd28  va 0x99bd00..0x99bd28
; Дефолт f(...,800,600) сайт #2 (рядом cmp 1024/768).
  0x0099bd00  0d 68 b9 82 00   or        eax, 0x82b968
  0x0099bd05  e8 26 0d ff ff   call      0x98ca30
  0x0099bd0a  68 58 02 00 00   push      0x258
  0x0099bd0f  68 20 03 00 00   push      0x320
  0x0099bd14  6a 00            push      0
  0x0099bd16  6a 00            push      0
  0x0099bd18  55               push      ebp
  0x0099bd19  ff 15 28 64 75 00 call      dword ptr [0x756428]
  0x0099bd1f  8b 4e 08         mov       ecx, dword ptr [esi + 8]
  0x0099bd22  55               push      ebp
  0x0099bd23  e8 68 39 ff ff   call      0x98f690
