# DSSE — мультимодальный набор данных «Птицы»

Набор данных по 10 видам птиц в трёх модальностях: текст, изображения, аудио.
Модальности связаны идентификатором вида (`slug`) из `metadata/species.csv`.

| Модальность | Расположение | Источник |
|---|---|---|
| Текст | `data/text/<slug>.txt` | Википедия (en, ru) |
| Изображения | `data/images/<slug>/` | Викисклад |
| Аудио | `data/audio/<slug>/` | Викисклад |

Источник, автор и лицензия каждого файла указаны в `metadata/manifest.csv`.

## Запуск

```bash
pip install -r requirements.txt
python src/collect_data.py
python src/verify_data.py
python src/make_readme.py
```

<!-- AUTO:START -->

## Структура репозитория

```
DSSE/
├── data/
│   ├── audio/
│   │   ├── barn_swallow/  [2]
│   │   ├── common_blackbird/  [2]
│   │   ├── common_cuckoo/  [2]
│   │   ├── common_nightingale/  [2]
│   │   ├── eurasian_magpie/  [2]
│   │   ├── great_tit/  [2]
│   │   ├── hooded_crow/  [2]
│   │   ├── house_sparrow/  [2]
│   │   ├── mallard/  [2]
│   │   └── white_stork/  [2]
│   ├── images/
│   │   ├── barn_swallow/  [3]
│   │   ├── common_blackbird/  [3]
│   │   ├── common_cuckoo/  [3]
│   │   ├── common_nightingale/  [3]
│   │   ├── eurasian_magpie/  [3]
│   │   ├── great_tit/  [3]
│   │   ├── hooded_crow/  [3]
│   │   ├── house_sparrow/  [3]
│   │   ├── mallard/  [3]
│   │   └── white_stork/  [3]
│   └── text/
│       ├── barn_swallow.txt
│       ├── common_blackbird.txt
│       ├── common_cuckoo.txt
│       ├── common_nightingale.txt
│       ├── eurasian_magpie.txt
│       ├── great_tit.txt
│       ├── hooded_crow.txt
│       ├── house_sparrow.txt
│       ├── mallard.txt
│       └── white_stork.txt
├── metadata/
│   ├── manifest.csv
│   └── species.csv
├── src/
│   ├── collect_data.py
│   ├── make_readme.py
│   └── verify_data.py
├── .gitignore
├── LICENSE
├── README.md
└── requirements.txt
```

## Состав набора данных

| Вид | Научное название | Текст | Изображения | Аудио |
|---|---|---|---|---|
| Домовый воробей (`house_sparrow`) | *Passer domesticus* | 1 | 3 | 2 |
| Большая синица (`great_tit`) | *Parus major* | 1 | 3 | 2 |
| Сорока (`eurasian_magpie`) | *Pica pica* | 1 | 3 | 2 |
| Серая ворона (`hooded_crow`) | *Corvus cornix* | 1 | 3 | 2 |
| Чёрный дрозд (`common_blackbird`) | *Turdus merula* | 1 | 3 | 2 |
| Обыкновенный соловей (`common_nightingale`) | *Luscinia megarhynchos* | 1 | 3 | 2 |
| Деревенская ласточка (`barn_swallow`) | *Hirundo rustica* | 1 | 3 | 2 |
| Обыкновенная кукушка (`common_cuckoo`) | *Cuculus canorus* | 1 | 3 | 2 |
| Белый аист (`white_stork`) | *Ciconia ciconia* | 1 | 3 | 2 |
| Кряква (`mallard`) | *Anas platyrhynchos* | 1 | 3 | 2 |
| **Итого** | | 10 | 30 | 20 |

Лицензии файлов: CC BY-SA 4.0 — 30, CC BY-SA 3.0 — 14, CC BY-SA 2.5 — 5, CC BY 4.0 — 4, CC BY 2.0 — 2, FAL — 1, CC BY-SA 2.0 — 1, Public domain — 1, GFDL 1.2 — 1, CC BY-NC-SA 4.0 — 1.

<!-- AUTO:END -->
