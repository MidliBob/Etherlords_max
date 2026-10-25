# Native v2 — реализация: хуки, code cave, верификация

Статус: **собиратель готов и верифицирован** (`tools/patch_native_v2.py`), ожидает
runtime-приемку на Windows (протокол — §6). План — docs/07 §6.2; модель
согласованности draw/hover/click — docs/04; урок v1 — docs/05.

Сборка (из корня репозитория, нужен ваш `Etherlords.exe` билда `409d3e08…`):

```bash
pip install pefile capstone
python3 tools/patch_native_v2.py /путь/к/Etherlords.exe --out Etherlords_native_v2.exe
```

Эталонная сборка из `reference/Etherlords.exe`: sha256 `868aed683f8b3809a86b37ddb60968a036a3699181e8790f963ced05fe643d63`.

---

## 1. Карта правок (4 группы, все — file-оффсеты билда 409d3e08…)

| # | что | site VA (file) | байты сайта | замена |
|---|---|---|---|---|
| P1a/b/c | форс `apply_layout(1)` при любом разрешении | 0x59bd4c/0x59bd58/0x59bd5f (0x19bd4c/58/5f) | `75 1c`/`75 10`/`75 09` | `eb 00`/`eb f4`/`eb ed` (как patch_layout.py) |
| H1 | трамплин живых W/H вместо immediate 1024/768 (ветка flag=1) | 0x59fccd (0x19fccd) | `ba 00 04 00 00` | `jmp trampA` (5 байт, nop не нужен) |
| H2 | пост-проход масштабирования контролов после `apply_flag` | 0x59fd20 (0x19fd20) | `8b 86 f0 00 00 00` | `jmp post_scale` + `nop` |
| H3 | mask-fix hit-test: dx/dy обратно в design-пространство | 0x58fcf6 (0x18fcf6) | `0f af 9e 84 01 00 00` | `jmp maskfix` + 2×`nop` |

Code cave: file `0x355656..0x356000` (VA `0x755656..0x756000`, нули в raw .text).
Занято 669 из 2474 байт:

| блок | VA | file | размер | назначение |
|---|---|---|---|---|
| trampA | 0x755656 | 0x355656 | 57 | H1: W,H = `[0x825de8]->+0x18->{+0x14,+0x18}`; null-guard → фолбэк 1024/768; возврат 0x59fcda |
| post_scale | 0x755696 | 0x355696 | 414 | H2: обход списка `[0x82b968]` (итератор 0x6c51a0, паттерн apply_flag), масштабирование RECT'ов/active/визуала; возврат 0x59fd26 |
| scale_rect | 0x755836 | 0x355836 | 63 | подпрограмма: RECT{L,T,R,B}: L,R = L,R*W/baseW; T,B = T,B*H/baseH (idiv, trunc) |
| maskfix | 0x755876 | 0x355876 | 125 | H3: dx = dx*baseW/W, dy = dy*baseH/H перед `imul [esi+0x184]`; возврат 0x58fd01 |

## 2. Что именно масштабируется (и что НЕ)

Пост-проход (H2) выполняется внутри `apply_layout` сразу после `apply_flag`, когда
все контролы уже переведены в профиль flag (relayout + OnLayoutChange отработали),
а экранные rect'ы `[screen+0xe8]` уже содержат живые W/H (результат H1).
Источник W/H для масштаба — `[screen+0xf0]/[screen+0xf4]` (right/bottom экранного
rect'а); base = (800,600) при flag==0, иначе (1024,768). **При W==baseW && H==baseH
проход пропускается** (k=1 тождественно; в т.ч. поэтому 1024x768 и 800x600 остаются
нетронутыми — оригинальное поведение).

Масштабируется (на каждый элемент списка `[0x82b968]`):

| поле | смысл | почему |
|---|---|---|
| RECT +0x154 | геометрия parent-relative | hit-test (цепочка родителей), клиппинг; abs = Σ relative — масштабирование звеньев согласованно по цепочке |
| RECT +0x164 | абсолютный кэш | hit-test когда нет маски |
| RECT +0x174 | локальный rect маски | маска hit-test (база abs — цепочка +0x154/+0x158 родителей) |
| active +0x1ac/+0x1b0 | X,Y «активной точки» | позиционирование игровых экранов/HUD от active |
| визуал +0x148 → для каждого subnode: `[[subnode+0x10]+0x40]` и `[+0x18]` | экранные rect'ы спрайтов (включая текст — Txt-rect хранится там же) | это ровно те два rect'а, которые сдвигает `visual->Offset` (0x58a5d0) при relayout — потребители отрисовки |

НЕ трогаются:

| поле | почему |
|---|---|
| record[0/1] +0x18c/+0x19c (включая sX/sY) и active sX/sY +0x1b4/+0x1b8 | данные профилей, источник дельт relayout; масштабирование сломало бы идемпотентность переключений |
| маска +0x150 и stride +0x184 | битовая карта design-размера; вместо её перерисовки H3 делит dx/dy обратно (пиксельная точность сохраняется) |
| `[[subnode+0x10]+0x30]` | source-rect выборки из текстуры — Offset его не сдвигает, значит не экранный |
| 4 экранных rect'а менеджера и полосы (W−163)/(W−133) | они и так получают живые W/H через H1 (пересчитываются после точки H2) |

Регистровая дисциплина H2: `pushad/popad` — контекст `apply_layout` (esi=screen,
ebx=flag, edi/ebp) сохраняется полностью; в конце выполняется украденная инструкция
`mov eax,[esi+0xf0]`. H3: портятся только eax/ecx/edx (мертвы в точке хука —
перезаписываются на 0x58fd01/0x58fd07), ebx/ecx несут результат, ebp/edi/esi целы.

## 3. Почему три потребителя теперь согласованы (инвариант docs/04)

- **draw**: визуал-rect'ы (+0x40/+0x18) и active — масштабированы в native.
- **hover/click**: hit-test читает +0x154/+0x164/+0x174 и цепочку родителей —
  те же масштабированные поля; mask-путь получает dx/dy в design-пространстве (H3).
- **живые поверхности** (миникарта и т.п.): читают live viewport (0x5a0070) — native.
- Экранные rect'ы `[screen+0xe8..]` = живые W/H (H1) → rect == baked в native.

Все три потребителя сходятся в одних точках: критерий приемки docs/04/06
(«нарисованное там, где раньше была hover-подсветка») должен выполняться.

## 4. Верификация сборки (встроена в собиратель, запускается всегда)

1. **Контрольные байты** всех 6 сайтов (P1a..c, H1..H3) — чужой билд не патчится.
2. **Capstone-аудит cave**: 167 инструкций декодируются без остатка; цели всех
   ветвлений — только разрешённый набор (внутри cave, 0x6c51a0, точки возврата).
3. **Аудит диффа**: изменены ТОЛЬКО байты сайтов и занятая часть cave (567 байт);
   любые другие изменения — abort.
4. **Функциональные тесты T1–T4** на встроенном интерпретаторе i386-подмножества
   (декодирование capstone, семантика на Python; без внешних зависимостей):
   исполняются НАСТОЯЩИЕ байты cave на синтетических структурах.
   Итератор 0x6c51a0 в тестовом образе — заглушка `slot=[slot+8]` (протокол вызова
   push&slot/call/add esp,4 и обработка слота — те же, что в apply_flag).

| тест | что проверяет | результат |
|---|---|---|
| T1 trampA | живые W/H=1600x900 → edx/[esp+0x24]; null-режим → фолбэк 1024/768 | OK |
| T2 maskfix | nib=2: dx 300→192, dy 100→85(*stride 20=1700); nib=1: 150/66(*20=1320); ebp сохранён | OK |
| T3 post_scale | обход 2 контролов: rect'ы {100,50,300,150}→{156,58,468,175}; mask-rect {0,0,64,64}→{0,0,100,75}; active {10,20,..}→{15,23,..}; records ЦЕЛЫ; визуал {10,10,110,60}→{15,11,171,70} (оба rect'а), source +0x30 ЦЕЛ; esp/edi/ebp/ebx/esi сохранены (pushad/popad); украденный mov eax=1600 | OK (316 шагов) |
| T4 identity | W,H==base → проход пропущен, rect'ы не тронуты | OK |

## 5. Известные риски / допущения (чем платить за непроверенный runtime)

1. **Однократность apply_layout за процесс.** Пост-проход не идемпотентен
   (масштабирует накопительные RECT'ы). Он безопасен, пока `apply_layout` вызывается
   один раз из `CScreenManager::Init` (единственный caller mode_check 0x59bd65), с
   предшествующей перезагрузкой Controls.reg (свежие design-координаты). Если игра
   где-то дёргает Init повторно БЕЗ перезагрузки контролов — будет двойной масштаб
   (лечится флагом однократности в cave; ждём результатов полевых испытаний).
2. **Клоны контролов, созданные после Init** (callers SetShift из лоадера/клонов),
   в список на момент пост-прохода не входят → останутся в design-координатах.
   Если в игре есть динамически создаваемые диалоги/элементы — они могут встать не
   там. Выявляется скриншотами; лечение — хук на attach-в-список либо повторный
   мини-проход по событию.
3. **Фон главного меню** (нативная текстура 1024x768) — отдельный путь (docs/04 §3):
   может растянуться/остаться в углу; к hit-test кнопок это не относится.
4. **Округление**: idiv trunc к нулю — рассогласование границ ±1 px между элементами
   возможно; на критерий приемки не влияет.
5. **H3 при profile-бите 0** (не должно возникать после Init) — по умолчанию base 1024x768.
6. Флаг 2/3 `apply_layout` (jump-table допускает) — не возникает: mode_check пушит
   только 0/1.

## 6. Протокол приемки на Windows (ваша сторона)

1. Бэкап `Etherlords.exe`.
2. `python3 tools/patch_native_v2.py Etherlords.exe` → `Etherlords_native_v2.exe`;
   положить вместо `Etherlords.exe`.
3. `settings.ini`: `VideoResolution=1600x900`. Запуск.
4. **Критерий (docs/04):** нарисованные кнопки стоят там, где в оригинале возникала
   hover-подсветка по периметру; hover И click срабатывают в той же зоне.
5. Скриншоты: главное меню, глобальная карта, бой (HUD + правая панель), диалог
   опций. Повторить на 2560x1440 (и, при возможности, 3840x2160).
6. Проверить: миникарта в правом верхнем, нижняя панель по низу, правая инфо-полоса
   у правого края; колесо команд — клики по секторам (маски!).
7. Регресс? Откат на бэкап; безопасный базис — `tools/patch_layout.py` (layout1024).
   Прислать: разрешение, скриншоты, что мертво/уехало — итерация по §5.

## 7. Листинг cave (capstone, эталонная сборка)

```
; ---- trampA @ VA 0x755656 (57 байт) ----
  0x00755656  a1 e8 5d 82 00            mov eax, dword ptr [0x825de8]
  0x0075565b  85 c0                     test eax, eax
  0x0075565d  0f 84 1a 00 00 00         je 0x75567d
  0x00755663  8b 40 18                  mov eax, dword ptr [eax + 0x18]
  0x00755666  85 c0                     test eax, eax
  0x00755668  0f 84 0f 00 00 00         je 0x75567d
  0x0075566e  8b 50 14                  mov edx, dword ptr [eax + 0x14]
  0x00755671  8b 48 18                  mov ecx, dword ptr [eax + 0x18]
  0x00755674  89 4c 24 24               mov dword ptr [esp + 0x24], ecx
  0x00755678  e9 5d a6 e4 ff            jmp 0x59fcda
  0x0075567d  ba 00 04 00 00            mov edx, 0x400
  0x00755682  c7 44 24 24 00 03 00 00   mov dword ptr [esp + 0x24], 0x300
  0x0075568a  e9 4b a6 e4 ff            jmp 0x59fcda

; ---- post_scale @ VA 0x755696 (414 байт) ----
  0x00755696  60                        pushal 
  0x00755697  83 ec 30                  sub esp, 0x30
  0x0075569a  8b 86 f0 00 00 00         mov eax, dword ptr [esi + 0xf0]
  0x007556a0  89 44 24 00               mov dword ptr [esp], eax
  0x007556a4  8b 86 f4 00 00 00         mov eax, dword ptr [esi + 0xf4]
  0x007556aa  89 44 24 04               mov dword ptr [esp + 4], eax
  0x007556ae  85 db                     test ebx, ebx
  0x007556b0  0f 85 15 00 00 00         jne 0x7556cb
  0x007556b6  c7 44 24 08 20 03 00 00   mov dword ptr [esp + 8], 0x320
  0x007556be  c7 44 24 0c 58 02 00 00   mov dword ptr [esp + 0xc], 0x258
  0x007556c6  e9 10 00 00 00            jmp 0x7556db
  0x007556cb  c7 44 24 08 00 04 00 00   mov dword ptr [esp + 8], 0x400
  0x007556d3  c7 44 24 0c 00 03 00 00   mov dword ptr [esp + 0xc], 0x300
  0x007556db  8b 44 24 00               mov eax, dword ptr [esp]
  0x007556df  3b 44 24 08               cmp eax, dword ptr [esp + 8]
  0x007556e3  0f 85 0e 00 00 00         jne 0x7556f7
  0x007556e9  8b 44 24 04               mov eax, dword ptr [esp + 4]
  0x007556ed  3b 44 24 0c               cmp eax, dword ptr [esp + 0xc]
  0x007556f1  0f 84 2e 01 00 00         je 0x755825
  0x007556f7  a1 68 b9 82 00            mov eax, dword ptr [0x82b968]
  0x007556fc  8b 00                     mov eax, dword ptr [eax]
  0x007556fe  89 44 24 14               mov dword ptr [esp + 0x14], eax
  0x00755702  8b 40 08                  mov eax, dword ptr [eax + 8]
  0x00755705  89 44 24 10               mov dword ptr [esp + 0x10], eax
  0x00755709  3b 44 24 14               cmp eax, dword ptr [esp + 0x14]
  0x0075570d  0f 84 12 01 00 00         je 0x755825
  0x00755713  8b 44 24 10               mov eax, dword ptr [esp + 0x10]
  0x00755717  8b 40 1c                  mov eax, dword ptr [eax + 0x1c]
  0x0075571a  89 44 24 18               mov dword ptr [esp + 0x18], eax
  0x0075571e  8d 88 54 01 00 00         lea ecx, [eax + 0x154]
  0x00755724  e8 0d 01 00 00            call 0x755836
  0x00755729  8b 44 24 18               mov eax, dword ptr [esp + 0x18]
  0x0075572d  8d 88 64 01 00 00         lea ecx, [eax + 0x164]
  0x00755733  e8 fe 00 00 00            call 0x755836
  0x00755738  8b 44 24 18               mov eax, dword ptr [esp + 0x18]
  0x0075573c  8d 88 74 01 00 00         lea ecx, [eax + 0x174]
  0x00755742  e8 ef 00 00 00            call 0x755836
  0x00755747  8b 44 24 18               mov eax, dword ptr [esp + 0x18]
  0x0075574b  8d 88 ac 01 00 00         lea ecx, [eax + 0x1ac]
  0x00755751  8b 01                     mov eax, dword ptr [ecx]
  0x00755753  0f af 44 24 00            imul eax, dword ptr [esp]
  0x00755758  99                        cdq 
  0x00755759  f7 7c 24 08               idiv dword ptr [esp + 8]
  0x0075575d  89 01                     mov dword ptr [ecx], eax
  0x0075575f  8b 41 04                  mov eax, dword ptr [ecx + 4]
  0x00755762  0f af 44 24 04            imul eax, dword ptr [esp + 4]
  0x00755767  99                        cdq 
  0x00755768  f7 7c 24 0c               idiv dword ptr [esp + 0xc]
  0x0075576c  89 41 04                  mov dword ptr [ecx + 4], eax
  0x0075576f  8b 44 24 18               mov eax, dword ptr [esp + 0x18]
  0x00755773  8b 80 48 01 00 00         mov eax, dword ptr [eax + 0x148]
  0x00755779  85 c0                     test eax, eax
  0x0075577b  0f 84 89 00 00 00         je 0x75580a
  0x00755781  8b 00                     mov eax, dword ptr [eax]
  0x00755783  89 44 24 1c               mov dword ptr [esp + 0x1c], eax
  0x00755787  8b 40 08                  mov eax, dword ptr [eax + 8]
  0x0075578a  89 44 24 20               mov dword ptr [esp + 0x20], eax
  0x0075578e  3b 44 24 1c               cmp eax, dword ptr [esp + 0x1c]
  0x00755792  0f 84 72 00 00 00         je 0x75580a
  0x00755798  8b 44 24 20               mov eax, dword ptr [esp + 0x20]
  0x0075579c  8b 40 14                  mov eax, dword ptr [eax + 0x14]
  0x0075579f  8b 00                     mov eax, dword ptr [eax]
  0x007557a1  89 44 24 24               mov dword ptr [esp + 0x24], eax
  0x007557a5  8b 40 08                  mov eax, dword ptr [eax + 8]
  0x007557a8  89 44 24 28               mov dword ptr [esp + 0x28], eax
  0x007557ac  3b 44 24 24               cmp eax, dword ptr [esp + 0x24]
  0x007557b0  0f 84 39 00 00 00         je 0x7557ef
  0x007557b6  8b 44 24 28               mov eax, dword ptr [esp + 0x28]
  0x007557ba  8b 40 10                  mov eax, dword ptr [eax + 0x10]
  0x007557bd  8d 48 40                  lea ecx, [eax + 0x40]
  0x007557c0  e8 71 00 00 00            call 0x755836
  0x007557c5  8b 44 24 28               mov eax, dword ptr [esp + 0x28]
  0x007557c9  8b 40 10                  mov eax, dword ptr [eax + 0x10]
  0x007557cc  8d 48 18                  lea ecx, [eax + 0x18]
  0x007557cf  e8 62 00 00 00            call 0x755836
  0x007557d4  8d 44 24 28               lea eax, [esp + 0x28]
  0x007557d8  50                        push eax
  0x007557d9  e8 c2 f9 f6 ff            call 0x6c51a0
  0x007557de  83 c4 04                  add esp, 4
  0x007557e1  8b 44 24 28               mov eax, dword ptr [esp + 0x28]
  0x007557e5  3b 44 24 24               cmp eax, dword ptr [esp + 0x24]
  0x007557e9  0f 85 c7 ff ff ff         jne 0x7557b6
  0x007557ef  8d 44 24 20               lea eax, [esp + 0x20]
  0x007557f3  50                        push eax
  0x007557f4  e8 a7 f9 f6 ff            call 0x6c51a0
  0x007557f9  83 c4 04                  add esp, 4
  0x007557fc  8b 44 24 20               mov eax, dword ptr [esp + 0x20]
  0x00755800  3b 44 24 1c               cmp eax, dword ptr [esp + 0x1c]
  0x00755804  0f 85 8e ff ff ff         jne 0x755798
  0x0075580a  8d 44 24 10               lea eax, [esp + 0x10]
  0x0075580e  50                        push eax
  0x0075580f  e8 8c f9 f6 ff            call 0x6c51a0
  0x00755814  83 c4 04                  add esp, 4
  0x00755817  8b 44 24 10               mov eax, dword ptr [esp + 0x10]
  0x0075581b  3b 44 24 14               cmp eax, dword ptr [esp + 0x14]
  0x0075581f  0f 85 ee fe ff ff         jne 0x755713
  0x00755825  83 c4 30                  add esp, 0x30
  0x00755828  61                        popal 
  0x00755829  8b 86 f0 00 00 00         mov eax, dword ptr [esi + 0xf0]
  0x0075582f  e9 f2 a4 e4 ff            jmp 0x59fd26

; ---- scale_rect @ VA 0x755836 (63 байт) ----
  0x00755836  8b 01                     mov eax, dword ptr [ecx]
  0x00755838  0f af 44 24 04            imul eax, dword ptr [esp + 4]
  0x0075583d  99                        cdq 
  0x0075583e  f7 7c 24 0c               idiv dword ptr [esp + 0xc]
  0x00755842  89 01                     mov dword ptr [ecx], eax
  0x00755844  8b 41 08                  mov eax, dword ptr [ecx + 8]
  0x00755847  0f af 44 24 04            imul eax, dword ptr [esp + 4]
  0x0075584c  99                        cdq 
  0x0075584d  f7 7c 24 0c               idiv dword ptr [esp + 0xc]
  0x00755851  89 41 08                  mov dword ptr [ecx + 8], eax
  0x00755854  8b 41 04                  mov eax, dword ptr [ecx + 4]
  0x00755857  0f af 44 24 08            imul eax, dword ptr [esp + 8]
  0x0075585c  99                        cdq 
  0x0075585d  f7 7c 24 10               idiv dword ptr [esp + 0x10]
  0x00755861  89 41 04                  mov dword ptr [ecx + 4], eax
  0x00755864  8b 41 0c                  mov eax, dword ptr [ecx + 0xc]
  0x00755867  0f af 44 24 08            imul eax, dword ptr [esp + 8]
  0x0075586c  99                        cdq 
  0x0075586d  f7 7c 24 10               idiv dword ptr [esp + 0x10]
  0x00755871  89 41 0c                  mov dword ptr [ecx + 0xc], eax
  0x00755874  c3                        ret 

; ---- maskfix @ VA 0x755876 (125 байт) ----
  0x00755876  8b cf                     mov ecx, edi
  0x00755878  2b c8                     sub ecx, eax
  0x0075587a  a1 e8 5d 82 00            mov eax, dword ptr [0x825de8]
  0x0075587f  85 c0                     test eax, eax
  0x00755881  0f 84 60 00 00 00         je 0x7558e7
  0x00755887  8b 40 18                  mov eax, dword ptr [eax + 0x18]
  0x0075588a  85 c0                     test eax, eax
  0x0075588c  0f 84 55 00 00 00         je 0x7558e7
  0x00755892  83 ec 08                  sub esp, 8
  0x00755895  8b 50 14                  mov edx, dword ptr [eax + 0x14]
  0x00755898  89 54 24 00               mov dword ptr [esp], edx
  0x0075589c  8b 50 18                  mov edx, dword ptr [eax + 0x18]
  0x0075589f  89 54 24 04               mov dword ptr [esp + 4], edx
  0x007558a3  8b 86 4c 01 00 00         mov eax, dword ptr [esi + 0x14c]
  0x007558a9  83 e0 0f                  and eax, 0xf
  0x007558ac  83 f8 01                  cmp eax, 1
  0x007558af  0f 84 11 00 00 00         je 0x7558c6
  0x007558b5  69 c9 00 04 00 00         imul ecx, ecx, 0x400
  0x007558bb  69 db 00 03 00 00         imul ebx, ebx, 0x300
  0x007558c1  e9 0c 00 00 00            jmp 0x7558d2
  0x007558c6  69 c9 20 03 00 00         imul ecx, ecx, 0x320
  0x007558cc  69 db 58 02 00 00         imul ebx, ebx, 0x258
  0x007558d2  8b c1                     mov eax, ecx
  0x007558d4  99                        cdq 
  0x007558d5  f7 7c 24 00               idiv dword ptr [esp]
  0x007558d9  8b c8                     mov ecx, eax
  0x007558db  8b c3                     mov eax, ebx
  0x007558dd  99                        cdq 
  0x007558de  f7 7c 24 04               idiv dword ptr [esp + 4]
  0x007558e2  8b d8                     mov ebx, eax
  0x007558e4  83 c4 08                  add esp, 8
  0x007558e7  0f af 9e 84 01 00 00      imul ebx, dword ptr [esi + 0x184]
  0x007558ee  e9 0e a4 e3 ff            jmp 0x58fd01
  capstone: 167 инструкций, все ветвления в разрешённом наборе, байт без остатка
```

Листинг воспроизводим: `python3 tools/patch_native_v2.py reference/Etherlords.exe --check --listing`.
