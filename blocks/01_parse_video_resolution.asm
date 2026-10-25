; 01_parse_video_resolution
; file 0x2db8f..0x2dbd6  va 0x42db8f..0x42dbd6
; Чтение VideoResolution из settings.ini -> atoi -> [esi+0x28]/[esi+0x2c]. Белый список отсутствует.
  0x0042db8f  ff 6a 78          jmp ptr [edx + 0x78]
  0x0042db92  8d 4c 24 14       lea ecx, [esp + 0x14]
  0x0042db96  51                push ecx
  0x0042db97  89 46 24          mov dword ptr [esi + 0x24], eax
  0x0042db9a  8b 06             mov eax, dword ptr [esi]
  0x0042db9c  68 3c e9 7e 00    push 0x7ee93c
  0x0042dba1  50                push eax
  0x0042dba2  8d 4c 24 1c       lea ecx, [esp + 0x1c]
  0x0042dba6  e8 a5 83 fd ff    call 0x405f50
  0x0042dbab  83 7c 24 18 02    cmp dword ptr [esp + 0x18], 2
  0x0042dbb0  75 22             jne 0x42dbd4
  0x0042dbb2  8b 54 24 14       mov edx, dword ptr [esp + 0x14]
  0x0042dbb6  8b 02             mov eax, dword ptr [edx]
  0x0042dbb8  50                push eax
  0x0042dbb9  e8 63 dd 2b 00    call 0x6eb921
  0x0042dbbe  89 46 28          mov dword ptr [esi + 0x28], eax
  0x0042dbc1  8b 44 24 18       mov eax, dword ptr [esp + 0x18]
  0x0042dbc5  8b 40 04          mov eax, dword ptr [eax + 4]
  0x0042dbc8  50                push eax
  0x0042dbc9  e8 53 dd 2b 00    call 0x6eb921
  0x0042dbce  83 c4 08          add esp, 8
  0x0042dbd1  89 46 2c          mov dword ptr [esi + 0x2c], eax
