# work/ — рабочее пространство автора (НЕ требуется для tools/)

Отслеживаемое содержимое каталога в репозитории — этот README и хелпер `disasm.py`.
Исторические сборки и кэши анализа **исключены из репозитория** в 0.0.6
(untrack-коммит `4a15a78`: на диске автора остались, в истории git — тоже;
`.gitignore` не даёт `git add -A` вернуть их в индекс).

- `disasm.py` — хелпер capstone-листингов по VA: `python3 work/disasm.py 0x58f690 [кол-во]`
  (запуск из любого каталога — пути выводятся от расположения скрипта). Использует
  кэш `work/insns.pkl`, если он есть; иначе дизассемблирует exe напрямую. Exe ищется
  по порядку: `reference/Etherlords.exe`, `../Etherlords_max/reference/Etherlords.exe`,
  `$EL_EXE` (env). Ни того ни другого нет — подсказка в stderr.
- `insns.pkl` (~43 МБ, полный дизассемблер .text), `xrefs.pkl` (~3 МБ), `vtbls.pkl` —
  кэши статического анализа. Инструментам `tools/` НЕ нужны; блоки регенерируются
  `tools/dump_blocks.py` из любой копии билда `409d3e08…`. Достать из истории:
  `git checkout cabb35c -- work/insns.pkl && git restore --staged work/insns.pkl`.
- `Etherlords_native_v3.exe`, `Etherlords_native_v4.exe` — исторические полевые сборки
  (материал post-mortem v4, docs/09 «Дополнение v4→v5»); из истории:
  `git checkout cabb35c -- work/Etherlords_native_v3.exe`. Актуальный собиратель —
  `tools/patch_native_v3.py` (release v6).
