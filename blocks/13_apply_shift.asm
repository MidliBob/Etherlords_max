; 13_apply_shift
; file 0x191190..0x1911f0  va 0x591190..0x5911f0
; ApplyShift(elem): rec1.X+=rec1.sX; rec1.Y+=rec1.sY; детям OffsetRecord(child,1,sX,sY).
  0x00591190  53                push ebx
  0x00591191  55                push ebp
  0x00591192  56                push esi
  0x00591193  8b f1             mov esi, ecx
  0x00591195  8b 9e a4 01 00 00  mov ebx, dword ptr [esi + 0x1a4]
  0x0059119b  8b ae a8 01 00 00  mov ebp, dword ptr [esi + 0x1a8]
  0x005911a1  8b 96 a0 01 00 00  mov edx, dword ptr [esi + 0x1a0]
  0x005911a7  57                push edi
  0x005911a8  8b be 9c 01 00 00  mov edi, dword ptr [esi + 0x19c]
  0x005911ae  8b c3             mov eax, ebx
  0x005911b0  03 f8             add edi, eax
  0x005911b2  8b cd             mov ecx, ebp
  0x005911b4  03 d1             add edx, ecx
  0x005911b6  89 be 9c 01 00 00  mov dword ptr [esi + 0x19c], edi
  0x005911bc  89 96 a0 01 00 00  mov dword ptr [esi + 0x1a0], edx
  0x005911c2  8b 46 48          mov eax, dword ptr [esi + 0x48]
  0x005911c5  33 ff             xor edi, edi
  0x005911c7  85 c0             test eax, eax
  0x005911c9  7e 17             jle 0x5911e2
  0x005911cb  8b 46 44          mov eax, dword ptr [esi + 0x44]
  0x005911ce  8b 0c b8          mov ecx, dword ptr [eax + edi*4]
  0x005911d1  55                push ebp
  0x005911d2  53                push ebx
  0x005911d3  6a 01             push 1
  0x005911d5  e8 16 00 00 00    call 0x5911f0
  0x005911da  8b 46 48          mov eax, dword ptr [esi + 0x48]
  0x005911dd  47                inc edi
  0x005911de  3b f8             cmp edi, eax
  0x005911e0  7c e9             jl 0x5911cb
  0x005911e2  5f                pop edi
  0x005911e3  5e                pop esi
  0x005911e4  5d                pop ebp
  0x005911e5  5b                pop ebx
  0x005911e6  c3                ret 
  0x005911e7  90                nop 
  0x005911e8  90                nop 
  0x005911e9  90                nop 
  0x005911ea  90                nop 
  0x005911eb  90                nop 
  0x005911ec  90                nop 
  0x005911ed  90                nop 
  0x005911ee  90                nop 
  0x005911ef  90                nop 
