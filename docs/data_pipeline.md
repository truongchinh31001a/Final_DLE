# Data Pipeline

Tai lieu nay mo ta luong du lieu mac dinh dang duoc repo su dung cho train/evaluate.

## Source Of Truth

Default pipeline hien tai dung `data/`, khong dung `data_lake/`.

Thu tu artifact:

1. `data/raw/`:
   - source folders nhu `Oto-Endoscopic_Images`, `Datos`
   - `data/raw/images/`
   - `data/raw/labels.csv`
2. `data/processed/`:
   - `data/processed/images/`
   - `data/processed/labels.csv`
   - `data/processed/processing_report.json`
3. `data/splits/`:
   - `train.csv`
   - `val.csv`
   - `test.csv`

`scripts/train.py`, `scripts/evaluate.py`, va `scripts/predict_image.py` mac dinh deu doc tu `configs/data.yaml`, nen chu yeu phu thuoc vao cac artifact trong `data/`.

## Raw Sources

`data/raw/pull_data.py` hien tai co 2 che do:

- Neu trong `data/raw/` da co cac folder source local chua anh, script se tu dong gom chung cac source do.
- Neu khong co local source va khong dung `--skip-download`, script se tai bo Kaggle/UCI ve staging dir.

Current local sources trong repo:

| Source | Classes | Images | Notes |
|---|---|---:|---|
| `Oto-Endoscopic_Images` | `acute_otitis_media`, `cerumen_impaction`, `chronic_otitis_media`, `myringosclerosis`, `normal` | 3014 | public Kaggle/UCI source |
| `Datos` | `cerumen_impaction`, `chronic_otitis_media`, `myringosclerosis`, `normal` | 880 | khong co `acute_otitis_media` |

Sau khi merge local sources, current `data/raw/labels.csv` co `3894` anh voi class counts:

| Label | Count |
|---|---:|
| `acute_otitis_media` | 601 |
| `cerumen_impaction` | 822 |
| `chronic_otitis_media` | 822 |
| `myringosclerosis` | 825 |
| `normal` | 824 |

## Build Raw Labels

Lenh mac dinh:

```bash
python data/raw/pull_data.py --force
```

Script se:

- quet source folders trong `data/raw/`
- infer label tu ten folder
- map alias, vi du `Earwax plug -> cerumen_impaction`
- copy anh vao `data/raw/images/<class>/...`
- tao `data/raw/labels.csv`
- them cot `source`, `patient_id_source`, `sha256`, `original_path`

```

## Processed Data

Process raw thanh anh resize 224x224:

```bash
python scripts/process_data.py --config configs/data.yaml --force
```

Script doc `data/raw/labels.csv` va ghi:

- `data/processed/images/<class>/<image_id>.jpg`
- `data/processed/labels.csv`
- `data/processed/processing_report.json`

Current processing config:

- resize ve `224x224`
- khong crop content cho dataset current (`crop_to_content: false`)
- giu metadata `raw_sha256`, `processed_sha256`, crop box, kich thuoc output

## Split

Tao split tu processed labels:

```bash
python scripts/prepare_data.py --config configs/data.yaml
```

Split config hien tai:

- `val_size: 0.15`
- `test_size: 0.15`
- `stratify_by_label: true`
- `group_column: raw_sha256`
- `deduplicate_by_group: true`

`group_column: raw_sha256` rat quan trong vi current public sources co duplicate exact-match. Nho group theo hash, duplicate se nam cung split thay vi leak train/val/test.
Khi bat `deduplicate_by_group: true`, moi hash chi giu 1 dai dien trong `train.csv`, `val.csv`, va `test.csv`, giup metric validation/test khong bi nhan trong so boi exact duplicates.

## EDA

```bash
python scripts/eda.py --config configs/data.yaml --output-dir reports/eda
```

Output chinh:

- `reports/eda/summary.json`
- `reports/eda/eda_report.md`
- `reports/eda/image_stats.csv`
- `reports/eda/duplicate_groups_raw_sha256.csv`
- `reports/figures/eda/*.png`

## Current Caveats

### 1. Current split khong phai patient-level split that

Ca `Oto-Endoscopic_Images` va `Datos` hien tai khong cung cap patient id that. `pull_data.py` sinh `patient_id` synthetic theo tung anh, nen train/eval hien tai van la image-level validation.

### 2. `Datos` co duplicate noi bo va duplicate cross-split trong split goc

Phan tich current `Datos`:

- `880` anh nhung chi co `811` hash duy nhat
- `66` duplicate hash groups
- `65` duplicate groups bac qua ca `Training-validation` va `Testing`

Vi vay, khong nen tin hoan toan split goc cua `Datos`. Neu dung source nay, nen tiep tuc split lai bang `raw_sha256` nhu current pipeline.

### 3. `Datos` khong co `acute_otitis_media`

Sau khi merge source:

- `acute_otitis_media` chi den tu `Oto-Endoscopic_Images`
- 4 class con lai nhan them du lieu tu `Datos`

Dieu nay can duoc ghi chu khi phan tich domain shift hay interpret confusion matrix.

### 4. `reports/metrics_newdata/` la khu vuc ad-hoc

`reports/metrics/` nen duoc xem la benchmark chinh da chot.

`reports/metrics_newdata/` phu hop cho:

- rerun evaluate khi raw data thay doi
- so sanh tam thoi tren bo du lieu moi
- nghien cuu domain shift

Khong nen coi `metrics_newdata` la benchmark chinh neu chua rerun dong bo cho tat ca model.

## Optional Data Lake

Repo van co `data_lake/` va cac script build/validate rieng, nhung hien tai day khong phai default path.

Chi nen dung `data_lake/` khi can:

- version hoa nhieu source theo bronze/silver/gold
- track metadata source-level ro rang hon
- tao curated dataset card rieng
