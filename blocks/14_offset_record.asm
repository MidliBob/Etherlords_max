; 14_offset_record
; file 0x1911f0..0x191250  va 0x5911f0..0x591250
; OffsetRecord(elem,flag,dx,dy): record[flag].X+=dx,.Y+=dy; рекурсия в детей (+0x44/+0x48).
  0x005911f0  53                push ebx
  0x005911f1  8b 5c 24 08       mov ebx, dword ptr [esp + 8]
  0x005911f5  55                push ebp
  0x005911f6  8b 6c 24 10       mov ebp, dword ptr [esp + 0x10]
  0x005911fa  56                push esi
  0x005911fb  8b f1             mov esi, ecx
  0x005911fd  8b 4c 24 18       mov ecx, dword ptr [esp + 0x18]
  0x00591201  8b c3             mov eax, ebx
  0x00591203  c1 e0 04          shl eax, 4
  0x00591206  8b 94 30 90 01 00 00  mov edx, dword ptr [eax + esi + 0x190]
  0x0059120d  8d 84 30 8c 01 00 00  lea eax, [eax + esi + 0x18c]
  0x00591214  57                push edi
  0x00591215  8b 38             mov edi, dword ptr [eax]
  0x00591217  03 fd             add edi, ebp
  0x00591219  03 d1             add edx, ecx
  0x0059121b  89 38             mov dword ptr [eax], edi
  0x0059121d  89 50 04          mov dword ptr [eax + 4], edx
  0x00591220  8b 46 48          mov eax, dword ptr [esi + 0x48]
  0x00591223  33 ff             xor edi, edi
  0x00591225  85 c0             test eax, eax
  0x00591227  7e 1a             jle 0x591243
  0x00591229  8b 54 24 1c       mov edx, dword ptr [esp + 0x1c]
  0x0059122d  8b 46 44          mov eax, dword ptr [esi + 0x44]
  0x00591230  8b 0c b8          mov ecx, dword ptr [eax + edi*4]
  0x00591233  52                push edx
  0x00591234  55                push ebp
  0x00591235  53                push ebx
  0x00591236  e8 b5 ff ff ff    call 0x5911f0
  0x0059123b  8b 46 48          mov eax, dword ptr [esi + 0x48]
  0x0059123e  47                inc edi
  0x0059123f  3b f8             cmp edi, eax
  0x00591241  7c e6             jl 0x591229
  0x00591243  5f                pop edi
  0x00591244  5e                pop esi
  0x00591245  5d                pop ebp
  0x00591246  5b                pop ebx
  0x00591247  c2 0c 00          ret 0xc
  0x0059124a  90                nop 
  0x0059124b  90                nop 
  0x0059124c  90                nop 
  0x0059124d  90                nop 
  0x0059124e  90                nop 
  0x0059124f  90                nop 
