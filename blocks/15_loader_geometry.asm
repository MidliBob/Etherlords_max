; 15_loader_geometry
; file 0x18c41d..0x18c4c9  va 0x58c41d..0x58c4c9
; Лоадер Controls.reg: Left/Top/Width/Height -> SetRect(elem+0x154,{L,T,L+W,T+H}); 0x590e90 переводит в parent-relative.
  0x0058c41d  68 70 bf 7f 00    push 0x7fbf70
  0x0058c422  52                push edx
  0x0058c423  8d 4c 24 48       lea ecx, [esp + 0x48]
  0x0058c427  e8 94 93 e7 ff    call 0x4057c0
  0x0058c42c  8b f8             mov edi, eax
  0x0058c42e  83 ff ff          cmp edi, -1
  0x0058c431  0f 84 92 00 00 00  je 0x58c4c9
  0x0058c437  8b 44 24 10       mov eax, dword ptr [esp + 0x10]
  0x0058c43b  6a 00             push 0
  0x0058c43d  68 6c bf 7f 00    push 0x7fbf6c
  0x0058c442  50                push eax
  0x0058c443  8d 4c 24 48       lea ecx, [esp + 0x48]
  0x0058c447  e8 74 93 e7 ff    call 0x4057c0
  0x0058c44c  8b 4c 24 10       mov ecx, dword ptr [esp + 0x10]
  0x0058c450  6a 00             push 0
  0x0058c452  68 64 bf 7f 00    push 0x7fbf64
  0x0058c457  51                push ecx
  0x0058c458  8d 4c 24 48       lea ecx, [esp + 0x48]
  0x0058c45c  8b f0             mov esi, eax
  0x0058c45e  e8 5d 93 e7 ff    call 0x4057c0
  0x0058c463  8b 54 24 10       mov edx, dword ptr [esp + 0x10]
  0x0058c467  6a 00             push 0
  0x0058c469  68 5c bf 7f 00    push 0x7fbf5c
  0x0058c46e  52                push edx
  0x0058c46f  8d 4c 24 48       lea ecx, [esp + 0x48]
  0x0058c473  8b e8             mov ebp, eax
  0x0058c475  e8 46 93 e7 ff    call 0x4057c0
  0x0058c47a  03 c6             add eax, esi
  0x0058c47c  89 84 24 9c 00 00 00  mov dword ptr [esp + 0x9c], eax
  0x0058c483  8d 84 24 90 00 00 00  lea eax, [esp + 0x90]
  0x0058c48a  03 ef             add ebp, edi
  0x0058c48c  50                push eax
  0x0058c48d  8b cb             mov ecx, ebx
  0x0058c48f  89 bc 24 94 00 00 00  mov dword ptr [esp + 0x94], edi
  0x0058c496  89 ac 24 9c 00 00 00  mov dword ptr [esp + 0x9c], ebp
  0x0058c49d  89 b4 24 98 00 00 00  mov dword ptr [esp + 0x98], esi
  0x0058c4a4  e8 e7 31 00 00    call 0x58f690
  0x0058c4a9  8b 43 34          mov eax, dword ptr [ebx + 0x34]
  0x0058c4ac  85 c0             test eax, eax
  0x0058c4ae  74 19             je 0x58c4c9
  0x0058c4b0  8b 88 58 01 00 00  mov ecx, dword ptr [eax + 0x158]
  0x0058c4b6  8b 80 54 01 00 00  mov eax, dword ptr [eax + 0x154]
  0x0058c4bc  f7 d9             neg ecx
  0x0058c4be  51                push ecx
  0x0058c4bf  f7 d8             neg eax
  0x0058c4c1  50                push eax
  0x0058c4c2  8b cb             mov ecx, ebx
  0x0058c4c4  e8 c7 49 00 00    call 0x590e90
