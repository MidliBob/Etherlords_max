; 09_push800x600_b
; file 0x19bd00..0x19bd28  va 0x59bd00..0x59bd28
; Дефолт SetRect(0,0,800,600) + set_rect([esi+8]) сайт #2 (перед mode_check).
  0x0059bd00  0d 68 b9 82 00    or eax, 0x82b968
  0x0059bd05  e8 26 0d ff ff    call 0x58ca30
  0x0059bd0a  68 58 02 00 00    push 0x258
  0x0059bd0f  68 20 03 00 00    push 0x320
  0x0059bd14  6a 00             push 0
  0x0059bd16  6a 00             push 0
  0x0059bd18  55                push ebp
  0x0059bd19  ff 15 28 64 75 00  call dword ptr [0x756428]
  0x0059bd1f  8b 4e 08          mov ecx, dword ptr [esi + 8]
  0x0059bd22  55                push ebp
  0x0059bd23  e8 68 39 ff ff    call 0x58f690
