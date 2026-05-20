import streamlit as st
import paho.mqtt.client as mqtt
import json
import time
import base64
import anthropic

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
.stApp { background-color: #0f172a; color: #e2e8f0; }
[data-testid="stSidebar"] {
    background-color: #1e293b !important;
    border-right: 1px solid #334155;
}
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    color: #38bdf8 !important; font-weight: 700 !important;
    font-size: 0.95rem !important; text-transform: uppercase !important;
}
h1 { color: #38bdf8 !important; font-weight: 700 !important; }
h2, h3 { color: #7dd3fc !important; font-weight: 600 !important; }
.stButton > button {
    background: #0284c7 !important; color: #ffffff !important;
    border: none !important; border-radius: 8px !important;
    font-weight: 600 !important; width: 100% !important;
}
.stButton > button:hover { background: #0369a1 !important; }
[data-testid="metric-container"] {
    background: #1e293b; border: 1px solid #334155;
    border-top: 3px solid #38bdf8; border-radius: 8px; padding: 18px 22px;
}
.device-card {
    background: #1e293b; border: 1px solid #334155;
    border-radius: 12px; padding: 24px 28px; margin-bottom: 16px;
}
.header-card {
    background: #1e293b; border: 1px solid #334155;
    border-left: 5px solid #38bdf8; border-radius: 8px;
    padding: 28px 36px; margin-bottom: 24px;
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
.alerta {
    background: #1c0a00; border: 1px solid #dc2626;
    border-left: 4px solid #ef4444; border-radius: 8px;
    padding: 14px 18px; margin: 8px 0;
    font-size: 0.92rem; color: #fca5a5; font-weight: 600;
}
</style>
""", unsafe_allow_html=True)

# ── MQTT ─────────────────────────────────────
BROKER          = "broker.mqttdashboard.com"
PORT            = 1883
TOPIC_SENSORES  = "casaIM/sensores"
TOPIC_CONTROL   = "casaIM/control"

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
    <div style='background:#0f172a;border:1px solid #334155;border-radius:8px;padding:12px 16px;'>
        <p style='margin:0;color:#94a3b8;font-size:0.82rem;'>🔌 Broker</p>
        <p style='margin:2px 0 0 0;color:#38bdf8;font-size:0.88rem;font-weight:600;'>{BROKER}</p>
        <p style='margin:8px 0 0 0;color:#94a3b8;font-size:0.82rem;'>📥 Topic sensores</p>
        <p style='margin:2px 0 0 0;color:#38bdf8;font-size:0.88rem;font-weight:600;'>{TOPIC_SENSORES}</p>
    </div>
    """, unsafe_allow_html=True)
    st.divider()
    st.markdown("### UMBRALES DE ALERTA")
    umbral_temp = st.slider("🌡️ Temp. máxima (°C)", 20, 50, 35)
    umbral_hum  = st.slider("💧 Humedad máxima (%)", 40, 100, 80)
    st.divider()
    st.markdown("### NAVEGACIÓN")
    st.page_link("inicio.py",          label="🏠 Panel de Control")
    st.page_link("pages/monitoreo.py", label="📡 Monitoreo y Acceso")

# ── Header ────────────────────────────────────
st.markdown("""
<div class="header-card">
    <h1 style="margin:0; font-size:2rem;">📡 Monitoreo y Acceso</h1>
    <p style="margin:6px 0 0 0; color:#38bdf8; font-size:0.97rem;">
        Temperatura · Humedad · Control de acceso con IA
    </p>
</div>
""", unsafe_allow_html=True)

# ── Layout ────────────────────────────────────
col1, col2 = st.columns(2, gap="large")

# ── Columna 1: Sensores ───────────────────────
with col1:
    st.markdown("### 🌡️ Sensores Ambientales")
    st.markdown('<div class="device-card">', unsafe_allow_html=True)

    if st.button("🔄 Actualizar Sensores"):
        with st.spinner("Leyendo sensores..."):
            datos = obtener_sensores()
            if datos and "error" not in datos:
                temp = datos.get("temp", 0)
                hum  = datos.get("hum", 0)
                # Guardar historial
                ts = time.strftime("%H:%M:%S")
                st.session_state["historial_temp"].append(temp)
                st.session_state["historial_hum"].append(hum)
                st.session_state["historial_ts"].append(ts)
                # Mantener últimas 20 lecturas
                for k in ["historial_temp", "historial_hum", "historial_ts"]:
                    if len(st.session_state[k]) > 20:
                        st.session_state[k] = st.session_state[k][-20:]

    # Métricas
    if st.session_state["historial_temp"]:
        temp = st.session_state["historial_temp"][-1]
        hum  = st.session_state["historial_hum"][-1]
        ts   = st.session_state["historial_ts"][-1]

        m1, m2 = st.columns(2)
        with m1:
            st.metric("🌡️ Temperatura", f"{temp}°C",
                      delta=f"{round(temp - st.session_state['historial_temp'][-2], 1)}°C"
                      if len(st.session_state["historial_temp"]) > 1 else None)
        with m2:
            st.metric("💧 Humedad", f"{hum}%",
                      delta=f"{round(hum - st.session_state['historial_hum'][-2], 1)}%"
                      if len(st.session_state["historial_hum"]) > 1 else None)

        st.markdown(f"<p style='color:#64748b;font-size:0.8rem;'>Última lectura: {ts}</p>",
                    unsafe_allow_html=True)

        # Alertas
        if temp > umbral_temp:
            st.markdown(f'<div class="alerta">🔥 ALERTA: Temperatura alta ({temp}°C > {umbral_temp}°C)</div>',
                        unsafe_allow_html=True)
        if hum > umbral_hum:
            st.markdown(f'<div class="alerta">💧 ALERTA: Humedad alta ({hum}% > {umbral_hum}%)</div>',
                        unsafe_allow_html=True)
    else:
        st.markdown("<p style='color:#64748b;'>Presiona 'Actualizar Sensores' para leer datos del ESP32.</p>",
                    unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # Gráfica de historial
    if len(st.session_state["historial_temp"]) > 1:
        st.markdown("### 📈 Historial")
        st.markdown('<div class="device-card">', unsafe_allow_html=True)
        chart_data = {
            "Temperatura (°C)": st.session_state["historial_temp"],
            "Humedad (%)":      st.session_state["historial_hum"],
        }
        st.line_chart(chart_data)
        st.markdown('</div>', unsafe_allow_html=True)

# ── Columna 2: Control de acceso con IA ───────
with col2:
    st.markdown("### 🔐 Control de Acceso con IA")
    st.markdown('<div class="device-card">', unsafe_allow_html=True)
    st.markdown("""
    <p style='color:#94a3b8;font-size:0.9rem;margin-bottom:16px;'>
    Sube una foto de la persona en la entrada. La IA analizará la imagen
    y decidirá si conceder o denegar el acceso.
    </p>
    """, unsafe_allow_html=True)

    # Lista de personas autorizadas (configurable)
    st.markdown("#### 👥 Personas autorizadas")
    personas_auth = st.text_area(
        "Una por línea:",
        value="María José\nEstudiante con uniforme\nPersona con gafas",
        height=80,
    )

    st.markdown("#### 📸 Imagen de la entrada")
    imagen = st.file_uploader("Sube una foto:", type=["jpg", "jpeg", "png"])

    if imagen:
        st.image(imagen, caption="Imagen capturada", use_container_width=True)

        if st.button("🔍 Analizar con IA"):
            with st.spinner("Analizando imagen..."):
                try:
                    # Convertir imagen a base64
                    img_bytes  = imagen.read()
                    img_base64 = base64.standard_b64encode(img_bytes).decode("utf-8")
                    ext        = imagen.name.split(".")[-1].lower()
                    media_type = "image/jpeg" if ext in ["jpg", "jpeg"] else "image/png"

                    # Llamar a Claude Vision
                    client_ai = anthropic.Anthropic()
                    lista_auth = personas_auth.strip()

                    respuesta = client_ai.messages.create(
                        model="claude-opus-4-5",
                        max_tokens=300,
                        messages=[{
                            "role": "user",
                            "content": [
                                {
                                    "type": "image",
                                    "source": {
                                        "type":       "base64",
                                        "media_type": media_type,
                                        "data":       img_base64,
                                    },
                                },
                                {
                                    "type": "text",
                                    "text": f"""Eres el sistema de control de acceso de una casa inteligente.
Analiza esta imagen y determina si la persona debe tener acceso.

Personas autorizadas:
{lista_auth}

Responde SOLO en este formato JSON exacto:
{{
  "decision": "AUTORIZADO" o "DENEGADO",
  "confianza": número del 0 al 100,
  "razon": "explicación breve en español"
}}"""
                                }
                            ],
                        }]
                    )

                    # Parsear respuesta
                    texto_resp = respuesta.content[0].text.strip()
                    # Limpiar posibles bloques de código
                    texto_resp = texto_resp.replace("```json", "").replace("```", "").strip()
                    resultado  = json.loads(texto_resp)
                    st.session_state["resultado_ia"] = resultado
                    st.session_state["ultimo_acceso"] = time.strftime("%H:%M:%S")

                    # Actuar según decisión
                    if resultado["decision"] == "AUTORIZADO":
                        publicar_mqtt({"acceso": "autorizado"})
                    else:
                        publicar_mqtt({"alarma": 1})
                        time.sleep(2)
                        publicar_mqtt({"alarma": 0})

                except Exception as e:
                    st.markdown(f'<div class="status-err">❌ Error: {e}</div>',
                                unsafe_allow_html=True)

    # Mostrar resultado
    if st.session_state["resultado_ia"]:
        r = st.session_state["resultado_ia"]
        ts = st.session_state["ultimo_acceso"]
        es_auth = r["decision"] == "AUTORIZADO"

        color  = "#052e16" if es_auth else "#1c0a00"
        border = "#22c55e" if es_auth else "#ef4444"
        text   = "#86efac" if es_auth else "#fca5a5"
        icono  = "✅" if es_auth else "🚫"

        st.markdown(f"""
        <div style='background:{color};border:1px solid {border};border-left:5px solid {border};
        border-radius:12px;padding:20px 24px;margin-top:16px;'>
            <h3 style='color:{text};margin:0 0 8px 0;font-size:1.3rem;'>
                {icono} {r["decision"]}
            </h3>
            <p style='color:{text};margin:0;font-size:0.9rem;'>
                <strong>Confianza:</strong> {r["confianza"]}%
            </p>
            <p style='color:{text};margin:6px 0 0 0;font-size:0.9rem;'>
                <strong>Razón:</strong> {r["razon"]}
            </p>
            <p style='color:#64748b;margin:8px 0 0 0;font-size:0.78rem;'>
                Analizado a las {ts}
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
