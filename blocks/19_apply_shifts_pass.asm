; 19_apply_shifts_pass
; file 0x18ca30..0x18ca88  va 0x58ca30..0x58ca88
; Пост-проход загрузки: ApplyShift(0x591190) для каждого элемента плоского списка менеджера.
  0x0058ca30  51                push ecx
  0x0058ca31  57                push edi
  0x0058ca32  8b f9             mov edi, ecx
  0x0058ca34  8b 0f             mov ecx, dword ptr [edi]
  0x0058ca36  c7 44 24 04 00 00 00 00  mov dword ptr [esp + 4], 0
  0x0058ca3e  8b 41 08          mov eax, dword ptr [ecx + 8]
  0x0058ca41  3b c1             cmp eax, ecx
  0x0058ca43  89 44 24 04       mov dword ptr [esp + 4], eax
  0x0058ca47  74 3f             je 0x58ca88
  0x0058ca49  53                push ebx
  0x0058ca4a  8b 1d 20 64 75 00  mov ebx, dword ptr [0x756420]
  0x0058ca50  56                push esi
  0x0058ca51  8b 70 1c          mov esi, dword ptr [eax + 0x1c]
  0x0058ca54  8b ce             mov ecx, esi
  0x0058ca56  e8 35 47 00 00    call 0x591190
  0x0058ca5b  8d 86 54 01 00 00  lea eax, [esi + 0x154]
  0x0058ca61  50                push eax
  0x0058ca62  ff d3             call ebx
  0x0058ca64  85 c0             test eax, eax
  0x0058ca66  74 07             je 0x58ca6f
  0x0058ca68  8b ce             mov ecx, esi
  0x0058ca6a  e8 41 43 00 00    call 0x590db0
  0x0058ca6f  8d 4c 24 0c       lea ecx, [esp + 0xc]
  0x0058ca73  51                push ecx
  0x0058ca74  e8 27 87 13 00    call 0x6c51a0
  0x0058ca79  8b 44 24 10       mov eax, dword ptr [esp + 0x10]
  0x0058ca7d  8b 0f             mov ecx, dword ptr [edi]
  0x0058ca7f  83 c4 04          add esp, 4
  0x0058ca82  3b c1             cmp eax, ecx
  0x0058ca84  75 cb             jne 0x58ca51
  0x0058ca86  5e                pop esi
  0x0058ca87  5b                pop ebx
