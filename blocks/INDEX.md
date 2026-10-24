# Блоки Etherlords.exe для работы

Это НЕ полный бинарник, а целевые регионы реверса.
Полный оригинал в репозиторий не кладётся (авторские права Nival/1C); для анализа он
берётся из вашей легальной копии и сверяется по хешам (см. `reference/original.md`).

ImageBase 0x400000; для .text va = file + 0x800000.

| # | блок | file range | va range | bytes | sha256[:16] | назначение |
|---|---|---|---|---|---|---|
| 1 | 01_parse_video_resolution | 0x2db8f..0x2dbd6 | 0x82db8f..0x82dbd6 | 71 | a8e674a9f9ff7977 | Чтение VideoResolution из settings.ini -> atoi -> [esi+0x28]/[esi+0x2c]. Белый список отсутствует. |
| 2 | 02_mode_check_layout | 0x19bd28..0x19bd90 | 0x99bd28..0x99bd90 | 104 | 56f2ce1dd1060a85 | Выбор раскладки: сверка с 1024x768/800x600; неизвестное разрешение ПРОПУСКАЕТ call apply_layout. |
| 3 | 03_apply_layout | 0x99fcb0..0x99fda0 | 0x119fcb0..0x119fda0 | 0 | e3b0c44298fc1c14 | apply_layout(flag): пишет экранный rect [esi+0xe8]=(0,0,W,H) из immediate; якоря [esi+0xec..0xf4] минус 0xa3/0x85. |
| 4 | 04_set_rect | 0x98f690..0x98f6b3 | 0x118f690..0x118f6b3 | 0 | e3b0c44298fc1c14 | set_rect: копирует rect в [this+0x154] (источник для hit-test/миникарты). |
| 5 | 05_apply_flag | 0x98bd70..0x98bdf2 | 0x118bd70..0x118bdf2 | 0 | e3b0c44298fc1c14 | apply_flag: обход кругового списка элементов [mgr]->head, node+8, elem=node+0x1c, flags=elem+0x14c. |
| 6 | 06_aspect_4_3 | 0x46f28..0x46f60 | 0x846f28..0x846f60 | 56 | d6de37e4d4700bf0 | push 0x3faaaaab (4/3) -> аргумент построения матрицы/вьюпорта. |
| 7 | 07_aspect_3_4 | 0x52b20..0x52b60 | 0x852b20..0x852b60 | 64 | 1fcf3d2ff6c7419f | mov eax,0x3f400000 (3/4) -> поле проекции [esi+0x20]. |
| 8 | 08_push800x600_a | 0x19ab28..0x19ab50 | 0x99ab28..0x99ab50 | 40 | 97a57d0e0ad9747b | Дефолт f(...,800,600) сайт #1. |
| 9 | 09_push800x600_b | 0x19bd00..0x19bd28 | 0x99bd00..0x99bd28 | 40 | 2e55441c6b3ef576 | Дефолт f(...,800,600) сайт #2 (рядом cmp 1024/768). |
