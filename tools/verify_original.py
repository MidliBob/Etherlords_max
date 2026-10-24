#!/usr/bin/env python3
"""Сверка вашего Etherlords.exe с анализируемым билдом (sha256[:16])."""
import hashlib, sys
EXPECT="409d3e08499ed61c"
p=sys.argv[1] if len(sys.argv)>1 else "Etherlords.exe"
d=open(p,"rb").read(); h=hashlib.sha256(d).hexdigest()
print(f"{p}: {len(d)} bytes sha256={h}")
print("MATCH: offsets/блоки применимы" if h.startswith(EXPECT) else "НЕ совпадает: другой билд")
