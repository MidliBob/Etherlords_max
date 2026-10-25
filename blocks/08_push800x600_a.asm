; 08_push800x600_a
; file 0x19ab28..0x19ab50  va 0x59ab28..0x59ab50
; Дефолт SetRect(&[esi+0xe8],0,0,800,600) сайт #1.
  0x0059ab28  8b c8             mov ecx, eax
  0x0059ab2a  89 5c 24 48       mov dword ptr [esp + 0x48], ebx
  0x0059ab2e  ff 52 04          call dword ptr [edx + 4]
  0x0059ab31  68 58 02 00 00    push 0x258
  0x0059ab36  68 20 03 00 00    push 0x320
  0x0059ab3b  57                push edi
  0x0059ab3c  57                push edi
  0x0059ab3d  8d ae e8 00 00 00  lea ebp, [esi + 0xe8]
  0x0059ab43  55                push ebp
  0x0059ab44  ff 15 28 64 75 00  call dword ptr [0x756428]
  0x0059ab4a  ff 15 34 61 75 00  call dword ptr [0x756134]
