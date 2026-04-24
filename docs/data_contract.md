# Data Contract

Dataset goc khong duoc sua truc tiep trong `data/raw/`. Moi buoc clean, resize, crop, quality filtering can sinh artifact rieng trong `data/interim/` hoac `data/processed/`.

Hien tai `data/raw/pull_data.py` co the merge nhieu local source vao cung `data/raw/labels.csv`, vi du `Oto-Endoscopic_Images` va `Datos`. Cot `source` vi vay rat quan trong de theo doi domain shift va debug metric.

## Required label columns

- `image_id`: id duy nhat cho anh.
- `image_path`: duong dan anh tuong doi voi `data/raw/images/` hoac duong dan tuyet doi.
- `patient_id`: id benh nhan; bat buoc de split tranh leakage.
- `label`: class nam trong `configs/data.yaml`.

## Kaggle Otoscopic Image Dataset

Nguon hien tai cua project la `ucimachinelearning/otoscopic-image-dataset` tren Kaggle. Dataset nay gom 5 class trong config:

- `acute_otitis_media`
- `cerumen_impaction`
- `chronic_otitis_media`
- `myringosclerosis`
- `normal`

Dataset khong cung cap `patient_id`, nen `data/raw/pull_data.py` sinh `patient_id` gia theo tung anh va gan `patient_id_source=synthetic_image_id`. Khi bao cao ket qua, can ghi ro day khong phai patient-level split that.

Dataset co mot so anh trung hash. Config split dung `split.group_column: raw_sha256` de cac duplicate exact-match nam trong cung split, tranh leakage train/val/test do anh trung.

## Recommended metadata

- `ear_side`: `left` hoac `right`.
- `age`, `sex`: chi dung neu duoc phep va da an danh.
- `source`: nguon thiet bi/benh vien/phong kham de danh gia domain shift.
- `quality`: `good`, `blurred`, `occluded`, `overexposed`, hoac nhan chat luong tuong duong.

## Current public-source caveats

- `Oto-Endoscopic_Images`: co 5 class.
- `Datos`: chi co 4 class, khong co `acute_otitis_media`.
- `Datos` co duplicate noi bo; split goc cua source nay khong nen duoc tin hoan toan neu chua group theo hash.

## Validation checklist

- Khong co cung `patient_id` xuat hien o nhieu split.
- Moi class co du anh trong train va test; neu class qua it, gop vao `other` hoac thu thap them.
- Bao cao rieng performance theo `source`, `quality`, va `ear_side` neu cac cot nay co san.
- Anh va metadata y te can duoc an danh truoc khi dua vao repo, artifact store, hoac demo.

## Processing output

`scripts/process_data.py` doc `data/raw/labels.csv` va ghi:

- `data/processed/images/<class>/<image_id>.jpg`
- `data/processed/labels.csv`
- `data/processed/processing_report.json`

Anh processed duoc crop vung sang neu co vien toi, resize ve kich thuoc trong `configs/data.yaml`, va giu lai metadata `raw_image_path`, `raw_sha256`, `processed_sha256`, crop box, kich thuoc output. Normalization khong ghi vao anh processed; buoc do nam trong training transform.

## EDA output

`scripts/eda.py` doc `data/processed/labels.csv` va split CSV, sau do ghi:

- `reports/eda/summary.json`
- `reports/eda/eda_report.md`
- `reports/eda/image_stats.csv`
- `reports/eda/duplicate_groups_<hash_col>.csv`
- `reports/figures/eda/*.png`

Neu `duplicate_reports.<hash_col>.cross_split_groups > 0`, can tao lai split bang group column phu hop truoc khi train.
