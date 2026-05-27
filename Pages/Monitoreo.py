"""
📡 Monitoreo y Acceso — Casa Inteligente
Interfaces Multimodales · Sensores DHT22 + Control de acceso por lista
"""

import streamlit as st
import paho.mqtt.client as mqtt
import json
import time
import threading

# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Monitoreo y Acceso",
    page_icon="📡",
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

/* Inputs */
textarea,
input[type="text"],
input,
.stTextInput input,
.stTextArea textarea {
    background-color: #FFFFFF !important;
    border: 1px solid var(--border-soft) !important;
    border-radius: 14px !important;
    color: var(--text-main) !important;
    font-weight: 500 !important;
}

textarea:focus,
input[type="text"]:focus,
.stTextInput input:focus,
.stTextArea textarea:focus {
    border-color: var(--primary) !important;
    box-shadow: 0 0 0 3px rgba(15, 118, 110, 0.12) !important;
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
    margin: 10px 0 16px 0;
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
    margin: 10px 0 16px 0;
    font-size: 0.92rem;
    color: #7F1D1D;
    font-weight: 700;
}

.alerta {
    background: #FFFBEB;
    border: 1px solid #FDE68A;
    border-left: 5px solid var(--warning);
    border-radius: 16px;
    padding: 14px 18px;
    margin: 10px 0;
    font-size: 0.93rem;
    color: #78350F;
    font-weight: 800;
}

.result-card-ok {
    background: #ECFDF5;
    border: 1px solid #BBF7D0;
    border-left: 6px solid var(--success);
    border-radius: 20px;
    padding: 20px 24px;
    margin-top: 16px;
}

.result-card-err {
    background: #FEF2F2;
    border: 1px solid #FECACA;
    border-left: 6px solid var(--danger);
    border-radius: 20px;
    padding: 20px 24px;
    margin-top: 16px;
}

.result-title {
    margin: 0 0 8px 0;
    font-size: 1.35rem;
    font-weight: 900;
    color: var(--text-main);
}

.result-text {
    color: var(--text-main);
    margin: 0;
    font-size: 0.92rem;
}

.result-time {
    color: var(--text-muted);
    margin: 8px 0 0 0;
    font-size: 0.8rem;
    font-weight: 700;
}

.help-text {
    color: var(--text-muted);
    font-size: 0.92rem;
    margin-bottom: 16px;
}

.last-reading {
    color: var(--text-muted);
    font-size: 0.82rem;
    margin-top: 8px;
    font-weight: 700;
}

.empty-state {
    background: #F8FAFC;
    border: 1px dashed var(--border-soft);
    border-radius: 18px;
    padding: 16px 18px;
    color: var(--text-muted);
    font-size: 0.92rem;
    font-weight: 600;
}

hr {
    border-color: var(--border-soft) !important;
}

/* Streamlit small fixes */
.block-container {
    padding-top: 2.2rem;
    padding-bottom: 3rem;
}

[data-testid="stMarkdownContainer"] p {
    line-height: 1.55;
}

[data-testid="stMetric"] {
    background: #F8FAFC;
    border: 1px solid var(--border-soft);
    border-radius: 18px;
    padding: 16px;
}

</style>
""", unsafe_allow_html=True)

# ── MQTT ──────────────────────────────────────────────────────────────────────
BROKER         = "broker.mqttdashboard.com"
PORT           = 1883
TOPIC_SENSORES = "casaIM/sensores"
TOPIC_CONTROL  = "casaIM/control"

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
        c = mqtt.Client(
            client_id=f"acceso_{int(time.time()*1000)}",
            clean_session=True,
            protocol=mqtt.MQTTv311,
        )
        c.on_connect = on_connect
        c.on_publish  = on_publish
        c.connect_async(BROKER, PORT, keepalive=10)
        c.loop_start()

        if not evt_conectado.wait(timeout=8):
            c.loop_stop(); c.disconnect()
            return False, "Timeout conectando al broker"
        if error[0]:
            c.loop_stop(); c.disconnect()
            return False, error[0]

        c.publish(TOPIC_CONTROL, json.dumps(payload), qos=1)

        if not evt_publicado.wait(timeout=6):
            c.loop_stop(); c.disconnect()
            return False, "Timeout esperando confirmación"

        c.loop_stop(); c.disconnect()
        return True, ""
    except Exception as e:
        return False, str(e)


def obtener_sensores() -> dict:
    """Se suscribe a TOPIC_SENSORES y espera el próximo mensaje del ESP32."""
    evt_conectado = threading.Event()
    evt_mensaje   = threading.Event()
    resultado = [None]
    error = [None]

    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            client.subscribe(TOPIC_SENSORES)
            evt_conectado.set()
        else:
            error[0] = f"Broker rechazó conexión rc={rc}"
            evt_conectado.set()

    def on_message(client, userdata, message):
        try:
            resultado[0] = json.loads(message.payload.decode())
            evt_mensaje.set()
        except Exception as e:
            error[0] = f"JSON inválido: {e}"
            evt_mensaje.set()

    try:
        c = mqtt.Client(
            client_id=f"monitor_{int(time.time()*1000)}",
            clean_session=True,
            protocol=mqtt.MQTTv311,
        )
        c.on_connect = on_connect
        c.on_message = on_message
        c.connect_async(BROKER, PORT, keepalive=10)
        c.loop_start()

        if not evt_conectado.wait(timeout=8):
            c.loop_stop(); c.disconnect()
            return {"error": "Timeout conectando al broker MQTT"}
        if error[0]:
            c.loop_stop(); c.disconnect()
            return {"error": error[0]}

        # El ESP32 publica cada 3s — esperamos hasta 10s
        if not evt_mensaje.wait(timeout=10):
            c.loop_stop(); c.disconnect()
            return {"error": "No se recibió respuesta del ESP32 en 10s. ¿Está corriendo Wokwi?"}

        c.loop_stop(); c.disconnect()
        if error[0]:
            return {"error": error[0]}
        return resultado[0]
    except Exception as e:
        return {"error": str(e)}


# ── Session state ─────────────────────────────────────────────────────────────
for key, default in {
    "historial_temp":  [],
    "historial_hum":   [],
    "historial_ts":    [],
    "ultimo_acceso":   None,
    "resultado_acceso": None,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📡 Monitoreo")
    st.caption("Lectura ambiental y control de acceso conectado a ESP32.")
    st.divider()

    st.markdown("### Conexión MQTT")
    st.markdown(f"""
    <div class='mqtt-box'>
        <p class='mqtt-label'>🔌 Broker</p>
        <p class='mqtt-value'>{BROKER}</p>

        <p class='mqtt-label'>📥 Topic sensores</p>
        <p class='mqtt-value'>{TOPIC_SENSORES}</p>

        <p class='mqtt-label'>📤 Topic control</p>
        <p class='mqtt-value' style='margin-bottom:0;'>{TOPIC_CONTROL}</p>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    st.markdown("### Umbrales de alerta")
    umbral_temp = st.slider("🌡️ Temperatura máxima (°C)", 20, 50, 35)
    umbral_hum  = st.slider("💧 Humedad máxima (%)", 40, 100, 80)

    st.divider()

    st.markdown("### Navegación")
    st.markdown("🏠 [Panel de control](https://finalinterfaces-mjjp.streamlit.app/)")
    st.markdown("📡 **Monitoreo y acceso**")

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="header-card">
    <h1 style="margin:0; font-size:2.35rem;">📡 Monitoreo y Acceso</h1>
    <p style="margin:10px 0 0 0; font-size:1rem;">
        Supervisión de temperatura y humedad con verificación de acceso por lista autorizada. 
        Comunicación en tiempo real con ESP32 mediante MQTT.
    </p>
</div>
""", unsafe_allow_html=True)

col1, col2 = st.columns(2, gap="large")

# ══════════════════════════════════════════════════════════════════════════════
# COLUMNA 1 — Sensores ambientales
# ══════════════════════════════════════════════════════════════════════════════
with col1:
    st.markdown("### 🌡️ Sensores ambientales")
    st.markdown(
        "<p class='panel-label'>Consulta las últimas lecturas del ESP32 y revisa alertas por temperatura o humedad.</p>",
        unsafe_allow_html=True
    )

    st.markdown('<div class="device-card"><h4>📊 Lectura en tiempo real</h4>', unsafe_allow_html=True)

    if st.button("🔄 Actualizar sensores"):
        with st.spinner("Esperando datos del ESP32... publica cada 3 segundos"):
            datos = obtener_sensores()

        if "error" in datos:
            st.markdown(f'<div class="status-err">❌ {datos["error"]}</div>', unsafe_allow_html=True)
        else:
            temp = datos.get("temp")
            hum  = datos.get("hum")
            if temp is None or hum is None:
                st.markdown('<div class="status-err">❌ Los datos recibidos del ESP32 están incompletos.</div>', unsafe_allow_html=True)
            else:
                ts = time.strftime("%H:%M:%S")
                st.session_state["historial_temp"].append(temp)
                st.session_state["historial_hum"].append(hum)
                st.session_state["historial_ts"].append(ts)
                for k in ["historial_temp", "historial_hum", "historial_ts"]:
                    if len(st.session_state[k]) > 20:
                        st.session_state[k] = st.session_state[k][-20:]

    if st.session_state["historial_temp"]:
        temp = st.session_state["historial_temp"][-1]
        hum  = st.session_state["historial_hum"][-1]
        ts   = st.session_state["historial_ts"][-1]
        n    = len(st.session_state["historial_temp"])

        m1, m2 = st.columns(2)

        with m1:
            dt = round(temp - st.session_state["historial_temp"][-2], 1) if n > 1 else None
            st.metric(
                "🌡️ Temperatura",
                f"{temp}°C",
                delta=f"{dt:+.1f}°C" if dt is not None else None
            )

        with m2:
            dh = round(hum - st.session_state["historial_hum"][-2], 1) if n > 1 else None
            st.metric(
                "💧 Humedad",
                f"{hum}%",
                delta=f"{dh:+.1f}%" if dh is not None else None
            )

        st.markdown(f"<p class='last-reading'>Última lectura registrada: {ts}</p>", unsafe_allow_html=True)

        if temp > umbral_temp:
            st.markdown(
                f'<div class="alerta">🔥 Alerta: temperatura alta detectada ({temp}°C &gt; {umbral_temp}°C)</div>',
                unsafe_allow_html=True
            )

        if hum > umbral_hum:
            st.markdown(
                f'<div class="alerta">💧 Alerta: humedad alta detectada ({hum}% &gt; {umbral_hum}%)</div>',
                unsafe_allow_html=True
            )
    else:
        st.markdown(
            "<div class='empty-state'>Presiona “Actualizar sensores” para leer los datos enviados por el ESP32.</div>",
            unsafe_allow_html=True
        )

    st.markdown('</div>', unsafe_allow_html=True)

    if len(st.session_state["historial_temp"]) > 1:
        st.markdown("### 📈 Historial")
        st.markdown('<div class="device-card"><h4>📉 Últimas lecturas registradas</h4>', unsafe_allow_html=True)
        st.line_chart({
            "Temperatura (°C)": st.session_state["historial_temp"],
            "Humedad (%)":      st.session_state["historial_hum"],
        })
        st.markdown('</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# COLUMNA 2 — Control de acceso por lista
# ══════════════════════════════════════════════════════════════════════════════
with col2:
    st.markdown("### 🔐 Control de acceso")
    st.markdown(
        "<p class='panel-label'>Valida si una persona está autorizada y envía la acción correspondiente al ESP32.</p>",
        unsafe_allow_html=True
    )

    st.markdown('<div class="device-card"><h4>👥 Verificación por lista autorizada</h4>', unsafe_allow_html=True)
    st.markdown(
        "<p class='help-text'>Ingresa el nombre de la persona. El sistema verificará si aparece en la lista y controlará la puerta automáticamente.</p>",
        unsafe_allow_html=True
    )

    st.markdown("**Personas autorizadas**")
    st.caption("Escribe un nombre por línea.")
    personas_texto = st.text_area(
        "Lista:",
        value="Juanita Nassar\nSalome Gomez",
        height=110,
        label_visibility="collapsed",
    )
    personas_auth = [p.strip().lower() for p in personas_texto.split("\n") if p.strip()]

    st.markdown("**📸 Foto de la entrada** *(opcional)*")
    imagen = st.file_uploader("Foto:", type=["jpg", "jpeg", "png"], label_visibility="collapsed")
    if imagen:
        st.image(imagen, caption="Imagen capturada en la entrada", use_container_width=True)

    st.markdown("**🪪 Nombre a verificar**")
    nombre_persona = st.text_input(
        "Nombre:",
        placeholder="Ej: María José",
        label_visibility="collapsed"
    )

    if st.button("🔍 Verificar acceso"):
        if not nombre_persona.strip():
            st.markdown('<div class="status-err">⚠️ Ingresa el nombre de la persona para continuar.</div>', unsafe_allow_html=True)
        else:
            # Verificación directa por lista (sin IA simulada)
            nombre_lower = nombre_persona.strip().lower()
            autorizado = any(
                nombre_lower in auth or auth in nombre_lower
                for auth in personas_auth
            )

            resultado = {
                "decision":  "AUTORIZADO" if autorizado else "DENEGADO",
                "nombre":    nombre_persona.strip(),
            }
            st.session_state["resultado_acceso"] = resultado
            st.session_state["ultimo_acceso"]    = time.strftime("%H:%M:%S")

            if autorizado:
                with st.spinner("Abriendo puerta..."):
                    ok, msg = publicar_mqtt({"Act1": "acceso autorizado"})
                if not ok:
                    st.markdown(f'<div class="status-err">⚠️ Acceso autorizado, pero ocurrió un error MQTT: {msg}</div>', unsafe_allow_html=True)
            else:
                with st.spinner("Activando alarma..."):
                    ok, msg = publicar_mqtt({"Act1": "acceso denegado"})
                if not ok:
                    st.markdown(f'<div class="status-err">⚠️ Acceso denegado, pero ocurrió un error MQTT: {msg}</div>', unsafe_allow_html=True)

    # Mostrar resultado
    if st.session_state["resultado_acceso"]:
        r  = st.session_state["resultado_acceso"]
        ts = st.session_state["ultimo_acceso"]
        es_auth = r["decision"] == "AUTORIZADO"
        icono   = "✅" if es_auth else "🚫"
        card_class = "result-card-ok" if es_auth else "result-card-err"

        st.markdown(f"""
        <div class='{card_class}'>
            <h3 class='result-title'>{icono} {r["decision"]}</h3>
            <p class='result-text'>
                <strong>Persona:</strong> {r["nombre"]}
            </p>
            <p class='result-time'>Verificado a las {ts}</p>
        </div>
        """, unsafe_allow_html=True)

        if es_auth:
            st.markdown(
                '<div class="status-ok">🚪 Puerta abierta automáticamente por 3 segundos en el ESP32.</div>',
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                '<div class="status-err">🚨 Alarma activada por 2 segundos en el ESP32.</div>',
                unsafe_allow_html=True
            )

    st.markdown('</div>', unsafe_allow_html=True)
