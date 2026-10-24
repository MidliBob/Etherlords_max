; 07_aspect_3_4
; file 0x52b20..0x52b60  va 0x852b20..0x852b60
; mov eax,0x3f400000 (3/4) -> поле проекции [esi+0x20].
  0x00852b20  5c               pop       esp
  0x00852b21  67 75 00         jne       0x852b24
  0x00852b24  eb 06            jmp       0x852b2c
  0x00852b26  d9 05 74 66 75 00 fld       dword ptr [0x756674]
  0x00852b2c  d9 56 10         fst       dword ptr [esi + 0x10]
  0x00852b2f  b8 00 00 40 3f   mov       eax, 0x3f400000
  0x00852b34  d9 c0            fld       st(0)
  0x00852b36  89 46 20         mov       dword ptr [esi + 0x20], eax
  0x00852b39  d8 05 74 66 75 00 fadd      dword ptr [0x756674]
  0x00852b3f  89 46 24         mov       dword ptr [esi + 0x24], eax
  0x00852b42  b8 00 00 00 3f   mov       eax, 0x3f000000
  0x00852b47  89 46 28         mov       dword ptr [esi + 0x28], eax
  0x00852b4a  d9 56 14         fst       dword ptr [esi + 0x14]
  0x00852b4d  89 46 2c         mov       dword ptr [esi + 0x2c], eax
  0x00852b50  8b 44 24 10      mov       eax, dword ptr [esp + 0x10]
  0x00852b54  d9 5e 18         fstp      dword ptr [esi + 0x18]
  0x00852b57  3b c3            cmp       eax, ebx
  0x00852b59  d9 5e 1c         fstp      dword ptr [esi + 0x1c]
  0x00852b5c  75 35            jne       0x852b93
