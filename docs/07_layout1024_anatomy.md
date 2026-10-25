# Анатомия профиля 1024x768: что именно он меняет и как устроен интерфейс

Разбор выполнен статически по `reference/Etherlords.exe` (sha256 `409d3e08…`, рус. 1.07).
Все адреса ниже — **настоящие VA** (ImageBase 0x400000). Блоки — `blocks/10..21`
(генератор `tools/dump_blocks.py`).

---

## 0. Критическая поправка адресов (docs/04–08 и старые blocks)

Старые листинги собраны с базисом «VA = file + 0x800000». Настоящий: **VA = file + 0x400000**
(ImageBase 0x400000, у .text/.rdata/.data RVA совпадает с file offset). Следствия:

- Все **адреса инструкций** в docs/04–08 и targets rel-call/jmp в них завышены на 0x400000.
  Абсолютные операнды (`push 0x7ee93c`, `mov eax,[0x825de8]`, `call [0x756428]`) — настоящие.
- `docs/08` советует брейкпоинты `Etherlords.0098F690` / `0099FCB0` — **этих адресов не
  существует** (SizeOfImage = 0x43b000 → потолок VA 0x83b000). Настоящие: **0x58F690** (set_rect),
  **0x59FCB0** (apply_layout), **0x591250** (relayout), **0x58FB70** (hit-test).
- Блоки `03..05` были пустыми: нарезка брала «file» 0x99fcb0/0x98f690/0x98bd70 — это VA
  сдвинутого базиса, лежащие за EOF (файл 0x41D000 байт).
- **File-оффсеты патчей верны** (от базы не зависят): `patch_layout.py` (0x19bd4c/0x19bd58/
  0x19bd5f) и трамплин `patch_native.py` (site 0x19fccd, cave file 0x355656) — ложились
  корректно, поэтому эксперименты B и v1 вообще запускались.

Таблица соответствия (старый VA из docs → настоящий):

| функция | VA в docs/04–08 | настоящий VA | file |
|---|---|---|---|
| mode_check_layout | 0x99bd28 | **0x59bd28** | 0x19bd28 |
| apply_layout(flag) | 0x99fcb0 | **0x59fcb0** | 0x19fcb0 |
| set_rect | 0x98f690 | **0x58f690** | 0x18f690 |
| apply_flag | 0x98bd70 | **0x58bd70** | 0x18bd70 |
| parse VideoResolution | 0x82db92 | **0x42db92** | 0x2db92 |

---

## 1. Ответ в одном абзаце

Профиль 1024x768 не «пересчитывает» интерфейс и ничего не масштабирует. Вся раскладка —
это **дизайн-координаты из data-файла `Controls.reg`** (в архивах игры, не в exe) плюс
**персональные сдвиги `ShiftX/ShiftY` каждого контрола** для второго профиля. При
переключении профиля каждый контрол просто **сдвигается** (`OffsetRect`) на свою
накопленную дельту, а четыре экранных rect'а менеджера экрана перезаписываются
**хардкодом** (0,0,W,H), (W−163,0,W,H), (0,0,W−133,H), где W,H — 800x600 или 1024x768.
Ни одного умножения/деления на размер экрана в UI-коде нет. Поэтому при «родном»
(не 800x600/1024x768) разрешении всё и рассыпается: часть потребителей читает живые W/H
режима (поверхности/hover), часть — дизайн-координаты (отрисовка/hit-test).

---

## 2. Источник данных интерфейса — `Controls.reg`

Лоадер: `0x58be10` → `0x58be30` (блоки 21, строки `Controls.reg` @0x7fbfd8, `CutParts.reg` @0x7fc02c).
Секции нумеруются `%d`; ключи (VA строк):

| ключ | VA строки | куда пишется |
|---|---|---|
| `Name` / `Type` | 0x7f73c0 / 0x7f743c | имя; тип: Panel/Text/Edit/PushButton/AutoButton/CheckButton/RadioButton/MultyButton (0x7fbfd0..0x7fbfb4) → класс+размер объекта (`new 0x1d0` Panel, `0x1d4` Text, …) |
| `Parent` | 0x7fbf7c | указатель на родителя → `[elem+0x34]` |
| `Left/Top/Width/Height` | 0x7fbf70/6c/64/5c | `SetRect([elem+0x154], {L,T,L+W,T+H})` (блок 15), затем `0x590e90` переводит в **parent-relative** (−Left/−Top родителя) |
| `Msk` | 0x7fbf78 | пиксельная маска hit-test → `[elem+0x150]`, шаг `[elem+0x184]` (0x58ce80/0x58e710) |
| `ShiftX` / `ShiftY` | 0x7fbee8 / 0x7fbee0 | `SetShift(elem, flag=1, ShiftX, ShiftY)` (блок 16) → `record[1].sX/sY` |
| `ScrL/ScrT/ScrW/ScrH` | 0x7fc000..0x7fbfe8 | rect'ы визуала (спрайта) контрола — инициализация CVisualObject `0x5899b0` |
| `Txt/TxtL/TxtT/TxtW/TxtH` | 0x7fc028..0x7fc008 | привязка текста внутри контрола |
| `Sound`, состояния (`Free/Push/Light/Disabled`, `Type1..8`, `Res1..4`, `Phase1..8`, `Last..Last4`) | 0x7fbf54, 0x7fc128.. | звук и кадры состояний кнопок |

**Ключевой факт: раскладка 1024x768 задана ДАННЫМИ.** `ShiftX/ShiftY` — это «на сколько
пикселей сдвинуть контрол (и каскадно детей) во втором профиле». Их можно извлечь/править
в `Controls.reg` без правки exe (файл лежит в архивах данных игры).

После загрузки всего списка выполняется проход `0x58ca30` (блок 19): для каждого элемента
`ApplyShift` (0x591190, блок 13) → `record[1].X += record[1].sX; record[1].Y += record[1].sY`
и рекурсивно детям `OffsetRecord(child, 1, sX, sY)` (0x5911f0, блок 14). Итог:
`record[1].X/Y = сумма ShiftX/ShiftY по цепочке предков + свой`.

---

## 3. Объект контрола (CControl, размер 0x1d0 у Panel)

| offset | поле | кто пишет | кто читает |
|---|---|---|---|
| +0x00 | vtable (Panel 0x75a734, base 0x75d984); **vtbl+0x5c = OnLayoutChange 0x5912e0** | ctor | relayout |
| +0x34 | parent | лоадер | hit-test (обход цепочки) |
| +0x44 / +0x48 | массив детей / количество | attach | hit-test, OffsetRecord, OnLayoutChange |
| +0x148 | CVisualObject (спрайт/прямоугольники отрисовки) | лоадер (Scr*/Msk/состояния) | draw; OnLayoutChange сдвигает его на (ΔX,ΔY) |
| +0x14c | флаги состояния; **нижний nibble = бит профиля** (1=800x600, 2=1024x768; 4/8 зарезервированы) | apply_flag | игровая логика (upper bits: 0x100000/0x200000/0x800000 — стиль/видимость) |
| +0x150 / +0x184 | пиксельная маска / шаг (в dword'ах*32 бит) | лоадер `Msk` | hit-test (пиксель-точно) |
| +0x154 | **RECT геометрии (parent-relative)** | SetRect из Left/Top/W/H; OnLayoutChange += (ΔShX,ΔShY) | hit-test, клиппинг |
| +0x164 | RECT (абсолютный кэш) | 0x58f550-путь | hit-test когда нет маски; OnLayoutChange += (ΔX,ΔY) |
| +0x174 | RECT маски (локальный) | лоадер | hit-test с маской (трансформируется цепочкой родителей) |
| +0x18c | **record[0] {X,Y,sX,sY} — профиль 800x600** (X,Y всегда 0) | ctor (нули) | relayout |
| +0x19c | **record[1] {X,Y,sX,sY} — профиль 1024x768}** (X,Y=Σ сдвигов, sX/sY=свой ShiftX/Y) | SetShift + ApplyShift | relayout |
| +0x1ac..+0x1bb | **active {X,Y,sX,sY} = record[flag]** | relayout | игровые экраны (позиционирование от «активной» точки) |

Записей ровно **две**: `record[2]` легла бы на +0x1ac (active) — движок физически
рассчитан на 2 профиля, хотя jump-table `apply_flag` допускает flag 0..3.

---

## 4. Переключение профиля (что меняет 1024x768)

Цепочка (все VA настоящие):

```
CScreenManager::Init (хвост, блоки 21+02) @0x59bc9e:
  set_rect(subscreens +0xb4/+0xb8/+0xc0, [0x82bc58], RECT{0,0,800,600})   ; дефолт SetRect
  0x58be10  загрузка Controls.reg (+ CutParts.reg 0x58ca90)
  0x58ca30  ApplyShifts: record[1].X/Y = Σ ShiftX/ShiftY
  SetRect(RECT{0,0,800,600}); set_rect([screen+8], RECT)
  mode_check @0x59bd28:
     W,H = [0x825de8]->+0x18->{+0x14,+0x18}          ; живой размер режима
     (W,H)==(1024,768) -> apply_layout(1)
     (W,H)==( 800, 600) -> apply_layout(0)
     иначе              -> call ПРОПУЩЕН (остаётся дефолт 800x600)

apply_layout(flag) @0x59fcb0 (блок 03):
  [screen+0x188] = flag
  (W,H) = (800,600) | (1024,768)      ; immediate @file 0x19fcdc..0x19fce8 / 0x19fccd..0x19fcd6
  [screen+0xe8] = RECT{0,0,W,H}       ; «экран»
  set_rect([screen+0x08], RECT{0,0,W,H})
  apply_flag(mgr=[0x82b968], flag)    ; ВСЕ контролы
  set_rect([screen+0x10], RECT{W-163,0,W,H})    ; правая инфо-полоса (163 px)
  set_rect([screen+0x0c], RECT{0,0,W-133,H})    ; игровая область
  set_rect([screen+0x34], RECT{0,0,W,H})

apply_flag(mgr,flag) @0x58bd70 (блок 05):
  bit = {0:1, 1:2, 2:4, 3:8}[flag]
  для каждого elem кругового списка ([mgr]->head, node=[node+8], elem=[node+0x1c]):
     [elem+0x14c] = ([elem+0x14c] & ~0xF) | bit     ; «какой профиль применён»
     relayout(elem, flag)

relayout(elem,flag) @0x591250 (блок 10):
  act{+0x1ac..0x1bb} = record[flag]{+0x18c+flag*16 .. +0xc}
  virtual OnLayoutChange(vtbl+0x5c)(ΔsX, ΔsY, ΔX, ΔY)   ; Δ = новое − старое (по active)

OnLayoutChange @0x5912e0 (блок 11):
  OffsetRect(&rect+0x154, ΔsX, ΔsY)        ; hit-rect: СОБСТВЕННЫЙ сдвиг (он parent-relative —
                                           ; сдвиг предков придёт через предка)
  if !IsRectEmpty(&rect+0x164):
      OffsetRect(&rect+0x164, ΔX, ΔY)      ; абсолютный кэш: ПОЛНЫЙ сдвиг
  if visual(+0x148): visual->Offset(ΔX,ΔY) ; спрайт: ПОЛНЫЙ сдвиг (0x58a5d0)
```

При 0→1: ΔsX = ShiftX (свой), ΔX = Σ сдвигов цепочки; при 1→0 — обратные.
Значения берутся из records, поэтому **переключения идемпотентны** (нет накопления дрейфа).

**Итого «профиль 1024x768» = 3 вещи:**
1. 4 экранных rect'а менеджера (хардкод W,H и производные W−163 / W−133);
2. сдвиг всех контролов на их `ShiftX/ShiftY` (данные `Controls.reg`, накопленные в record[1]);
3. бит профиля в `[elem+0x14c]` (и flag в `[screen+0x188]`).

---

## 5. Потребители координат (почему при 1600x900 «hover есть, клика нет»)

| потребитель | источник координат | поведение при неизвестном разрешении (apply_layout пропущен) |
|---|---|---|
| отрисовка контролов | visual +0x148 (Scr*/Msk/состояния) + rect'ы — дизайн-координаты 800x600 | рисуется в «квадрате 800x600» |
| hit-test / click @0x58fb70 (блок 17) | rect +0x154 (parent-relative) / +0x164 / маска +0x174+0x150; PtInRect [0x756430] | те же дизайн-координаты → клик мимо |
| «живые» поверхности (миникарта, hover-подсветка, backbuffer-оверлеи) | viewport `0x5a0070` (блок 20): RECT{0,0,**realW,realH**} из объекта режима [0x825de8] | native → подсветка по реальному периметру |
| игровые экраны/HUD | active +0x1ac/+0x1b0 (draw 0x591430→0x5a3100) + собственные поля, часть кодов читает realW/H | смесь: панель у левого края, якоря по native |

Это ровно та триада из `docs/06`, теперь с именами функций: draw/click = design-coords
(пропущенный apply_layout оставил их в 800x600), hover/миникарта = live-режим.
Инвариант «rect == baked» — частный случай согласованности этих трёх потребителей.

---

## 6. Что это меняет в плане native (ревизия docs/07–08)

1. **CE-протокол (docs/08) больше не нужен.** Offset'ы, которые он предлагал искать в рантайме,
   известны статически: record X/Y = `elem+0x18c+flag*16`, active = `elem+0x1ac`, геометрия =
   `elem+0x154` (relative) / `+0x164` (abs) / маска `+0x150,+0x174,+0x184`, визуал `+0x148`,
   список = `[0x82b968]` (обход как в apply_flag). Брейкпоинты: **0x59FCB0, 0x591250, 0x58FB70,
   0x58F690**.
2. **Правильная точка хука v2** — не «после call 0x99fcb0 масштабировать x/y/w/h элементов»
   (элементы не хранят x/y/w/h в явном виде — у них RECT'ы и records со сдвигами), а:
   - форсировать `apply_layout(1)` при любом разрешении (уже делает patch_layout.py — 6 байт);
   - внутри/после apply_layout подменить 4 экранных rect'а на live W/H
     (трамплин v1 на immediate @file 0x19fccd — годится, но ТОЛЬКО вместе с п.3, иначе рассинхрон);
   - **после apply_flag** обойти список контролов и масштабировать:
     `rect+0x154` (LTRB, parent-relative — масштабируется согласованно по всей цепочке:
     abs = Σ relative), `rect+0x164`, `rect+0x174`, rect'ы визуала `+0x148` (через его поля
     +0x30/+0x40/… см. 0x5899b0), а также active `+0x1ac..+0x1bb` и полосы `W−163/W−133`;
   - hit-test с маской: пиксельная маска не масштабируется — либо в хуке hit-test делить
     локальные (x−left, y−top) на масштаб, либо отключать маску (перехват [elem+0x150]→0)
     для масштабированных контролов.
3. **Альтернатива без кода в exe (data-путь):** поскольку Shift-профиль живёт в `Controls.reg`,
   можно собрать «третий профиль» = scaled-координаты под целевое разрешение и форсировать
   его 6-байтным патчем. Ограничение: records в объекте ровно две (см. §3), поэтому
   data-путь даёт только замену 1024x768-профиля на, скажем, 1920x1080-профиль
   (X*1920/1024 в reg + патч immediate'ов W,H/полос в apply_layout). Для произвольного
   разрешения всё равно нужен рантайм-масштаб (п.2).
4. Код-кейв: file 0x355656..0x356000 (VA 0x755656..0x756000, ~2.4 КБ, в пределах
   SizeOfRawData .text → исполняемый). v1 его уже использовал.

---

## 7. Быстрая шпаргалка (настоящие VA / file)

| сущность | VA | file |
|---|---|---|
| parse VideoResolution | 0x42db92 | 0x2db92 |
| CScreenManager::Init (хвост) | 0x59bc9e | 0x19bc9e |
| mode_check (1024/800 ветки) | 0x59bd28 | 0x19bd28 |
| apply_layout(flag) | 0x59fcb0 | 0x19fcb0 |
| — immediate W=1024 / H=768 | 0x59fccd / 0x59fcd2 | 0x19fccd / 0x19fcd2 |
| — immediate W=800 / H=600 | 0x59fcdc / 0x59fce1 | 0x19fcdc / 0x19fce1 |
| apply_flag(mgr,flag) | 0x58bd70 | 0x18bd70 |
| relayout(elem,flag) | 0x591250 | 0x191250 |
| OnLayoutChange (vtbl+0x5c) | 0x5912e0 | 0x1912e0 |
| SetShift(elem,flag,sx,sy) | 0x591170 | 0x191170 |
| ApplyShift(elem) | 0x591190 | 0x191190 |
| OffsetRecord(elem,flag,dx,dy) | 0x5911f0 | 0x1911f0 |
| set_rect(this,RECT→+0x154) | 0x58f690 | 0x18f690 |
| hit-test | 0x58fb70 | 0x18fb70 |
| лоадер Controls.reg | 0x58be30 | 0x18be30 |
| лоадер CutParts.reg | 0x58ca90 | 0x18ca90 |
| ApplyShifts-проход | 0x58ca30 | 0x18ca30 |
| live viewport (realW/H) | 0x5a0070 (чтение режима 0x5a00fd) | 0x1a0070 |
| глобальный менеджер контролов | 0x82b968 (dword) | .data(bss) |
| глобальный объект экрана/режима | 0x825de8 (dword) | .data(bss) |
| строка "Controls.reg" | 0x7fbfd8 | 0x3fbfd8 |
| строки ShiftX/ShiftY | 0x7fbee8 / 0x7fbee0 | 0x3fbee8 / 0x3fbee0 |
| IAT: SetRect/OffsetRect/PtInRect/IntersectRect/IsRectEmpty | 0x756428/0x756464/0x756430/0x756418/0x756420 | — |

Проверено: xref'ы строк, call-граф (callers of 0x591250 = {0x58bdd6}; of 0x59fcb0 = {0x59bd65};
of 0x591190 = {0x58ca56}; of 0x591170 = лоадер 0x58c93f + клоны контролов), vtable Panel
(+0x5c = 0x5912e0), дизассемблер capstone, x86-32.
