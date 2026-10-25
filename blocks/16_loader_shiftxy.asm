; 16_loader_shiftxy
; file 0x18c905..0x18c944  va 0x58c905..0x58c944
; Лоадер Controls.reg: ShiftX/ShiftY -> SetShift(elem,1,ShiftX,ShiftY) = record[1].sX/sY.
  0x0058c905  8b 54 24 10       mov edx, dword ptr [esp + 0x10]
  0x0058c909  6a 00             push 0
  0x0058c90b  68 e8 be 7f 00    push 0x7fbee8
  0x0058c910  52                push edx
  0x0058c911  8d 4c 24 48       lea ecx, [esp + 0x48]
  0x0058c915  e8 a6 8e e7 ff    call 0x4057c0
  0x0058c91a  6a 00             push 0
  0x0058c91c  8b f0             mov esi, eax
  0x0058c91e  8b 44 24 14       mov eax, dword ptr [esp + 0x14]
  0x0058c922  68 e0 be 7f 00    push 0x7fbee0
  0x0058c927  50                push eax
  0x0058c928  8d 4c 24 48       lea ecx, [esp + 0x48]
  0x0058c92c  e8 8f 8e e7 ff    call 0x4057c0
  0x0058c931  85 f6             test esi, esi
  0x0058c933  75 04             jne 0x58c939
  0x0058c935  85 c0             test eax, eax
  0x0058c937  74 0b             je 0x58c944
  0x0058c939  50                push eax
  0x0058c93a  56                push esi
  0x0058c93b  6a 01             push 1
  0x0058c93d  8b cb             mov ecx, ebx
  0x0058c93f  e8 2c 48 00 00    call 0x591170
