# Блоки Etherlords.exe для работы

Это НЕ полный бинарник, а целевые регионы реверса.
**ImageBase 0x400000; для .text/.rdata/.data: VA = file + 0x400000** (см. docs/07, раздел 0 —
старые листинги в docs/02–06 использовали сдвинутый на +0x400000 базис).

Блоки нарезаны `tools/dump_blocks.py` (воспроизводимо):
`python3 tools/dump_blocks.py reference/Etherlords.exe blocks`

| # | блок | file range | va range | bytes | sha256[:16] | назначение |
|---|---|---|---|---|---|---|
| 1 | 01_parse_video_resolution | 0x2db8f..0x2dbd6 | 0x42db8f..0x42dbd6 | 71 | a8e674a9f9ff7977 | Чтение VideoResolution из settings.ini -> atoi -> [esi+0x28]/[esi+0x2c]. Белый список отсутствует. |
| 2 | 02_mode_check_layout | 0x19bd28..0x19bd90 | 0x59bd28..0x59bd90 | 104 | 56f2ce1dd1060a85 | Выбор раскладки: ==1024x768 -> apply_layout(1); ==800x600 -> apply_layout(0); иначе ПРОПУСК. |
| 3 | 03_apply_layout | 0x19fcb0..0x19fda0 | 0x59fcb0..0x59fda0 | 240 | 8448d1fe6ac96d61 | apply_layout(flag): W,H=(800,600)\|(1024,768) immediate; [screen+0xe8]=(0,0,W,H); set_rect subscreens; apply_flag(mgr,flag); полосы (W-163) и (W-133). |
| 4 | 04_set_rect | 0x18f690..0x18f6b3 | 0x58f690..0x58f6b3 | 35 | bd0659d9e07d15bd | set_rect(this,RECT): копирует RECT в [this+0x154]. |
| 5 | 05_apply_flag | 0x18bd70..0x18be08 | 0x58bd70..0x58be08 | 152 | 5d4571ce403454e7 | apply_flag(mgr,flag): flag->бит (0->1,1->2,2->4,3->8) в нижний nibble [elem+0x14c]; обход кругового списка [mgr]->head,[node+8],elem=[node+0x1c]; relayout(elem,flag). |
| 6 | 06_aspect_4_3 | 0x46f28..0x46f60 | 0x446f28..0x446f60 | 56 | d6de37e4d4700bf0 | push 0x3faaaaab (4/3) -> аргумент построения матрицы/вьюпорта. |
| 7 | 07_aspect_3_4 | 0x52b20..0x52b60 | 0x452b20..0x452b60 | 64 | 1fcf3d2ff6c7419f | mov eax,0x3f400000 (3/4) -> поле проекции [esi+0x20]. |
| 8 | 08_push800x600_a | 0x19ab28..0x19ab50 | 0x59ab28..0x59ab50 | 40 | 97a57d0e0ad9747b | Дефолт SetRect(&[esi+0xe8],0,0,800,600) сайт #1. |
| 9 | 09_push800x600_b | 0x19bd00..0x19bd28 | 0x59bd00..0x59bd28 | 40 | 2e55441c6b3ef576 | Дефолт SetRect(0,0,800,600) + set_rect([esi+8]) сайт #2 (перед mode_check). |
| 10 | 10_relayout_elem | 0x191250..0x1912de | 0x591250..0x5912de | 142 | 092dcfcdfa2fd120 | relayout(elem,flag): act{+0x1ac..0x1bb} = record[flag]{+0x18c+flag*16}; virtual OnLayoutChange(vtbl+0x5c)(dShX,dShY,dX,dY). |
| 11 | 11_on_layout_change | 0x1912e0..0x191339 | 0x5912e0..0x591339 | 89 | a7dc112874eef465 | OnLayoutChange: OffsetRect(+0x154,dShX,dShY); если +0x164 непуст OffsetRect(+0x164,dX,dY); visual(+0x148): 0x58a5d0(dX,dY). |
| 12 | 12_set_shift | 0x191170..0x191190 | 0x591170..0x591190 | 32 | 0a854f85ad7ac354 | SetShift(elem,flag,sx,sy): record[flag].sX(+8)=sx, .sY(+12)=sy. Из лоадера: SetShift(1,ShiftX,ShiftY). |
| 13 | 13_apply_shift | 0x191190..0x1911f0 | 0x591190..0x5911f0 | 96 | fddab33ac44be610 | ApplyShift(elem): rec1.X+=rec1.sX; rec1.Y+=rec1.sY; детям OffsetRecord(child,1,sX,sY). |
| 14 | 14_offset_record | 0x1911f0..0x191250 | 0x5911f0..0x591250 | 96 | cd96d5315f857ffa | OffsetRecord(elem,flag,dx,dy): record[flag].X+=dx,.Y+=dy; рекурсия в детей (+0x44/+0x48). |
| 15 | 15_loader_geometry | 0x18c41d..0x18c4c9 | 0x58c41d..0x58c4c9 | 172 | a29918ed594aa4c8 | Лоадер Controls.reg: Left/Top/Width/Height -> SetRect(elem+0x154,{L,T,L+W,T+H}); 0x590e90 переводит в parent-relative. |
| 16 | 16_loader_shiftxy | 0x18c905..0x18c944 | 0x58c905..0x58c944 | 63 | c3abff9bdf67e74e | Лоадер Controls.reg: ShiftX/ShiftY -> SetShift(elem,1,ShiftX,ShiftY) = record[1].sX/sY. |
| 17 | 17_hittest | 0x18fb70..0x18fd44 | 0x58fb70..0x58fd44 | 468 | e840e93d9152bad1 | HitTest(x,y): рекурсия детей; маска +0x150 (stride +0x184, rect +0x174, цепочка родителей +0x34->+0x154/0x158, PtInRect+бит маски); иначе rect +0x164/+0x154 + PtInRect. |
| 18 | 18_ctor_zero_records | 0x18f261..0x18f2b0 | 0x58f261..0x58f2b0 | 79 | 11252ba42a623f17 | Базовый конструктор контрола: зануляет record[0..1] (+0x18c..0x1ab) и act (+0x1ac..0x1bb). Размер Panel=0x1d0: место ровно под ДВЕ записи. |
| 19 | 19_apply_shifts_pass | 0x18ca30..0x18ca88 | 0x58ca30..0x58ca88 | 88 | dd22a3c57c3859e3 | Пост-проход загрузки: ApplyShift(0x591190) для каждого элемента плоского списка менеджера. |
| 20 | 20_live_viewport | 0x1a0070..0x1a0175 | 0x5a0070..0x5a0175 | 261 | 76fd01a3639ea6df | Создание viewport'а ЖИВЫМ размером: RECT{0,0,realW,realH} из [0x825de8]->+0x18->{+0x14,+0x18} (0x5a00fd). Потребитель — миникарта/hover-поверхности. |
| 21 | 21_screen_init_defaults | 0x19bc9e..0x19bd28 | 0x59bc9e..0x59bd28 | 138 | 563f8fee9bc03cb9 | CScreenManager::Init: set_rect(0,0,800,600) для subscreens +0xb4/+0xb8/+0xc0 и [0x82bc58]; загрузка Controls.reg (0x58be10) и CutParts.reg (0x58ca90); ApplyShifts (0x58ca30). |

Хеши блоков 01, 02, 06–09 совпадают со старой версией INDEX (file-диапазоны не менялись;
исправлены только VA-подписи). Блоки 03–05 раньше были ПУСТЫМИ (нарезка шла «file-смещениями»
0x99fcb0/0x98f690/0x98bd70, которые на самом деле VA из сдвинутого базиса и лежат за EOF).
