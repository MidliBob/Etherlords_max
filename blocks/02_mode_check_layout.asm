; 02_mode_check_layout
; file 0x19bd28..0x19bd90  va 0x99bd28..0x99bd90
; Выбор раскладки: сверка с 1024x768/800x600; неизвестное разрешение ПРОПУСКАЕТ call apply_layout.
  0x0099bd28  a1 e8 5d 82 00   mov       eax, dword ptr [0x825de8]
  0x0099bd2d  8b 48 14         mov       ecx, dword ptr [eax + 0x14]
  0x0099bd30  85 c9            test      ecx, ecx
  0x0099bd32  5d               pop       ebp
  0x0099bd33  5b               pop       ebx
  0x0099bd34  74 2b            je        0x99bd61
  0x0099bd36  8b 40 18         mov       eax, dword ptr [eax + 0x18]
  0x0099bd39  8b 48 14         mov       ecx, dword ptr [eax + 0x14]
  0x0099bd3c  81 f9 00 04 00 00 cmp       ecx, 0x400
  0x0099bd42  8b 40 18         mov       eax, dword ptr [eax + 0x18]
  0x0099bd45  75 0b            jne       0x99bd52
  0x0099bd47  3d 00 03 00 00   cmp       eax, 0x300
  0x0099bd4c  75 1c            jne       0x99bd6a
  0x0099bd4e  6a 01            push      1
  0x0099bd50  eb 11            jmp       0x99bd63
  0x0099bd52  81 f9 20 03 00 00 cmp       ecx, 0x320
  0x0099bd58  75 10            jne       0x99bd6a
  0x0099bd5a  3d 58 02 00 00   cmp       eax, 0x258
  0x0099bd5f  75 09            jne       0x99bd6a
  0x0099bd61  6a 00            push      0
  0x0099bd63  8b ce            mov       ecx, esi
  0x0099bd65  e8 46 3f 00 00   call      0x99fcb0
  0x0099bd6a  8b 4e 20         mov       ecx, dword ptr [esi + 0x20]
  0x0099bd6d  e8 9e 48 ff ff   call      0x990610
  0x0099bd72  8b 4e 10         mov       ecx, dword ptr [esi + 0x10]
  0x0099bd75  e8 96 77 f6 ff   call      0x903510
  0x0099bd7a  8b 4c 24 38      mov       ecx, dword ptr [esp + 0x38]
  0x0099bd7e  c6 86 24 01 00 00 01 mov       byte ptr [esi + 0x124], 1
  0x0099bd85  5f               pop       edi
  0x0099bd86  b8 01 00 00 00   mov       eax, 1
  0x0099bd8b  5e               pop       esi
