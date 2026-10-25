; 18_ctor_zero_records
; file 0x18f261..0x18f2b0  va 0x58f261..0x58f2b0
; Базовый контор контрола: зануляет record[0..1] (+0x18c..0x1ab) и act (+0x1ac..0x1bb). Размер Panel=0x1d0: место ровно под ДВЕ записи.
  0x0058f261  33 d2             xor edx, edx
  0x0058f263  33 ff             xor edi, edi
  0x0058f265  8d 86 94 01 00 00  lea eax, [esi + 0x194]
  0x0058f26b  b9 02 00 00 00    mov ecx, 2
  0x0058f270  89 50 f8          mov dword ptr [eax - 8], edx
  0x0058f273  33 ed             xor ebp, ebp
  0x0058f275  89 78 fc          mov dword ptr [eax - 4], edi
  0x0058f278  89 28             mov dword ptr [eax], ebp
  0x0058f27a  89 68 04          mov dword ptr [eax + 4], ebp
  0x0058f27d  83 c0 10          add eax, 0x10
  0x0058f280  49                dec ecx
  0x0058f281  75 ed             jne 0x58f270
  0x0058f283  8b 3d 24 64 75 00  mov edi, dword ptr [0x756424]
  0x0058f289  33 c0             xor eax, eax
  0x0058f28b  8d 8e 54 01 00 00  lea ecx, [esi + 0x154]
  0x0058f291  89 86 ac 01 00 00  mov dword ptr [esi + 0x1ac], eax
  0x0058f297  89 86 b4 01 00 00  mov dword ptr [esi + 0x1b4], eax
  0x0058f29d  51                push ecx
  0x0058f29e  89 9e b0 01 00 00  mov dword ptr [esi + 0x1b0], ebx
  0x0058f2a4  89 9e b8 01 00 00  mov dword ptr [esi + 0x1b8], ebx
