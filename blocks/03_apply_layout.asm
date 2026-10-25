; 03_apply_layout
; file 0x19fcb0..0x19fda0  va 0x59fcb0..0x59fda0
; apply_layout(flag): W,H=(800,600)|(1024,768) immediate; [screen+0xe8]=(0,0,W,H); set_rect subscreens; apply_flag(mgr,flag); полосы (W-163) и (W-133).
  0x0059fcb0  83 ec 10          sub esp, 0x10
  0x0059fcb3  53                push ebx
  0x0059fcb4  8b 5c 24 18       mov ebx, dword ptr [esp + 0x18]
  0x0059fcb8  55                push ebp
  0x0059fcb9  56                push esi
  0x0059fcba  8b c3             mov eax, ebx
  0x0059fcbc  83 e8 00          sub eax, 0
  0x0059fcbf  8b f1             mov esi, ecx
  0x0059fcc1  57                push edi
  0x0059fcc2  89 9e 88 01 00 00  mov dword ptr [esi + 0x188], ebx
  0x0059fcc8  74 12             je 0x59fcdc
  0x0059fcca  48                dec eax
  0x0059fccb  75 1e             jne 0x59fceb
  0x0059fccd  ba 00 04 00 00    mov edx, 0x400
  0x0059fcd2  c7 44 24 24 00 03 00 00  mov dword ptr [esp + 0x24], 0x300
  0x0059fcda  eb 13             jmp 0x59fcef
  0x0059fcdc  ba 20 03 00 00    mov edx, 0x320
  0x0059fce1  c7 44 24 24 58 02 00 00  mov dword ptr [esp + 0x24], 0x258
  0x0059fce9  eb 04             jmp 0x59fcef
  0x0059fceb  8b 54 24 24       mov edx, dword ptr [esp + 0x24]
  0x0059fcef  8d be e8 00 00 00  lea edi, [esi + 0xe8]
  0x0059fcf5  33 c0             xor eax, eax
  0x0059fcf7  33 c9             xor ecx, ecx
  0x0059fcf9  8b ef             mov ebp, edi
  0x0059fcfb  89 45 00          mov dword ptr [ebp], eax
  0x0059fcfe  8b 44 24 24       mov eax, dword ptr [esp + 0x24]
  0x0059fd02  89 4d 04          mov dword ptr [ebp + 4], ecx
  0x0059fd05  8b 4e 08          mov ecx, dword ptr [esi + 8]
  0x0059fd08  89 55 08          mov dword ptr [ebp + 8], edx
  0x0059fd0b  57                push edi
  0x0059fd0c  89 45 0c          mov dword ptr [ebp + 0xc], eax
  0x0059fd0f  e8 7c f9 fe ff    call 0x58f690
  0x0059fd14  8b 0d 68 b9 82 00  mov ecx, dword ptr [0x82b968]
  0x0059fd1a  53                push ebx
  0x0059fd1b  e8 50 c0 fe ff    call 0x58bd70
  0x0059fd20  8b 86 f0 00 00 00  mov eax, dword ptr [esi + 0xf0]
  0x0059fd26  8b 96 ec 00 00 00  mov edx, dword ptr [esi + 0xec]
  0x0059fd2c  8d 88 5d ff ff ff  lea ecx, [eax - 0xa3]
  0x0059fd32  89 4c 24 10       mov dword ptr [esp + 0x10], ecx
  0x0059fd36  8d 4c 24 10       lea ecx, [esp + 0x10]
  0x0059fd3a  89 44 24 18       mov dword ptr [esp + 0x18], eax
  0x0059fd3e  8b 86 f4 00 00 00  mov eax, dword ptr [esi + 0xf4]
  0x0059fd44  51                push ecx
  0x0059fd45  8b 4e 10          mov ecx, dword ptr [esi + 0x10]
  0x0059fd48  89 54 24 18       mov dword ptr [esp + 0x18], edx
  0x0059fd4c  89 44 24 20       mov dword ptr [esp + 0x20], eax
  0x0059fd50  e8 3b f9 fe ff    call 0x58f690
  0x0059fd55  8b 86 ec 00 00 00  mov eax, dword ptr [esi + 0xec]
  0x0059fd5b  8b 17             mov edx, dword ptr [edi]
  0x0059fd5d  8b 8e f0 00 00 00  mov ecx, dword ptr [esi + 0xf0]
  0x0059fd63  81 e9 85 00 00 00  sub ecx, 0x85
  0x0059fd69  89 44 24 14       mov dword ptr [esp + 0x14], eax
  0x0059fd6d  89 54 24 10       mov dword ptr [esp + 0x10], edx
  0x0059fd71  8b 96 f4 00 00 00  mov edx, dword ptr [esi + 0xf4]
  0x0059fd77  8d 44 24 10       lea eax, [esp + 0x10]
  0x0059fd7b  89 4c 24 18       mov dword ptr [esp + 0x18], ecx
  0x0059fd7f  8b 4e 0c          mov ecx, dword ptr [esi + 0xc]
  0x0059fd82  50                push eax
  0x0059fd83  89 54 24 20       mov dword ptr [esp + 0x20], edx
  0x0059fd87  e8 04 f9 fe ff    call 0x58f690
  0x0059fd8c  8b 4e 34          mov ecx, dword ptr [esi + 0x34]
  0x0059fd8f  57                push edi
  0x0059fd90  e8 fb f8 fe ff    call 0x58f690
  0x0059fd95  5f                pop edi
  0x0059fd96  5e                pop esi
  0x0059fd97  5d                pop ebp
  0x0059fd98  5b                pop ebx
  0x0059fd99  83 c4 10          add esp, 0x10
  0x0059fd9c  c2 04 00          ret 4
  0x0059fd9f  90                nop 
