# Ear Disease Classifier

Pipeline phan loai benh tai tu anh noi soi tai. Repo nay gom data ingestion, processing, split duplicate-aware, train/evaluate, inference, demo app, va bo docs de giai thich trang thai hien tai cua project.

> Luu y: day la project nghien cuu/ho tro sang loc, khong thay the chan doan cua bac si.

## Trang Thai Hien Tai

- Default pipeline dang dung `data/`, khong dung `data_lake/` trong train/eval mac dinh.
- Default train config la [`configs/train.yaml`](configs/train.yaml), tuong ung run `baseline_effb0`.
- `data/raw/pull_data.py` co the gom nhieu local source trong `data/raw/` nhu `Oto-Endoscopic_Images` va `Datos`.
- Benchmark chinh hien tai nam trong `reports/metrics/`.
- `reports/metrics_newdata/` nen xem la khu vuc evaluate ad-hoc khi bo du lieu thay doi.

## Cau Truc

```text
configs/                 # data, train, evaluate, inference config
data/
  raw/                   # source folders, raw/images, raw/labels.csv
  processed/             # anh resize + metadata sau processing
  splits/                # train/val/test CSV
docs/                    # docs chinh cua project
models/                  # checkpoints va exported models
reports/                 # metrics, EDA, model comparison
scripts/                 # CLI entrypoints
src/ear_classifier/      # package chinh
tests/                   # smoke/unit tests
```

## Cai Dat

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev,app,tracking,data]"
```

Neu chi can train/evaluate local theo config mac dinh (MLflow bat san):

```bash
python -m pip install -e ".[dev,tracking]"
```

## Quick Start

1. Gom local sources va tao raw labels:

```bash
python data/raw/pull_data.py --force
```

2. Process raw images:

```bash
python scripts/process_data.py --config configs/data.yaml --force
```

3. Tao train/val/test split:

```bash
python scripts/prepare_data.py --config configs/data.yaml
```

4. Chay EDA:

```bash
python scripts/eda.py --config configs/data.yaml --output-dir reports/eda
```

5. Train default model:

```bash
python scripts/train.py --config configs/train.yaml
```

Run metrics se duoc log local vao `mlruns/`.

6. Evaluate default model:

```bash
python scripts/evaluate.py --config configs/train.yaml --checkpoint models/checkpoints/baseline_effb0/best.pt --split test
```

## Docs

- [`docs/project_summary.md`](docs/project_summary.md): ban tong hop tu dau den cuoi cua project, tu du lieu den model chot.
- [`docs/data_pipeline.md`](docs/data_pipeline.md): luong du lieu mac dinh, current sources, caveat cua `Datos`, va y nghia tung artifact.
- [`docs/models.md`](docs/models.md): inventory model, metric benchmark, va khuyen nghi model nen chot.
- [`docs/data_contract.md`](docs/data_contract.md): schema/metadata contract cho `labels.csv`.
- [`docs/data_lake.md`](docs/data_lake.md): pipeline data lake. Hien tai la path optional, khong phai default.

## Du Lieu

Hai local source dang co mat trong `data/raw/`:

- `Oto-Endoscopic_Images`: 5 class goc tu bo Kaggle/UCI.
- `Datos`: 4 class (`cerumen_impaction`, `chronic_otitis_media`, `myringosclerosis`, `normal`), khong co `acute_otitis_media`.

Khi chay `python data/raw/pull_data.py --force`, script se:

- uu tien gom cac folder source local trong `data/raw/`
- copy anh vao `data/raw/images/<class>/...`
- tao `data/raw/labels.csv`
- gan cot `source` de track anh den tu source nao
- sinh `patient_id` synthetic theo tung anh vi current public sources khong co patient id that

Current split van la image-level proxy split, khong phai patient-level split that. Config split dung `raw_sha256` de duplicate exact-match nam cung split.
Mac dinh moi cung bat `split.deduplicate_by_group: true`, nen moi `raw_sha256` chi giu 1 dai dien trong CSV split.

Neu can build chi tu mot source cu the:

```bash
python data/raw/pull_data.py --force --skip-download --source-dir data/raw/Oto-Endoscopic_Images
python data/raw/pull_data.py --force --skip-download --source-dir data/raw/Datos
```

## Model Recommendation

Neu can chot mot model mac dinh cho repo luc nay, nen chot `baseline_effb0`.

Lineup chot cua repo:

- `baseline_effb0`
- `baseline_resnet18`
- `baseline_custom_cnn`

Ly do:

- dang cao nhat tren benchmark chinh
- nhe hon benchmark transfer-learning va van la backbone quen thuoc, de defend trong report
- da co san config default cho train, evaluate, va inference
- cac bien the CBAM/SE/strong augmentation hien tai chua cho thay loi ich on dinh de thay baseline

Goi y cach dung:

- `baseline_effb0`: default model cho train/inference/demo
- `baseline_resnet18`: benchmark transfer-learning de so sanh trong nghien cuu
- `baseline_custom_cnn`: phuong an nhe nhat neu uu tien size/checkpoint

Notebook `ResNet50` duoc giu lai nhu artifact lich su, nhung khong nam trong lineup chot nua.

Chi tiet metric, params, checkpoint size, va ly do chon model nam trong [`docs/models.md`](docs/models.md).

## Inference Va Demo

Predict mot anh bang model mac dinh:

```bash
python scripts/predict_image.py ^
  --config configs/inference.yaml ^
  --checkpoint models/checkpoints/baseline_effb0/best.pt ^
  --image data/raw/images/example.jpg
```

Streamlit demo:

```bash
streamlit run app/streamlit_app.py
```

FastAPI demo:

```bash
uvicorn app.api:app --reload
```

Next.js web UI (`app/ai_diagnosis_UI`) hien co the goi truc tiep FastAPI `/predict`.
Neu khong set `API_URL_AI`, server route cua UI se mac dinh goi:

```text
http://127.0.0.1:8000/predict
```

De chay UI cung FastAPI local:

```bash
uvicorn app.api:app --reload
cd app/ai_diagnosis_UI
npm install
npm run dev
```

Neu muon override AI endpoint, dat `API_URL_AI` trong env cua Next.js app.

## Docker

Repo co san stack Docker cho:

- `ai-api`: FastAPI inference service
- `web`: Next.js web app

File lien quan:

- `Dockerfile.api`
- `app/ai_diagnosis_UI/Dockerfile`
- `docker-compose.yml`
- `.env.docker.example`

Buoc chay:

```bash
copy .env.docker.example .env.docker
docker compose --env-file .env.docker up --build
```

Mac dinh:

- web app: `http://localhost:3000`
- FastAPI: `http://localhost:8000`

Luu y:

- `docker-compose.yml` mount `./models` vao container `ai-api`, nen checkpoint local can ton tai, toi thieu la `models/checkpoints/baseline_effb0/best.pt`.
- `API_URL_AI` trong compose mac dinh la `http://ai-api:8000/predict`.
- Neu de trong `MONGO_URI`, web app van chay duoc luong upload/predict nhung se o che do `no-DB`.
- O che do `no-DB`, cac tinh nang luu profile, history, report, va manage se khong hoat dong.
- Cac bien `NEXT_PUBLIC_FIREBASE_*` va `FIREBASE_SERVICE_ACCOUNT_KEY_PATH` chi can dien khi muon dung auth/profile/report day du cung MongoDB ngoai.
- Volume `web_uploads` duoc dung de giu anh upload cua web app qua cac lan restart container.

## Model Comparison

Tong hop so sanh cac run da train:

```bash
python scripts/compare_models.py
python scripts/plot_training_history.py
```

Artifacts duoc ghi vao:

- `reports/model_comparison/`
- `reports/training_history/`

## Data Lake

Project van giu `data_lake/` va script lien quan, nhung hien tai day khong phai luong mac dinh. Neu khong can quan ly bronze/silver/gold thi co the bo qua muc nay.

Neu can:

```bash
python scripts/build_data_lake.py --config configs/data_lake.yaml --stage all --force
python scripts/validate_data_lake.py --config configs/data_lake.yaml
```

Chi tiet xem tai [`docs/data_lake.md`](docs/data_lake.md).
