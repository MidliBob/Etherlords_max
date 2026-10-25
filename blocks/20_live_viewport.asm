; 20_live_viewport
; file 0x1a0070..0x1a0175  va 0x5a0070..0x5a0175
; Создание viewport'а ЖИВЫМ размером: RECT{0,0,realW,realH} из [0x825de8]->+0x18->{+0x14,+0x18} (0x5a00fd). Потребитель — миникарта/hover-поверхности.
  0x005a0070  6a ff             push -1
  0x005a0072  68 ab 23 73 00    push 0x7323ab
  0x005a0077  64 a1 00 00 00 00  mov eax, dword ptr fs:[0]
  0x005a007d  50                push eax
  0x005a007e  64 89 25 00 00 00 00  mov dword ptr fs:[0], esp
  0x005a0085  83 ec 0c          sub esp, 0xc
  0x005a0088  53                push ebx
  0x005a0089  8b 5c 24 20       mov ebx, dword ptr [esp + 0x20]
  0x005a008d  55                push ebp
  0x005a008e  8b e9             mov ebp, ecx
  0x005a0090  8a 85 8c 01 00 00  mov al, byte ptr [ebp + 0x18c]
  0x005a0096  56                push esi
  0x005a0097  57                push edi
  0x005a0098  c6 85 8c 01 00 00 00  mov byte ptr [ebp + 0x18c], 0
  0x005a009f  8b 3b             mov edi, dword ptr [ebx]
  0x005a00a1  85 ff             test edi, edi
  0x005a00a3  89 6c 24 14       mov dword ptr [esp + 0x14], ebp
  0x005a00a7  88 44 24 13       mov byte ptr [esp + 0x13], al
  0x005a00ab  74 2e             je 0x5a00db
  0x005a00ad  33 f6             xor esi, esi
  0x005a00af  8b 0f             mov ecx, dword ptr [edi]
  0x005a00b1  03 ce             add ecx, esi
  0x005a00b3  51                push ecx
  0x005a00b4  8b 0d 20 c6 82 00  mov ecx, dword ptr [0x82c620]
  0x005a00ba  e8 91 8f 00 00    call 0x5a9050
  0x005a00bf  8b 10             mov edx, dword ptr [eax]
  0x005a00c1  8b c8             mov ecx, eax
  0x005a00c3  ff 52 10          call dword ptr [edx + 0x10]
  0x005a00c6  46                inc esi
  0x005a00c7  83 fe 0c          cmp esi, 0xc
  0x005a00ca  7c e3             jl 0x5a00af
  0x005a00cc  57                push edi
  0x005a00cd  e8 7c c6 15 00    call 0x6fc74e
  0x005a00d2  83 c4 04          add esp, 4
  0x005a00d5  c7 03 00 00 00 00  mov dword ptr [ebx], 0
  0x005a00db  6a 14             push 0x14
  0x005a00dd  e8 43 c6 15 00    call 0x6fc725
  0x005a00e2  8b f8             mov edi, eax
  0x005a00e4  83 c4 04          add esp, 4
  0x005a00e7  89 7c 24 18       mov dword ptr [esp + 0x18], edi
  0x005a00eb  85 ff             test edi, edi
  0x005a00ed  c7 44 24 24 00 00 00 00  mov dword ptr [esp + 0x24], 0
  0x005a00f5  74 4c             je 0x5a0143
  0x005a00f7  8b 6c 24 30       mov ebp, dword ptr [esp + 0x30]
  0x005a00fb  89 2f             mov dword ptr [edi], ebp
  0x005a00fd  a1 e8 5d 82 00    mov eax, dword ptr [0x825de8]
  0x005a0102  8b 40 18          mov eax, dword ptr [eax + 0x18]
  0x005a0105  8b 48 18          mov ecx, dword ptr [eax + 0x18]
  0x005a0108  8b 40 14          mov eax, dword ptr [eax + 0x14]
  0x005a010b  33 d2             xor edx, edx
  0x005a010d  8d 5f 04          lea ebx, [edi + 4]
  0x005a0110  89 13             mov dword ptr [ebx], edx
  0x005a0112  33 f6             xor esi, esi
  0x005a0114  89 73 04          mov dword ptr [ebx + 4], esi
  0x005a0117  89 43 08          mov dword ptr [ebx + 8], eax
  0x005a011a  89 4b 0c          mov dword ptr [ebx + 0xc], ecx
  0x005a011d  8b 0d 20 c6 82 00  mov ecx, dword ptr [0x82c620]
  0x005a0123  8d 04 2e          lea eax, [esi + ebp]
  0x005a0126  50                push eax
  0x005a0127  e8 24 8f 00 00    call 0x5a9050
  0x005a012c  8b 50 04          mov edx, dword ptr [eax + 4]
  0x005a012f  42                inc edx
  0x005a0130  46                inc esi
  0x005a0131  83 fe 0c          cmp esi, 0xc
  0x005a0134  89 50 04          mov dword ptr [eax + 4], edx
  0x005a0137  7c e4             jl 0x5a011d
  0x005a0139  8b 5c 24 2c       mov ebx, dword ptr [esp + 0x2c]
  0x005a013d  8b 6c 24 14       mov ebp, dword ptr [esp + 0x14]
  0x005a0141  eb 02             jmp 0x5a0145
  0x005a0143  33 ff             xor edi, edi
  0x005a0145  8b cf             mov ecx, edi
  0x005a0147  c7 44 24 24 ff ff ff ff  mov dword ptr [esp + 0x24], 0xffffffff
  0x005a014f  89 3b             mov dword ptr [ebx], edi
  0x005a0151  e8 7a fc ff ff    call 0x59fdd0
  0x005a0156  8a 4c 24 13       mov cl, byte ptr [esp + 0x13]
  0x005a015a  5f                pop edi
  0x005a015b  88 8d 8c 01 00 00  mov byte ptr [ebp + 0x18c], cl
  0x005a0161  8b 4c 24 18       mov ecx, dword ptr [esp + 0x18]
  0x005a0165  5e                pop esi
  0x005a0166  5d                pop ebp
  0x005a0167  5b                pop ebx
  0x005a0168  64 89 0d 00 00 00 00  mov dword ptr fs:[0], ecx
  0x005a016f  83 c4 18          add esp, 0x18
  0x005a0172  c2 08 00          ret 8
