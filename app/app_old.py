import os
import time
import numpy as np
import pandas as pd
import streamlit as st

# ----------------------------
# PAGE CONFIG
# ----------------------------
st.set_page_config(
    page_title="NASA Mission Control - Aditya L1",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ----------------------------
# STYLE
# ----------------------------
st.markdown("""
<style>
    body {
        background-color: #0B0F19;
        color: #E6F1FF;
    }
    .title {
        font-size: 28px;
        font-weight: 700;
        color: #7DD3FC;
    }
    .subtitle {
        color: #93C5FD;
        font-size: 16px;
    }
</style>
""", unsafe_allow_html=True)


# ----------------------------
# LOAD DATA (SAFE)
# ----------------------------
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

df = pd.read_parquet(os.path.join(BASE_DIR, "outputs", "clean_data.parquet"))

try:
    events = pd.read_csv(os.path.join(BASE_DIR, "outputs", "event_catalogue.csv"))
except:
    events = pd.DataFrame()


# ----------------------------
# FIX: ENSURE REQUIRED COLUMNS EXIST
# ----------------------------
if "flare_prob" not in df.columns:
    df["flare_prob"] = 0.0

if "flare_now" not in df.columns:
    df["flare_now"] = False

# 🔥 IMPORTANT FIX (your error)
if "flare_future" not in df.columns:
    # fallback = simple approximation
    df["flare_future"] = df["flare_prob"] > 0.5


# ----------------------------
# STATUS ENGINE
# ----------------------------
def solar_status(p):
    if p < 0.2:
        return "🟢 QUIET SUN"
    elif p < 0.5:
        return "🟡 ACTIVE REGION"
    elif p < 0.8:
        return "🟠 SOLAR ACTIVITY RISING"
    else:
        return "🔴 SOLAR STORM WARNING"


# ----------------------------
# SIDEBAR
# ----------------------------
st.sidebar.title("🛰 Mission Control Panel")
speed = st.sidebar.slider("Replay Speed", 0.1, 2.0, 0.5)


# ----------------------------
# TITLE
# ----------------------------
st.markdown('<div class="title">🌞 NASA-STYLE SOLAR FLARE DASHBOARD</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Aditya-L1 Real-Time System</div>', unsafe_allow_html=True)

placeholder = st.empty()
step = max(1, len(df) // 300)


# ----------------------------
# LIVE LOOP
# ----------------------------
for i in range(100, len(df), step):

    window = df.iloc[:i]
    latest = window.iloc[-1]

    with placeholder.container():

        # ------------------------
        # METRICS
        # ------------------------
        c1, c2, c3, c4 = st.columns(4)

        c1.metric("TIME", str(latest["time"]))
        c2.metric("SOFT X-RAY", f"{latest['soft_flux']:.3f}")
        c3.metric("HARD X-RAY", f"{latest['hard_flux']:.3f}")

        prob = float(latest["flare_prob"])
        c4.metric("FLARE RISK", f"{prob:.1%}")

        st.divider()

        # ------------------------
        # STATUS
        # ------------------------
        st.markdown("### ☀ Solar Status")
        st.success(solar_status(prob))
        st.progress(prob)

        # ------------------------
        # ALERTS
        # ------------------------
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### 🚨 NOWCAST")
            if latest["flare_now"]:
                st.error("ACTIVE SOLAR FLARE DETECTED")
            else:
                st.success("No active flare")

        with col2:
            st.markdown("### 🔮 FORECAST")
            if latest["flare_future"]:
                st.warning("Flare expected within 15 minutes")
            else:
                st.info("No flare expected")

        # ------------------------
        # GRAPH
        # ------------------------
        st.markdown("### 📡 X-Ray Telescope Feed")

        st.line_chart(
            window[["soft_flux", "hard_flux"]].tail(400)
        )

        # ------------------------
        # EVENTS
        # ------------------------
        st.markdown("### 📌 Flare Event Log")

        if len(events) > 0:
            st.dataframe(events.tail(10), use_container_width=True)
        else:
            st.info("No flare events detected")

        # ------------------------
        # TELEMETRY (FIXED)
        # ------------------------
        with st.expander("🧪 Raw Telemetry Data (Explained View)"):

            raw = window.tail(8).copy()

            def interpret(v, mode):
                if mode == "soft":
                    return "Normal" if v < 1 else "Elevated" if v < 3 else "High flare region"
                else:
                    return "Stable" if v < 0.5 else "Moderate" if v < 1.5 else "Strong disturbance"

            table = pd.DataFrame()

            table["Time"] = raw["time"]
            table["Soft X-ray"] = raw["soft_flux"].round(3)
            table["Soft Status"] = raw["soft_flux"].apply(lambda x: interpret(x, "soft"))

            table["Hard X-ray"] = raw["hard_flux"].round(3)
            table["Hard Status"] = raw["hard_flux"].apply(lambda x: interpret(x, "hard"))

            table["Nowcast"] = raw["flare_now"].apply(lambda x: "🚨 ACTIVE" if x else "OK")

            table["Forecast"] = raw["flare_future"].apply(lambda x: "⚠ YES" if x else "Stable")

            table["Risk"] = raw["flare_prob"].apply(
                lambda x: "Low" if x < 0.2 else "Medium" if x < 0.5 else "High" if x < 0.8 else "Critical"
            )

            st.dataframe(table, use_container_width=True)

    time.sleep(speed)