st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* Fondo general */
.stApp {
    background: linear-gradient(135deg, #0F172A 0%, #111827 100%);
    color: #F8FAFC;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: #111827 !important;
    border-right: 1px solid #1E293B;
}

[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    color: #38BDF8 !important;
    font-weight: 700 !important;
    letter-spacing: 1px;
}

[data-testid="stSidebar"] label,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span {
    color: #CBD5E1 !important;
}

/* Títulos */
h1 {
    color: #FFFFFF !important;
    font-weight: 700 !important;
}

h2, h3 {
    color: #38BDF8 !important;
    font-weight: 600 !important;
}

/* Botones */
.stButton > button {
    background: linear-gradient(90deg, #06B6D4, #3B82F6) !important;
    color: white !important;
    border: none !important;
    border-radius: 12px !important;
    font-weight: 600 !important;
    width: 100% !important;
    padding: 0.75rem 1.2rem !important;
    transition: all 0.25s ease !important;
    box-shadow: 0 4px 12px rgba(59,130,246,0.25);
}

.stButton > button:hover {
    transform: translateY(-2px);
    background: linear-gradient(90deg, #0284C7, #2563EB) !important;
}

/* Tarjetas */
.device-card {
    background: rgba(15, 23, 42, 0.75);
    border: 1px solid #1E293B;
    border-radius: 18px;
    padding: 24px;
    margin-bottom: 18px;
    backdrop-filter: blur(8px);
    box-shadow: 0 4px 20px rgba(0,0,0,0.25);
}

.device-card h4 {
    color: #F8FAFC !important;
    margin-bottom: 18px !important;
    font-size: 1.1rem !important;
}

/* Header principal */
.header-card {
    background: linear-gradient(135deg, #1E293B, #0F172A);
    border: 1px solid #334155;
    border-radius: 20px;
    padding: 32px;
    margin-bottom: 28px;
    box-shadow: 0 6px 24px rgba(0,0,0,0.35);
}

/* Mensajes */
.status-ok {
    background: rgba(34,197,94,0.15);
    border: 1px solid #22C55E;
    border-left: 5px solid #22C55E;
    border-radius: 10px;
    padding: 14px 18px;
    margin: 10px 0;
    color: #DCFCE7;
    font-weight: 500;
}

.status-err {
    background: rgba(239,68,68,0.15);
    border: 1px solid #EF4444;
    border-left: 5px solid #EF4444;
    border-radius: 10px;
    padding: 14px 18px;
    margin: 10px 0;
    color: #FEE2E2;
    font-weight: 500;
}

/* Botón de voz */
.bk-btn {
    background: linear-gradient(90deg, #8B5CF6, #6366F1) !important;
    color: white !important;
    border: none !important;
    border-radius: 12px !important;
    font-weight: 700 !important;
    font-size: 1rem !important;
    padding: 14px 0 !important;
    width: 100% !important;
    transition: all 0.25s ease !important;
}

.bk-btn:hover {
    background: linear-gradient(90deg, #7C3AED, #4F46E5) !important;
    transform: translateY(-2px);
}

.bk-toolbar-box,
.bk,
.bk-root {
    border: none !important;
    background: transparent !important;
    box-shadow: none !important;
}

iframe[title="streamlit_bokeh_events"] {
    border: none !important;
    background: transparent !important;
}

/* Chips de comandos */
.command-chip {
    background: rgba(56,189,248,0.12);
    border: 1px solid #38BDF8;
    color: #BAE6FD;
    border-radius: 999px;
    padding: 6px 14px;
    font-size: 0.8rem;
}

/* Scroll */
::-webkit-scrollbar {
    width: 8px;
}

::-webkit-scrollbar-thumb {
    background: #334155;
    border-radius: 10px;
}
</style>
""", unsafe_allow_html=True)

Y además cambia el header por este para que se vea mucho más profesional:

st.markdown("""
<div class="header-card">
    <h1 style="margin:0; font-size:2.3rem;">
        🏠 SmartHome Control Center
    </h1>

    <p style="
        margin-top:10px;
        color:#CBD5E1;
        font-size:1rem;
        line-height:1.6;
    ">
        Plataforma de automatización inteligente con control multimodal 
        mediante voz, interfaz interactiva y comunicación MQTT en tiempo real.
    </p>
</div>
""", unsafe_allow_html=True)
