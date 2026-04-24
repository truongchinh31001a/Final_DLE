# Models

Tai lieu nay gom 3 model chinh cua repo sau khi da don lineup.

## Main Lineup

Repo hien tai chi giu 3 model chinh:

| Run | Architecture | Vai tro |
|---|---|---|
| `baseline_effb0` | EfficientNet-B0 | model mac dinh cho train/inference/demo |
| `baseline_resnet18` | ResNet18 | benchmark transfer-learning |
| `baseline_custom_cnn` | CustomCNN | phuong an nhe, checkpoint nho |

Muc tieu cua viec rut lineup:

- giam so luong config/checkpoint/doc can bao tri
- de cau chuyen benchmark ro rang hon
- tranh giu cac bien the attention/augmentation khong dem lai loi ich on dinh

## Benchmark Chinh

Benchmark chinh hien tai la `reports/metrics/`.

Can luu y:

- current split van la image-level proxy split vi current public sources khong co patient id that
- `reports/metrics_newdata/` la khu vuc evaluate ad-hoc, khong phai benchmark chinh da chot

## So Sanh 3 Model Chinh

| Run | Params (M) | Checkpoint (MB) | Test Accuracy | Test Macro F1 | Test Loss | Vai tro khuyen nghi |
|---|---:|---:|---:|---:|---:|---|
| `baseline_effb0` | 4.01 | 46.35 | 0.9964 | 0.9967 | 0.0152 | model mac dinh |
| `baseline_resnet18` | 11.18 | 128.05 | 0.9929 | 0.9933 | 0.0269 | model benchmark |
| `baseline_custom_cnn` | 1.21 | 13.86 | 0.9929 | 0.9933 | 0.0258 | model nhe |

So lieu tren duoc tong hop tu:

- `reports/metrics/<run_name>/test_metrics.json`
- `models/checkpoints/<run_name>/best.pt`
- `reports/model_comparison/model_comparison.md`

Tom tat nhanh:

- `baseline_effb0` dang cao nhat tren benchmark chinh va van giu checkpoint nho hon `baseline_resnet18` rat nhieu.
- `baseline_resnet18` la benchmark transfer-learning de doi chieu voi backbone quen thuoc trong report.
- `baseline_custom_cnn` gan nhu ngang `baseline_resnet18` tren split hien tai nhung nhe hon dang ke.

## Nen Chot Model Nao?

Neu can chot **mot model mac dinh cho repo**, nen chot:

`baseline_effb0`

Ly do:

- metric dang cao nhat trong 3 model chot
- nhe hon `baseline_resnet18` rat nhieu
- da co san config mac dinh cho train va inference
- de defend hon trong report so voi mot CNN tu thiet ke

## Vai Tro Tung Model

### 1. `baseline_effb0`

Dung cho:

- `configs/train.yaml`
- `configs/inference.yaml`
- demo app
- tai lieu chinh cua project

Day la model can bang tot nhat giua:

- performance
- size checkpoint
- do quen thuoc cua backbone pretrained

### 2. `baseline_resnet18`

Dung cho:

- benchmark transfer-learning
- bang so sanh trong report
- kiem tra xem dataset moi co thuong backbone lon hon hay khong

Model nay hien da co benchmark day du tren split chinh va nen duoc giu de doi chieu voi `EfficientNet-B0`.

### 3. `baseline_custom_cnn`

Dung cho:

- baseline nhe
- demo local nhanh
- khi uu tien checkpoint nho va simplicity

Model nay la phuong an backup hop ly neu can mot architecture don gian hon backbone pretrained.

## Cac Bien The Khong Con Trong Main Lineup

Mot so bien the attention, strong augmentation, va trial noi bo da duoc loai khoi lineup chinh.

Ly do chung:

- khong vuot model chinh mot cach on dinh
- lam repo, docs, config va artifact kho bao tri hon
- khong can thiet cho cau chuyen benchmark chinh

## Khi Data Thay Doi

Gan day repo co them source `Datos`, va benchmark ad-hoc trong `reports/metrics_newdata/` chua duoc rerun dong bo cho tat ca model.

Vi vay:

- khong nen doi model mac dinh chi dua tren `metrics_newdata`
- neu muon chot lai model sau khi doi data, nen rerun evaluate cung mot bo split cho ca 3 model chinh

## Lenh Huu Ich

Train model mac dinh:

```bash
python scripts/train.py --config configs/train.yaml
```

Train benchmark ResNet18:

```bash
python scripts/train.py --config configs/train_resnet18.yaml
```

Train lightweight model:

```bash
python scripts/train.py --config configs/train_custom_cnn.yaml
```

Evaluate default model:

```bash
python scripts/evaluate.py ^
  --config configs/train.yaml ^
  --checkpoint models/checkpoints/baseline_effb0/best.pt ^
  --split test
```

Predict mot anh bang default model:

```bash
python scripts/predict_image.py ^
  --config configs/inference.yaml ^
  --checkpoint models/checkpoints/baseline_effb0/best.pt ^
  --image data/raw/images/example.jpg
```

Tong hop model comparison:

```bash
python scripts/compare_models.py
python scripts/plot_training_history.py
```
