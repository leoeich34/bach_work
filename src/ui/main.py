# src/ui/main.py

"""
Интерактивная панель Streamlit для анализа сетевого трафика:
• Batch-анализ загруженного файла
• Live-мониторинг из Kafka topic=flows
• Генерация тестовых аномалий (порт-скан, DoS, tcpreplay)
"""

from __future__ import annotations
import json
import subprocess
import threading
import time
from collections import deque
from pathlib import Path
from typing import Tuple

import joblib
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from kafka import KafkaConsumer

from src.actions.firewall import block_ip
from src.ui.utils import load_model_and_scaler, prepare_dataframe, predict_batch

# --- Настройки ---
MODEL_PATH = Path("src/models/saved/random_forest.joblib")
SCALER_PATH = Path("src/features/scaler.joblib")
COLUMNS_FILE = Path("src/features/columns.txt")
THRESHOLD = 0.80

KAFKA_BROKER = "localhost:29092"
KAFKA_TOPIC = "flows"
LIVE_INTERVAL = 5  # секунд между батчами
LIVE_WINDOW = 12   # сколько последних точек хранить

st.set_page_config(
    page_title="Anomaly-Detector UI",
    page_icon="🚦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Загрузка модели и скейлера
@st.cache_resource
def init_assets() -> Tuple[object, object]:
    model = joblib.load(MODEL_PATH)
    scaler = joblib.load(SCALER_PATH)
    return model, scaler

model, scaler = init_assets()

# Табы
tab_batch, tab_live, tab_sim = st.tabs([
    "🔍 Batch-анализ",
    "📈 Live-мониторинг",
    "🚨 Симуляция",
])

# ---------------------- TAB: Batch-анализ ----------------------
with tab_batch:
    st.header("🔍 Batch-анализ загруженного файла")
    uploaded = st.file_uploader(
        "Загрузите CSV / Parquet / NPY с фичами (70 столбцов)",
        type=["csv", "parquet", "npy"],
        key="batch_uploader"
    )
    if not uploaded:
        st.info("⬅️ Загрузите файл, чтобы начать.")
    else:
        # Чтение
        if uploaded.name.endswith(".csv"):
            df_raw = pd.read_csv(uploaded, low_memory=False)
        elif uploaded.name.endswith(".parquet"):
            df_raw = pd.read_parquet(uploaded)
        else:  # npy
            arr = np.load(uploaded)
            # для npy требуется columns.txt
            cols = [c.strip() for c in COLUMNS_FILE.read_text().splitlines() if c.strip()]
            df_raw = pd.DataFrame(arr, columns=cols)

        df = prepare_dataframe(df_raw, COLUMNS_FILE)
        X = df.values
        st.success(f"Загружено {len(df):,} строк, {df.shape[1]} признаков.")

        # Batch-инференс
        preds, probs = predict_batch(model, scaler, X, THRESHOLD)

        # Распределение по реальным меткам
        st.subheader("⚡ Распределение по реальным меткам (Label)")
        if "Label" in df_raw.columns:
            vc = df_raw["Label"].value_counts()
            fig = px.pie(
                names=vc.index.tolist(),
                values=vc.values.tolist(),
                color_discrete_sequence=px.colors.qualitative.Set2,
                title="Реальные метки"
            )
        else:
            count_anom = int((preds == 1).sum())
            fig = px.pie(
                names=["Benign", "Anomaly"],
                values=[len(df)-count_anom, count_anom],
                color_discrete_sequence=px.colors.qualitative.Set2,
                title="Предсказания модели"
            )
        st.plotly_chart(fig, use_container_width=True)

        # Топ-анималий по score
        st.subheader("🔎 Топ-анималий по score")
        top_n = st.slider("Показать топ N:", 5, 100, 20)
        idx = np.argsort(-probs)[:top_n]
        df_top = df_raw.iloc[idx].copy()
        df_top.insert(0, "score", probs[idx])
        st.dataframe(df_top, use_container_width=True)

        # Скачивание
        buf = df_raw.copy()
        buf["score"] = probs
        buf["label_pred"] = preds
        st.download_button(
            "💾 Скачать результаты (CSV)",
            data=buf.to_csv(index=False),
            file_name="predictions.csv",
            mime="text/csv"
        )

# ---------------------- TAB: Live-мониторинг ----------------------
with tab_live:
    st.header("📈 Live-мониторинг трафика")
    st.write(f"Читаем из Kafka `topic={KAFKA_TOPIC}` каждые {LIVE_INTERVAL}s.")

    # История
    times = deque(maxlen=LIVE_WINDOW)
    counts = deque(maxlen=LIVE_WINDOW)

    placeholder_metric = st.empty()
    placeholder_chart = st.empty()

    def consume_live():
        consumer = KafkaConsumer(
            KAFKA_TOPIC,
            bootstrap_servers=KAFKA_BROKER,
            value_deserializer=lambda b: json.loads(b.decode()),
            auto_offset_reset="latest",
            enable_auto_commit=True
        )
        for msg in consumer:
            batch = np.array(msg.value, dtype=float)
            Xb = scaler.transform(batch)
            probs_b = model.predict_proba(Xb)[:,1]
            num = int((probs_b >= THRESHOLD).sum())

            t = time.strftime("%H:%M:%S")
            times.append(t)
            counts.append(num)

            placeholder_metric.metric("Аномалий в последнем батче", f"{num}")
            fig = go.Figure(go.Scatter(x=list(times), y=list(counts), mode="lines+markers"))
            fig.update_layout(
                title="Аномалии во времени",
                xaxis_title="Время", yaxis_title="Число аномалий"
            )
            placeholder_chart.plotly_chart(fig, use_container_width=True)

    if st.button("▶️ Запустить Live-мониторинг"):
        threading.Thread(target=consume_live, daemon=True).start()
        st.info("Live-мониторинг запущен.")

    # Блокировка IP (если есть хранение suspects в session_state)
    st.write("---")
    st.subheader("🔒 Блокировка подозрительных IP")
    if "suspects" not in st.session_state:
        st.session_state.suspects = set()
    for ip in st.session_state.suspects:
        c1, c2 = st.columns([3,1])
        c1.write(f"– {ip}")
        if c2.button("Блок", key=f"blk_{ip}"):
            block_ip(ip)
            st.success(f"IP {ip} заблокирован")

# ---------------------- TAB: Симуляция ----------------------
with tab_sim:
    st.header("🚨 Генерация тестовых аномалий")
    target = st.text_input("Цель (IP)", "127.0.0.1")
    iface  = st.text_input("Интерфейс для tcpreplay", "en0")

    if st.button("🔍 Запустить порт-скан (nmap)"):
        subprocess.Popen(["nmap","-sS","-p1-1000",target])
        st.info("nmap в фоне…")

    if st.button("💥 DoS-импульс (hping3)"):
        subprocess.Popen(["sudo","hping3","-S","-c","2000","-i","u1000","-p","80",target])
        st.info("hping3 запущен…")

    if st.button("▶️ tcpreplay sample"):
        sample = Path("samples/test_attack.pcap")
        subprocess.Popen(["sudo","tcpreplay","--intf1",iface,str(sample)])
        st.info("tcpreplay запущен…")