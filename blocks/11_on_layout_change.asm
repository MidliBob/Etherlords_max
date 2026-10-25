; 11_on_layout_change
; file 0x1912e0..0x191339  va 0x5912e0..0x591339
; OnLayoutChange: OffsetRect(+0x154,dShX,dShY); если +0x164 непуст OffsetRect(+0x164,dX,dY); visual(+0x148): 0x58a5d0(dX,dY).
  0x005912e0  8b 44 24 08       mov eax, dword ptr [esp + 8]
  0x005912e4  53                push ebx
  0x005912e5  8b 1d 64 64 75 00  mov ebx, dword ptr [0x756464]
  0x005912eb  55                push ebp
  0x005912ec  56                push esi
  0x005912ed  57                push edi
  0x005912ee  8b f1             mov esi, ecx
  0x005912f0  8b 4c 24 14       mov ecx, dword ptr [esp + 0x14]
  0x005912f4  50                push eax
  0x005912f5  51                push ecx
  0x005912f6  8d 96 54 01 00 00  lea edx, [esi + 0x154]
  0x005912fc  52                push edx
  0x005912fd  ff d3             call ebx
  0x005912ff  8d be 64 01 00 00  lea edi, [esi + 0x164]
  0x00591305  57                push edi
  0x00591306  ff 15 20 64 75 00  call dword ptr [0x756420]
  0x0059130c  85 c0             test eax, eax
  0x0059130e  8b 6c 24 1c       mov ebp, dword ptr [esp + 0x1c]
  0x00591312  75 09             jne 0x59131d
  0x00591314  8b 44 24 20       mov eax, dword ptr [esp + 0x20]
  0x00591318  50                push eax
  0x00591319  55                push ebp
  0x0059131a  57                push edi
  0x0059131b  ff d3             call ebx
  0x0059131d  8b 8e 48 01 00 00  mov ecx, dword ptr [esi + 0x148]
  0x00591323  85 c9             test ecx, ecx
  0x00591325  74 0b             je 0x591332
  0x00591327  8b 54 24 20       mov edx, dword ptr [esp + 0x20]
  0x0059132b  52                push edx
  0x0059132c  55                push ebp
  0x0059132d  e8 9e 92 ff ff    call 0x58a5d0
  0x00591332  5f                pop edi
  0x00591333  5e                pop esi
  0x00591334  5d                pop ebp
  0x00591335  5b                pop ebx
  0x00591336  c2 10 00          ret 0x10
