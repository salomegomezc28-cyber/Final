st.markdown("""
<style>

@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Poppins', sans-serif;
}

/* ─────────────────────────────────────────────
   Fondo general
───────────────────────────────────────────── */

.stApp {
    background: linear-gradient(135deg, #081120 0%, #0B172A 100%);
    color: #F4F7FB;
}

/* ─────────────────────────────────────────────
   Sidebar
───────────────────────────────────────────── */

[data-testid="stSidebar"] {
    background: #0D1B2A !important;
    border-right: 1px solid rgba(0,191,255,0.15);
}

[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    color: #00BFFF !important;
    font-weight: 700 !important;
    letter-spacing: 1px;
    text-transform: uppercase;
}

[data-testid="stSidebar"] label,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span {
    color: #D9E6F2 !important;
}

/* ─────────────────────────────────────────────
   Tipografía
───────────────────────────────────────────── */

h1 {
    color: #FFFFFF !important;
    font-weight: 700 !important;
    letter-spacing: -1px;
}

h2, h3 {
    color: #00BFFF !important;
    font-weight: 600 !important;
}

p {
    color: #AFC6DD;
}

/* ─────────────────────────────────────────────
   Header principal
───────────────────────────────────────────── */

.header-card {
    background: linear-gradient(135deg, #111C34 0%, #162544 100%);
    border: 1px solid rgba(0,191,255,0.2);
    border-left: 6px solid #00BFFF;
    border-radius: 20px;
    padding: 32px;
    margin-bottom: 28px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.25);
}

/* ─────────────────────────────────────────────
   Tarjetas de dispositivos
───────────────────────────────────────────── */

.device-card {
    background: rgba(17, 28, 52, 0.95);
    border: 1px solid rgba(0,191,255,0.12);
    border-radius: 18px;
    padding: 26px;
    margin-bottom: 20px;
    box-shadow: 0 8px 24px rgba(0,0,0,0.22);
    transition: all 0.25s ease;
}

.device-card:hover {
    transform: translateY(-2px);
    border: 1px solid rgba(0,191,255,0.35);
}

.device-card h4 {
    color: #FFFFFF !important;
    margin-bottom: 18px !important;
    font-size: 1.08rem !important;
    font-weight: 600 !important;
}

/* ─────────────────────────────────────────────
   Botones
───────────────────────────────────────────── */

.stButton > button {
    background: linear-gradient(135deg, #00BFFF 0%, #0099FF 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 12px !important;
    font-weight: 600 !important;
    width: 100% !important;
    padding: 0.75rem 1rem !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 4px 12px rgba(0,191,255,0.25);
}

.stButton > button:hover {
    transform: translateY(-1px);
    background: linear-gradient(135deg, #19C8FF 0%, #00A2FF 100%) !important;
    box-shadow: 0 6px 18px rgba(0,191,255,0.35);
}

/* ─────────────────────────────────────────────
   Estados
───────────────────────────────────────────── */

.status-ok {
    background: rgba(0,230,118,0.12);
    border: 1px solid rgba(0,230,118,0.3);
    border-left: 5px solid #00E676;
    border-radius: 12px;
    padding: 14px 18px;
    margin: 10px 0;
    color: #DFFFEA;
    font-weight: 500;
}

.status-err {
    background: rgba(255,77,109,0.12);
    border: 1px solid rgba(255,77,109,0.3);
    border-left: 5px solid #FF4D6D;
    border-radius: 12px;
    padding: 14px 18px;
    margin: 10px 0;
    color: #FFDCE3;
    font-weight: 500;
}

/* ─────────────────────────────────────────────
   Chips de comandos de voz
───────────────────────────────────────────── */

.voice-chip {
    background: rgba(0,191,255,0.08);
    border: 1px solid rgba(0,191,255,0.3);
    border-radius: 30px;
    padding: 6px 14px;
    font-size: 0.8rem;
    color: #8ED8FF;
}

/* ─────────────────────────────────────────────
   Historial
───────────────────────────────────────────── */

.history-item {
    display:flex;
    gap:12px;
    padding:10px 0;
    border-bottom:1px solid rgba(255,255,255,0.06);
}

/* ─────────────────────────────────────────────
   Bokeh botón voz
───────────────────────────────────────────── */

.bk-btn {
    background: linear-gradient(135deg, #00BFFF 0%, #008CFF 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 14px !important;
    font-weight: 700 !important;
    font-size: 1rem !important;
    font-family: 'Poppins', sans-serif !important;
    padding: 14px 0 !important;
    width: 100% !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 6px 18px rgba(0,191,255,0.25);
}

.bk-btn:hover {
    background: linear-gradient(135deg, #19C8FF 0%, #00A2FF 100%) !important;
}

/* ─────────────────────────────────────────────
   Containers y bordes
───────────────────────────────────────────── */

iframe[title="streamlit_bokeh_events"] {
    border: none !important;
    background: transparent !important;
}

hr {
    border-color: rgba(255,255,255,0.08) !important;
}

</style>
""", unsafe_allow_html=True)
