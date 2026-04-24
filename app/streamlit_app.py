from __future__ import annotations

import tempfile
from pathlib import Path

import streamlit as st

from ear_classifier.inference.predictor import OtoscopyPredictor


st.set_page_config(page_title="Ear Disease Classifier", page_icon=":ear:")
st.title("Ear Disease Classifier")
st.caption("Research screening demo. Not a clinical diagnosis.")

config_path = st.text_input("Inference config", "configs/inference.yaml")
checkpoint_path = st.text_input("Checkpoint override", "")
uploaded = st.file_uploader("Upload otoscopy image", type=["jpg", "jpeg", "png", "bmp", "webp"])

if uploaded:
    suffix = Path(uploaded.name).suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as file:
        file.write(uploaded.getbuffer())
        image_path = file.name

    st.image(image_path, caption="Input image", use_container_width=True)
    if st.button("Predict"):
        predictor = OtoscopyPredictor(config_path, checkpoint_path or None)
        result = predictor.predict(image_path)
        st.subheader(result["label"])
        st.write(f"Confidence: {result['confidence']:.4f}")
        st.table(result["top_k"])

