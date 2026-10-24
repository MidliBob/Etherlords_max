; 01_parse_video_resolution
; file 0x2db8f..0x2dbd6  va 0x82db8f..0x82dbd6
; Чтение VideoResolution из settings.ini -> atoi -> [esi+0x28]/[esi+0x2c]. Белый список отсутствует.
  0x0082db8f  ff 6a 78         jmp       ptr [edx + 0x78]
  0x0082db92  8d 4c 24 14      lea       ecx, [esp + 0x14]
  0x0082db96  51               push      ecx
  0x0082db97  89 46 24         mov       dword ptr [esi + 0x24], eax
  0x0082db9a  8b 06            mov       eax, dword ptr [esi]
  0x0082db9c  68 3c e9 7e 00   push      0x7ee93c
  0x0082dba1  50               push      eax
  0x0082dba2  8d 4c 24 1c      lea       ecx, [esp + 0x1c]
  0x0082dba6  e8 a5 83 fd ff   call      0x805f50
  0x0082dbab  83 7c 24 18 02   cmp       dword ptr [esp + 0x18], 2
  0x0082dbb0  75 22            jne       0x82dbd4
  0x0082dbb2  8b 54 24 14      mov       edx, dword ptr [esp + 0x14]
  0x0082dbb6  8b 02            mov       eax, dword ptr [edx]
  0x0082dbb8  50               push      eax
  0x0082dbb9  e8 63 dd 2b 00   call      0xaeb921
  0x0082dbbe  89 46 28         mov       dword ptr [esi + 0x28], eax
  0x0082dbc1  8b 44 24 18      mov       eax, dword ptr [esp + 0x18]
  0x0082dbc5  8b 40 04         mov       eax, dword ptr [eax + 4]
  0x0082dbc8  50               push      eax
  0x0082dbc9  e8 53 dd 2b 00   call      0xaeb921
  0x0082dbce  83 c4 08         add       esp, 8
  0x0082dbd1  89 46 2c         mov       dword ptr [esi + 0x2c], eax
