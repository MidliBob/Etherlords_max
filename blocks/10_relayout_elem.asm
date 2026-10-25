; 10_relayout_elem
; file 0x191250..0x1912de  va 0x591250..0x5912de
; relayout(elem,flag): act{+0x1ac..0x1bb} = record[flag]{+0x18c+flag*16}; virtual OnLayoutChange(vtbl+0x5c)(dShX,dShY,dX,dY).
  0x00591250  8b 44 24 04       mov eax, dword ptr [esp + 4]
  0x00591254  8b 91 ac 01 00 00  mov edx, dword ptr [ecx + 0x1ac]
  0x0059125a  53                push ebx
  0x0059125b  8b 99 b8 01 00 00  mov ebx, dword ptr [ecx + 0x1b8]
  0x00591261  55                push ebp
  0x00591262  56                push esi
  0x00591263  8b b1 b0 01 00 00  mov esi, dword ptr [ecx + 0x1b0]
  0x00591269  57                push edi
  0x0059126a  8b b9 b4 01 00 00  mov edi, dword ptr [ecx + 0x1b4]
  0x00591270  c1 e0 04          shl eax, 4
  0x00591273  8b ac 08 8c 01 00 00  mov ebp, dword ptr [eax + ecx + 0x18c]
  0x0059127a  03 c1             add eax, ecx
  0x0059127c  89 a9 ac 01 00 00  mov dword ptr [ecx + 0x1ac], ebp
  0x00591282  8b a8 90 01 00 00  mov ebp, dword ptr [eax + 0x190]
  0x00591288  89 a9 b0 01 00 00  mov dword ptr [ecx + 0x1b0], ebp
  0x0059128e  8b a8 94 01 00 00  mov ebp, dword ptr [eax + 0x194]
  0x00591294  89 a9 b4 01 00 00  mov dword ptr [ecx + 0x1b4], ebp
  0x0059129a  8b a8 98 01 00 00  mov ebp, dword ptr [eax + 0x198]
  0x005912a0  89 a9 b8 01 00 00  mov dword ptr [ecx + 0x1b8], ebp
  0x005912a6  8b a9 ac 01 00 00  mov ebp, dword ptr [ecx + 0x1ac]
  0x005912ac  f7 da             neg edx
  0x005912ae  03 d5             add edx, ebp
  0x005912b0  8b a9 b0 01 00 00  mov ebp, dword ptr [ecx + 0x1b0]
  0x005912b6  f7 de             neg esi
  0x005912b8  03 f5             add esi, ebp
  0x005912ba  8b a8 94 01 00 00  mov ebp, dword ptr [eax + 0x194]
  0x005912c0  8b 80 98 01 00 00  mov eax, dword ptr [eax + 0x198]
  0x005912c6  56                push esi
  0x005912c7  f7 db             neg ebx
  0x005912c9  03 d8             add ebx, eax
  0x005912cb  8b 01             mov eax, dword ptr [ecx]
  0x005912cd  52                push edx
  0x005912ce  f7 df             neg edi
  0x005912d0  53                push ebx
  0x005912d1  03 fd             add edi, ebp
  0x005912d3  57                push edi
  0x005912d4  ff 50 5c          call dword ptr [eax + 0x5c]
  0x005912d7  5f                pop edi
  0x005912d8  5e                pop esi
  0x005912d9  5d                pop ebp
  0x005912da  5b                pop ebx
  0x005912db  c2 04 00          ret 4
