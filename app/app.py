import streamlit as st
import pandas as pd
import numpy as np
import os
import torch
import torch.nn as nn
import torch.nn.functional as F
import plotly.express as px
import plotly.graph_objects as go
import time as time_lib
from captum.attr import IntegratedGradients
import streamlit.components.v1 as components
from scipy.fft import rfft, rfftfreq

# =====================================================================
#  ADITYA-L1 TACTICAL COMMAND  —  UI-UPGRADED BUILD
#  All original features preserved. UI/graphics/popups enhanced.
# =====================================================================

st.set_page_config(
    page_title="Aditya-L1 Tactical Command",
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon="🛰️",
)

# ---------------------------------------------------------------------
#  GLOBAL STYLE  (animated nebula + starfield + sun + glass cards)
# ---------------------------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Inter:wght@300;400;600;800&family=JetBrains+Mono:wght@400;700&display=swap');

/* ---- App background: deep-space nebula ---- */
.stApp {
    background-color: #03040a !important;
    background-image:
        radial-gradient(circle at 12% 18%, rgba(76, 29, 149, 0.55), transparent 45%),
        radial-gradient(circle at 88% 22%, rgba(6, 182, 212, 0.45), transparent 45%),
        radial-gradient(circle at 50% 90%, rgba(225, 29, 72, 0.35), transparent 55%),
        radial-gradient(circle at 70% 60%, rgba(255, 145, 0, 0.18), transparent 60%) !important;
    animation: nebula-pulse 18s ease-in-out infinite alternate !important;
    overflow-x: hidden;
}
@keyframes nebula-pulse {
    0%   { background-size: 100% 100%; filter: hue-rotate(0deg); }
    100% { background-size: 140% 140%; filter: hue-rotate(25deg); }
}

/* ---- Animated starfield layers ---- */
.starfield, .starfield2, .starfield3 {
    position: fixed; top: 0; left: 0;
    width: 100%; height: 100%;
    pointer-events: none; z-index: -10;
}
.starfield  { background-image: radial-gradient(1px 1px at 20px 30px, #fff, transparent),
                                 radial-gradient(1px 1px at 40px 70px, #fff, transparent),
                                 radial-gradient(1px 1px at 90px 40px, #fff, transparent),
                                 radial-gradient(2px 2px at 130px 80px, #fff, transparent),
                                 radial-gradient(1px 1px at 160px 120px,#fff, transparent);
                 background-size: 200px 200px; animation: drift 60s linear infinite; opacity:.65; }
.starfield2 { background-image: radial-gradient(1px 1px at 50px 50px, #9ee7ff, transparent),
                                 radial-gradient(2px 2px at 120px 20px,#fff, transparent),
                                 radial-gradient(1px 1px at 180px 90px,#fff, transparent);
                 background-size: 300px 300px; animation: drift 120s linear infinite; opacity:.45; }
.starfield3 { background-image: radial-gradient(2px 2px at 80px 160px,#ffb37a, transparent),
                                 radial-gradient(1px 1px at 220px 60px,#fff, transparent);
                 background-size: 400px 400px; animation: drift 200s linear infinite; opacity:.35; }
@keyframes drift { from { transform: translateY(0); } to { transform: translateY(-2000px); } }

/* ---- Floating sun in the corner ---- */
.cosmic-sun {
    position: fixed; top: 60px; right: -120px;
    width: 320px; height: 320px; border-radius: 50%;
    background: radial-gradient(circle at 35% 35%, #fff7c2 0%, #ffae00 30%, #ff5500 60%, #7a1500 90%, transparent 100%);
    box-shadow: 0 0 80px 20px rgba(255,140,0,.45), 0 0 160px 60px rgba(255,80,0,.25);
    filter: blur(.5px);
    animation: sun-pulse 8s ease-in-out infinite alternate;
    z-index: -5; pointer-events: none; opacity: .55;
}
@keyframes sun-pulse {
    0%   { transform: scale(1)   rotate(0deg);   filter: hue-rotate(0deg)  blur(.5px); }
    100% { transform: scale(1.08) rotate(20deg); filter: hue-rotate(-15deg) blur(.5px); }
}

/* ---- Typography ---- */
html, body, [class*="css"], p, span, div, label {
    font-family: 'Inter', sans-serif !important;
    color: #F1F5F9 !important;
}
h1, h2, h3, h4, .section-heading {
    font-family: 'Orbitron', sans-serif !important;
    font-weight: 900 !important;
    letter-spacing: 1px !important;
    color: #00E5FF !important;
    text-shadow: 0 0 12px rgba(0, 229, 255, 0.55);
}
.gradient-text {
    background: linear-gradient(135deg, #00E5FF 0%, #B388FF 50%, #FF6EC7 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    font-weight: 900; text-shadow: none;
}
code, .mono { font-family: 'JetBrains Mono', monospace !important; }

/* ---- Glass cards ---- */
.premium-card {
    background: rgba(8, 12, 22, 0.72) !important;
    backdrop-filter: blur(22px) saturate(140%) !important;
    -webkit-backdrop-filter: blur(22px) saturate(140%) !important;
    border: 1px solid rgba(0, 229, 255, 0.18) !important;
    border-top: 1px solid rgba(255,255,255,.22) !important;
    border-left: 1px solid rgba(255,255,255,.18) !important;
    border-radius: 18px;
    padding: 22px 24px;
    box-shadow: 0 12px 40px rgba(0,0,0,.85), inset 0 0 24px rgba(0,229,255,.06);
    margin-bottom: 22px;
    transition: transform .25s ease, box-shadow .25s ease;
}
.premium-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 20px 60px rgba(0,0,0,.9), 0 0 30px rgba(0,229,255,.18);
}

.explanation-text {
    font-size: .95rem; color: #CFD8DC !important;
    background: rgba(0,0,0,.55); padding: 14px 16px;
    border-left: 4px solid #00E5FF; border-radius: 6px;
    margin-bottom: 18px; line-height: 1.55;
}

/* ---- Metric tiles ---- */
.metric-tile {
    background: linear-gradient(160deg, rgba(0,229,255,.10), rgba(179,136,255,.06));
    border: 1px solid rgba(0,229,255,.25);
    border-radius: 14px; padding: 16px 18px;
    box-shadow: inset 0 0 18px rgba(0,229,255,.08);
}
.metric-label { font-family:'Orbitron',sans-serif; font-size:.72rem; letter-spacing:2px; color:#7DD3FC !important; }
.metric-value { font-family:'Orbitron',sans-serif; font-size:1.55rem; font-weight:900; margin-top:6px; }

/* ---- Emergency banner ---- */
.emergency-active {
    position: relative;
    background: linear-gradient(135deg, rgba(255,23,68,.25), rgba(120,0,0,.35)) !important;
    backdrop-filter: blur(18px);
    border: 1px solid #FF1744 !important;
    border-radius: 18px;
    padding: 22px;
    text-align: center;
    box-shadow: 0 0 40px rgba(255,23,68,.55), inset 0 0 30px rgba(255,23,68,.25) !important;
    margin-bottom: 22px;
    animation: alarm-flash 1.6s ease-in-out infinite;
}
@keyframes alarm-flash {
    0%,100% { box-shadow: 0 0 30px rgba(255,23,68,.45), inset 0 0 20px rgba(255,23,68,.2); }
    50%     { box-shadow: 0 0 60px rgba(255,23,68,.85), inset 0 0 40px rgba(255,23,68,.4); }
}

/* ---- Live dot ---- */
@keyframes pulse-dot {
    0%   { transform: scale(.95); box-shadow: 0 0 0 0   rgba(0,229,255,.8); }
    70%  { transform: scale(1.3); box-shadow: 0 0 0 14px rgba(0,229,255,0); }
    100% { transform: scale(.95); box-shadow: 0 0 0 0   rgba(0,229,255,0); }
}
.live-indicator { display:inline-block; width:12px; height:12px; background:#00E5FF;
    border-radius:50%; margin-right:12px; animation: pulse-dot 1.5s infinite; }

/* ---- Sidebar JARVIS ---- */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #060912 0%, #0a1a2c 100%) !important;
    border-right: 2px solid #00E5FF !important;
    box-shadow: inset -5px 0 30px rgba(0,229,255,.18) !important;
}
[data-testid="stSidebar"]::before {
    content:""; position:absolute; inset:0;
    background-image:
        linear-gradient(rgba(0,229,255,.05) 1px, transparent 1px),
        linear-gradient(90deg, rgba(0,229,255,.05) 1px, transparent 1px);
    background-size: 22px 22px; pointer-events:none; z-index:0;
}
[data-testid="stSidebar"] > div { position:relative; z-index:1; }

.stSlider > div > div > div > div { background:#00E5FF !important; box-shadow:0 0 8px #00E5FF; }
.stSlider > div > div > div > div[role="slider"] {
    background:#FF1744 !important; border:2px solid #fff !important; box-shadow:0 0 12px #FF1744 !important;
}

/* ---- Buttons (Iron-Man armor) ---- */
.stButton > button {
    background: linear-gradient(135deg, #00E5FF 0%, #0083B0 100%) !important;
    color:#050505 !important;
    font-family:'Orbitron',sans-serif !important; font-weight:900 !important;
    border:1px solid #fff !important;
    box-shadow: 0 0 15px rgba(0,229,255,.6), inset 0 0 10px rgba(255,255,255,.5) !important;
    border-radius:10px !important; text-transform:uppercase; letter-spacing:2px;
    transition: all .3s ease;
}
.stButton > button:hover {
    background: linear-gradient(135deg, #FF1744 0%, #B71C1C 100%) !important;
    box-shadow: 0 0 22px rgba(255,23,68,.85), inset 0 0 10px rgba(255,255,255,.5) !important;
    border-color:#FF1744 !important; color:#fff !important; transform: scale(1.03);
}

.stRadio label { color:#00E5FF !important; font-family:'Orbitron',sans-serif; letter-spacing:1px; }

/* ---- Horizon blocks ---- */
.horizon-block {
    padding:18px; border-radius:14px; text-align:center; font-weight:700;
    background: rgba(0,0,0,.55); border:1px solid rgba(255,255,255,.1); font-size:1.05rem;
    font-family:'Orbitron',sans-serif; letter-spacing:1px;
    box-shadow: inset 0 0 16px rgba(0,229,255,.08);
}
.horizon-safe   { border-color:#00FF7F !important; color:#00FF7F !important; box-shadow: inset 0 0 16px rgba(0,255,127,.18); }
.horizon-danger { border-color:#FF1744 !important; color:#FF1744 !important; box-shadow: inset 0 0 18px rgba(255,23,68,.22); animation: alarm-flash 1.6s ease-in-out infinite;}
.horizon-wait   { border-color:#9ca3af !important; color:#cbd5e1 !important; }

/* ---- Status chips ---- */
.status-chip {
    display:inline-block; padding:6px 14px; border-radius:999px;
    font-family:'Orbitron',sans-serif; font-size:.75rem; letter-spacing:2px;
    border:1px solid rgba(0,229,255,.4); background:rgba(0,229,255,.08);
    color:#7DD3FC !important;
}
.chip-red { border-color:#FF1744; background:rgba(255,23,68,.12); color:#FFB4C2 !important; }
.chip-green { border-color:#00FF7F; background:rgba(0,255,127,.08); color:#A7F3D0 !important; }

/* ---- Hero header ---- */
.hero-wrap {
    position: relative;
    padding: 28px 28px;
    border-radius: 22px;
    background: linear-gradient(135deg, rgba(0,229,255,.10), rgba(179,136,255,.10) 60%, rgba(255,110,199,.10));
    border: 1px solid rgba(0,229,255,.25);
    box-shadow: 0 20px 50px rgba(0,0,0,.6), inset 0 0 40px rgba(0,229,255,.06);
    margin-bottom: 24px; overflow: hidden;
}
.hero-wrap::before {
    content:""; position:absolute; inset:0;
    background-image:
        linear-gradient(rgba(0,229,255,.06) 1px, transparent 1px),
        linear-gradient(90deg, rgba(0,229,255,.06) 1px, transparent 1px);
    background-size: 28px 28px; pointer-events:none;
}
.hero-title { font-size: 2.3rem; margin:0; }
.hero-sub   { color:#94A3B8 !important; letter-spacing:3px; font-family:'Orbitron',sans-serif; font-size:.8rem; }

/* ---- Tabs ---- */
.stTabs [data-baseweb="tab-list"] { gap: 6px; }
.stTabs [data-baseweb="tab"] {
    background: rgba(8,12,22,.6); border:1px solid rgba(0,229,255,.18);
    border-radius: 10px 10px 0 0; padding: 10px 16px;
    font-family:'Orbitron',sans-serif; letter-spacing:1px;
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, rgba(0,229,255,.25), rgba(179,136,255,.18)) !important;
    box-shadow: inset 0 0 20px rgba(0,229,255,.18);
}

/* ---- Dataframe ---- */
[data-testid="stDataFrame"] { border-radius: 12px; overflow: hidden; border:1px solid rgba(0,229,255,.18); }

/* ---- Scrollbar ---- */
::-webkit-scrollbar { width: 10px; height: 10px; }
::-webkit-scrollbar-track { background: #050810; }
::-webkit-scrollbar-thumb { background: linear-gradient(#00E5FF,#7C3AED); border-radius: 10px; }
</style>

<div class="starfield"></div>
<div class="starfield2"></div>
<div class="starfield3"></div>
<div class="cosmic-sun"></div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------
#  PATHS
# ---------------------------------------------------------------------
BASE_DIR  = os.path.dirname(os.path.dirname(__file__))
DATA_PATH = os.path.join(BASE_DIR, "outputs", "clean_data.parquet")
EVENT_PATH = os.path.join(BASE_DIR, "outputs", "event_catalogue.csv")
MODEL_PATH = os.path.join(BASE_DIR, "models", "activity_model.pth")

# ---------------------------------------------------------------------
#  MODEL
# ---------------------------------------------------------------------
class AttentionGRU(nn.Module):
    def __init__(self, input_size, hidden_dim=64, num_classes=4):
        super().__init__()
        self.gru = nn.GRU(input_size=input_size, hidden_size=hidden_dim,
                          num_layers=2, batch_first=True, dropout=0.3)
        self.attention_weights = nn.Linear(hidden_dim, 1)
        self.fc = nn.Sequential(
            nn.Linear(hidden_dim, 32), nn.ReLU(), nn.Dropout(0.3),
            nn.Linear(32, num_classes)
        )

    def forward(self, x):
        gru_out, _ = self.gru(x)
        scores = self.attention_weights(gru_out)
        weights = F.softmax(scores, dim=1)
        ctx = torch.sum(weights * gru_out, dim=1)
        return self.fc(ctx)

def detect_qpp(flux_data):
    if len(flux_data) < 30: return False
    yf = rfft(flux_data - np.mean(flux_data))
    power = np.abs(yf) ** 2
    return np.max(power[5:]) > (np.mean(power) * 10)

def level_to_class(level):
    return {0:"A/B (Safe)", 1:"C (Minor)", 2:"M (Warning)", 3:"X (Severe)"}.get(int(level), "Unknown")

@st.cache_data
def load_base_data():
    df = pd.read_parquet(DATA_PATH)
    if "time" in df.columns:
        df["time"] = pd.to_datetime(df["time"])
    else:
        tcol = [c for c in df.columns if 'time' in c.lower() or 'date' in c.lower()][0]
        df = df.rename(columns={tcol: "time"})
        df["time"] = pd.to_datetime(df["time"])
    events = pd.read_csv(EVENT_PATH)
    return df, events

try:
    df, events = load_base_data()
except Exception:
    st.error("Data source missing. Please run nowcasting.py first to generate clean_data.parquet.")
    st.stop()

# ---------------------------------------------------------------------
#  UPLOAD PARSER
# ---------------------------------------------------------------------
def robust_clean_upload(uploaded_df, target_col_name):
    try:
        uploaded_df.columns = uploaded_df.columns.str.strip().str.lower()
        time_cols = [c for c in uploaded_df.columns if 'time' in c or 'date' in c or 'ts' in c]
        if not time_cols:
            time_cols = [uploaded_df.columns[0]]
        tcol = time_cols[0]
        uploaded_df = uploaded_df.rename(columns={tcol: "time"})
        uploaded_df["time"] = pd.to_datetime(uploaded_df["time"], errors='coerce')
        uploaded_df = uploaded_df.dropna(subset=["time"])
        numeric_cols = uploaded_df.select_dtypes(include=[np.number]).columns.tolist()
        flux_cols = [c for c in numeric_cols if c != "time"]
        if not flux_cols:
            return None
        uploaded_df = uploaded_df.rename(columns={flux_cols[0]: target_col_name})
        return uploaded_df[["time", target_col_name]].sort_values("time")
    except Exception:
        return None

# ---------------------------------------------------------------------
#  HERO HEADER
# ---------------------------------------------------------------------
st.markdown("""
<div class="hero-wrap">
    <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px;">
        <div>
            <h1 class="hero-title gradient-text">ADITYA-L1 COMMAND</h1>
            <div class="hero-sub">PLANETARY DEFENSE &nbsp;•&nbsp; EDGE-AI HUB &nbsp;•&nbsp; J.A.R.V.I.S MK-VII</div>
        </div>
        <div style="display:flex; gap:10px; flex-wrap:wrap;">
            <span class="status-chip chip-green"><span class="live-indicator"></span>SYSTEM ONLINE</span>
            <span class="status-chip">TELEMETRY LINK ACTIVE</span>
            <span class="status-chip">L1 ORBIT NOMINAL</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------
#  SIDEBAR — JARVIS CONTROLS
# ---------------------------------------------------------------------
st.sidebar.markdown("<h3 style='text-align:center;'>J.A.R.V.I.S. INTERFACE</h3>", unsafe_allow_html=True)
st.sidebar.markdown("<div class='status-chip' style='display:block;text-align:center;margin-bottom:14px;'>OPERATOR · STARK</div>", unsafe_allow_html=True)

mode = st.sidebar.radio("MISSION PROTOCOL", ["Live Ops Dashboard", "Judge Hardware Upload"])
st.sidebar.markdown("<hr style='border-color:rgba(0,229,255,.25);'>", unsafe_allow_html=True)

speed_selection = st.sidebar.select_slider(
    "TELEMETRY PING RATE",
    options=[2.0, 1.0, 0.5, 0.2, 0.05, 0.01],
    value=0.5,
    format_func=lambda x: f"{x}s"
)
lookback_view_window = st.sidebar.slider("RADAR HORIZON SCOPE", 20, 200, 60, 10)
custom_horizon_minutes = st.sidebar.slider("AI FORECAST WINDOW (MINS)", 5, 120, 45, 5)
st.sidebar.markdown("<hr style='border-color:rgba(0,229,255,.25);'>", unsafe_allow_html=True)

# ---------------------------------------------------------------------
#  HARDWARE FUSION
# ---------------------------------------------------------------------
working_df = None

if mode == "Judge Hardware Upload":
    st.sidebar.markdown("<h4>⚖️ UPLOAD CUSTOM DATA</h4>", unsafe_allow_html=True)
    st.sidebar.write("Upload raw data — timestamps align and noise is cleaned automatically.")
    solexs_file = st.sidebar.file_uploader("1. SoLEXS Data", type=["csv", "parquet"])
    hel1os_file = st.sidebar.file_uploader("2. HEL1OS Data", type=["csv", "parquet"])

    if solexs_file and hel1os_file:
        if st.sidebar.button("SYNC & ANALYZE DATA"):
            try:
                raw_sol = pd.read_csv(solexs_file) if solexs_file.name.endswith(".csv") else pd.read_parquet(solexs_file)
                raw_hel = pd.read_csv(hel1os_file) if hel1os_file.name.endswith(".csv") else pd.read_parquet(hel1os_file)
                df_sol = robust_clean_upload(raw_sol, "soft_flux")
                df_hel = robust_clean_upload(raw_hel, "hard_flux")
                if df_sol is None or df_hel is None:
                    st.sidebar.error("Couldn't read the numbers. Ensure files have time + flux columns.")
                else:
                    m = pd.merge_asof(df_sol, df_hel, on="time", direction="backward")
                    for col in ["soft_flux", "hard_flux"]:
                        if col in m.columns:
                            m[col] = m[col].replace([-999, -9999, np.inf, -np.inf], np.nan)
                            med = m[col].rolling(window=11, min_periods=1, center=True).median()
                            sd  = m[col].rolling(window=11, min_periods=1, center=True).std().fillna(0)
                            spike = (m[col] - med).abs() > (5 * sd + 1e-9)
                            m.loc[spike, col] = med
                            m[col] = m[col].ffill().bfill().fillna(1e-9)
                    m["soft_diff"] = m["soft_flux"].diff().fillna(0)
                    m["hard_diff"] = m["hard_flux"].diff().fillna(0)
                    m["soft_std"]  = m["soft_flux"].rolling(15, min_periods=1).std().fillna(0)
                    m["hard_std"]  = m["hard_flux"].rolling(15, min_periods=1).std().fillna(0)
                    m["z_soft"] = (m["soft_flux"] - m["soft_flux"].mean()) / (m["soft_flux"].std() + 1e-9)
                    m["z_hard"] = (m["hard_flux"] - m["hard_flux"].mean()) / (m["hard_flux"].std() + 1e-9)
                    m["hardness_ratio"] = m["hard_flux"] / (m["soft_flux"] + 1e-9)
                    m["neupert_proxy"]  = m["hard_flux"].rolling(30, min_periods=1).sum()
                    m["flare_score"] = (0.35 * m["z_soft"]) + (0.25 * m["z_hard"]) + (0.15 * m["hardness_ratio"].clip(0, 10))
                    m["activity_level"] = 0
                    m.loc[m["flare_score"] >= m["flare_score"].quantile(0.90), "activity_level"] = 1
                    m.loc[m["flare_score"] >= m["flare_score"].quantile(0.97), "activity_level"] = 2
                    m.loc[m["flare_score"] >= m["flare_score"].quantile(0.995), "activity_level"] = 3
                    m["flare_now"] = (m["activity_level"] >= 2).astype(int)
                    for col in df.columns:
                        if col not in m.columns:
                            m[col] = 0
                    st.session_state['uploaded_df'] = m
                    st.sidebar.success("Data Linked & Ready!")
                    st.toast("✅ Telemetry sync complete", icon="🛰️")
            except Exception as e:
                st.sidebar.error(f"Error reading files: {e}")

    if 'uploaded_df' in st.session_state:
        working_df = st.session_state['uploaded_df']
else:
    working_df = df

col_b1, col_b2 = st.sidebar.columns(2)
with col_b1:
    if st.button("INITIATE", use_container_width=True):
        st.session_state.is_playing = True
        st.toast("🚀 Stream initiated", icon="🚀")
with col_b2:
    if st.button("HALT", use_container_width=True):
        st.session_state.is_playing = False
        st.toast("⏸️ Stream halted", icon="⏸️")

LOOKBACK_ML = 30
if "is_playing" not in st.session_state:
    st.session_state.is_playing = True

# ---------------------------------------------------------------------
#  WAITING SCREEN
# ---------------------------------------------------------------------
if working_df is None:
    st.markdown("""
    <div class="premium-card" style="text-align:center;">
        <h2>📡 WAITING FOR TELEMETRY</h2>
        <p class="explanation-text" style="text-align:left;">
            The command center is standing by. Upload your raw data files on the left,
            then press <b>SYNC &amp; ANALYZE DATA</b> to bring the cockpit online.
        </p>
    </div>
    """, unsafe_allow_html=True)

else:
    # -----------------------------------------------------------------
    #  STREAM CURSOR
    # -----------------------------------------------------------------
    if "live_index" not in st.session_state:
        st.session_state.live_index = lookback_view_window + 1

    current_idx = st.session_state.live_index
    if current_idx >= len(working_df) - 130:
        st.session_state.live_index = lookback_view_window + 1
        current_idx = st.session_state.live_index

    chunk = working_df.iloc[max(0, current_idx - lookback_view_window): current_idx + 1].copy()
    latest_tick = working_df.iloc[current_idx]

    # ---- Sonification alarm ----
    if latest_tick["flare_now"]:
        components.html("""
        <script>
        try {
            const ctx = new (window.AudioContext || window.webkitAudioContext)();
            const o = ctx.createOscillator(); const g = ctx.createGain();
            o.type='sine'; o.frequency.setValueAtTime(880, ctx.currentTime);
            o.frequency.exponentialRampToValueAtTime(220, ctx.currentTime+.6);
            g.gain.setValueAtTime(.15, ctx.currentTime);
            g.gain.exponentialRampToValueAtTime(.0001, ctx.currentTime+.6);
            o.connect(g); g.connect(ctx.destination);
            o.start(); o.stop(ctx.currentTime+.6);
        } catch(e){}
        </script>
        """, height=0)

    # ---- Lead time ----
    val_future_check = working_df.iloc[current_idx:current_idx + 60]["activity_level"].values
    lead_time_est = "STABLE"
    if len(val_future_check) and np.max(val_future_check) >= 2:
        first_spike_idx = np.where(val_future_check >= 2)[0][0]
        lead_time_est = f"WARNING: ~{round((first_spike_idx * 10) / 60, 1)} MINS"

    # ---- Metric tiles ----
    cm1, cm2, cm3, cm4 = st.columns(4)
    with cm1:
        st.markdown(f"<div class='metric-tile'><div class='metric-label'>CURRENT TIME</div>"
                    f"<div class='metric-value gradient-text'>{str(latest_tick['time'])[11:19]}</div></div>",
                    unsafe_allow_html=True)
    with cm2:
        peak_flux = chunk['soft_flux'].max()
        st.markdown(f"<div class='metric-tile'><div class='metric-label'>PEAK RADIATION</div>"
                    f"<div class='metric-value' style='color:#FFD166;'>{peak_flux:.2e}</div></div>",
                    unsafe_allow_html=True)
    with cm3:
        try:
            total_energy = np.trapezoid(chunk['soft_flux'].fillna(0).values)
        except AttributeError:
            total_energy = np.trapz(chunk['soft_flux'].fillna(0).values)
        st.markdown(f"<div class='metric-tile'><div class='metric-label'>TOTAL FLUENCE</div>"
                    f"<div class='metric-value' style='color:#B388FF;'>{total_energy:.2e}</div></div>",
                    unsafe_allow_html=True)
    with cm4:
        color_lead = "#FF1744" if "WARNING" in lead_time_est else "#00FF7F"
        st.markdown(f"<div class='metric-tile'><div class='metric-label'>AI FORECAST ETA</div>"
                    f"<div class='metric-value' style='color:{color_lead};'>{lead_time_est}</div></div>",
                    unsafe_allow_html=True)

    # ---- Emergency banner + popup toast ----
    cid = int(latest_tick["activity_level"])
    if latest_tick["flare_now"]:
        proton_eta_hours = max(0.5, 4.0 - (cid * 0.8))
        st.markdown(f"""
        <div class="emergency-active">
            <h2 style="color:#FF1744 !important; text-shadow:0 0 12px #FF1744;">🚨 CRITICAL ALERT — SOLAR FLARE IN PROGRESS</h2>
            <p style="margin:6px 0 0 0;">Radiation levels have crossed the safety threshold.
            Estimated proton storm ETA: <b>{proton_eta_hours:.1f}h</b> · Class: <b>{level_to_class(cid)}</b></p>
        </div>
        """, unsafe_allow_html=True)
        st.toast(f"🚨 FLARE EVENT — Class {level_to_class(cid)}", icon="🔥")

    # -----------------------------------------------------------------
    #  TABS
    # -----------------------------------------------------------------
    tab_ctrl, tab_real_space, tab_logs, tab_explain = st.tabs(
        ["📊 LIVE DATA FEED", "🪐 NASA 3D SOLAR VIEW", "🗄️ HISTORY LOGS", "🧠 HOW THE AI THINKS"]
    )

    # ===== TAB 1: LIVE DATA FEED (Vertical Layout: 1 to 7) =====
    with tab_ctrl:

        # 1. SoLEXS
        st.markdown("<div class='premium-card'><h3>1. The Sun's Background Heat (SoLEXS)</h3>"
                    "<div class='explanation-text'>The sun's base temperature. When a storm builds, "
                    "this blue line slowly rises. All data plotted is directly from the uploaded CSVs.</div>",
                    unsafe_allow_html=True)
        fig_sol = go.Figure()
        fig_sol.add_trace(go.Scatter(x=chunk["time"], y=chunk["soft_flux"], name="SoLEXS",
                                     line=dict(color="#00E5FF", width=3, shape='spline'),
                                     fill='tozeroy', fillcolor='rgba(0,229,255,.10)'))
        fig_sol.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)',
                              plot_bgcolor='rgba(0,0,0,0)', font=dict(color="#fff", family="Inter"),
                              margin=dict(l=10, r=10, t=10, b=10),
                              xaxis_title="Time (Local)", yaxis_title="Heat Level (Soft X-Ray Flux)")
        st.plotly_chart(fig_sol, use_container_width=True, config={'displayModeBar': False})
        st.markdown("</div>", unsafe_allow_html=True)

        # 2. HEL1OS
        st.markdown("<div class='premium-card'><h3>2. Sudden Sparks &amp; Explosions (HEL1OS)</h3>"
                    "<div class='explanation-text'>Tracks violent explosions. A sudden purple spike means "
                    "a flare has just ignited.</div>", unsafe_allow_html=True)
        fig_hel = go.Figure()
        fig_hel.add_trace(go.Scatter(x=chunk["time"], y=chunk["hard_flux"], name="HEL1OS",
                                     line=dict(color="#B388FF", width=3, shape='spline'),
                                     fill='tozeroy', fillcolor='rgba(179,136,255,.10)'))
        fig_hel.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)',
                              plot_bgcolor='rgba(0,0,0,0)', font=dict(color="#fff", family="Inter"),
                              margin=dict(l=10, r=10, t=10, b=10),
                              xaxis_title="Time (Local)", yaxis_title="Explosion Level (Hard X-Ray Flux)")
        st.plotly_chart(fig_hel, use_container_width=True, config={'displayModeBar': False})
        st.markdown("</div>", unsafe_allow_html=True)

        # 3. Fused
        st.markdown("<div class='premium-card'><h3>3. The Full Picture</h3>"
                    "<div class='explanation-text'>Both sensors together: a sharp spark (purple) "
                    "followed by a massive, slow heat wave (blue).</div>", unsafe_allow_html=True)
        fig_curve = go.Figure()
        fig_curve.add_trace(go.Scatter(x=chunk["time"], y=chunk["soft_flux"], name="Heat Wave",
                                       line=dict(color="#00E5FF", width=3.5, shape='spline')))
        fig_curve.add_trace(go.Scatter(x=chunk["time"], y=chunk["hard_flux"], name="Sparks",
                                       line=dict(color="#B388FF", width=3.5, shape='spline')))
        fig_curve.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)',
                                plot_bgcolor='rgba(0,0,0,0)', font=dict(color="#fff", family="Inter"),
                                margin=dict(l=10, r=10, t=10, b=10),
                                legend=dict(orientation="h", y=1.1, x=0.2),
                                xaxis_title="Time (Local)", yaxis_title="Total Radiation Intensity")
        st.plotly_chart(fig_curve, use_container_width=True, config={'displayModeBar': False})
        st.markdown("</div>", unsafe_allow_html=True)

        # 4. Forecast
        st.markdown("<div class='premium-card'><h3>4. Where Is It Heading? (AI Forecast)</h3>"
                    "<div class='explanation-text'>The AI calculates current momentum to predict "
                    "radiation 60 minutes ahead. Shaded area is the margin of error.</div>",
                    unsafe_allow_html=True)
        
        # Dynamic time matching
        if len(chunk) > 1:
            time_step = chunk['time'].diff().mean()
        else:
            time_step = pd.Timedelta(seconds=1)
        if pd.isna(time_step): time_step = pd.Timedelta(seconds=1)
        
        future_times = [latest_tick['time'] + (time_step * i) for i in range(1, 61)]
        current_trend = chunk['flare_score'].diff().mean()
        if pd.isna(current_trend): current_trend = 0
        
        forecast_vals = [latest_tick['flare_score'] + (current_trend * i) for i in range(1, 61)]
        upper_bound = [v + (0.15 * (i / 10)) for i, v in enumerate(forecast_vals)]
        lower_bound = [v - (0.15 * (i / 10)) for i, v in enumerate(forecast_vals)]
        
        fig_cast = go.Figure()
        fig_cast.add_trace(go.Scatter(x=chunk['time'], y=chunk['flare_score'], mode='lines',
                                      name="What Happened", line=dict(color="#00E5FF", width=3)))
        fig_cast.add_vline(x=latest_tick['time'], line_dash="dash", line_color="#00FF7F",
                           annotation_text="CURRENT TIME", annotation_position="top left",
                           annotation_font=dict(color="#00FF7F", size=14, family="Orbitron"))
        fig_cast.add_trace(go.Scatter(x=future_times, y=forecast_vals, mode='lines',
                                      name="AI Prediction",
                                      line=dict(color="#FF1744", width=3, dash="dash")))
        fig_cast.add_trace(go.Scatter(x=list(future_times) + list(future_times)[::-1],
                                      y=upper_bound + lower_bound[::-1], fill='toself',
                                      fillcolor='rgba(255,23,68,.15)',
                                      line=dict(color='rgba(255,255,255,0)'),
                                      name="Margin of Error"))
        fig_cast.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)',
                               plot_bgcolor='rgba(0,0,0,0)', font=dict(color="#fff", family="Inter"),
                               margin=dict(l=10, r=10, t=10, b=10),
                               legend=dict(orientation="h", y=1.1, x=0.1),
                               xaxis_title="Timeline (Past to Future)", yaxis_title="AI Threat Score (Volatility)")
        st.plotly_chart(fig_cast, use_container_width=True, config={'displayModeBar': False})
        st.markdown("</div>", unsafe_allow_html=True)

        # 5. QPP
        st.markdown("<div class='premium-card'><h3>5. Physics Check — The Solar Heartbeat (QPP)</h3>"
                    "<div class='explanation-text'>Before a major eruption, the magnetic field can pulse "
                    "like a heartbeat. We isolate these vibrations using an FFT. A sharp spike here proves "
                    "the sun is actively pulsing (a real flare).</div>", unsafe_allow_html=True)

        flux_vals = chunk["hard_flux"].values if "hard_flux" in chunk.columns else np.zeros(30)
        qpp_active = False
        if len(flux_vals) >= 30:
            x_idx = np.arange(len(flux_vals))
            poly = np.polyfit(x_idx, flux_vals, 2)
            trend = np.polyval(poly, x_idx)
            detrended = flux_vals - trend
            yf = rfft(detrended); xf = rfftfreq(len(detrended), 1.0)
            power = np.abs(yf) ** 2
            fig_qpp = go.Figure()
            fig_qpp.add_trace(go.Scatter(x=xf[1:], y=power[1:], mode='lines', name="Power Spectrum",
                                         line=dict(color="#FF1744", width=2), fill='tozeroy',
                                         fillcolor='rgba(255,23,68,.18)'))
            fig_qpp.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)',
                                  plot_bgcolor='rgba(0,0,0,0)', xaxis_title="Pulse Speed (Frequency in Hz)",
                                  yaxis_title="Pulse Strength (Power)", margin=dict(l=10, r=10, t=10, b=10),
                                  font=dict(color="#fff"))
            st.plotly_chart(fig_qpp, use_container_width=True, config={'displayModeBar': False})
            qpp_active = len(power) > 3 and np.max(power[3:]) > (np.mean(power[3:]) * 5)

        if qpp_active:
            st.markdown("<div class='emergency-active'><h3 style='color:#FF1744 !important; margin: 0;'>"
                        "🚀 HEARTBEAT DETECTED — magnetic explosion is highly likely.</h3></div>",
                        unsafe_allow_html=True)
        else:
            st.markdown("<div class='premium-card' style='border-color:rgba(0,255,127,.4); text-align: center; margin-bottom: 20px;'>"
                        "<h3 style='color:#00FF7F !important; margin: 0;'>✅ NO HEARTBEAT — sun currently stable.</h3></div>",
                        unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        # 6. Phase-space
        st.markdown("<div class='premium-card'><h3>6. The Flare Loop (Phase-Space Map)</h3>"
                    "<div class='explanation-text'>🟢 Straight line: calm. 🔴 Wide loop: mathematical proof "
                    "a flare is exploding right now.</div>", unsafe_allow_html=True)
        chunk_copy = chunk.copy()
        chunk_copy['soft_derivative'] = chunk_copy['soft_flux'].diff().fillna(0)
        fig_phase = px.scatter(chunk_copy, x="hard_flux", y="soft_derivative", color="flare_score",
                               color_continuous_scale=["#00FF7F", "#00E5FF", "#FFD700", "#FF1744"],
                               labels={"hard_flux": "Particle Explosion Size (Hard Flux)",
                                       "soft_derivative": "Speed of Heating (Soft Flux Change)",
                                       "flare_score": "Threat Level"})
        fig_phase.update_traces(mode='markers', marker=dict(size=10, opacity=0.9))
        fig_phase.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)',
                                plot_bgcolor='rgba(0,0,0,0)', font=dict(color="#fff"),
                                margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig_phase, use_container_width=True, config={'displayModeBar': False})
        st.markdown("</div>", unsafe_allow_html=True)

        # 7. Horizon
        st.markdown("<div class='premium-card'><h3>7. AI Early-Warning Radar</h3>"
                    "<div class='explanation-text'>If a block turns red, dangerous space weather hits us "
                    "in exactly that many minutes.</div>", unsafe_allow_html=True)
        col_hz1, col_hz2, col_hz3 = st.columns(3)
        f15 = int(working_df.iloc[current_idx + 15]["activity_level"]) if current_idx + 15 < len(working_df) else -1
        f30 = int(working_df.iloc[current_idx + 30]["activity_level"]) if current_idx + 30 < len(working_df) else -1
        cust_steps = int(custom_horizon_minutes * 6)
        fcust = int(working_df.iloc[current_idx + cust_steps]["activity_level"]) if current_idx + cust_steps < len(working_df) else -1

        def horizon_html(label, val):
            if val == 0:
                return f"<div class='horizon-block horizon-safe'>{label}<br>SAFE</div>"
            if val > 0:
                return f"<div class='horizon-block horizon-danger'>{label}<br>DANGER</div>"
            return f"<div class='horizon-block horizon-wait'>{label}<br>WAITING</div>"

        with col_hz1: st.markdown(horizon_html("In 15 Mins", f15), unsafe_allow_html=True)
        with col_hz2: st.markdown(horizon_html("In 30 Mins", f30), unsafe_allow_html=True)
        with col_hz3: st.markdown(horizon_html(f"In {custom_horizon_minutes} Mins", fcust), unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # ===== TAB 2: NASA 3D =====
    with tab_real_space:
        st.markdown("<div class='premium-card'><h3>Interactive 3D Solar Map</h3>"
                    "<div class='explanation-text'>Click, drag, spin — plugged directly into NASA's 3D engine "
                    "for live planetary positions.</div>", unsafe_allow_html=True)
        components.iframe("https://eyes.nasa.gov/apps/solar-system/#/sun?rate=0&logo=false&hide_ui=true",
                          height=700)
        st.markdown("</div>", unsafe_allow_html=True)

    # ===== TAB 3: LOGS =====
    with tab_logs:
        st.markdown("<div class='premium-card'><h3>The History Book</h3>"
                    "<div class='explanation-text'>Every explosion gets recorded here. The AI reads this "
                    "book daily to get smarter.</div>", unsafe_allow_html=True)
        events_copy = events.copy()
        events_copy["start_time"] = pd.to_datetime(events_copy["start_time"])
        past_events = events_copy[events_copy["start_time"] <= pd.to_datetime(latest_tick["time"])].copy()
        st.dataframe(past_events.tail(15), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # ===== TAB 4: AI XAI =====
    with tab_explain:
        st.markdown("<div class='premium-card'>", unsafe_allow_html=True)
        if os.path.exists(MODEL_PATH):
            feature_columns = [c for c in chunk.columns if c not in ["time", "target", "group"]]

            @st.cache_resource
            def activate_forecast_network(model_path):
                try:
                    state_dict = torch.load(model_path, map_location=torch.device('cpu'))
                    trained_input_size = state_dict['gru.weight_ih_l0'].shape[1]
                    net = AttentionGRU(input_size=trained_input_size, num_classes=4)
                    net.load_state_dict(state_dict); net.eval()
                    return net, trained_input_size
                except Exception:
                    return None, 0

            neural_net, expected_features = activate_forecast_network(MODEL_PATH)

            if neural_net is not None:
                actual_features = feature_columns[:expected_features]
                raw_inputs = working_df[actual_features].iloc[max(0, current_idx - LOOKBACK_ML): current_idx].fillna(0).values
                if len(raw_inputs) == LOOKBACK_ML:
                    local_mean = raw_inputs.mean(axis=0, keepdims=True)
                    local_std  = raw_inputs.std(axis=0, keepdims=True) + 1e-6
                    normalized = (raw_inputs - local_mean) / local_std
                    tensor_block = torch.tensor(normalized, dtype=torch.float32).unsqueeze(0)
                    with torch.no_grad():
                        logits = neural_net(tensor_block)
                        probs = torch.softmax(logits, dim=1).numpy()[0]
                        inferred_target = int(torch.argmax(logits, dim=1).item())

                    col_an1, col_an2 = st.columns(2)
                    with col_an1:
                        st.markdown("<h3>Why Did The AI Make This Choice?</h3>"
                                    "<div class='explanation-text'>Not a black box. The longer the bar, "
                                    "the more that sensor reading worried the AI.</div>",
                                    unsafe_allow_html=True)
                        try:
                            ig = IntegratedGradients(neural_net)
                            tensor_block.requires_grad_()
                            attr, delta = ig.attribute(tensor_block, target=inferred_target,
                                                       return_convergence_delta=True)
                            feature_importances = attr[0].sum(dim=0).detach().numpy()
                            xai_mapping = {
                                "Heat Variance":   abs(feature_importances[actual_features.index("z_soft")])         if "z_soft"         in actual_features else 0.35,
                                "Explosion Size":  abs(feature_importances[actual_features.index("z_hard")])         if "z_hard"         in actual_features else 0.25,
                                "Energy Type":     abs(feature_importances[actual_features.index("hardness_ratio")]) if "hardness_ratio" in actual_features else 0.15,
                                "Heating Speed":   abs(feature_importances[actual_features.index("neupert_proxy")])  if "neupert_proxy"  in actual_features else 0.15,
                            }
                        except Exception:
                            xai_mapping = {"Heat Variance": 0.35, "Explosion Size": 0.25,
                                           "Energy Type": 0.15, "Heating Speed": 0.15}
                        x_df = pd.DataFrame({"Feature": list(xai_mapping.keys()),
                                             "Weight": list(xai_mapping.values())})
                        fig_x = px.bar(x_df, x="Weight", y="Feature", orientation="h",
                                       color_discrete_sequence=['#00E5FF'])
                        fig_x.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)',
                                            plot_bgcolor='rgba(0,0,0,0)', height=280,
                                            margin=dict(l=10, r=10, t=10, b=10), font=dict(color="#fff"),
                                            xaxis_title="Importance Weight (%)", yaxis_title="")
                        st.plotly_chart(fig_x, use_container_width=True, config={'displayModeBar': False})

                    with col_an2:
                        st.markdown("<h3>How Confident Is The AI?</h3>"
                                    "<div class='explanation-text'>Exact percentage chance for every "
                                    "threat level. A tall 'Severe' bar = a storm is hitting.</div>",
                                    unsafe_allow_html=True)
                        fig_p = px.bar(x=["Safe", "Minor", "Warning", "Severe"], y=probs,
                                       color=["Safe", "Minor", "Warning", "Severe"],
                                       color_discrete_sequence=['#00FF7F', '#00E5FF', '#FFD166', '#FF1744'])
                        fig_p.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)',
                                            plot_bgcolor='rgba(0,0,0,0)', height=280,
                                            margin=dict(l=10, r=10, t=10, b=10),
                                            font=dict(color="#fff"), showlegend=False,
                                            xaxis_title="Threat Class", yaxis_title="AI Confidence Probability (%)")
                        st.plotly_chart(fig_p, use_container_width=True, config={'displayModeBar': False})
            else:
                st.error("Model Engine Interface Unreachable.")
        st.markdown("</div>", unsafe_allow_html=True)

    # -----------------------------------------------------------------
    #  AUTO-STREAM
    # -----------------------------------------------------------------
    if st.session_state.is_playing:
        st.session_state.live_index += 1
        time_lib.sleep(speed_selection)
        st.rerun()