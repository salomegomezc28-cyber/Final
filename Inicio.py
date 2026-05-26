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
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.stApp { background-color: #FFE5D9; color: #5a4a4a; }
[data-testid="stSidebar"] { background-color: #D8E2DC !important; border-right: 1px solid #FFCAD4; }
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 { color: #9D8189 !important; font-weight: 700 !important; font-size: 0.95rem !important; text-transform: uppercase !important; }
[data-testid="stSidebar"] label { color: #5a4a4a !important; font-size: 0.85rem !important; }
h1 { color: #fefcfb !important; font-weight: 700 !important; }
h2, h3 { color: #9D8189 !important; font-weight: 600 !important; }
.stButton > button { background: #F4ACB7 !important; color: #ffffff !important; border: none !important; border-radius: 8px !important; font-weight: 600 !important; width: 100% !important; padding: 0.6rem 1.4rem !important; transition: background 0.2s ease !important; }
.stButton > button:hover { background: #9D8189 !important; }
.device-card { background: #FFCAD4; border: 1px solid #F4ACB7; border-radius: 12px; padding: 24px 28px; margin-bottom: 16px; }
.device-card h4 { color: #9D8189 !important; margin: 0 0 16px 0 !important; font-size: 1.05rem !important; font-weight: 600 !important; }
.header-card { background: #FFCAD4; border: 1px solid #F4ACB7; border-left: 5px solid #9D8189; border-radius: 8px; padding: 28px 36px; margin-bottom: 24px; }
.status-ok { background: #D8E2DC; border: 1px solid #9D8189; border-left: 4px solid #9D8189; border-radius: 8px; padding: 12px 18px; margin: 8px 0; font-size: 0.88rem; color: #5a4a4a; font-weight: 500; }
.status-err { background: #FFCAD4; border: 1px solid #F4ACB7; border-left: 4px solid #F4ACB7; border-radius: 8px; padding: 12px 18px; margin: 8px 0; font-size: 0.88rem; color: #9D8189; font-weight: 500; }
hr { border-color: #FFCAD4 !important; }

/* Bokeh button */
.bk-btn { background: #F4ACB7 !important; color: #fff !important; border: none !important; border-radius: 8px !important; font-weight: 700 !important; font-size: 1rem !important; font-family: 'Inter', sans-serif !important; padding: 14px 0 !important; width: 100% !important; cursor: pointer !important; transition: background 0.2s !important; }
.bk-btn:hover { background: #9D8189 !important; }
.bk-toolbar-box, .bk, .bk-root { border: none !important; background: transparent !important; box-shadow: none !important; }
iframe[title="streamlit_bokeh_events"] { border: none !important; background: transparent !important; }
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
            return False, "Timeout: broker no respondió en 8s"
        if error[0]:
            c.loop_stop(); c.disconnect()
            return False, error[0]

        c.publish(TOPIC, json.dumps(payload), qos=1)

        if not evt_publicado.wait(timeout=6):
            c.loop_stop(); c.disconnect()
            return False, "Timeout: broker no confirmó publicación"

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
    st.divider()
    st.markdown("### CONEXIÓN MQTT")
    st.markdown(f"""
    <div style='background:#FFE5D9;border:1px solid #F4ACB7;border-radius:8px;padding:12px 16px;'>
        <p style='margin:0;color:#9D8189;font-size:0.82rem;'>🔌 Broker</p>
        <p style='margin:2px 0 0 0;color:#5a4a4a;font-size:0.88rem;font-weight:600;'>{BROKER}</p>
        <p style='margin:8px 0 0 0;color:#9D8189;font-size:0.82rem;'>📢 Topic</p>
        <p style='margin:2px 0 0 0;color:#5a4a4a;font-size:0.88rem;font-weight:600;'>{TOPIC}</p>
    </div>
    """, unsafe_allow_html=True)
    st.divider()
    st.markdown("### ESTADO ACTUAL")
    st.markdown(f"💡 Luz: {'🟢 Encendida' if st.session_state['luz'] else '🔴 Apagada'}")
    st.markdown(f"🚨 Alarma: {'🟢 Activa' if st.session_state['alarma'] else '🔴 Inactiva'}")
    st.markdown(f"🚪 Puerta: {'🔓 Abierta' if st.session_state['puerta'] == 'abierta' else '🔒 Cerrada'}")
    st.divider()
    st.markdown("### NAVEGACIÓN")
    st.markdown("🏠 **Panel de Control**")
    st.markdown("📡 [Monitoreo y Acceso](./monitoreo)")

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="header-card">
    <h1 style="margin:0; font-size:2rem;">🏠 Panel de Control</h1>
    <p style="margin:6px 0 0 0; color:#9D8189; font-size:0.97rem;">
        Casa Inteligente — Control por voz y botones · ESP32 vía MQTT
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
    st.markdown("### 🎛️ Control Manual")

    # ── Luz ──────────────────────────────────────────────────────────────────
    st.markdown('<div class="device-card"><h4>💡 Luz de la Sala</h4>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Encender 💡", key="luz_on"):
            with st.spinner("Enviando..."):
                ok, msg = publicar_mqtt({"Act1": "enciende las luces"})
            if ok:
                aplicar_estado("enciende las luces")
                st.session_state["historial"].append({"ts": time.strftime("%H:%M:%S"), "cmd": "💡 Luz encendida"})
                st.session_state["mqtt_ok"]  = True
                st.session_state["mqtt_msg"] = "Luz encendida — confirmado"
            else:
                st.session_state["mqtt_ok"]  = False
                st.session_state["mqtt_msg"] = msg
            st.rerun()
    with c2:
        if st.button("Apagar 💡", key="luz_off"):
            with st.spinner("Enviando..."):
                ok, msg = publicar_mqtt({"Act1": "apaga las luces"})
            if ok:
                aplicar_estado("apaga las luces")
                st.session_state["historial"].append({"ts": time.strftime("%H:%M:%S"), "cmd": "💡 Luz apagada"})
                st.session_state["mqtt_ok"]  = True
                st.session_state["mqtt_msg"] = "Luz apagada — confirmado"
            else:
                st.session_state["mqtt_ok"]  = False
                st.session_state["mqtt_msg"] = msg
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Puerta ───────────────────────────────────────────────────────────────
    st.markdown('<div class="device-card"><h4>🚪 Puerta Principal</h4>', unsafe_allow_html=True)
    p1, p2 = st.columns(2)
    with p1:
        if st.button("Abrir 🔓", key="puerta_open"):
            with st.spinner("Enviando..."):
                ok, msg = publicar_mqtt({"Act1": "abre la puerta"})
            if ok:
                aplicar_estado("abre la puerta")
                st.session_state["historial"].append({"ts": time.strftime("%H:%M:%S"), "cmd": "🚪 Puerta abierta"})
                st.session_state["mqtt_ok"]  = True
                st.session_state["mqtt_msg"] = "Puerta abierta — confirmado"
            else:
                st.session_state["mqtt_ok"]  = False
                st.session_state["mqtt_msg"] = msg
            st.rerun()
    with p2:
        if st.button("Cerrar 🔒", key="puerta_close"):
            with st.spinner("Enviando..."):
                ok, msg = publicar_mqtt({"Act1": "cierra la puerta"})
            if ok:
                aplicar_estado("cierra la puerta")
                st.session_state["historial"].append({"ts": time.strftime("%H:%M:%S"), "cmd": "🚪 Puerta cerrada"})
                st.session_state["mqtt_ok"]  = True
                st.session_state["mqtt_msg"] = "Puerta cerrada — confirmado"
            else:
                st.session_state["mqtt_ok"]  = False
                st.session_state["mqtt_msg"] = msg
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Alarma ───────────────────────────────────────────────────────────────
    st.markdown('<div class="device-card"><h4>🚨 Alarma</h4>', unsafe_allow_html=True)
    a1, a2 = st.columns(2)
    with a1:
        if st.button("Activar 🚨", key="alarma_on"):
            with st.spinner("Enviando..."):
                ok, msg = publicar_mqtt({"Act1": "activa la alarma"})
            if ok:
                aplicar_estado("activa la alarma")
                st.session_state["historial"].append({"ts": time.strftime("%H:%M:%S"), "cmd": "🚨 Alarma activada"})
                st.session_state["mqtt_ok"]  = True
                st.session_state["mqtt_msg"] = "Alarma activada — confirmado"
            else:
                st.session_state["mqtt_ok"]  = False
                st.session_state["mqtt_msg"] = msg
            st.rerun()
    with a2:
        if st.button("Desactivar 🚨", key="alarma_off"):
            with st.spinner("Enviando..."):
                ok, msg = publicar_mqtt({"Act1": "desactiva la alarma"})
            if ok:
                aplicar_estado("desactiva la alarma")
                st.session_state["historial"].append({"ts": time.strftime("%H:%M:%S"), "cmd": "🚨 Alarma desactivada"})
                st.session_state["mqtt_ok"]  = True
                st.session_state["mqtt_msg"] = "Alarma desactivada — confirmado"
            else:
                st.session_state["mqtt_ok"]  = False
                st.session_state["mqtt_msg"] = msg
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# COLUMNA 2 — Control por voz (streamlit_bokeh_events)
# ══════════════════════════════════════════════════════════════════════════════
with col2:
    st.markdown("### 🎙️ Control por Voz")
    st.markdown('<div class="device-card"><h4>🎙️ Habla un comando</h4>', unsafe_allow_html=True)
    st.markdown("""
    <p style='color:#9D8189;font-size:0.9rem;margin-bottom:12px;'>
    Presiona el botón, otorga permiso al micrófono y di uno de estos comandos:
    </p>
    <div style='display:flex;flex-wrap:wrap;gap:6px;margin-bottom:16px;'>
        <span style='background:#FFE5D9;border:1px solid #9D8189;border-radius:20px;padding:4px 12px;font-size:0.8rem;color:#9D8189;'>"enciende las luces"</span>
        <span style='background:#FFE5D9;border:1px solid #9D8189;border-radius:20px;padding:4px 12px;font-size:0.8rem;color:#9D8189;'>"apaga las luces"</span>
        <span style='background:#FFE5D9;border:1px solid #9D8189;border-radius:20px;padding:4px 12px;font-size:0.8rem;color:#9D8189;'>"abre la puerta"</span>
        <span style='background:#FFE5D9;border:1px solid #9D8189;border-radius:20px;padding:4px 12px;font-size:0.8rem;color:#9D8189;'>"cierra la puerta"</span>
        <span style='background:#FFE5D9;border:1px solid #9D8189;border-radius:20px;padding:4px 12px;font-size:0.8rem;color:#9D8189;'>"activa la alarma"</span>
        <span style='background:#FFE5D9;border:1px solid #9D8189;border-radius:20px;padding:4px 12px;font-size:0.8rem;color:#9D8189;'>"desactiva la alarma"</span>
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
            st.markdown(f'<div class="status-err">❌ Error micrófono: {texto_raw}</div>', unsafe_allow_html=True)
        else:
            texto = texto_raw.lower()
            # Evitar reprocesar el mismo texto si Streamlit hace rerun
            if texto != st.session_state["ultimo_voz"]:
                st.session_state["ultimo_voz"] = texto
                st.markdown(f'<div style="background:#FFE5D9;border:1px solid #F4ACB7;border-radius:8px;padding:10px 16px;margin:8px 0;font-size:0.95rem;color:#5a4a4a;">🎙️ <strong>"{texto_raw}"</strong></div>', unsafe_allow_html=True)

                # Buscar comando coincidente
                cmd_encontrado = None
                for cmd in COMANDOS_VOZ:
                    if cmd in texto:
                        cmd_encontrado = cmd
                        break

                if cmd_encontrado:
                    with st.spinner("Enviando al ESP32..."):
                        ok, msg = publicar_mqtt(COMANDOS_VOZ[cmd_encontrado])
                    if ok:
                        aplicar_estado(cmd_encontrado)
                        st.session_state["historial"].append({
                            "ts": time.strftime("%H:%M:%S"),
                            "cmd": f"🎙️ Voz: {cmd_encontrado}"
                        })
                        st.session_state["mqtt_ok"]  = True
                        st.session_state["mqtt_msg"] = f'Voz ejecutada: "{cmd_encontrado}"'
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
        st.markdown("### 📋 Historial de Comandos")
        st.markdown('<div class="device-card">', unsafe_allow_html=True)
        for item in reversed(st.session_state["historial"][-8:]):
            st.markdown(f"""
            <div style='display:flex;gap:12px;padding:6px 0;border-bottom:1px solid #FFE5D9;'>
                <span style='color:#9D8189;font-size:0.82rem;min-width:70px;'>{item['ts']}</span>
                <span style='color:#5a4a4a;font-size:0.82rem;'>{item['cmd']}</span>
            </div>""", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
