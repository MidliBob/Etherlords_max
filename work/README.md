# work/ — рабочее пространство автора (НЕ требуется для tools/)

- `Etherlords_native_v3.exe`, `Etherlords_native_v4.exe` — исторические полевые
  сборки (материал post-mortem v4, docs/09 «Дополнение v4→v5»). Актуальный
  собиратель — `tools/patch_native_v3.py` (release v6).
- `disasm.py` — хелпер capstone-листингов по VA:
  `python3 work/disasm.py 0x58f690 [кол-во]`; использует кэш `work/insns.pkl` и
  `reference/Etherlords.exe` (путь в скрипте `../Etherlords_max/reference/...` —
  запускать из корня репозитория, клон должен называться `Etherlords_max`).
- `insns.pkl` (~43 МБ), `xrefs.pkl` (~3 МБ), `vtbls.pkl` — кэши статического
  анализа (полный дизассемблер .text, xref'ы, vtable'и). Инструментам `tools/`
  НЕ нужны; можно удалить локально — на воспроизводимость блоков/патчей это не
  влияет (блоки regenerируются `tools/dump_blocks.py` из `reference/Etherlords.exe`).
