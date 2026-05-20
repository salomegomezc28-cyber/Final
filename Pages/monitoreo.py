import streamlit as st
import paho.mqtt.client as mqtt
import json
import time
import random

# ── Configuración de página ──────────────────
st.set_page_config(
    page_title="Monitoreo y Acceso",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Estilos ──────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.stApp { background-color: #FFE5D9; color: #5a4a4a; }
[data-testid="stSidebar"] {
    background-color: #D8E2DC !important;
    border-right: 1px solid #FFCAD4;
}
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    color: #9D8189 !important; font-weight: 700 !important;
    font-size: 0.95rem !important; text-transform: uppercase !important;
}
[data-testid="stSidebar"] label { color: #5a4a4a !important; font-size: 0.85rem !important; }
h1 { color: #FFF5F5 !important; font-weight: 700 !important; }
h2, h3 { color: #9D8189 !important; font-weight: 600 !important; }
.stButton > button {
    background: #F4ACB7 !important; color: #ffffff !important;
    border: none !important; border-radius: 8px !important;
    font-weight: 600 !important; width: 100% !important;
    padding: 0.6rem 1.4rem !important;
    transition: background 0.2s ease !important;
}
.stButton > button:hover { background: #9D8189 !important; }
[data-testid="metric-container"] {
    background: #FFCAD4; border: 1px solid #F4ACB7;
    border-top: 3px solid #9D8189;
    border-radius: 8px; padding: 18px 22px;
}
[data-testid="metric-container"] label {
    color: #9D8189 !important; font-size: 0.78rem !important;
    font-weight: 600 !important; text-transform: uppercase !important;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    color: #5a4a4a !important; font-weight: 700 !important;
}
.device-card {
    background: #FFCAD4; border: 1px solid #F4ACB7;
    border-radius: 12px; padding: 24px 28px; margin-bottom: 16px;
}
.device-card h4 {
    color: #9D8189 !important; margin: 0 0 16px 0 !important;
    font-size: 1.05rem !important; font-weight: 600 !important;
}
.header-card {
    background: #FFCAD4; border: 1px solid #F4ACB7;
    border-left: 5px solid #9D8189; border-radius: 8px;
    padding: 28px 36px; margin-bottom: 24px;
}
.status-ok {
    background: #D8E2DC; border: 1px solid #9D8189;
    border-left: 4px solid #9D8189; border-radius: 8px;
    padding: 12px 18px; margin: 8px 0;
    font-size: 0.88rem; color: #5a4a4a; font-weight: 500;
}
.status-err {
    background: #FFCAD4; border: 1px solid #F4ACB7;
    border-left: 4px solid #F4ACB7; border-radius: 8px;
    padding: 12px 18px; margin: 8px 0;
    font-size: 0.88rem; color: #9D8189; font-weight: 500;
}
.alerta {
    background: #F4ACB7; border: 1px solid #9D8189;
    border-left: 4px solid #9D8189; border-radius: 8px;
    padding: 14px 18px; margin: 8px 0;
    font-size: 0.92rem; color: #5a4a4a; font-weight: 600;
}
hr { border-color: #FFCAD4 !important; }
textarea, input[type="text"] {
    background-color: #FFE5D9 !important;
    border: 1px solid #F4ACB7 !important;
    border-radius: 6px !important;
    color: #5a4a4a !important;
}
</style>
""", unsafe_allow_html=True)

# ── MQTT ─────────────────────────────────────
BROKER         = "test.mosquitto.org"
PORT           = 1883
TOPIC_SENSORES = "casaIM/sensores"
TOPIC_CONTROL  = "casaIM/control"

def obtener_sensores():
    datos = {"received": False, "payload": None}
    def on_message(client, userdata, message):
        try:
            datos["payload"] = json.loads(message.payload.decode())
            datos["received"] = True
        except:
            pass
    try:
        c = mqtt.Client(client_id=f"monitor_{int(time.time())}")
        c.on_message = on_message
        c.connect(BROKER, PORT, 60)
        c.subscribe(TOPIC_SENSORES)
        c.loop_start()
        timeout = time.time() + 5
        while not datos["received"] and time.time() < timeout:
            time.sleep(0.1)
        c.loop_stop()
        c.disconnect()
        return datos["payload"]
    except Exception as e:
        return {"error": str(e)}

def publicar_mqtt(payload: dict):
    try:
        c = mqtt.Client(client_id=f"acceso_{int(time.time())}")
        c.connect(BROKER, PORT, 60)
        c.publish(TOPIC_CONTROL, json.dumps(payload))
        c.disconnect()
        return True
    except:
        return False

def analizar_acceso_simulado(nombre: str, personas_auth: list):
    time.sleep(1.5)
    nombre_lower      = nombre.strip().lower()
    autorizados_lower = [p.strip().lower() for p in personas_auth if p.strip()]
    autorizado = any(
        nombre_lower in auth or auth in nombre_lower
        for auth in autorizados_lower
    )
    if autorizado:
        return {
            "decision":  "AUTORIZADO",
            "confianza": random.randint(88, 99),
            "razon":     f"Persona identificada como '{nombre}' en la lista de acceso autorizado."
        }
    else:
        return {
            "decision":  "DENEGADO",
            "confianza": random.randint(85, 97),
            "razon":     f"'{nombre}' no se encuentra registrado en la lista de acceso."
        }

# ── Session state ─────────────────────────────
for key, default in {
    "historial_temp": [],
    "historial_hum":  [],
    "historial_ts":   [],
    "ultimo_acceso":  None,
    "resultado_ia":   None,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ── Sidebar ───────────────────────────────────
with st.sidebar:
    st.markdown("## 📡 Monitoreo")
    st.divider()
    st.markdown("### CONEXIÓN MQTT")
    st.markdown(f"""
    <div style='background:#FFE5D9;border:1px solid #F4ACB7;border-radius:8px;padding:12px 16px;'>
        <p style='margin:0;color:#9D8189;font-size:0.82rem;'>🔌 Broker</p>
        <p style='margin:2px 0 0 0;color:#5a4a4a;font-size:0.88rem;font-weight:600;'>{BROKER}</p>
        <p style='margin:8px 0 0 0;color:#9D8189;font-size:0.82rem;'>📥 Topic sensores</p>
        <p style='margin:2px 0 0 0;color:#5a4a4a;font-size:0.88rem;font-weight:600;'>{TOPIC_SENSORES}</p>
    </div>
    """, unsafe_allow_html=True)
    st.divider()
    st.markdown("### UMBRALES DE ALERTA")
    umbral_temp = st.slider("🌡️ Temp. máxima (°C)", 20, 50, 35)
    umbral_hum  = st.slider("💧 Humedad máxima (%)", 40, 100, 80)
    st.divider()
    st.markdown("### NAVEGACIÓN")
    st.markdown("🏠 [Panel de Control](inicio)")
    st.markdown("📡 **Monitoreo y Acceso**")

# ── Header ────────────────────────────────────
st.markdown("""
<div class="header-card">
    <h1 style="margin:0; font-size:2rem;">📡 Monitoreo y Acceso</h1>
    <p style="margin:6px 0 0 0; color:#9D8189; font-size:0.97rem;">
        Temperatura · Humedad · Control de acceso inteligente
    </p>
</div>
""", unsafe_allow_html=True)

# ── Layout ────────────────────────────────────
col1, col2 = st.columns(2, gap="large")

# ── Columna 1: Sensores ───────────────────────
with col1:
    st.markdown("### 🌡️ Sensores Ambientales")
    st.markdown('<div class="device-card"><h4>📊 Lectura en tiempo real</h4>', unsafe_allow_html=True)

    if st.button("🔄 Actualizar Sensores"):
        with st.spinner("Leyendo sensores del ESP32..."):
            datos = obtener_sensores()
            if datos and "error" not in datos:
                temp = datos.get("temp", 0)
                hum  = datos.get("hum",  0)
                ts   = time.strftime("%H:%M:%S")
                st.session_state["historial_temp"].append(temp)
                st.session_state["historial_hum"].append(hum)
                st.session_state["historial_ts"].append(ts)
                for k in ["historial_temp", "historial_hum", "historial_ts"]:
                    if len(st.session_state[k]) > 20:
                        st.session_state[k] = st.session_state[k][-20:]
            else:
                st.markdown('<div class="status-err">❌ No se recibieron datos. Verifica que Wokwi esté corriendo.</div>',
                            unsafe_allow_html=True)

    if st.session_state["historial_temp"]:
        temp = st.session_state["historial_temp"][-1]
        hum  = st.session_state["historial_hum"][-1]
        ts   = st.session_state["historial_ts"][-1]

        m1, m2 = st.columns(2)
        with m1:
            delta_t = round(temp - st.session_state["historial_temp"][-2], 1) \
                      if len(st.session_state["historial_temp"]) > 1 else None
            st.metric("🌡️ Temperatura", f"{temp}°C", delta=f"{delta_t}°C" if delta_t else None)
        with m2:
            delta_h = round(hum - st.session_state["historial_hum"][-2], 1) \
                      if len(st.session_state["historial_hum"]) > 1 else None
            st.metric("💧 Humedad", f"{hum}%", delta=f"{delta_h}%" if delta_h else None)

        st.markdown(f"<p style='color:#9D8189;font-size:0.8rem;margin-top:8px;'>Última lectura: {ts}</p>",
                    unsafe_allow_html=True)

        if temp > umbral_temp:
            st.markdown(f'<div class="alerta">🔥 ALERTA: Temperatura alta ({temp}°C > {umbral_temp}°C)</div>',
                        unsafe_allow_html=True)
        if hum > umbral_hum:
            st.markdown(f'<div class="alerta">💧 ALERTA: Humedad alta ({hum}% > {umbral_hum}%)</div>',
                        unsafe_allow_html=True)
    else:
        st.markdown("<p style='color:#9D8189;'>Presiona 'Actualizar Sensores' para leer datos del ESP32.</p>",
                    unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # Gráfica historial
    if len(st.session_state["historial_temp"]) > 1:
        st.markdown("### 📈 Historial")
        st.markdown('<div class="device-card"><h4>📉 Últimas lecturas</h4>', unsafe_allow_html=True)
        st.line_chart({
            "Temperatura (°C)": st.session_state["historial_temp"],
            "Humedad (%)":      st.session_state["historial_hum"],
        })
        st.markdown('</div>', unsafe_allow_html=True)

# ── Columna 2: Control de acceso ──────────────
with col2:
    st.markdown("### 🔐 Control de Acceso")
    st.markdown('<div class="device-card"><h4>👥 Verificación de identidad</h4>', unsafe_allow_html=True)
    st.markdown("""
    <p style='color:#9D8189;font-size:0.9rem;margin-bottom:16px;'>
    Sube una foto de la persona en la entrada e ingresa su nombre.
    El sistema verificará si está autorizada y controlará la puerta automáticamente.
    </p>
    """, unsafe_allow_html=True)

    st.markdown("**Personas autorizadas** — una por línea:")
    personas_texto = st.text_area(
        "Lista de acceso:",
        value="María José\nJuan Pérez\nProfesor\nEstudiante",
        height=100,
        label_visibility="collapsed",
    )
    personas_auth = [p.strip() for p in personas_texto.split("\n") if p.strip()]

    st.markdown("**📸 Foto de la entrada**")
    imagen = st.file_uploader("Sube una foto:", type=["jpg", "jpeg", "png"], label_visibility="collapsed")

    if imagen:
        st.image(imagen, caption="Imagen capturada en la entrada", use_container_width=True)

    st.markdown("**🪪 Nombre a verificar**")
    nombre_persona = st.text_input("Nombre:", placeholder="Ej: María José", label_visibility="collapsed")

    if st.button("🔍 Verificar Acceso"):
        if not nombre_persona.strip():
            st.markdown('<div class="status-err">⚠️ Ingresa el nombre de la persona.</div>',
                        unsafe_allow_html=True)
        else:
            with st.spinner("Verificando identidad..."):
                resultado = analizar_acceso_simulado(nombre_persona, personas_auth)
                st.session_state["resultado_ia"]  = resultado
                st.session_state["ultimo_acceso"] = time.strftime("%H:%M:%S")

                if resultado["decision"] == "AUTORIZADO":
                    publicar_mqtt({"acceso": "autorizado"})
                else:
                    publicar_mqtt({"alarma": 1})
                    time.sleep(2)
                    publicar_mqtt({"alarma": 0})

    # Resultado
    if st.session_state["resultado_ia"]:
        r       = st.session_state["resultado_ia"]
        ts      = st.session_state["ultimo_acceso"]
        es_auth = r["decision"] == "AUTORIZADO"

        color  = "#D8E2DC" if es_auth else "#FFCAD4"
        border = "#9D8189" if es_auth else "#F4ACB7"
        icono  = "✅" if es_auth else "🚫"

        st.markdown(f"""
        <div style='background:{color};border:1px solid {border};border-left:5px solid {border};
        border-radius:12px;padding:20px 24px;margin-top:16px;'>
            <h3 style='color:#5a4a4a;margin:0 0 8px 0;font-size:1.3rem;'>
                {icono} {r["decision"]}
            </h3>
            <p style='color:#5a4a4a;margin:0;font-size:0.9rem;'>
                <strong>Confianza:</strong> {r["confianza"]}%
            </p>
            <p style='color:#5a4a4a;margin:6px 0 0 0;font-size:0.9rem;'>
                <strong>Razón:</strong> {r["razon"]}
            </p>
            <p style='color:#9D8189;margin:8px 0 0 0;font-size:0.78rem;'>
                Verificado a las {ts}
            </p>
        </div>
        """, unsafe_allow_html=True)

        if es_auth:
            st.markdown('<div class="status-ok">🚪 Puerta abierta automáticamente por 3 segundos</div>',
                        unsafe_allow_html=True)
        else:
            st.markdown('<div class="status-err">🚨 Alarma activada — acceso denegado</div>',
                        unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
