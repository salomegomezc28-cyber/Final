import streamlit as st
import paho.mqtt.client as mqtt
import json
import time
from bokeh.models.widgets import Button
from bokeh.models import CustomJS
from streamlit_bokeh_events import streamlit_bokeh_events

# ── Configuración de página ──────────────────
st.set_page_config(
    page_title="Casa Inteligente",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Estilos ──────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.stApp { background-color: #0f172a; color: #e2e8f0; }
[data-testid="stSidebar"] {
    background-color: #1e293b !important;
    border-right: 1px solid #334155;
}
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    color: #38bdf8 !important;
    font-weight: 700 !important;
    font-size: 0.95rem !important;
    text-transform: uppercase !important;
}
[data-testid="stSidebar"] label { color: #94a3b8 !important; font-size: 0.85rem !important; }
h1 { color: #38bdf8 !important; font-weight: 700 !important; }
h2, h3 { color: #7dd3fc !important; font-weight: 600 !important; }
.stButton > button {
    background: #0284c7 !important; color: #ffffff !important;
    border: none !important; border-radius: 8px !important;
    font-weight: 600 !important; width: 100% !important;
    padding: 0.6rem 1.4rem !important;
    transition: background 0.2s ease !important;
}
.stButton > button:hover { background: #0369a1 !important; }
[data-testid="metric-container"] {
    background: #1e293b; border: 1px solid #334155;
    border-top: 3px solid #38bdf8;
    border-radius: 8px; padding: 18px 22px;
}
.device-card {
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 12px;
    padding: 24px 28px;
    margin-bottom: 16px;
}
.header-card {
    background: #1e293b;
    border: 1px solid #334155;
    border-left: 5px solid #38bdf8;
    border-radius: 8px;
    padding: 28px 36px;
    margin-bottom: 24px;
}
.status-ok {
    background: #052e16; border: 1px solid #166534;
    border-left: 4px solid #22c55e; border-radius: 8px;
    padding: 12px 18px; margin: 8px 0;
    font-size: 0.88rem; color: #86efac; font-weight: 500;
}
.status-err {
    background: #1c0a00; border: 1px solid #9a3412;
    border-left: 4px solid #f97316; border-radius: 8px;
    padding: 12px 18px; margin: 8px 0;
    font-size: 0.88rem; color: #fdba74; font-weight: 500;
}
.bk-btn { 
    background: #0284c7 !important; color: #fff !important;
    border-radius: 8px !important; font-weight: 700 !important;
    font-size: 1rem !important; min-height: 50px !important;
    width: 100% !important;
}
</style>
""", unsafe_allow_html=True)

# ── MQTT ─────────────────────────────────────
BROKER  = "broker.mqttdashboard.com"
PORT    = 1883
TOPIC   = "casaIM/control"

def publicar_mqtt(payload: dict):
    try:
        c = mqtt.Client(client_id=f"streamlit_{int(time.time())}")
        c.connect(BROKER, PORT, 60)
        c.publish(TOPIC, json.dumps(payload))
        c.disconnect()
        return True
    except Exception as e:
        st.session_state["mqtt_error"] = str(e)
        return False

# ── Session state ─────────────────────────────
for key, default in {
    "luz": False,
    "alarma": False,
    "puerta": "cerrada",
    "mqtt_error": "",
    "historial": [],
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ── Sidebar ───────────────────────────────────
with st.sidebar:
    st.markdown("## 🏠 Casa Inteligente")
    st.divider()
    st.markdown("### CONEXIÓN MQTT")
    st.markdown(f"""
    <div style='background:#0f172a;border:1px solid #334155;border-radius:8px;padding:12px 16px;'>
        <p style='margin:0;color:#94a3b8;font-size:0.82rem;'>🔌 Broker</p>
        <p style='margin:2px 0 0 0;color:#38bdf8;font-size:0.88rem;font-weight:600;'>{BROKER}</p>
        <p style='margin:8px 0 0 0;color:#94a3b8;font-size:0.82rem;'>📢 Topic</p>
        <p style='margin:2px 0 0 0;color:#38bdf8;font-size:0.88rem;font-weight:600;'>{TOPIC}</p>
    </div>
    """, unsafe_allow_html=True)
    st.divider()
    st.markdown("### ESTADO ACTUAL")
    st.markdown(f"💡 Luz: {'🟢 Encendida' if st.session_state['luz'] else '🔴 Apagada'}")
    st.markdown(f"🚨 Alarma: {'🟢 Activa' if st.session_state['alarma'] else '🔴 Inactiva'}")
    st.markdown(f"🚪 Puerta: {'🔓 Abierta' if st.session_state['puerta'] == 'abierta' else '🔒 Cerrada'}")
    st.divider()
    st.markdown("### NAVEGACIÓN")
    st.page_link("inicio.py",            label="🏠 Panel de Control", )
    st.page_link("pages/monitoreo.py",   label="📡 Monitoreo y Acceso")

# ── Header ────────────────────────────────────
st.markdown("""
<div class="header-card">
    <h1 style="margin:0; font-size:2rem;">🏠 Panel de Control</h1>
    <p style="margin:6px 0 0 0; color:#38bdf8; font-size:0.97rem;">
        Casa Inteligente — Control por voz, botones y slider · ESP32 vía MQTT
    </p>
</div>
""", unsafe_allow_html=True)

# ── Layout principal ──────────────────────────
col1, col2 = st.columns(2, gap="large")

# ── Columna 1: Control manual ─────────────────
with col1:
    st.markdown("### 🎛️ Control Manual")

    # Luz
    st.markdown('<div class="device-card">', unsafe_allow_html=True)
    st.markdown("#### 💡 Luz de la Sala")
    luz_col1, luz_col2 = st.columns(2)
    with luz_col1:
        if st.button("Encender 💡"):
            if publicar_mqtt({"luz": 1}):
                st.session_state["luz"] = True
                st.session_state["historial"].append({"ts": time.strftime("%H:%M:%S"), "cmd": "Luz encendida"})
                st.markdown('<div class="status-ok">✅ Luz encendida</div>', unsafe_allow_html=True)
    with luz_col2:
        if st.button("Apagar 💡"):
            if publicar_mqtt({"luz": 0}):
                st.session_state["luz"] = False
                st.session_state["historial"].append({"ts": time.strftime("%H:%M:%S"), "cmd": "Luz apagada"})
                st.markdown('<div class="status-ok">✅ Luz apagada</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Puerta
    st.markdown('<div class="device-card">', unsafe_allow_html=True)
    st.markdown("#### 🚪 Puerta Principal")
    p_col1, p_col2 = st.columns(2)
    with p_col1:
        if st.button("Abrir 🔓"):
            if publicar_mqtt({"puerta": "abre"}):
                st.session_state["puerta"] = "abierta"
                st.session_state["historial"].append({"ts": time.strftime("%H:%M:%S"), "cmd": "Puerta abierta"})
                st.markdown('<div class="status-ok">✅ Puerta abierta</div>', unsafe_allow_html=True)
    with p_col2:
        if st.button("Cerrar 🔒"):
            if publicar_mqtt({"puerta": "cierra"}):
                st.session_state["puerta"] = "cerrada"
                st.session_state["historial"].append({"ts": time.strftime("%H:%M:%S"), "cmd": "Puerta cerrada"})
                st.markdown('<div class="status-ok">✅ Puerta cerrada</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Alarma
    st.markdown('<div class="device-card">', unsafe_allow_html=True)
    st.markdown("#### 🚨 Alarma")
    a_col1, a_col2 = st.columns(2)
    with a_col1:
        if st.button("Activar 🚨"):
            if publicar_mqtt({"alarma": 1}):
                st.session_state["alarma"] = True
                st.session_state["historial"].append({"ts": time.strftime("%H:%M:%S"), "cmd": "Alarma activada"})
                st.markdown('<div class="status-ok">✅ Alarma activada</div>', unsafe_allow_html=True)
    with a_col2:
        if st.button("Desactivar 🚨"):
            if publicar_mqtt({"alarma": 0}):
                st.session_state["alarma"] = False
                st.session_state["historial"].append({"ts": time.strftime("%H:%M:%S"), "cmd": "Alarma desactivada"})
                st.markdown('<div class="status-ok">✅ Alarma desactivada</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ── Columna 2: Control por voz ────────────────
with col2:
    st.markdown("### 🎙️ Control por Voz")
    st.markdown('<div class="device-card">', unsafe_allow_html=True)
    st.markdown("""
    <p style='color:#94a3b8;font-size:0.9rem;margin-bottom:16px;'>
    Toca el botón, habla uno de estos comandos y se enviará automáticamente al ESP32:
    </p>
    <div style='display:flex;flex-wrap:wrap;gap:8px;margin-bottom:16px;'>
        <span style='background:#0f172a;border:1px solid #38bdf8;border-radius:20px;padding:4px 12px;font-size:0.82rem;color:#38bdf8;'>"enciende las luces"</span>
        <span style='background:#0f172a;border:1px solid #38bdf8;border-radius:20px;padding:4px 12px;font-size:0.82rem;color:#38bdf8;'>"apaga las luces"</span>
        <span style='background:#0f172a;border:1px solid #38bdf8;border-radius:20px;padding:4px 12px;font-size:0.82rem;color:#38bdf8;'>"abre la puerta"</span>
        <span style='background:#0f172a;border:1px solid #38bdf8;border-radius:20px;padding:4px 12px;font-size:0.82rem;color:#38bdf8;'>"cierra la puerta"</span>
        <span style='background:#0f172a;border:1px solid #38bdf8;border-radius:20px;padding:4px 12px;font-size:0.82rem;color:#38bdf8;'>"activa la alarma"</span>
        <span style='background:#0f172a;border:1px solid #38bdf8;border-radius:20px;padding:4px 12px;font-size:0.82rem;color:#38bdf8;'>"desactiva la alarma"</span>
    </div>
    """, unsafe_allow_html=True)

    stt_button = Button(label="🎙 Iniciar escucha", width=400, button_type="primary")
    stt_button.js_on_event("button_click", CustomJS(code="""
        var recognition = new webkitSpeechRecognition();
        recognition.lang = 'es-ES';
        recognition.continuous = false;
        recognition.interimResults = false;
        recognition.onresult = function(e) {
            var value = e.results[0][0].transcript.toLowerCase().trim();
            if (value != "") {
                document.dispatchEvent(new CustomEvent("GET_TEXT", {detail: value}));
            }
        }
        recognition.start();
    """))

    result = streamlit_bokeh_events(
        stt_button, events="GET_TEXT", key="voz_control",
        refresh_on_update=False, override_height=80, debounce_time=0,
    )

    if result and "GET_TEXT" in result:
        texto = result["GET_TEXT"].strip().lower()
        st.markdown(f"""
        <div style='background:#0f172a;border:1px solid #334155;border-radius:8px;
        padding:12px 16px;margin:12px 0;font-size:0.95rem;color:#e2e8f0;'>
        🎙 <strong>"{texto}"</strong>
        </div>""", unsafe_allow_html=True)

        # Mapeo de comandos de voz
        comandos = {
            "enciende las luces":   {"luz": 1},
            "apaga las luces":      {"luz": 0},
            "abre la puerta":       {"puerta": "abre"},
            "cierra la puerta":     {"puerta": "cierra"},
            "activa la alarma":     {"alarma": 1},
            "desactiva la alarma":  {"alarma": 0},
        }

        reconocido = False
        for cmd, payload in comandos.items():
            if cmd in texto:
                if publicar_mqtt(payload):
                    # Actualizar estado
                    if "luz" in payload:
                        st.session_state["luz"] = payload["luz"] == 1
                    if "puerta" in payload:
                        st.session_state["puerta"] = "abierta" if payload["puerta"] == "abre" else "cerrada"
                    if "alarma" in payload:
                        st.session_state["alarma"] = payload["alarma"] == 1
                    st.session_state["historial"].append({"ts": time.strftime("%H:%M:%S"), "cmd": f'Voz: "{texto}"'})
                    st.markdown(f'<div class="status-ok">✅ Comando ejecutado: <strong>{cmd}</strong></div>', unsafe_allow_html=True)
                reconocido = True
                break

        if not reconocido:
            st.markdown('<div class="status-err">⚠️ Comando no reconocido. Intenta de nuevo.</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # Historial de comandos
    if st.session_state["historial"]:
        st.markdown("### 📋 Historial de Comandos")
        st.markdown('<div class="device-card">', unsafe_allow_html=True)
        for item in reversed(st.session_state["historial"][-8:]):
            st.markdown(f"""
            <div style='display:flex;gap:12px;padding:6px 0;border-bottom:1px solid #1e293b;'>
                <span style='color:#38bdf8;font-size:0.82rem;min-width:70px;'>{item['ts']}</span>
                <span style='color:#e2e8f0;font-size:0.82rem;'>{item['cmd']}</span>
            </div>""", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

# ── Error MQTT ────────────────────────────────
if st.session_state["mqtt_error"]:
    st.markdown(f'<div class="status-err">❌ Error MQTT: {st.session_state["mqtt_error"]}</div>', unsafe_allow_html=True)
