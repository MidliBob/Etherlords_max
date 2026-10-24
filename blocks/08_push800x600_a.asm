; 08_push800x600_a
; file 0x19ab28..0x19ab50  va 0x99ab28..0x99ab50
; Дефолт f(...,800,600) сайт #1.
  0x0099ab28  8b c8            mov       ecx, eax
  0x0099ab2a  89 5c 24 48      mov       dword ptr [esp + 0x48], ebx
  0x0099ab2e  ff 52 04         call      dword ptr [edx + 4]
  0x0099ab31  68 58 02 00 00   push      0x258
  0x0099ab36  68 20 03 00 00   push      0x320
  0x0099ab3b  57               push      edi
  0x0099ab3c  57               push      edi
  0x0099ab3d  8d ae e8 00 00 00 lea       ebp, [esi + 0xe8]
  0x0099ab43  55               push      ebp
  0x0099ab44  ff 15 28 64 75 00 call      dword ptr [0x756428]
  0x0099ab4a  ff 15 34 61 75 00 call      dword ptr [0x756134]
