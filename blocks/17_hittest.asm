; 17_hittest
; file 0x18fb70..0x18fd44  va 0x58fb70..0x58fd44
; HitTest(x,y): рекурсия детей; маска +0x150 (stride +0x184, rect +0x174, цепочка родителей +0x34->+0x154/0x158, PtInRect+бит маски); иначе rect +0x164/+0x154 + PtInRect.
  0x0058fb70  83 ec 54          sub esp, 0x54
  0x0058fb73  53                push ebx
  0x0058fb74  8b 5c 24 60       mov ebx, dword ptr [esp + 0x60]
  0x0058fb78  56                push esi
  0x0058fb79  8b f1             mov esi, ecx
  0x0058fb7b  8b 46 48          mov eax, dword ptr [esi + 0x48]
  0x0058fb7e  57                push edi
  0x0058fb7f  33 ff             xor edi, edi
  0x0058fb81  85 c0             test eax, eax
  0x0058fb83  7e 21             jle 0x58fba6
  0x0058fb85  8b 44 24 64       mov eax, dword ptr [esp + 0x64]
  0x0058fb89  8b 4e 44          mov ecx, dword ptr [esi + 0x44]
  0x0058fb8c  8b 0c b9          mov ecx, dword ptr [ecx + edi*4]
  0x0058fb8f  53                push ebx
  0x0058fb90  50                push eax
  0x0058fb91  e8 da ff ff ff    call 0x58fb70
  0x0058fb96  85 c0             test eax, eax
  0x0058fb98  0f 85 9d 01 00 00  jne 0x58fd3b
  0x0058fb9e  8b 46 48          mov eax, dword ptr [esi + 0x48]
  0x0058fba1  47                inc edi
  0x0058fba2  3b f8             cmp edi, eax
  0x0058fba4  7c df             jl 0x58fb85
  0x0058fba6  8b 86 50 01 00 00  mov eax, dword ptr [esi + 0x150]
  0x0058fbac  85 c0             test eax, eax
  0x0058fbae  55                push ebp
  0x0058fbaf  0f 85 a2 00 00 00  jne 0x58fc57
  0x0058fbb5  8d be 64 01 00 00  lea edi, [esi + 0x164]
  0x0058fbbb  57                push edi
  0x0058fbbc  ff 15 20 64 75 00  call dword ptr [0x756420]
  0x0058fbc2  85 c0             test eax, eax
  0x0058fbc4  8d 96 54 01 00 00  lea edx, [esi + 0x154]
  0x0058fbca  52                push edx
  0x0058fbcb  74 2e             je 0x58fbfb
  0x0058fbcd  8d 44 24 38       lea eax, [esp + 0x38]
  0x0058fbd1  50                push eax
  0x0058fbd2  8b ce             mov ecx, esi
  0x0058fbd4  e8 77 f9 ff ff    call 0x58f550
  0x0058fbd9  8b 4c 24 34       mov ecx, dword ptr [esp + 0x34]
  0x0058fbdd  8b 54 24 38       mov edx, dword ptr [esp + 0x38]
  0x0058fbe1  8b 44 24 3c       mov eax, dword ptr [esp + 0x3c]
  0x0058fbe5  89 4c 24 24       mov dword ptr [esp + 0x24], ecx
  0x0058fbe9  8b 4c 24 40       mov ecx, dword ptr [esp + 0x40]
  0x0058fbed  89 54 24 28       mov dword ptr [esp + 0x28], edx
  0x0058fbf1  89 44 24 2c       mov dword ptr [esp + 0x2c], eax
  0x0058fbf5  89 4c 24 30       mov dword ptr [esp + 0x30], ecx
  0x0058fbf9  eb 3b             jmp 0x58fc36
  0x0058fbfb  8d 44 24 48       lea eax, [esp + 0x48]
  0x0058fbff  50                push eax
  0x0058fc00  8b ce             mov ecx, esi
  0x0058fc02  e8 49 f9 ff ff    call 0x58f550
  0x0058fc07  8b 4c 24 44       mov ecx, dword ptr [esp + 0x44]
  0x0058fc0b  8b 54 24 48       mov edx, dword ptr [esp + 0x48]
  0x0058fc0f  8b 44 24 4c       mov eax, dword ptr [esp + 0x4c]
  0x0058fc13  89 4c 24 54       mov dword ptr [esp + 0x54], ecx
  0x0058fc17  8b 4c 24 50       mov ecx, dword ptr [esp + 0x50]
  0x0058fc1b  89 54 24 58       mov dword ptr [esp + 0x58], edx
  0x0058fc1f  57                push edi
  0x0058fc20  8d 54 24 28       lea edx, [esp + 0x28]
  0x0058fc24  89 4c 24 64       mov dword ptr [esp + 0x64], ecx
  0x0058fc28  52                push edx
  0x0058fc29  8d 4c 24 5c       lea ecx, [esp + 0x5c]
  0x0058fc2d  89 44 24 64       mov dword ptr [esp + 0x64], eax
  0x0058fc31  e8 1a 01 00 00    call 0x58fd50
  0x0058fc36  8b 44 24 68       mov eax, dword ptr [esp + 0x68]
  0x0058fc3a  53                push ebx
  0x0058fc3b  50                push eax
  0x0058fc3c  8d 4c 24 2c       lea ecx, [esp + 0x2c]
  0x0058fc40  51                push ecx
  0x0058fc41  ff 15 30 64 75 00  call dword ptr [0x756430]
  0x0058fc47  f7 d8             neg eax
  0x0058fc49  5d                pop ebp
  0x0058fc4a  1b c0             sbb eax, eax
  0x0058fc4c  5f                pop edi
  0x0058fc4d  23 c6             and eax, esi
  0x0058fc4f  5e                pop esi
  0x0058fc50  5b                pop ebx
  0x0058fc51  83 c4 54          add esp, 0x54
  0x0058fc54  c2 08 00          ret 8
  0x0058fc57  8d 96 74 01 00 00  lea edx, [esi + 0x174]
  0x0058fc5d  8b 0a             mov ecx, dword ptr [edx]
  0x0058fc5f  8b 7a 04          mov edi, dword ptr [edx + 4]
  0x0058fc62  8b 6a 08          mov ebp, dword ptr [edx + 8]
  0x0058fc65  8b 42 0c          mov eax, dword ptr [edx + 0xc]
  0x0058fc68  8b 56 34          mov edx, dword ptr [esi + 0x34]
  0x0058fc6b  89 44 24 60       mov dword ptr [esp + 0x60], eax
  0x0058fc6f  8b c2             mov eax, edx
  0x0058fc71  85 c0             test eax, eax
  0x0058fc73  89 4c 24 14       mov dword ptr [esp + 0x14], ecx
  0x0058fc77  89 7c 24 18       mov dword ptr [esp + 0x18], edi
  0x0058fc7b  74 23             je 0x58fca0
  0x0058fc7d  8b b8 58 01 00 00  mov edi, dword ptr [eax + 0x158]
  0x0058fc83  89 7c 24 10       mov dword ptr [esp + 0x10], edi
  0x0058fc87  03 88 54 01 00 00  add ecx, dword ptr [eax + 0x154]
  0x0058fc8d  8b 7c 24 10       mov edi, dword ptr [esp + 0x10]
  0x0058fc91  01 7c 24 18       add dword ptr [esp + 0x18], edi
  0x0058fc95  89 4c 24 14       mov dword ptr [esp + 0x14], ecx
  0x0058fc99  8b 40 34          mov eax, dword ptr [eax + 0x34]
  0x0058fc9c  85 c0             test eax, eax
  0x0058fc9e  75 dd             jne 0x58fc7d
  0x0058fca0  8b c2             mov eax, edx
  0x0058fca2  85 c0             test eax, eax
  0x0058fca4  8b 54 24 60       mov edx, dword ptr [esp + 0x60]
  0x0058fca8  8b cd             mov ecx, ebp
  0x0058fcaa  89 4c 24 1c       mov dword ptr [esp + 0x1c], ecx
  0x0058fcae  89 54 24 20       mov dword ptr [esp + 0x20], edx
  0x0058fcb2  74 23             je 0x58fcd7
  0x0058fcb4  8b 90 58 01 00 00  mov edx, dword ptr [eax + 0x158]
  0x0058fcba  8b a8 54 01 00 00  mov ebp, dword ptr [eax + 0x154]
  0x0058fcc0  8b 7c 24 20       mov edi, dword ptr [esp + 0x20]
  0x0058fcc4  03 cd             add ecx, ebp
  0x0058fcc6  03 fa             add edi, edx
  0x0058fcc8  89 4c 24 1c       mov dword ptr [esp + 0x1c], ecx
  0x0058fccc  89 7c 24 20       mov dword ptr [esp + 0x20], edi
  0x0058fcd0  8b 40 34          mov eax, dword ptr [eax + 0x34]
  0x0058fcd3  85 c0             test eax, eax
  0x0058fcd5  75 dd             jne 0x58fcb4
  0x0058fcd7  8b 7c 24 68       mov edi, dword ptr [esp + 0x68]
  0x0058fcdb  53                push ebx
  0x0058fcdc  57                push edi
  0x0058fcdd  8d 44 24 1c       lea eax, [esp + 0x1c]
  0x0058fce1  50                push eax
  0x0058fce2  ff 15 30 64 75 00  call dword ptr [0x756430]
  0x0058fce8  85 c0             test eax, eax
  0x0058fcea  74 46             je 0x58fd32
  0x0058fcec  8b 6c 24 18       mov ebp, dword ptr [esp + 0x18]
  0x0058fcf0  8b 44 24 14       mov eax, dword ptr [esp + 0x14]
  0x0058fcf4  2b dd             sub ebx, ebp
  0x0058fcf6  0f af 9e 84 01 00 00  imul ebx, dword ptr [esi + 0x184]
  0x0058fcfd  8b cf             mov ecx, edi
  0x0058fcff  2b c8             sub ecx, eax
  0x0058fd01  8b 86 50 01 00 00  mov eax, dword ptr [esi + 0x150]
  0x0058fd07  8b d1             mov edx, ecx
  0x0058fd09  c1 fa 05          sar edx, 5
  0x0058fd0c  03 da             add ebx, edx
  0x0058fd0e  83 e1 1f          and ecx, 0x1f
  0x0058fd11  ba 01 00 00 00    mov edx, 1
  0x0058fd16  d3 e2             shl edx, cl
  0x0058fd18  85 14 98          test dword ptr [eax + ebx*4], edx
  0x0058fd1b  76 15             jbe 0x58fd32
  0x0058fd1d  b8 01 00 00 00    mov eax, 1
  0x0058fd22  f7 d8             neg eax
  0x0058fd24  5d                pop ebp
  0x0058fd25  1b c0             sbb eax, eax
  0x0058fd27  5f                pop edi
  0x0058fd28  23 c6             and eax, esi
  0x0058fd2a  5e                pop esi
  0x0058fd2b  5b                pop ebx
  0x0058fd2c  83 c4 54          add esp, 0x54
  0x0058fd2f  c2 08 00          ret 8
  0x0058fd32  33 c0             xor eax, eax
  0x0058fd34  f7 d8             neg eax
  0x0058fd36  1b c0             sbb eax, eax
  0x0058fd38  23 c6             and eax, esi
  0x0058fd3a  5d                pop ebp
  0x0058fd3b  5f                pop edi
  0x0058fd3c  5e                pop esi
  0x0058fd3d  5b                pop ebx
  0x0058fd3e  83 c4 54          add esp, 0x54
  0x0058fd41  c2 08 00          ret 8
