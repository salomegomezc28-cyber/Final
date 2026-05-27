"""
🏠 Casa Inteligente — Panel de Control
Interfaces Multimodales · MQTT + Voz (streamlit-bokeh-events)
"""

import streamlit as st
import streamlit.components.v1 as components
from bokeh.models.widgets import Button
from bokeh.models import CustomJS
from streamlit_bokeh_events import streamlit_bokeh_events
import paho.mqtt.client as paho
import json
import time
import threading

# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Casa Inteligente",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# ESTILOS VISUALES
# Solo se modifica presentación: colores, tipografía, espaciado y redacción visual.
# La lógica funcional se conserva intacta.
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

:root {
    --bg-main: #F4F8FB;
    --bg-soft: #EAF3F5;
    --bg-card: #FFFFFF;
    --primary: #0F766E;
    --primary-dark: #115E59;
    --secondary: #2563EB;
    --accent: #38BDF8;
    --warning: #F59E0B;
    --danger: #DC2626;
    --success: #16A34A;
    --text-main: #172033;
    --text-muted: #64748B;
    --border-soft: #D6E4EA;
    --shadow-soft: 0 18px 45px rgba(15, 23, 42, 0.08);
}

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background:
        radial-gradient(circle at top left, rgba(56, 189, 248, 0.18), transparent 32%),
        linear-gradient(135deg, #F4F8FB 0%, #EAF3F5 52%, #F8FAFC 100%);
    color: var(--text-main);
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #E0F2F1 0%, #F8FAFC 100%) !important;
    border-right: 1px solid var(--border-soft);
}

[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    color: var(--primary-dark) !important;
    font-weight: 800 !important;
    font-size: 0.86rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.07em !important;
}

[data-testid="stSidebar"] p,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] span {
    color: var(--text-main) !important;
}

[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] {
    font-size: 0.92rem;
}

/* Headings */
h1 {
    color: #FFFFFF !important;
    font-weight: 900 !important;
    letter-spacing: -0.04em !important;
}

h2, h3 {
    color: var(--primary-dark) !important;
    font-weight: 800 !important;
    letter-spacing: -0.02em !important;
}

/* Buttons */
.stButton > button {
    background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%) !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 14px !important;
    font-weight: 800 !important;
    width: 100% !important;
    padding: 0.78rem 1.35rem !important;
    transition: all 0.22s ease !important;
    box-shadow: 0 10px 24px rgba(15, 118, 110, 0.18) !important;
}

.stButton > button:hover {
    transform: translateY(-1px);
    background: linear-gradient(135deg, var(--primary-dark) 0%, #1D4ED8 100%) !important;
    box-shadow: 0 14px 28px rgba(15, 118, 110, 0.24) !important;
}

.stButton > button:active {
    transform: translateY(0);
}

/* Cards */
.header-card {
    background:
        linear-gradient(135deg, rgba(15, 118, 110, 0.98) 0%, rgba(37, 99, 235, 0.96) 100%);
    border: 1px solid rgba(255, 255, 255, 0.18);
    border-radius: 26px;
    padding: 34px 40px;
    margin-bottom: 28px;
    box-shadow: var(--shadow-soft);
    position: relative;
    overflow: hidden;
}

.header-card:after {
    content: "";
    position: absolute;
    right: -80px;
    top: -80px;
    width: 210px;
    height: 210px;
    background: rgba(255, 255, 255, 0.12);
    border-radius: 50%;
}

.header-card p {
    color: rgba(255, 255, 255, 0.86) !important;
}

.device-card {
    background: rgba(255, 255, 255, 0.94);
    border: 1px solid var(--border-soft);
    border-radius: 22px;
    padding: 24px 26px;
    margin-bottom: 20px;
    box-shadow: var(--shadow-soft);
}

.device-card h4 {
    color: var(--text-main) !important;
    margin: 0 0 18px 0 !important;
    font-size: 1.02rem !important;
    font-weight: 800 !important;
    letter-spacing: -0.01em !important;
}

.panel-label {
    color: var(--text-muted);
    font-size: 0.92rem;
    margin: -6px 0 18px 0;
}

.mqtt-box {
    background: rgba(255, 255, 255, 0.72);
    border: 1px solid var(--border-soft);
    border-radius: 18px;
    padding: 15px 17px;
    box-shadow: 0 10px 26px rgba(15, 23, 42, 0.05);
}

.mqtt-label {
    margin: 0;
    color: var(--primary-dark);
    font-size: 0.77rem;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}

.mqtt-value {
    margin: 4px 0 12px 0;
    color: var(--text-main);
    font-size: 0.88rem;
    font-weight: 700;
    word-break: break-word;
}

.status-ok {
    background: #ECFDF5;
    border: 1px solid #BBF7D0;
    border-left: 5px solid var(--success);
    border-radius: 16px;
    padding: 13px 18px;
    margin: 10px 0 22px 0;
    font-size: 0.92rem;
    color: #14532D;
    font-weight: 700;
}

.status-err {
    background: #FEF2F2;
    border: 1px solid #FECACA;
    border-left: 5px solid var(--danger);
    border-radius: 16px;
    padding: 13px 18px;
    margin: 10px 0 22px 0;
    font-size: 0.92rem;
    color: #7F1D1D;
    font-weight: 700;
}

.voice-pill {
    background: #F0F9FF;
    border: 1px solid #BAE6FD;
    border-radius: 999px;
    padding: 6px 12px;
    font-size: 0.78rem;
    color: #075985;
    font-weight: 700;
}

.voice-result {
    background: #F8FAFC;
    border: 1px solid var(--border-soft);
    border-radius: 16px;
    padding: 12px 16px;
    margin: 10px 0;
    font-size: 0.95rem;
    color: var(--text-main);
}

.history-row {
    display: flex;
    gap: 12px;
    padding: 9px 0;
    border-bottom: 1px solid #E2E8F0;
}

.history-time {
    color: var(--primary-dark);
    font-size: 0.82rem;
    min-width: 72px;
    font-weight: 800;
}

.history-cmd {
    color: var(--text-main);
    font-size: 0.84rem;
    font-weight: 600;
}

hr {
    border-color: var(--border-soft) !important;
}

/* Bokeh voice button */
.bk-btn {
    background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%) !important;
    color: #fff !important;
    border: none !important;
    border-radius: 14px !important;
    font-weight: 800 !important;
    font-size: 1rem !important;
    font-family: 'Inter', sans-serif !important;
    padding: 15px 0 !important;
    width: 100% !important;
    cursor: pointer !important;
    transition: all 0.22s ease !important;
    box-shadow: 0 10px 24px rgba(15, 118, 110, 0.18) !important;
}

.bk-btn:hover {
    background: linear-gradient(135deg, var(--primary-dark) 0%, #1D4ED8 100%) !important;
    transform: translateY(-1px);
}

.bk-toolbar-box, .bk, .bk-root {
    border: none !important;
    background: transparent !important;
    box-shadow: none !important;
}

iframe[title="streamlit_bokeh_events"] {
    border: none !important;
    background: transparent !important;
}

/* Streamlit small fixes */
.block-container {
    padding-top: 2.2rem;
    padding-bottom: 3rem;
}

[data-testid="stMarkdownContainer"] p {
    line-height: 1.55;
}

</style>
""", unsafe_allow_html=True)

# ── MQTT ──────────────────────────────────────────────────────────────────────
BROKER = "broker.mqttdashboard.com"
PORT   = 1883
TOPIC  = "casaIM/control"

def publicar_mqtt(payload: dict) -> tuple[bool, str]:
    """Publica en MQTT esperando CONNACK antes de publicar (QoS 1)."""
    evt_conectado = threading.Event()
    evt_publicado = threading.Event()
    error = [None]

    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            evt_conectado.set()
        else:
            error[0] = f"Broker rechazó conexión rc={rc}"
            evt_conectado.set()

    def on_publish(client, userdata, mid):
        evt_publicado.set()

    try:
        c = paho.Client(
            client_id=f"streamlit_{int(time.time() * 1000)}",
            clean_session=True,
            protocol=paho.MQTTv311,
        )
        c.on_connect = on_connect
        c.on_publish  = on_publish
        c.connect_async(BROKER, PORT, keepalive=10)
        c.loop_start()

        if not evt_conectado.wait(timeout=8):
            c.loop_stop(); c.disconnect()
            return False, "Timeout: el broker no respondió en 8 segundos"
        if error[0]:
            c.loop_stop(); c.disconnect()
            return False, error[0]

        c.publish(TOPIC, json.dumps(payload), qos=1)

        if not evt_publicado.wait(timeout=6):
            c.loop_stop(); c.disconnect()
            return False, "Timeout: el broker no confirmó la publicación"

        c.loop_stop()
        c.disconnect()
        return True, ""
    except Exception as e:
        return False, str(e)

# ── Session state ─────────────────────────────────────────────────────────────
for key, default in {
    "luz":       False,
    "alarma":    False,
    "puerta":    "cerrada",
    "mqtt_ok":   None,
    "mqtt_msg":  "",
    "historial": [],
    "ultimo_voz": "",
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ── Comandos de voz reconocidos ───────────────────────────────────────────────
COMANDOS_VOZ = {
    "enciende las luces":  {"Act1": "enciende las luces"},
    "apaga las luces":     {"Act1": "apaga las luces"},
    "abre la puerta":      {"Act1": "abre la puerta"},
    "cierra la puerta":    {"Act1": "cierra la puerta"},
    "activa la alarma":    {"Act1": "activa la alarma"},
    "desactiva la alarma": {"Act1": "desactiva la alarma"},
}

def aplicar_estado(cmd: str):
    """Actualiza el session_state según el comando ejecutado."""
    if cmd == "enciende las luces":  st.session_state["luz"]    = True
    if cmd == "apaga las luces":     st.session_state["luz"]    = False
    if cmd == "abre la puerta":      st.session_state["puerta"] = "abierta"
    if cmd == "cierra la puerta":    st.session_state["puerta"] = "cerrada"
    if cmd == "activa la alarma":    st.session_state["alarma"] = True
    if cmd == "desactiva la alarma": st.session_state["alarma"] = False

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🏠 Casa Inteligente")
    st.caption("Panel multimodal conectado a ESP32 mediante MQTT.")
    st.divider()

    st.markdown("### Conexión MQTT")
    st.markdown(f"""
    <div class='mqtt-box'>
        <p class='mqtt-label'>🔌 Broker</p>
        <p class='mqtt-value'>{BROKER}</p>
        <p class='mqtt-label'>📢 Topic</p>
        <p class='mqtt-value' style='margin-bottom:0;'>{TOPIC}</p>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    st.markdown("### Estado actual")
    st.markdown(f"💡 **Luz:** {'🟢 Encendida' if st.session_state['luz'] else '🔴 Apagada'}")
    st.markdown(f"🚨 **Alarma:** {'🟢 Activa' if st.session_state['alarma'] else '🔴 Inactiva'}")
    st.markdown(f"🚪 **Puerta:** {'🔓 Abierta' if st.session_state['puerta'] == 'abierta' else '🔒 Cerrada'}")

    st.divider()

    st.markdown("### Navegación")
    st.markdown("🏠 **Panel de control**")
    st.markdown("📡 [Monitoreo y acceso](https://finalinterfaces-monitoreo.streamlit.app/)")

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="header-card">
    <h1 style="margin:0; font-size:2.35rem;">🏠 Panel de Control Inteligente</h1>
    <p style="margin:10px 0 0 0; font-size:1rem;">
        Control de iluminación, acceso y seguridad mediante botones y comandos de voz. 
        Comunicación en tiempo real con ESP32 usando MQTT.
    </p>
</div>
""", unsafe_allow_html=True)

# Feedback del último comando
if st.session_state["mqtt_ok"] is True:
    st.markdown(f'<div class="status-ok">✅ {st.session_state["mqtt_msg"]}</div>', unsafe_allow_html=True)
elif st.session_state["mqtt_ok"] is False:
    st.markdown(f'<div class="status-err">❌ Error MQTT: {st.session_state["mqtt_msg"]}</div>', unsafe_allow_html=True)

col1, col2 = st.columns(2, gap="large")

# ══════════════════════════════════════════════════════════════════════════════
# COLUMNA 1 — Control manual por botones
# ══════════════════════════════════════════════════════════════════════════════
with col1:
    st.markdown("### 🎛️ Control manual")
    st.markdown(
        "<p class='panel-label'>Gestiona los dispositivos principales de la casa desde controles directos.</p>",
        unsafe_allow_html=True
    )

    # ── Luz ──────────────────────────────────────────────────────────────────
    st.markdown('<div class="device-card"><h4>💡 Iluminación de la sala</h4>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Encender luz 💡", key="luz_on"):
            with st.spinner("Enviando comando..."):
                ok, msg = publicar_mqtt({"Act1": "enciende las luces"})
            if ok:
                aplicar_estado("enciende las luces")
                st.session_state["historial"].append({"ts": time.strftime("%H:%M:%S"), "cmd": "💡 Luz encendida"})
                st.session_state["mqtt_ok"]  = True
                st.session_state["mqtt_msg"] = "Luz encendida correctamente"
            else:
                st.session_state["mqtt_ok"]  = False
                st.session_state["mqtt_msg"] = msg
            st.rerun()
    with c2:
        if st.button("Apagar luz 💡", key="luz_off"):
            with st.spinner("Enviando comando..."):
                ok, msg = publicar_mqtt({"Act1": "apaga las luces"})
            if ok:
                aplicar_estado("apaga las luces")
                st.session_state["historial"].append({"ts": time.strftime("%H:%M:%S"), "cmd": "💡 Luz apagada"})
                st.session_state["mqtt_ok"]  = True
                st.session_state["mqtt_msg"] = "Luz apagada correctamente"
            else:
                st.session_state["mqtt_ok"]  = False
                st.session_state["mqtt_msg"] = msg
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Puerta ───────────────────────────────────────────────────────────────
    st.markdown('<div class="device-card"><h4>🚪 Acceso principal</h4>', unsafe_allow_html=True)
    p1, p2 = st.columns(2)
    with p1:
        if st.button("Abrir puerta 🔓", key="puerta_open"):
            with st.spinner("Enviando comando..."):
                ok, msg = publicar_mqtt({"Act1": "abre la puerta"})
            if ok:
                aplicar_estado("abre la puerta")
                st.session_state["historial"].append({"ts": time.strftime("%H:%M:%S"), "cmd": "🚪 Puerta abierta"})
                st.session_state["mqtt_ok"]  = True
                st.session_state["mqtt_msg"] = "Puerta abierta correctamente"
            else:
                st.session_state["mqtt_ok"]  = False
                st.session_state["mqtt_msg"] = msg
            st.rerun()
    with p2:
        if st.button("Cerrar puerta 🔒", key="puerta_close"):
            with st.spinner("Enviando comando..."):
                ok, msg = publicar_mqtt({"Act1": "cierra la puerta"})
            if ok:
                aplicar_estado("cierra la puerta")
                st.session_state["historial"].append({"ts": time.strftime("%H:%M:%S"), "cmd": "🚪 Puerta cerrada"})
                st.session_state["mqtt_ok"]  = True
                st.session_state["mqtt_msg"] = "Puerta cerrada correctamente"
            else:
                st.session_state["mqtt_ok"]  = False
                st.session_state["mqtt_msg"] = msg
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Alarma ───────────────────────────────────────────────────────────────
    st.markdown('<div class="device-card"><h4>🚨 Sistema de alarma</h4>', unsafe_allow_html=True)
    a1, a2 = st.columns(2)
    with a1:
        if st.button("Activar alarma 🚨", key="alarma_on"):
            with st.spinner("Enviando comando..."):
                ok, msg = publicar_mqtt({"Act1": "activa la alarma"})
            if ok:
                aplicar_estado("activa la alarma")
                st.session_state["historial"].append({"ts": time.strftime("%H:%M:%S"), "cmd": "🚨 Alarma activada"})
                st.session_state["mqtt_ok"]  = True
                st.session_state["mqtt_msg"] = "Alarma activada correctamente"
            else:
                st.session_state["mqtt_ok"]  = False
                st.session_state["mqtt_msg"] = msg
            st.rerun()
    with a2:
        if st.button("Desactivar alarma 🚨", key="alarma_off"):
            with st.spinner("Enviando comando..."):
                ok, msg = publicar_mqtt({"Act1": "desactiva la alarma"})
            if ok:
                aplicar_estado("desactiva la alarma")
                st.session_state["historial"].append({"ts": time.strftime("%H:%M:%S"), "cmd": "🚨 Alarma desactivada"})
                st.session_state["mqtt_ok"]  = True
                st.session_state["mqtt_msg"] = "Alarma desactivada correctamente"
            else:
                st.session_state["mqtt_ok"]  = False
                st.session_state["mqtt_msg"] = msg
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# COLUMNA 2 — Control por voz (streamlit_bokeh_events)
# ══════════════════════════════════════════════════════════════════════════════
with col2:
    st.markdown("### 🎙️ Control por voz")
    st.markdown(
        "<p class='panel-label'>Activa funciones de la casa usando comandos hablados en español.</p>",
        unsafe_allow_html=True
    )

    st.markdown('<div class="device-card"><h4>🎙️ Dicta un comando</h4>', unsafe_allow_html=True)
    st.markdown("""
    <p style='color:#64748B;font-size:0.93rem;margin-bottom:14px;'>
    Presiona el botón, permite el uso del micrófono y pronuncia uno de estos comandos:
    </p>
    <div style='display:flex;flex-wrap:wrap;gap:8px;margin-bottom:18px;'>
        <span class='voice-pill'>"enciende las luces"</span>
        <span class='voice-pill'>"apaga las luces"</span>
        <span class='voice-pill'>"abre la puerta"</span>
        <span class='voice-pill'>"cierra la puerta"</span>
        <span class='voice-pill'>"activa la alarma"</span>
        <span class='voice-pill'>"desactiva la alarma"</span>
    </div>
    """, unsafe_allow_html=True)

    # Botón de escucha Bokeh
    stt_button = Button(label="🎙  Iniciar escucha", width=400, button_type="warning")
    stt_button.js_on_event("button_click", CustomJS(code="""
        var recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
        recognition.lang = 'es-ES';
        recognition.continuous = false;
        recognition.interimResults = false;
        recognition.onresult = function(e) {
            var value = "";
            for (var i = e.resultIndex; i < e.results.length; ++i) {
                if (e.results[i].isFinal) value += e.results[i][0].transcript;
            }
            if (value != "") {
                document.dispatchEvent(new CustomEvent("GET_TEXT", {detail: value}));
            }
        };
        recognition.onerror = function(e) {
            document.dispatchEvent(new CustomEvent("GET_TEXT", {detail: "ERROR:" + e.error}));
        };
        recognition.start();
    """))

    result = streamlit_bokeh_events(
        stt_button,
        events="GET_TEXT",
        key="voz_inicio",
        refresh_on_update=False,
        override_height=75,
        debounce_time=0,
    )

    # Procesar resultado de voz
    if result and "GET_TEXT" in result:
        texto_raw = result["GET_TEXT"].strip()

        if texto_raw.startswith("ERROR:"):
            st.markdown(f'<div class="status-err">❌ Error del micrófono: {texto_raw}</div>', unsafe_allow_html=True)
        else:
            texto = texto_raw.lower()
            # Evitar reprocesar el mismo texto si Streamlit hace rerun
            if texto != st.session_state["ultimo_voz"]:
                st.session_state["ultimo_voz"] = texto
                st.markdown(f'<div class="voice-result">🎙️ Comando detectado: <strong>"{texto_raw}"</strong></div>', unsafe_allow_html=True)

                # Buscar comando coincidente
                cmd_encontrado = None
                for cmd in COMANDOS_VOZ:
                    if cmd in texto:
                        cmd_encontrado = cmd
                        break

                if cmd_encontrado:
                    with st.spinner("Enviando comando al ESP32..."):
                        ok, msg = publicar_mqtt(COMANDOS_VOZ[cmd_encontrado])
                    if ok:
                        aplicar_estado(cmd_encontrado)
                        st.session_state["historial"].append({
                            "ts": time.strftime("%H:%M:%S"),
                            "cmd": f"🎙️ Voz: {cmd_encontrado}"
                        })
                        st.session_state["mqtt_ok"]  = True
                        st.session_state["mqtt_msg"] = f'Comando de voz ejecutado: "{cmd_encontrado}"'
                        st.markdown(f'<div class="status-ok">✅ Ejecutado: <strong>"{cmd_encontrado}"</strong></div>', unsafe_allow_html=True)
                    else:
                        st.session_state["mqtt_ok"]  = False
                        st.session_state["mqtt_msg"] = msg
                        st.markdown(f'<div class="status-err">❌ Error MQTT: {msg}</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="status-err">⚠️ Comando no reconocido: "{texto_raw}"</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # ── Historial ─────────────────────────────────────────────────────────────
    if st.session_state["historial"]:
        st.markdown("### 📋 Historial de comandos")
        st.markdown('<div class="device-card">', unsafe_allow_html=True)
        for item in reversed(st.session_state["historial"][-8:]):
            st.markdown(f"""
            <div class='history-row'>
                <span class='history-time'>{item['ts']}</span>
                <span class='history-cmd'>{item['cmd']}</span>
            </div>""", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
