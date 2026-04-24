# Project Summary

Tai lieu nay tong hop qua trinh cua project tu luc gom du lieu den khi chot lineup model cuoi cung.

## 1. Muc tieu bai toan

Project huong toi phan loai anh noi soi tai thanh 5 nhom:

- `acute_otitis_media`
- `cerumen_impaction`
- `chronic_otitis_media`
- `myringosclerosis`
- `normal`

Repo duoc to chuc de phuc vu toan bo quy trinh:

- gom va hop nhat du lieu
- xu ly va chuan hoa artifact
- tao split train/val/test
- train, evaluate, predict
- tong hop benchmark va docs

## 2. Du lieu dau vao

Pipeline mac dinh hien tai dung thu muc `data/`, khong dung `data_lake/` trong train/evaluate hang ngay.

Hai source local chinh da duoc hop nhat trong `data/raw/`:

| Source | So anh | Ghi chu |
|---|---:|---|
| `Oto-Endoscopic_Images` | 3014 | bo public co du 5 class |
| `Datos` | 880 | khong co `acute_otitis_media` |

Sau khi merge, current raw dataset co:

- `3894` anh tong cong
- `3894` dong sau processing
- `0` dong bi bo qua trong processing hien tai

Phan bo class hien tai:

| Label | Count |
|---|---:|
| `acute_otitis_media` | 601 |
| `cerumen_impaction` | 822 |
| `chronic_otitis_media` | 822 |
| `myringosclerosis` | 825 |
| `normal` | 824 |

Dieu can nho:

- `acute_otitis_media` hien chi den tu `Oto-Endoscopic_Images`
- 4 class con lai duoc bo sung them tu `Datos`

## 3. Gom raw data

Buoc dau tien cua pipeline:

```bash
python data/raw/pull_data.py --force
```

Script nay se:

- quet cac source local trong `data/raw/`
- map ten folder ve label chuan
- copy anh vao `data/raw/images/<class>/...`
- tao `data/raw/labels.csv`
- gan them metadata nhu `source`, `sha256`, `original_path`

Mot han che quan trong la public sources hien khong co patient id that. Vi vay `patient_id` trong repo hien la synthetic theo tung anh, khong du de xem day la patient-level dataset.

## 4. Xu ly anh va metadata

Buoc tiep theo:

```bash
python scripts/process_data.py --config configs/data.yaml --force
```

Pipeline processing hien tai:

- resize anh ve `224x224`
- luu anh vao `data/processed/images/`
- tao `data/processed/labels.csv`
- ghi `data/processed/processing_report.json`

Nhung diem chinh cua processing:

- khong normalize pixel o buoc processing
- normalization duoc de lai cho training transforms
- giu lai `raw_sha256` va `processed_sha256` de phuc vu EDA va split duplicate-aware

## 5. Kiem soat data leakage va tao split

Day la phan quan trong nhat cua qua trinh lam sach pipeline.

### Van de gap phai

Du lieu public co 2 han che:

1. khong co patient id that
2. co duplicate exact-match trong mot so source

Neu split thong thuong theo tung dong anh, duplicate co the roi vao train/val/test khac nhau va lam metric bi lac quan.

### Cach repo dang xu ly

Split hien tai duoc tao bang:

```bash
python scripts/prepare_data.py --config configs/data.yaml
```

Trong `configs/data.yaml`, repo da chot:

- `val_size: 0.15`
- `test_size: 0.15`
- `stratify_by_label: true`
- `group_column: raw_sha256`
- `deduplicate_by_group: true`

Y nghia:

- group theo `raw_sha256` de duplicate exact-match nam cung mot nhom
- deduplicate truoc khi ghi CSV split de moi hash chi con 1 dai dien trong train/val/test

Split hien tai sau khi deduplicate:

| Split | So dong |
|---|---:|
| Train | 2613 |
| Val | 560 |
| Test | 560 |

Ket luan ngan cho phan leakage:

- pipeline hien tai da giam duoc leakage do exact duplicates
- benchmark hien tai la image-level benchmark sach hon truoc day
- day van chua phai patient-level validation that vi khong co patient metadata goc

## 6. EDA va kiem tra chat luong

Sau khi co split, repo co buoc EDA:

```bash
python scripts/eda.py --config configs/data.yaml --output-dir reports/eda
```

Artifacts chinh:

- `reports/eda/eda_report.md`
- `reports/eda/summary.json`
- `reports/eda/image_stats.csv`
- `reports/eda/duplicate_groups_raw_sha256.csv`
- `reports/figures/eda/*.png`

Buoc nay giup xac nhan:

- phan bo class
- do sang/contrast co ban
- duplicate groups theo hash
- mau anh dai dien cua dataset

## 7. Thu nghiem va rut gon lineup model

Repo da di qua giai doan thu nghiem nhieu bien the, nhung hien tai chi giu 3 model chinh de docs va benchmark nhat quan hon.

Lineup chot:

| Run | Architecture | Vai tro |
|---|---|---|
| `baseline_effb0` | EfficientNet-B0 | model mac dinh |
| `baseline_resnet18` | ResNet18 | benchmark transfer-learning |
| `baseline_custom_cnn` | Custom CNN | baseline nhe |

Nhung huong khong con trong main lineup:

- `ResNet50` benchmark cu
- `custom_cnn_8layer`
- trial them softmax rieng o output
- mot so bien the attention/augmentation khong cho loi ich on dinh

Muc tieu cua viec rut lineup:

- de cau chuyen benchmark ro rang
- giam chi phi bao tri config, docs, artifact
- giu lai 3 huong de so sanh de hieu nhat: pretrained nhe, pretrained benchmark, va CNN tu thiet ke

### Thiet ke cua `baseline_custom_cnn`

`baseline_custom_cnn` la CNN tu thiet ke, khong dung pretrained backbone. Model nay duoc giu lai nhu baseline nhe de doi chieu voi hai huong transfer-learning.

Kien truc cua model gom 2 phan:

- `feature extractor`: 4 `ConvBlock` lien tiep voi so kenh tang dan `32 -> 64 -> 128 -> 256`
- `classifier head`: `Global Average Pooling -> BatchNorm1d -> Dropout -> Linear(256 -> 128) -> ReLU -> Dropout -> Linear(128 -> num_classes)`

Moi `ConvBlock` co cau truc:

- `Conv3x3 -> BatchNorm -> ReLU`
- `Conv3x3 -> BatchNorm -> ReLU`
- `MaxPool2d`

Y tuong cua thiet ke nay la:

- giu model don gian, de giai thich
- tang dan do sau va so kenh de hoc dac trung tu muc thap den muc cao
- dung `AdaptiveAvgPool2d(1)` de rut gon dac trung truoc khi dua vao fully connected head
- dung `Dropout` o classifier head de giam overfitting

Trong repo hien tai, config mac dinh cua model nay dung:

- `dropout: 0.3`
- `head_hidden_dim: 128`
- `pretrained: false`

Model nay khong phai model duoc chot cuoi cung, nhung van rat huu ich trong benchmark vi checkpoint nho, de train, va cho phep so sanh xem mot CNN tu thiet ke co the di den dau tren bo du lieu hien tai.

## 8. Train va evaluate

Train model mac dinh:

```bash
python scripts/train.py --config configs/train.yaml
```

Train 2 model con lai:

```bash
python scripts/train.py --config configs/train_resnet18.yaml
python scripts/train.py --config configs/train_custom_cnn.yaml
```

Evaluate:

```bash
python scripts/evaluate.py --config configs/train.yaml --checkpoint models/checkpoints/baseline_effb0/best.pt --split test
```

Tong hop benchmark:

```bash
python scripts/compare_models.py
python scripts/plot_training_history.py
```

Benchmark chinh duoc luu trong:

- `reports/metrics/`
- `reports/model_comparison/`
- `reports/training_history/`

`reports/metrics_newdata/` chi nen xem la khu vuc evaluate ad-hoc khi bo du lieu thay doi, khong phai benchmark chinh da chot.

## 9. Ket qua cuoi cung

Theo benchmark hien tai trong `reports/model_comparison/comparison.csv`:

| Run | Params (M) | Checkpoint (MB) | Best Epoch | Test Accuracy | Test Macro F1 | Test Loss |
|---|---:|---:|---:|---:|---:|---:|
| `baseline_effb0` | 4.01 | 46.35 | 6 | 0.9964 | 0.9967 | 0.0152 |
| `baseline_custom_cnn` | 1.21 | 13.86 | 32 | 0.9929 | 0.9933 | 0.0258 |
| `baseline_resnet18` | 11.18 | 128.05 | 7 | 0.9929 | 0.9933 | 0.0269 |

Dien giai nhanh:

- `baseline_effb0` dang cho ket qua tot nhat tren benchmark chinh
- `baseline_custom_cnn` nhe nhat va co metric rat gan `ResNet18`
- `baseline_resnet18` dong vai tro benchmark transfer-learning de doi chieu voi backbone quen thuoc

## 10. Mo hinh duoc chot

Neu can chot mot model mac dinh cho train, inference, demo, va docs thi repo hien chot:

`baseline_effb0`

Ly do:

- metric cao nhat trong 3 model chot
- nhe hon `ResNet18` rat nhieu
- da la config mac dinh trong `configs/train.yaml` va `configs/inference.yaml`
- de giai thich hon trong tai lieu cuoi cung

Vai tro 2 model con lai:

- `baseline_resnet18`: model benchmark de so sanh trong report
- `baseline_custom_cnn`: phuong an nhe nhat khi uu tien checkpoint size

## 11. Gioi han hien tai

Nhung diem can ghi ro trong docs va report:

1. current validation la image-level, chua phai patient-level
2. `Datos` khong co `acute_otitis_media`, nen can than trong khi ban ve domain shift
3. benchmark hien tai la noi bo tren bo split da deduplicate, chua thay the external validation
4. neu data tiep tuc doi, can rerun dong bo cho ca 3 model truoc khi chot lai benchmark

## 12. Lenh tu dau den cuoi

Neu muon chay lai toan bo pipeline theo thu tu, co the di theo flow sau:

```bash
python data/raw/pull_data.py --force
python scripts/process_data.py --config configs/data.yaml --force
python scripts/prepare_data.py --config configs/data.yaml
python scripts/eda.py --config configs/data.yaml --output-dir reports/eda
python scripts/train.py --config configs/train.yaml
python scripts/evaluate.py --config configs/train.yaml --checkpoint models/checkpoints/baseline_effb0/best.pt --split test
python scripts/compare_models.py
python scripts/plot_training_history.py
```

Neu can mot cau tong ket ngan:

Project da di tu bo du lieu public hop nhat, qua buoc lam sach va split duplicate-aware, thu nghiem nhieu bien the model, rut gon ve 3 model chinh, va hien chot `EfficientNet-B0` la model mac dinh cho pipeline.
