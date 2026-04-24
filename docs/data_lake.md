# Data Lake

> Ghi chu: data lake hien tai la path optional/secondary. Default train/evaluate pipeline cua repo dang dung `data/`, khong dung `data_lake/`.

Project dung data lake de quan ly nhieu nguon anh noi soi tai theo cac tang:

- `raw`: metadata goc theo tung source, khong sua du lieu goc.
- `bronze`: manifest hop nhat tu moi source.
- `silver`: nhan da map ve schema chuan, duplicate/quality flags.
- `gold`: dataset version dung de train/evaluate.

## Build

```bash
python scripts/build_data_lake.py --config configs/data_lake.yaml --stage all --force
```

Output chinh:

- `data_lake/bronze/unified_manifest.csv`
- `data_lake/silver/labels.csv`
- `data_lake/silver/quality_report.json`
- `data_lake/gold/classification_v1/labels.csv`
- `data_lake/gold/classification_v1/splits/train.csv`
- `data_lake/gold/classification_v1/splits/val.csv`
- `data_lake/gold/classification_v1/splits/test.csv`
- `data_lake/gold/classification_v1/dataset_card.md`

## Validate

```bash
python scripts/validate_data_lake.py --config configs/data_lake.yaml
```

Gold split dung `raw_sha256` lam group column de duplicate exact-match khong roi qua nhieu split.

## Train From Gold

```bash
python scripts/train.py --config configs/train_gold_resnet18.yaml
python scripts/evaluate.py ^
  --config configs/train_gold_resnet18.yaml ^
  --checkpoint models/checkpoints/gold_resnet18/best.pt ^
  --split test
python scripts/summarize_run.py --run-name gold_resnet18
```

## Add New Source

Them mot source moi vao `configs/data_lake.yaml`:

```yaml
sources:
  - source_id: hospital_a_v1
    source_name: Hospital A Otoscopy Dataset
    license: private research agreement
    site: hospital_a
    device: device_name
    image_root: path/to/images
    labels_csv: path/to/labels.csv
    processed_image_root: path/to/processed/images
    processed_labels_csv: path/to/processed/labels.csv
    patient_id_source: real_patient_id
```

Sau do cap nhat `configs/label_mapping.yaml` neu source moi co nhan khac schema hien tai.

## Caveat

Nguon Kaggle hien tai khong co `patient_id` that. Data lake van giu `patient_id_source=synthetic_image_id`, nen ket qua tren gold dataset hien tai van la image-level validation. Khi co source co patient ID that, nen tao external test set theo source/benh nhan rieng.
