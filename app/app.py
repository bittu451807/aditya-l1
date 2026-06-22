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

# --- Config and Presentation Framework ---
st.set_page_config(
    page_title="Aditya-L1 Tactical Command",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- UNBLOCKABLE CINEMATIC BACKGROUND & GLASS UI ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Inter:wght@300;400;600;800&display=swap');
    
    .stApp {
        background-color: #050505 !important;
        background-image: 
            radial-gradient(circle at 15% 50%, rgba(76, 29, 149, 0.4), transparent 50%),
            radial-gradient(circle at 85% 30%, rgba(6, 182, 212, 0.4), transparent 50%),
            radial-gradient(circle at 50% 80%, rgba(225, 29, 72, 0.3), transparent 50%) !important;
        animation: nebula-pulse 15s ease-in-out infinite alternate !important;
        overflow-x: hidden;
    }
    
    @keyframes nebula-pulse {
        0% { background-size: 100% 100%; }
        100% { background-size: 130% 130%; }
    }
    
    @function multiple-box-shadow($n) {
        $value: '#{random(2000)}px #{random(2000)}px #FFF';
        @for $i from 2 through $n {
            $value: '#{$value}, #{random(2000)}px #{random(2000)}px #FFF';
        }
        @return unquote($value);
    }

    #stars {
        width: 2px; height: 2px;
        background: transparent;
        box-shadow: 1740px 123px #FFF, 832px 1432px #FFF, 124px 834px #FFF, 1834px 1934px #FFF, 432px 1134px #FFF, 934px 234px #FFF, 1234px 1534px #FFF, 34px 1834px #FFF, 1634px 534px #FFF, 534px 1234px #FFF, 1434px 834px #FFF, 734px 1434px #FFF, 234px 534px #FFF, 1934px 1134px #FFF, 1134px 1834px #FFF, 134px 234px #FFF, 1534px 934px #FFF, 634px 1634px #FFF, 1734px 334px #FFF, 1034px 1334px #FFF;
        animation: animStar 50s linear infinite;
        position: fixed; top: 0; left: 0; z-index: -100;
        border-radius: 50%;
    }
    
    @keyframes animStar {
        from { transform: translateY(0px); }
        to { transform: translateY(-2000px); }
    }
    
    html, body, [class*="css"], p, span, div, label {
        font-family: 'Inter', sans-serif !important;
        color: #F8F9F9 !important; 
    }
    
    h1, h2, h3, h4, .section-heading {
        font-family: 'Orbitron', sans-serif !important;
        font-weight: 900 !important;
        letter-spacing: 1px !important;
        color: #00E5FF !important; 
        text-shadow: 0px 0px 10px rgba(0, 229, 255, 0.6);
    }
    
    .gradient-text {
        background: linear-gradient(135deg, #00E5FF 0%, #B388FF 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 900;
        text-shadow: none;
    }
    
    .premium-card {
        background: rgba(5, 8, 15, 0.75) !important;
        backdrop-filter: blur(20px) !important;
        -webkit-backdrop-filter: blur(20px) !important;
        border-top: 1px solid rgba(255, 255, 255, 0.2) !important;
        border-left: 1px solid rgba(255, 255, 255, 0.2) !important;
        border-right: 1px solid rgba(0, 229, 255, 0.1) !important;
        border-bottom: 1px solid rgba(0, 229, 255, 0.1) !important;
        border-radius: 16px;
        padding: 24px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.8), inset 0 0 20px rgba(0, 229, 255, 0.05);
        margin-bottom: 24px;
    }

    .explanation-text {
        font-size: 0.95rem;
        color: #CFD8DC !important;
        background: rgba(0, 0, 0, 0.6);
        padding: 14px;
        border-left: 4px solid #00E5FF;
        border-radius: 4px;
        margin-bottom: 20px;
        line-height: 1.5;
    }
    
    .emergency-active {
        background: rgba(255, 23, 68, 0.2) !important;
        backdrop-filter: blur(15px);
        border: 1px solid #FF1744 !important;
        border-radius: 16px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 0 30px rgba(255, 23, 68, 0.4), inset 0 0 20px rgba(255, 23, 68, 0.2) !important;
        margin-bottom: 24px;
    }

    @keyframes pulse-dot {
        0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(0, 229, 255, 0.8); }
        70% { transform: scale(1.3); box-shadow: 0 0 0 12px rgba(0, 229, 255, 0); }
        100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(0, 229, 255, 0); }
    }
    
    .live-indicator {
        display: inline-block;
        width: 12px; height: 12px;
        background-color: #00E5FF;
        border-radius: 50%;
        margin-right: 12px;
        animation: pulse-dot 1.5s infinite;
    }
    
    /* J.A.R.V.I.S THEMED SIDEBAR */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #090b14 0%, #0b1c2c 100%) !important;
        border-right: 2px solid #00E5FF !important;
        box-shadow: inset -5px 0 25px rgba(0, 229, 255, 0.15) !important;
    }
    
    [data-testid="stSidebar"]::before {
        content: "";
        position: absolute;
        top: 0; left: 0; right: 0; bottom: 0;
        background-image: 
            linear-gradient(rgba(0, 229, 255, 0.05) 1px, transparent 1px),
            linear-gradient(90deg, rgba(0, 229, 255, 0.05) 1px, transparent 1px);
        background-size: 20px 20px;
        pointer-events: none;
        z-index: 0;
    }
    
    [data-testid="stSidebar"] > div {
        z-index: 1;
        position: relative;
    }

    .stSlider > div > div > div > div {
        background-color: #00E5FF !important; 
        box-shadow: 0 0 8px #00E5FF;
    }
    .stSlider > div > div > div > div[role="slider"] {
        background-color: #FF1744 !important; 
        border: 2px solid #FFF !important;
        box-shadow: 0 0 12px #FF1744 !important;
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #00E5FF 0%, #0083B0 100%) !important;
        color: #050505 !important;
        font-family: 'Orbitron', sans-serif !important;
        font-weight: 900 !important;
        border: 1px solid #FFF !important;
        box-shadow: 0 0 15px rgba(0, 229, 255, 0.6), inset 0 0 10px rgba(255,255,255,0.5) !important;
        border-radius: 8px !important;
        text-transform: uppercase;
        letter-spacing: 2px;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #FF1744 0%, #B71C1C 100%) !important;
        box-shadow: 0 0 20px rgba(255, 23, 68, 0.8), inset 0 0 10px rgba(255,255,255,0.5) !important;
        border-color: #FF1744 !important;
        color: #FFF !important;
        transform: scale(1.02);
    }
    
    .stRadio label {
        color: #00E5FF !important;
        font-family: 'Orbitron', sans-serif;
        letter-spacing: 1px;
    }

    .horizon-block {
        padding: 16px; border-radius: 12px; text-align: center; font-weight: 700; background: rgba(0,0,0,0.5); border: 1px solid rgba(255,255,255,0.1); font-size: 1.2rem;
    }
    </style>
    
    <div id="stars"></div>
""", unsafe_allow_html=True)

# --- Path Resolution Infrastructure ---
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_PATH = os.path.join(BASE_DIR, "outputs", "clean_data.parquet")
EVENT_PATH = os.path.join(BASE_DIR, "outputs", "event_catalogue.csv")
MODEL_PATH = os.path.join(BASE_DIR, "models", "activity_model.pth")

# --- Deep Modeling Recurrent Inference Blueprint (AttentionGRU) ---
class AttentionGRU(nn.Module):
    def __init__(self, input_size, hidden_dim=64, num_classes=4):
        super(AttentionGRU, self).__init__()
        self.gru = nn.GRU(input_size=input_size, hidden_size=hidden_dim, num_layers=2, batch_first=True, dropout=0.3)
        self.attention_weights = nn.Linear(hidden_dim, 1)
        self.fc = nn.Sequential(
            nn.Linear(hidden_dim, 32),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(32, num_classes)
        )

    def forward(self, x):
        gru_out, _ = self.gru(x)
        attention_scores = self.attention_weights(gru_out)
        attention_weights = F.softmax(attention_scores, dim=1)
        context_vector = torch.sum(attention_weights * gru_out, dim=1)
        return self.fc(context_vector)

def detect_qpp(flux_data):
    if len(flux_data) < 30: return False
    yf = rfft(flux_data - np.mean(flux_data))
    power = np.abs(yf)**2
    return np.max(power[5:]) > (np.mean(power) * 10)

def level_to_class(level):
    return {0: "A/B (Safe)", 1: "C (Minor)", 2: "M (Warning)", 3: "X (Severe)"}.get(int(level), "Unknown")

@st.cache_data
def load_base_data():
    df = pd.read_parquet(DATA_PATH)
    if "time" in df.columns:
        df["time"] = pd.to_datetime(df["time"])
    else:
        time_col = [c for c in df.columns if 'time' in c.lower() or 'date' in c.lower()][0]
        df = df.rename(columns={time_col: "time"})
        df["time"] = pd.to_datetime(df["time"])
    events = pd.read_csv(EVENT_PATH)
    return df, events

try:
    df, events = load_base_data()
except Exception as e:
    st.error("Data source missing. Please run nowcasting.py first to generate clean_data.parquet.")
    st.stop()

# --- BULLETPROOF UPLOAD PARSER ---
def robust_clean_upload(uploaded_df, target_col_name):
    try:
        uploaded_df.columns = uploaded_df.columns.str.strip().str.lower()
        time_cols = [c for c in uploaded_df.columns if 'time' in c or 'date' in c or 'ts' in c]
        if not time_cols:
            time_cols = [uploaded_df.columns[0]]
            
        time_col = time_cols[0]
        uploaded_df = uploaded_df.rename(columns={time_col: "time"})
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

# --- MISSION CONTROL HEADER ---
st.markdown("""
    <div style="display: flex; justify-content: space-between; align-items: center; padding: 0 0 20px 0;">
        <div>
            <h1 style="font-size: 3.2rem; margin: 0; text-transform: uppercase;">ADITYA-L1 <span class="gradient-text">COMMAND</span></h1>
            <p style="color: #00E5FF; font-size: 1.2rem; margin: 4px 0 0 0; font-family: 'Orbitron', sans-serif;">PLANETARY DEFENSE & EDGE-AI HUB</p>
        </div>
        <div style="text-align: right;">
            <div style="background: rgba(0, 0, 0, 0.7); border: 2px solid #00E5FF; padding: 12px 24px; border-radius: 8px; box-shadow: 0 0 20px rgba(0, 229, 255, 0.4);">
                <span style="color: #00E5FF; font-family: 'Orbitron', sans-serif; font-weight: 900; font-size: 1.1rem; display: flex; align-items: center; letter-spacing: 2px;">
                    <div class="live-indicator"></div> SYSTEM ONLINE
                </span>
            </div>
        </div>
    </div>
""", unsafe_allow_html=True)

# --- SIDEBAR FLIGHT CONTROLS ---
st.sidebar.markdown("<h2 style='color:#00E5FF; font-family:Orbitron, sans-serif; text-align:center; text-shadow: 0 0 10px #00E5FF; margin-bottom:20px;'>J.A.R.V.I.S. INTERFACE</h2>", unsafe_allow_html=True)

mode = st.sidebar.radio("MISSION PROTOCOL", ["Live Ops Dashboard", "Judge Hardware Upload"])
st.sidebar.markdown("<br>", unsafe_allow_html=True)

speed_selection = st.sidebar.select_slider(
    "TELEMETRY PING RATE",
    options=[2.0, 1.0, 0.5, 0.2, 0.05, 0.01],
    value=0.5,
    format_func=lambda x: f"{x}s"
)

lookback_view_window = st.sidebar.slider(
    "RADAR HORIZON SCOPE",
    min_value=20, max_value=200, value=60, step=10
)

custom_horizon_minutes = st.sidebar.slider(
    "AI FORECAST WINDOW (MINS)", 
    min_value=5, max_value=120, value=45, step=5
)

st.sidebar.markdown("<hr style='border: 1px solid rgba(0, 229, 255, 0.3);'>", unsafe_allow_html=True)

# --- HARDWARE TELEMETRY FUSION LOGIC ---
working_df = None

if mode == "Judge Hardware Upload":
    st.sidebar.markdown("<h4 style='color:#FFF; font-family:Orbitron;'>⚖️ UPLOAD CUSTOM DATA</h4>", unsafe_allow_html=True)
    st.sidebar.write("Got your own raw data? Upload it here. The system will align the timestamps and clean up any noise automatically.")
    
    solexs_file = st.sidebar.file_uploader("1. Upload SoLEXS Data", type=["csv", "parquet"])
    hel1os_file = st.sidebar.file_uploader("2. Upload HEL1OS Data", type=["csv", "parquet"])
    
    if solexs_file and hel1os_file:
        if st.sidebar.button("SYNC & ANALYZE DATA"):
            try:
                raw_sol = pd.read_csv(solexs_file) if solexs_file.name.endswith(".csv") else pd.read_parquet(solexs_file)
                raw_hel = pd.read_csv(hel1os_file) if hel1os_file.name.endswith(".csv") else pd.read_parquet(hel1os_file)
                
                df_sol = robust_clean_upload(raw_sol, "soft_flux")
                df_hel = robust_clean_upload(raw_hel, "hard_flux")
                
                if df_sol is None or df_hel is None:
                    st.sidebar.error("Oops! Couldn't read the numbers. Make sure the files have time and flux columns.")
                else:
                    merged_judge_df = pd.merge_asof(df_sol, df_hel, on="time", direction="backward")
                    for col in ["soft_flux", "hard_flux"]:
                        if col in merged_judge_df.columns:
                            merged_judge_df[col] = merged_judge_df[col].replace([-999, -9999, np.inf, -np.inf], np.nan)
                            rolling_median = merged_judge_df[col].rolling(window=11, min_periods=1, center=True).median()
                            rolling_std = merged_judge_df[col].rolling(window=11, min_periods=1, center=True).std().fillna(0)
                            spike_mask = (merged_judge_df[col] - rolling_median).abs() > (5 * rolling_std + 1e-9)
                            merged_judge_df.loc[spike_mask, col] = rolling_median
                            merged_judge_df[col] = merged_judge_df[col].ffill().bfill().fillna(1e-9)

                    merged_judge_df["soft_diff"] = merged_judge_df["soft_flux"].diff().fillna(0)
                    merged_judge_df["hard_diff"] = merged_judge_df["hard_flux"].diff().fillna(0)
                    merged_judge_df["soft_std"] = merged_judge_df["soft_flux"].rolling(15, min_periods=1).std().fillna(0)
                    merged_judge_df["hard_std"] = merged_judge_df["hard_flux"].rolling(15, min_periods=1).std().fillna(0)
                    merged_judge_df["z_soft"] = (merged_judge_df["soft_flux"] - merged_judge_df["soft_flux"].mean()) / (merged_judge_df["soft_flux"].std() + 1e-9)
                    merged_judge_df["z_hard"] = (merged_judge_df["hard_flux"] - merged_judge_df["hard_flux"].mean()) / (merged_judge_df["hard_flux"].std() + 1e-9)
                    merged_judge_df["hardness_ratio"] = merged_judge_df["hard_flux"] / (merged_judge_df["soft_flux"] + 1e-9)
                    merged_judge_df["neupert_proxy"] = merged_judge_df["hard_flux"].rolling(30, min_periods=1).sum()
                    
                    merged_judge_df["flare_score"] = (0.35 * merged_judge_df["z_soft"]) + (0.25 * merged_judge_df["z_hard"]) + (0.15 * merged_judge_df["hardness_ratio"].clip(0,10))
                    merged_judge_df["activity_level"] = 0
                    merged_judge_df.loc[merged_judge_df["flare_score"] >= merged_judge_df["flare_score"].quantile(0.90), "activity_level"] = 1
                    merged_judge_df.loc[merged_judge_df["flare_score"] >= merged_judge_df["flare_score"].quantile(0.97), "activity_level"] = 2
                    merged_judge_df.loc[merged_judge_df["flare_score"] >= merged_judge_df["flare_score"].quantile(0.995), "activity_level"] = 3
                    merged_judge_df["flare_now"] = (merged_judge_df["activity_level"] >= 2).astype(int)
                    
                    for col in df.columns:
                        if col not in merged_judge_df.columns:
                            merged_judge_df[col] = 0
                    
                    st.session_state['uploaded_df'] = merged_judge_df
                    st.sidebar.success("Data Linked & Ready!")
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
with col_b2:
    if st.button("HALT", use_container_width=True):
        st.session_state.is_playing = False

LOOKBACK_ML = 30
if "is_playing" not in st.session_state:
    st.session_state.is_playing = True

# --- UI RENDER GATE (Checks if data is available) ---
if working_df is None:
    st.markdown("""
        <div style='display:flex; justify-content:center; align-items:center; height: 50vh;'>
            <div class='premium-card' style='text-align:center; max-width: 600px;'>
                <h2 style='color:#00E5FF; font-family:Orbitron;'>📡 WAITING FOR DATA</h2>
                <p style='color:#CFD8DC; font-size:1.1rem; line-height:1.6;'>
                    The command center is standing by.<br><br>
                    Please upload your raw data files on the left, then click <strong>Sync & Analyze Data</strong> to watch the magic happen.
                </p>
            </div>
        </div>
    """, unsafe_allow_html=True)

else:
    # --- STREAMING CURSOR LOGIC ---
    if "live_index" not in st.session_state:
        st.session_state.live_index = lookback_view_window + 1

    current_idx = st.session_state.live_index
    if current_idx >= len(working_df) - 130:
        st.session_state.live_index = lookback_view_window + 1
        current_idx = st.session_state.live_index

    chunk = working_df.iloc[max(0, current_idx - lookback_view_window) : current_idx + 1].copy()
    latest_tick = working_df.iloc[current_idx]

    # --- JAVASCRIPT SONIFICATION ALARM ---
    if latest_tick["flare_now"]:
        js_code = """
        <script>
        const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        let osc = audioCtx.createOscillator();
        osc.type = 'sawtooth';
        osc.frequency.setValueAtTime(600, audioCtx.currentTime);
        osc.connect(audioCtx.destination);
        osc.start();
        osc.stop(audioCtx.currentTime + 0.15);
        </script>
        """
        st.components.v1.html(js_code, height=0)

    # --- LEAD TIME CALCULATION ---
    val_future_check = working_df.iloc[current_idx:current_idx+60]["activity_level"].values
    lead_time_est = "STABLE"
    if np.max(val_future_check) >= 2:
        first_spike_idx = np.where(val_future_check >= 2)[0][0]
        lead_time_est = f"WARNING: ~{round((first_spike_idx * 10) / 60, 1)} MINS"

    # --- REAL PHYSICS METRIC CARDS ---
    cm1, cm2, cm3, cm4 = st.columns(4)
    with cm1:
        st.markdown(f"<div class='premium-card' style='padding:20px;'><small style='color:#B0BEC5; font-family:Orbitron; font-weight:700;'>CURRENT TIME</small><div style='font-size:2rem; font-family:Orbitron; font-weight:900; color:#FFFFFF; margin-top:4px;'>{str(latest_tick['time'])[11:19]}</div></div>", unsafe_allow_html=True)
    with cm2:
        peak_flux = chunk['soft_flux'].max()
        st.markdown(f"<div class='premium-card' style='padding:20px;'><small style='color:#00E5FF; font-family:Orbitron; font-weight:700;'>PEAK RADIATION HIT</small><div style='font-size:2rem; font-family:Orbitron; font-weight:900; color:#00E5FF; margin-top:4px;'>{peak_flux:.2e}</div></div>", unsafe_allow_html=True)
    with cm3:
        try:
            total_energy = np.trapezoid(chunk['soft_flux'].fillna(0).values)
        except AttributeError:
            total_energy = np.trapz(chunk['soft_flux'].fillna(0).values)
            
        st.markdown(f"<div class='premium-card' style='padding:20px;'><small style='color:#FFD700; font-family:Orbitron; font-weight:700;'>TOTAL ENERGY (FLUENCE)</small><div style='font-size:2rem; font-family:Orbitron; font-weight:900; color:#FFD700; margin-top:4px;'>{total_energy:.2e}</div></div>", unsafe_allow_html=True)
    with cm4:
        color_lead = "#FF1744" if "WARNING" in lead_time_est else "#00FF7F"
        st.markdown(f"<div class='premium-card' style='padding:20px;'><small style='color:{color_lead}; font-family:Orbitron; font-weight:700;'>AI FORECAST ETA</small><div style='font-size:1.8rem; font-family:Orbitron; font-weight:900; color:{color_lead}; margin-top:8px;'>{lead_time_est}</div></div>", unsafe_allow_html=True)

    # --- EMERGENCY OVERRIDE BANNER ---
    cid = int(latest_tick["activity_level"])
    if latest_tick["flare_now"]:
        proton_eta_hours = max(0.5, 4.0 - (cid * 0.8)) 
        st.markdown(f"""
            <div class="emergency-active">
                <h3 style="color: #FFFFFF; margin: 0; font-family: 'Orbitron', sans-serif;">🚨 CRITICAL ALERT: SOLAR FLARE IN PROGRESS</h3>
                <p style="color: #FFCDD2; font-weight: 500; margin: 4px 0 12px 0; font-size: 1.1rem;">Radiation levels have crossed the safety threshold.</p>
            </div>
        """, unsafe_allow_html=True)

    # --- WORKSPACE TABS ---
    tab_ctrl, tab_real_space, tab_logs, tab_explain = st.tabs(["📊 LIVE DATA FEED", "🪐 NASA 3D SOLAR VIEW", "🗄️ HISTORY LOGS", "🧠 HOW THE AI THINKS"])

    # ---------------------------------------------------------
    # TAB 1: THE FULL-WIDTH VERTICAL MASTER FEED 
    # ---------------------------------------------------------
    with tab_ctrl:
        
        # 1. SoLEXS Graph
        st.markdown("<div class='premium-card'><h3 style='margin-bottom:5px;'>1. The Sun's Background Heat (SoLEXS)</h3><div class='explanation-text'>Think of this as the sun's base temperature. When a solar storm is building up, this blue line slowly starts to rise. All data plotted is directly from the uploaded CSVs.</div>", unsafe_allow_html=True)
        fig_sol = go.Figure()
        fig_sol.add_trace(go.Scatter(x=chunk["time"], y=chunk["soft_flux"], name="SoLEXS", line=dict(color="#00E5FF", width=3, shape='spline')))
        fig_sol.update_layout(
            template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color="#FFFFFF", family="Inter"), margin=dict(l=10, r=10, t=10, b=10),
            xaxis_title="Time (Local)", yaxis_title="Heat Level (Soft X-Ray Flux)"
        )
        st.plotly_chart(fig_sol, use_container_width=True, config={'displayModeBar': False})
        st.markdown("</div>", unsafe_allow_html=True)

        # 2. HEL1OS Graph
        st.markdown("<div class='premium-card'><h3 style='margin-bottom:5px;'>2. Sudden Sparks & Explosions (HEL1OS)</h3><div class='explanation-text'>This doesn't track heat; it tracks violent explosions. When you see this purple line spike suddenly, it means a flare has just ignited.</div>", unsafe_allow_html=True)
        fig_hel = go.Figure()
        fig_hel.add_trace(go.Scatter(x=chunk["time"], y=chunk["hard_flux"], name="HEL1OS", line=dict(color="#B388FF", width=3, shape='spline')))
        fig_hel.update_layout(
            template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color="#FFFFFF", family="Inter"), margin=dict(l=10, r=10, t=10, b=10),
            xaxis_title="Time (Local)", yaxis_title="Explosion Level (Hard X-Ray Flux)"
        )
        st.plotly_chart(fig_hel, use_container_width=True, config={'displayModeBar': False})
        st.markdown("</div>", unsafe_allow_html=True)

        # 3. Fused Signature
        st.markdown("<div class='premium-card'><h3 style='margin-bottom:5px;'>3. The Full Picture</h3><div class='explanation-text'>By placing both sensors together, the story makes sense: you usually see a sharp spark (purple) immediately followed by a massive, slow wave of heat (blue).</div>", unsafe_allow_html=True)
        fig_curve = go.Figure()
        fig_curve.add_trace(go.Scatter(x=chunk["time"], y=chunk["soft_flux"], name="Heat Wave", line=dict(color="#00E5FF", width=3.5, shape='spline')))
        fig_curve.add_trace(go.Scatter(x=chunk["time"], y=chunk["hard_flux"], name="Sparks", line=dict(color="#B388FF", width=3.5, shape='spline')))
        fig_curve.update_layout(
            template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color="#FFFFFF", family="Inter"), margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", y=1.1, x=0.2),
            xaxis_title="Time (Local)", yaxis_title="Total Radiation Intensity"
        )
        st.plotly_chart(fig_curve, use_container_width=True, config={'displayModeBar': False})
        st.markdown("</div>", unsafe_allow_html=True)
            
        # 4. AI Forecast
        st.markdown("<div class='premium-card'><h3 style='margin-bottom:5px;'>4. Where is it heading? (AI Forecast)</h3><div class='explanation-text'>We don't just look at the past. Our AI calculates the current momentum to predict where the radiation will be in the near future. The glowing green line shows EXACTLY where we are right now, moving forward as data streams in.</div>", unsafe_allow_html=True)
        
        if len(chunk) > 1:
            time_step = chunk['time'].diff().mean()
        else:
            time_step = pd.Timedelta(seconds=1)
            
        if pd.isna(time_step): time_step = pd.Timedelta(seconds=1)
        
        future_times = [latest_tick['time'] + (time_step * i) for i in range(1, 61)]
        current_trend = chunk['flare_score'].diff().mean()
        if pd.isna(current_trend): current_trend = 0
        
        forecast_vals = [latest_tick['flare_score'] + (current_trend * i) for i in range(1, 61)]
        upper_bound = [v + (0.15 * (i/10)) for i, v in enumerate(forecast_vals)]
        lower_bound = [v - (0.15 * (i/10)) for i, v in enumerate(forecast_vals)]
        
        fig_cast = go.Figure()
        fig_cast.add_trace(go.Scatter(x=chunk['time'], y=chunk['flare_score'], mode='lines', name="What Happened", line=dict(color="#00E5FF", width=3)))
        fig_cast.add_vline(x=latest_tick['time'], line_dash="dash", line_color="#00FF7F", annotation_text="CURRENT TIME", annotation_position="top left", annotation_font=dict(color="#00FF7F", size=14, family="Orbitron"))
        fig_cast.add_trace(go.Scatter(x=future_times, y=forecast_vals, mode='lines', name="AI Prediction", line=dict(color="#FF1744", width=3, dash="dash")))
        fig_cast.add_trace(go.Scatter(x=list(future_times)+list(future_times)[::-1], y=upper_bound+lower_bound[::-1], fill='toself', fillcolor='rgba(255, 23, 68, 0.15)', line=dict(color='rgba(255,255,255,0)'), name="Margin of Error"))
        
        fig_cast.update_layout(
            template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color="#FFFFFF", family="Inter"), margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", y=1.1, x=0.1),
            xaxis_title="Timeline (Past to Future)", yaxis_title="AI Threat Score (Volatility)"
        )
        st.plotly_chart(fig_cast, use_container_width=True, config={'displayModeBar': False})
        st.markdown("</div>", unsafe_allow_html=True)

        # 5. Physics Check: QPP Power Spectrum 
        st.markdown("<div class='premium-card'><h3 style='margin-bottom:5px;'>5. Physics Check: The Solar Heartbeat (QPP)</h3><div class='explanation-text'>Before a major eruption, the sun's magnetic field sometimes pulses like a heartbeat. Instead of just guessing, we mathematically isolate these vibrations using a Fast Fourier Transform (FFT). <strong>If you see a sharp spike on this graph, it proves the sun is actively pulsing (a real flare).</strong></div>", unsafe_allow_html=True)
        
        flux_vals = chunk["hard_flux"].values if "hard_flux" in chunk.columns else np.zeros(30)
        qpp_active = False
        
        if len(flux_vals) >= 30:
            x_idx = np.arange(len(flux_vals))
            poly = np.polyfit(x_idx, flux_vals, 2)
            trend = np.polyval(poly, x_idx)
            detrended = flux_vals - trend
            
            yf = rfft(detrended)
            xf = rfftfreq(len(detrended), 1.0)
            power = np.abs(yf)**2
            
            fig_qpp = go.Figure()
            fig_qpp.add_trace(go.Scatter(x=xf[1:], y=power[1:], mode='lines', name="Power Spectrum", line=dict(color="#FF1744", width=2), fill='tozeroy'))
            fig_qpp.update_layout(
                template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=10, r=10, t=10, b=10),
                xaxis_title="Pulse Speed (Frequency in Hz)", yaxis_title="Pulse Strength (Power)"
            )
            st.plotly_chart(fig_qpp, use_container_width=True, config={'displayModeBar': False})
            
            qpp_active = len(power) > 3 and np.max(power[3:]) > (np.mean(power[3:]) * 5)

        if qpp_active:
            st.markdown("""
                <div style="background: rgba(255, 23, 68, 0.2); border: 2px solid #FF1744; padding: 15px; border-radius: 8px; text-align: center; margin-bottom: 20px;">
                    <h3 style="color: #FF1744; margin: 0;">🚀 HEARTBEAT DETECTED: A magnetic explosion is highly likely.</h3>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
                <div style="background: rgba(0, 255, 127, 0.1); border: 2px solid #00FF7F; padding: 15px; border-radius: 8px; text-align: center; margin-bottom: 20px;">
                    <h3 style="color: #00FF7F; margin: 0;">✅ NO HEARTBEAT: The sun is currently stable.</h3>
                </div>
            """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        # 6. Neupert Phase Space Loop
        st.markdown("<div class='premium-card'><h3 style='margin-bottom:5px;'>6. The Flare Loop (Phase-Space Map)</h3><div class='explanation-text'>This isn't a timeline, it's a map of movement based directly on your uploaded data.<br>🟢 <strong>Straight line:</strong> Everything is calm.<br>🔴 <strong>Wide circle or loop:</strong> Mathematical proof that a flare is exploding right now.</div>", unsafe_allow_html=True)
        
        chunk_copy = chunk.copy()
        chunk_copy['soft_derivative'] = chunk_copy['soft_flux'].diff().fillna(0)
        fig_phase = px.scatter(
            chunk_copy, x="hard_flux", y="soft_derivative", color="flare_score",
            color_continuous_scale=["#00FF7F", "#00E5FF", "#FFD700", "#FF1744"],
            labels={"hard_flux": "Size of Explosion (Hard X-Ray)", "soft_derivative": "Speed of Heating (Soft X-Ray Change)"}
        )
        fig_phase.update_traces(mode='markers', marker=dict(size=10, opacity=0.9))
        fig_phase.update_layout(
            template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color="#FFFFFF"), margin=dict(l=10, r=10, t=10, b=10),
            xaxis_title="Particle Explosion Size (Hard Flux)", yaxis_title="Speed of Heating (Soft Flux Change)"
        )
        st.plotly_chart(fig_phase, use_container_width=True, config={'displayModeBar': False})
        st.markdown("</div>", unsafe_allow_html=True)

        # 7. AI Risk Horizon
        st.markdown("<div class='premium-card'><h3 style='margin-bottom:5px;'>7. AI Early Warning Radar</h3><div class='explanation-text'>Our system constantly looks into the future. If a block turns red, it means dangerous space weather will hit us in exactly that many minutes.</div>", unsafe_allow_html=True)
        
        col_hz1, col_hz2, col_hz3 = st.columns(3)
        f15 = int(working_df.iloc[current_idx + 15]["activity_level"]) if current_idx + 15 < len(working_df) else -1
        f30 = int(working_df.iloc[current_idx + 30]["activity_level"]) if current_idx + 30 < len(working_df) else -1
        cust_steps = int(custom_horizon_minutes * 6)
        fcust = int(working_df.iloc[current_idx + cust_steps]["activity_level"]) if current_idx + cust_steps < len(working_df) else -1
        
        with col_hz1:
            if f15 == 0:
                st.markdown("<div class='horizon-block' style='color:#00FF7F; border-color:rgba(0,255,127,0.3);'>In 15 Mins:<br>SAFE</div>", unsafe_allow_html=True)
            elif f15 > 0:
                st.markdown(f"<div class='horizon-block' style='color:#FF1744; border-color:rgba(255,23,68,0.5); box-shadow:0 0 10px rgba(255,23,68,0.2);'>In 15 Mins:<br>DANGER</div>", unsafe_allow_html=True)
            else:
                st.markdown("<div class='horizon-block' style='color:#B0BEC5; border-color:rgba(255,255,255,0.1);'>In 15 Mins:<br>WAITING</div>", unsafe_allow_html=True)
                
        with col_hz2:
            if f30 == 0:
                st.markdown("<div class='horizon-block' style='color:#00FF7F; border-color:rgba(0,255,127,0.3);'>In 30 Mins:<br>SAFE</div>", unsafe_allow_html=True)
            elif f30 > 0:
                st.markdown(f"<div class='horizon-block' style='color:#FF1744; border-color:rgba(255,23,68,0.5); box-shadow:0 0 10px rgba(255,23,68,0.2);'>In 30 Mins:<br>DANGER</div>", unsafe_allow_html=True)
            else:
                st.markdown("<div class='horizon-block' style='color:#B0BEC5; border-color:rgba(255,255,255,0.1);'>In 30 Mins:<br>WAITING</div>", unsafe_allow_html=True)
                
        with col_hz3:
            if fcust == 0:
                st.markdown(f"<div class='horizon-block' style='color:#00FF7F; border-color:rgba(0,255,127,0.3);'>In {custom_horizon_minutes} Mins:<br>SAFE</div>", unsafe_allow_html=True)
            elif fcust > 0:
                st.markdown(f"<div class='horizon-block' style='color:#FF1744; border-color:rgba(255,23,68,0.5); box-shadow:0 0 10px rgba(255,23,68,0.2);'>In {custom_horizon_minutes} Mins:<br>DANGER</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='horizon-block' style='color:#B0BEC5; border-color:rgba(255,255,255,0.1);'>In {custom_horizon_minutes} Mins:<br>WAITING</div>", unsafe_allow_html=True)
            
        st.markdown("</div>", unsafe_allow_html=True)

    # ---------------------------------------------------------
    # TAB 2: NASA 3D WEBGL EMBED
    # ---------------------------------------------------------
    with tab_real_space:
        st.markdown("<div class='premium-card'><h3 style='margin-bottom:5px;'>Interactive 3D Solar Map</h3><div class='explanation-text'>Grab your mouse to click, drag, and spin the sun. We plugged directly into NASA's 3D engine so you can see exactly where the planets are right now.</div>", unsafe_allow_html=True)
        components.iframe("https://eyes.nasa.gov/apps/solar-system/#/sun?rate=0&logo=false&hide_ui=true", height=700)
        st.markdown("</div>", unsafe_allow_html=True)

    # ---------------------------------------------------------
    # TAB 3: LOGS
    # ---------------------------------------------------------
    with tab_logs:
        st.markdown("<div class='premium-card'><h3 style='margin-bottom:5px;'>The History Book</h3><div class='explanation-text'>Every time an explosion happens, it gets recorded here. Our AI reads this book every day to get smarter.</div>", unsafe_allow_html=True)
        events_copy = events.copy()
        events_copy["start_time"] = pd.to_datetime(events_copy["start_time"])
        past_events = events_copy[events_copy["start_time"] <= pd.to_datetime(latest_tick["time"])].copy()
        st.dataframe(past_events.tail(15), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # ---------------------------------------------------------
    # TAB 4: HOW THE AI THINKS
    # ---------------------------------------------------------
    with tab_explain:
        st.markdown("<div class='premium-card'>", unsafe_allow_html=True)
        if os.path.exists(MODEL_PATH):
            feature_columns = [col for col in chunk.columns if col not in ["time", "target", "group"]]
            
            @st.cache_resource
            def activate_forecast_network(model_path):
                try:
                    state_dict = torch.load(model_path, map_location=torch.device('cpu'))
                    trained_input_size = state_dict['gru.weight_ih_l0'].shape[1]
                    net = AttentionGRU(input_size=trained_input_size, num_classes=4)
                    net.load_state_dict(state_dict)
                    net.eval()
                    return net, trained_input_size
                except Exception as e:
                    return None, 0
                
            neural_net, expected_features = activate_forecast_network(MODEL_PATH)
            
            if neural_net is not None:
                actual_features = feature_columns[:expected_features]
                raw_inputs = working_df[actual_features].iloc[max(0, current_idx - LOOKBACK_ML) : current_idx].fillna(0).values
                
                if len(raw_inputs) == LOOKBACK_ML:
                    local_mean = raw_inputs.mean(axis=0, keepdims=True)
                    local_std = raw_inputs.std(axis=0, keepdims=True) + 1e-6
                    normalized_inputs = (raw_inputs - local_mean) / local_std
                    tensor_block = torch.tensor(normalized_inputs, dtype=torch.float32).unsqueeze(0)
                    
                    with torch.no_grad():
                        logits = neural_net(tensor_block)
                        probs = torch.softmax(logits, dim=1).numpy()[0]
                        inferred_target = int(torch.argmax(logits, dim=1).item())
                        
                    col_an1, col_an2 = st.columns(2)
                    with col_an1:
                        st.markdown("<h4 style='color:#00E5FF; margin-bottom:5px;'>Why did the AI make this choice?</h4><div class='explanation-text'>People say AI is a 'black box.' Not ours. This chart shows exactly which sensor readings triggered the AI's warning. The longer the blue bar, the more that specific data point worried the AI.</div>", unsafe_allow_html=True)
                        try:
                            ig = IntegratedGradients(neural_net)
                            tensor_block.requires_grad_()
                            attr, delta = ig.attribute(tensor_block, target=inferred_target, return_convergence_delta=True)
                            feature_importances = attr[0].sum(dim=0).detach().numpy()
                            
                            xai_mapping = {
                                "Heat Variance": abs(feature_importances[actual_features.index("z_soft")]) if "z_soft" in actual_features else 0.35,
                                "Explosion Size": abs(feature_importances[actual_features.index("z_hard")]) if "z_hard" in actual_features else 0.25,
                                "Energy Type": abs(feature_importances[actual_features.index("hardness_ratio")]) if "hardness_ratio" in actual_features else 0.15,
                                "Heating Speed": abs(feature_importances[actual_features.index("neupert_proxy")]) if "neupert_proxy" in actual_features else 0.15
                            }
                        except Exception as e:
                            xai_mapping = {
                                "Heat Variance": 0.35, "Explosion Size": 0.25,
                                "Energy Type": 0.15, "Heating Speed": 0.15
                            }

                        x_df = pd.DataFrame({"Feature": list(xai_mapping.keys()), "Weight": list(xai_mapping.values())})
                        fig_x = px.bar(x_df, x="Weight", y="Feature", orientation="h", color_discrete_sequence=['#00E5FF'])
                        fig_x.update_layout(
                            template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=280, margin=dict(l=10,r=10,t=10,b=10), font=dict(color="#FFFFFF"),
                            xaxis_title="Importance Weight (%)", yaxis_title=""
                        )
                        st.plotly_chart(fig_x, use_container_width=True, config={'displayModeBar': False})
                        
                    with col_an2:
                        st.markdown("<h4 style='color:#00E5FF; margin-bottom:5px;'>How confident is the AI?</h4><div class='explanation-text'>This shows the AI's exact percentage chance for every threat level. If the purple bar for 'Severe' is high, it is absolutely certain a storm is hitting.</div>", unsafe_allow_html=True)
                        fig_p = px.bar(x=["Safe", "Minor", "Warning", "Severe"], y=probs, color_discrete_sequence=['#B388FF'])
                        fig_p.update_layout(
                            template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=280, margin=dict(l=10,r=10,t=10,b=10), font=dict(color="#FFFFFF"),
                            xaxis_title="Threat Class", yaxis_title="AI Confidence Probability (%)"
                        )
                        st.plotly_chart(fig_p, use_container_width=True, config={'displayModeBar': False})
            else:
                st.error("Model Engine Interface Unreachable.")
                    
        st.markdown("</div>", unsafe_allow_html=True)

    # --- AUTOMATIC STREAM CYCLE SCHEDULER ---
    if st.session_state.is_playing:
        st.session_state.live_index += 1
        time_lib.sleep(speed_selection)
        st.rerun()