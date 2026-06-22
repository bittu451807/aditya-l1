import os
import time
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Aditya-L1 Solar Intelligence",
    page_icon="☀",
    layout="wide"
)

st.markdown("""
<style>
.stApp{
    background:#030712;
    color:white;
}
.main-title{
    font-size:42px;
    font-weight:bold;
    text-align:center;
    color:#60A5FA;
}
.sub-title{
    font-size:18px;
    text-align:center;
    color:#CBD5E1;
}
[data-testid="stMetric"]{
    background:#111827;
    padding:12px;
    border-radius:10px;
}
</style>""", unsafe_allow_html=True)

st.markdown("""
<div class="main-title">
☀ ADITYA-L1 SOLAR INTELLIGENCE SYSTEM
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="sub-title">
Real Time Solar Monitoring | Forecasting | Explainable AI
</div>
""", unsafe_allow_html=True)

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

DATA_PATH = os.path.join(BASE_DIR, "outputs", "clean_data.parquet")
CATALOGUE_PATH = os.path.join(BASE_DIR, "outputs", "event_catalogue.csv")


@st.cache_data
def load_data():
    df = pd.read_parquet(DATA_PATH)
    df["time"] = pd.to_datetime(df["time"])
    return df


@st.cache_data
def load_catalogue():
    if os.path.exists(CATALOGUE_PATH):
        return pd.read_csv(CATALOGUE_PATH)
    return pd.DataFrame()


default_df = load_data()
catalogue = load_catalogue()

st.sidebar.title("🛰 Mission Control")

replay_speed = st.sidebar.slider("Replay Speed", 0.01, 1.0, 0.05)
window_size = st.sidebar.slider("Graph Window", 100, 5000, 1000)
judge_mode = st.sidebar.checkbox("🧪 Judge Evaluation Mode")

df = default_df

if judge_mode:
    solexs_file = st.sidebar.file_uploader("Upload SoLEXS File", type=["csv", "parquet"], key="solexs")
    hel1os_file = st.sidebar.file_uploader("Upload HEL1OS File", type=["csv", "parquet"], key="hel1os")

    if solexs_file is not None and hel1os_file is not None:
        if solexs_file.name.endswith(".csv"):
            solexs = pd.read_csv(solexs_file)
        else:
            solexs = pd.read_parquet(solexs_file)

        if hel1os_file.name.endswith(".csv"):
            hel1os = pd.read_csv(hel1os_file)
        else:
            hel1os = pd.read_parquet(hel1os_file)

        solexs["time"] = pd.to_datetime(solexs["time"])
        hel1os["time"] = pd.to_datetime(hel1os["time"])

        solexs = solexs.sort_values("time")
        hel1os = hel1os.sort_values("time")

        df = pd.merge_asof(solexs, hel1os, on="time", direction="nearest")

        if "activity_level" not in df.columns:
            df["activity_level"] = 0
        if "activity_score" not in df.columns:
            df["activity_score"] = 0.0
        if "flare_now" not in df.columns:
            df["flare_now"] = False

        st.sidebar.success(f"Loaded {len(df):,} rows")


def level_to_class(level):
    if level == 0:
        return "A/B"
    elif level == 1:
        return "C"
    elif level == 2:
        return "M"
    return "X"


def level_to_text(level):
    if level == 0:
        return "Quiet Sun"
    elif level == 1:
        return "Moderate Activity"
    elif level == 2:
        return "Strong Activity"
    return "Extreme Activity"


dashboard = st.empty()
step_size = max(1, len(df) // 500)

for i in range(window_size, len(df), step_size):
    window = df.iloc[max(0, i - window_size):i]
    latest = window.iloc[-1]

    activity_level = int(latest.get("activity_level", 0))
    activity_score = float(latest.get("activity_score", 0))
    solar_class = level_to_class(activity_level)

    risk = min(99, max(1, int(abs(activity_score) * 10)))

    with dashboard.container():
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Solar Class", solar_class)
        m2.metric("Risk %", risk)
        m3.metric("Activity Level", activity_level)
        m4.metric("Time", str(latest["time"]))

        st.markdown("---")

        if activity_level == 0:
            st.success("🟢 Quiet Sun")
        elif activity_level == 1:
            st.warning("🟡 C-Class Activity")
        elif activity_level == 2:
            st.error("🟠 M-Class Activity")
        else:
            st.error("🔴 X-Class Activity")

        st.progress(risk / 100)

        left, right = st.columns(2)

        with left:
            if "soft_flux" in window.columns:
                st.markdown("### SoLEXS Live Feed")
                st.line_chart(window.set_index("time")[["soft_flux"]])

        with right:
            if "hard_flux" in window.columns:
                st.markdown("### HEL1OS Live Feed")
                st.line_chart(window.set_index("time")[["hard_flux"]])

        if "soft_flux" in window.columns and "hard_flux" in window.columns:
            st.markdown("### Combined Solar Activity")
            st.line_chart(window.set_index("time")[["soft_flux", "hard_flux"]])

        if "activity_score" in window.columns:
            st.markdown("### Activity Score")
            st.line_chart(window.set_index("time")[["activity_score"]])

        st.markdown("### Explainable AI")

        if activity_level == 0:
            st.info("Solar emissions are currently stable.")
        elif activity_level == 1:
            st.warning("Detected behaviour resembles historical C-class activity.")
        elif activity_level == 2:
            st.error("Detected behaviour resembles historical M-class activity.")
        else:
            st.error("Detected behaviour resembles historical X-class activity.")

    time.sleep(replay_speed)

st.markdown("---")
st.markdown("## 🌋 Solar Event Catalogue")

if len(catalogue) > 0:
    display_catalogue = catalogue.copy()
    if "activity_level" in display_catalogue.columns:
        display_catalogue["Class"] = display_catalogue["activity_level"].apply(level_to_class)

    st.dataframe(display_catalogue.tail(100), use_container_width=True, height=350)
else:
    st.info("No events available")

st.markdown("---")
st.markdown("## 🏆 Strongest Solar Events")

if len(catalogue) > 0 and "peak_flux" in catalogue.columns:
    strongest = catalogue.sort_values("peak_flux", ascending=False).head(10)
    st.dataframe(strongest, use_container_width=True)

st.markdown("---")
st.markdown("## 📊 Activity Distribution")

if "activity_level" in df.columns:
    counts = df["activity_level"].value_counts().sort_index()
    distribution = pd.DataFrame({
        "Class": ["A/B", "C", "M", "X"],
        "Count": [
            counts.get(0, 0),
            counts.get(1, 0),
            counts.get(2, 0),
            counts.get(3, 0)
        ]
    })
    st.bar_chart(distribution.set_index("Class"))

st.markdown("---")
st.markdown("## 🚀 Mission Statistics")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Samples", f"{len(df):,}")
c2.metric("Detected Events", f"{len(catalogue):,}")

if "activity_level" in df.columns:
    c3.metric("Highest Class", level_to_class(int(df["activity_level"].max())))
    c4.metric("Maximum Level", int(df["activity_level"].max()))

if judge_mode:
    st.markdown("---")
    st.markdown("## 🧪 Judge Evaluation Mode")

    detected_events = int((df["activity_level"] >= 2).sum())
    avg_score = round(float(df["activity_score"].mean()), 2)

    j1, j2, j3 = st.columns(3)
    j1.metric("Detected Events", detected_events)
    j2.metric("Average Score", avg_score)
    j3.metric("Highest Class", level_to_class(int(df["activity_level"].max())))

    st.success("Judge uploaded dataset is driving all visualizations and analysis.")

st.markdown("---")
st.markdown("## ⬇ Download Results")

if len(catalogue) > 0:
    csv_data = catalogue.to_csv(index=False)
    st.download_button(
        label="Download Event Catalogue",
        data=csv_data,
        file_name="solar_events.csv",
        mime="text/csv"
    )

st.markdown("---")
st.markdown("""
🌟 System Capabilities

✅ SoLEXS Data Processing  
✅ HEL1OS Data Processing  
✅ Real-Time Solar Monitoring  
✅ Solar Activity Detection  
✅ Activity Classification
✅ Judge Evaluation Mode

✅ Forecasting Architecture

✅ Space Weather Intelligence

✅ Aditya-L1 Mission Dashboard
""")

st.markdown("---")

st.caption(
"Aditya-L1 Solar Intelligence System | Bharatiya Antariksh Hackathon 2026"
)


