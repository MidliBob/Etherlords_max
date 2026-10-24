"""
!!! ВНИМАНИЕ: v1 ДАЁТ РЕГРЕССИЮ (мёртвые кнопки). Не применять.
!!! Оставлен как разбор ошибки: подмена rect рассинхронизирует hit-test и baked-таблицу.
!!! См. docs/06_hit_test_model.md и docs/07_native_v1_regression.md.
import struct
SRC="Etherlords.exe"; DST="Etherlords_native.exe"
data=bytearray(open(SRC,"rb").read())
VA2F=lambda va: va-0x800000
CAVE=0xb55656
def put(va, bs):
    f=VA2F(va); data[f:f+len(bs)]=bs

# --- B: неизвестное разрешение -> форсируем раскладку flag=1 (jmp на push 1 @0x99bd4e) ---
put(0x0099bd4c, b"\xeb\x00")   # jne bd6a -> jmp bd4e  (w==1024, h!=768)
put(0x0099bd58, b"\xeb\xf4")   # jne bd6a -> jmp bd4e  (w!=800)
put(0x0099bd5f, b"\xeb\xed")   # jne bd6a -> jmp bd4e  (w==800, h!=600)

# --- A: трамплин: реальные W/H из цепочки режима вместо 1024/768 ---
t  = b"\xa1\xe8\x5d\x82\x00"   # mov eax,[0x825de8]
t += b"\x8b\x40\x18"           # mov eax,[eax+0x18]
t += b"\x8b\x50\x14"           # mov edx,[eax+0x14]   (W)
t += b"\x8b\x48\x18"           # mov ecx,[eax+0x18]   (H)
t += b"\x89\x4c\x24\x24"       # mov [esp+0x24],ecx
t += b"\xe9" + struct.pack("<i", 0x0099fcda - (CAVE + len(t) + 5))
put(CAVE, t)

# --- хук ветки flag==1 (mov edx,0x400) на трамплин ---
site=0x0099fccd
put(site, b"\xe9" + struct.pack("<i", CAVE - (site+5)))

open(DST,"wb").write(bytes(data))
print("wrote", DST, len(data))
