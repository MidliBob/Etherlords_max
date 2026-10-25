; 05_apply_flag
; file 0x18bd70..0x18be08  va 0x58bd70..0x58be08
; apply_flag(mgr,flag): flag->бит (0->1,1->2,2->4,3->8) в нижний nibble [elem+0x14c]; обход кругового списка [mgr]->head,[node+8],elem=[node+0x1c]; relayout(elem,flag).
  0x0058bd70  53                push ebx
  0x0058bd71  8b 5c 24 08       mov ebx, dword ptr [esp + 8]
  0x0058bd75  83 fb 03          cmp ebx, 3
  0x0058bd78  56                push esi
  0x0058bd79  57                push edi
  0x0058bd7a  8b f9             mov edi, ecx
  0x0058bd7c  77 23             ja 0x58bda1
  0x0058bd7e  ff 24 9d f8 bd 58 00  jmp dword ptr [ebx*4 + 0x58bdf8]
  0x0058bd85  be 01 00 00 00    mov esi, 1
  0x0058bd8a  eb 19             jmp 0x58bda5
  0x0058bd8c  be 02 00 00 00    mov esi, 2
  0x0058bd91  eb 12             jmp 0x58bda5
  0x0058bd93  be 04 00 00 00    mov esi, 4
  0x0058bd98  eb 0b             jmp 0x58bda5
  0x0058bd9a  be 08 00 00 00    mov esi, 8
  0x0058bd9f  eb 04             jmp 0x58bda5
  0x0058bda1  8b 74 24 10       mov esi, dword ptr [esp + 0x10]
  0x0058bda5  8b 0f             mov ecx, dword ptr [edi]
  0x0058bda7  c7 44 24 10 00 00 00 00  mov dword ptr [esp + 0x10], 0
  0x0058bdaf  8b 41 08          mov eax, dword ptr [ecx + 8]
  0x0058bdb2  3b c1             cmp eax, ecx
  0x0058bdb4  89 44 24 10       mov dword ptr [esp + 0x10], eax
  0x0058bdb8  74 38             je 0x58bdf2
  0x0058bdba  8b 40 1c          mov eax, dword ptr [eax + 0x1c]
  0x0058bdbd  8b 88 4c 01 00 00  mov ecx, dword ptr [eax + 0x14c]
  0x0058bdc3  83 e1 f0          and ecx, 0xfffffff0
  0x0058bdc6  0b ce             or ecx, esi
  0x0058bdc8  89 88 4c 01 00 00  mov dword ptr [eax + 0x14c], ecx
  0x0058bdce  8b 54 24 10       mov edx, dword ptr [esp + 0x10]
  0x0058bdd2  8b 4a 1c          mov ecx, dword ptr [edx + 0x1c]
  0x0058bdd5  53                push ebx
  0x0058bdd6  e8 75 54 00 00    call 0x591250
  0x0058bddb  8d 44 24 10       lea eax, [esp + 0x10]
  0x0058bddf  50                push eax
  0x0058bde0  e8 bb 93 13 00    call 0x6c51a0
  0x0058bde5  8b 44 24 14       mov eax, dword ptr [esp + 0x14]
  0x0058bde9  8b 0f             mov ecx, dword ptr [edi]
  0x0058bdeb  83 c4 04          add esp, 4
  0x0058bdee  3b c1             cmp eax, ecx
  0x0058bdf0  75 c8             jne 0x58bdba
  0x0058bdf2  5f                pop edi
  0x0058bdf3  5e                pop esi
  0x0058bdf4  5b                pop ebx
  0x0058bdf5  c2 04 00          ret 4
  0x0058bdf8  85 bd 58 00 8c bd  test dword ptr [ebp - 0x4273ffa8], edi
  0x0058bdfe  58                pop eax
  0x0058bdff  00 93 bd 58 00 9a  add byte ptr [ebx - 0x65ffa743], dl
