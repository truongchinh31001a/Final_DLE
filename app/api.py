from __future__ import annotations

from functools import lru_cache
import tempfile
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile

from ear_classifier.inference.predictor import OtoscopyPredictor
from ear_classifier.inference.model_registry import (
    DEFAULT_MODEL_ID,
    list_available_models,
    resolve_model_checkpoint,
)


app = FastAPI(title="Ear Disease Classifier API")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/models")
def models() -> dict[str, object]:
    return {
        "default_model_id": DEFAULT_MODEL_ID,
        "models": list_available_models(),
    }


@lru_cache(maxsize=8)
def get_predictor(config: str, checkpoint: str | None) -> OtoscopyPredictor:
    return OtoscopyPredictor(config, checkpoint)


@app.post("/predict")
async def predict(
    file: UploadFile | None = File(None),
    files: list[UploadFile] | None = File(None),
    config: str = "configs/inference.yaml",
    model_id: str | None = None,
    checkpoint: str | None = None,
) -> dict:
    upload = file or (files[0] if files else None)
    if upload is None:
        raise HTTPException(status_code=400, detail="No file uploaded.")

    resolved_checkpoint = resolve_model_checkpoint(model_id=model_id, checkpoint=checkpoint)
    if model_id and resolved_checkpoint is None:
        available_model_ids = [item["id"] for item in list_available_models()]
        raise HTTPException(
            status_code=400,
            detail={
                "message": f"Unsupported model_id: {model_id}",
                "available_model_ids": available_model_ids,
            },
        )

    suffix = Path(upload.filename or "image.jpg").suffix or ".jpg"
    content = await upload.read()
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(content)
        image_path = Path(tmp.name)

    try:
        predictor = get_predictor(config, resolved_checkpoint)
        return predictor.predict(image_path)
    finally:
        image_path.unlink(missing_ok=True)
