; 06_aspect_4_3
; file 0x46f28..0x46f60  va 0x446f28..0x446f60
; push 0x3faaaaab (4/3) -> аргумент построения матрицы/вьюпорта.
  0x00446f28  ec                in al, dx
  0x00446f29  8b 4b 08          mov ecx, dword ptr [ebx + 8]
  0x00446f2c  50                push eax
  0x00446f2d  8b 45 e4          mov eax, dword ptr [ebp - 0x1c]
  0x00446f30  52                push edx
  0x00446f31  68 ab aa aa 3f    push 0x3faaaaab
  0x00446f36  50                push eax
  0x00446f37  8d 55 88          lea edx, [ebp - 0x78]
  0x00446f3a  52                push edx
  0x00446f3b  e8 c0 8d fd ff    call 0x41fd00
  0x00446f40  8b 53 08          mov edx, dword ptr [ebx + 8]
  0x00446f43  8b 42 48          mov eax, dword ptr [edx + 0x48]
  0x00446f46  85 c0             test eax, eax
  0x00446f48  75 16             jne 0x446f60
  0x00446f4a  8b 7a 44          mov edi, dword ptr [edx + 0x44]
  0x00446f4d  b9 10 00 00 00    mov ecx, 0x10
  0x00446f52  8d 75 88          lea esi, [ebp - 0x78]
  0x00446f55  c7 42 48 01 00 00 00  mov dword ptr [edx + 0x48], 1
  0x00446f5c  f3 a5             rep movsd dword ptr es:[edi], dword ptr [esi]
  0x00446f5e  eb 20             jmp 0x446f80
