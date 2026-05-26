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

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.stApp { background-color: #FFE5D9; color: #5a4a4a; }
[data-testid="stSidebar"] { background-color: #D8E2DC !important; border-right: 1px solid #FFCAD4; }
[data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 { color: #9D8189 !important; font-weight: 700 !important; font-size: 0.95rem !important; text-transform: uppercase !important; }
[data-testid="stSidebar"] label { color: #5a4a4a !important; font-size: 0.85rem !important; }
h1 { color: #FFF5F5 !important; font-weight: 700 !important; }
h2, h3 { color: #9D8189 !important; font-weight: 600 !important; }
.stButton > button { background: #F4ACB7 !important; color: #ffffff !important; border: none !important; border-radius: 8px !important; font-weight: 600 !important; width: 100% !important; padding: 0.6rem 1.4rem !important; transition: background 0.2s ease !important; }
.stButton > button:hover { background: #9D8189 !important; }
.device-card { background: #FFCAD4; border: 1px solid #F4ACB7; border-radius: 12px; padding: 24px 28px; margin-bottom: 16px; }
.device-card h4 { color: #9D8189 !important; margin: 0 0 16px 0 !important; font-size: 1.05rem !important; font-weight: 600 !important; }
.header-card { background: #FFCAD4; border: 1px solid #F4ACB7; border-left: 5px solid #9D8189; border-radius: 8px; padding: 28px 36px; margin-bottom: 24px; }
.status-ok { background: #D8E2DC; border: 1px solid #9D8189; border-left: 4px solid #9D8189; border-radius: 8px; padding: 12px 18px; margin: 8px 0; font-size: 0.88rem; color: #5a4a4a; font-weight: 500; }
.status-err { background: #FFCAD4; border: 1px solid #F4ACB7; border-left: 4px solid #F4ACB7; border-radius: 8px; padding: 12px 18px; margin: 8px 0; font-size: 0.88rem; color: #9D8189; font-weight: 500; }
.alerta { background: #F4ACB7; border: 1px solid #9D8189; border-left: 4px solid #9D8189; border-radius: 8px; padding: 14px 18px; margin: 8px 0; font-size: 0.92rem; color: #5a4a4a; font-weight: 600; }
hr { border-color: #FFCAD4 !important; }
textarea, input[type="text"] { background-color: #FFE5D9 !important; border: 1px solid #F4ACB7 !important; border-radius: 6px !important; color: #5a4a4a !important; }
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
    st.markdown("🏠 [Panel de Control](https://finalinterfaces-mjjp.streamlit.app/)")
    st.markdown("📡 **Monitoreo y Acceso**")

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="header-card">
    <h1 style="margin:0; font-size:2rem;">📡 Monitoreo y Acceso</h1>
    <p style="margin:6px 0 0 0; color:#9D8189; font-size:0.97rem;">
        Temperatura · Humedad · Control de acceso por lista
    </p>
</div>
""", unsafe_allow_html=True)

col1, col2 = st.columns(2, gap="large")

# ══════════════════════════════════════════════════════════════════════════════
# COLUMNA 1 — Sensores ambientales
# ══════════════════════════════════════════════════════════════════════════════
with col1:
    st.markdown("### 🌡️ Sensores Ambientales")
    st.markdown('<div class="device-card"><h4>📊 Lectura en tiempo real</h4>', unsafe_allow_html=True)

    if st.button("🔄 Actualizar Sensores"):
        with st.spinner("Esperando datos del ESP32... (publica cada 3s)"):
            datos = obtener_sensores()

        if "error" in datos:
            st.markdown(f'<div class="status-err">❌ {datos["error"]}</div>', unsafe_allow_html=True)
        else:
            temp = datos.get("temp")
            hum  = datos.get("hum")
            if temp is None or hum is None:
                st.markdown('<div class="status-err">❌ Datos incompletos del ESP32.</div>', unsafe_allow_html=True)
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
            st.metric("🌡️ Temperatura", f"{temp}°C", delta=f"{dt:+.1f}°C" if dt is not None else None)
        with m2:
            dh = round(hum - st.session_state["historial_hum"][-2], 1) if n > 1 else None
            st.metric("💧 Humedad", f"{hum}%", delta=f"{dh:+.1f}%" if dh is not None else None)
        st.markdown(f"<p style='color:#9D8189;font-size:0.8rem;margin-top:8px;'>Última lectura: {ts}</p>", unsafe_allow_html=True)
        if temp > umbral_temp:
            st.markdown(f'<div class="alerta">🔥 ALERTA: Temperatura alta ({temp}°C &gt; {umbral_temp}°C)</div>', unsafe_allow_html=True)
        if hum > umbral_hum:
            st.markdown(f'<div class="alerta">💧 ALERTA: Humedad alta ({hum}% &gt; {umbral_hum}%)</div>', unsafe_allow_html=True)
    else:
        st.markdown("<p style='color:#9D8189;'>Presiona 'Actualizar Sensores' para leer datos del ESP32.</p>", unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    if len(st.session_state["historial_temp"]) > 1:
        st.markdown("### 📈 Historial")
        st.markdown('<div class="device-card"><h4>📉 Últimas lecturas</h4>', unsafe_allow_html=True)
        st.line_chart({
            "Temperatura (°C)": st.session_state["historial_temp"],
            "Humedad (%)":      st.session_state["historial_hum"],
        })
        st.markdown('</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# COLUMNA 2 — Control de acceso por lista
# ══════════════════════════════════════════════════════════════════════════════
with col2:
    st.markdown("### 🔐 Control de Acceso")
    st.markdown('<div class="device-card"><h4>👥 Verificación por lista</h4>', unsafe_allow_html=True)
    st.markdown("<p style='color:#9D8189;font-size:0.9rem;margin-bottom:16px;'>Ingresa el nombre de la persona. El sistema verificará si está en la lista y controlará la puerta automáticamente.</p>", unsafe_allow_html=True)

    st.markdown("**Personas autorizadas** — una por línea:")
    personas_texto = st.text_area(
        "Lista:",
        value="María José\nJuan Pérez\nProfesor\nEstudiante",
        height=100,
        label_visibility="collapsed",
    )
    personas_auth = [p.strip().lower() for p in personas_texto.split("\n") if p.strip()]

    st.markdown("**📸 Foto de la entrada** *(opcional)*")
    imagen = st.file_uploader("Foto:", type=["jpg", "jpeg", "png"], label_visibility="collapsed")
    if imagen:
        st.image(imagen, caption="Imagen capturada en la entrada", use_container_width=True)

    st.markdown("**🪪 Nombre a verificar**")
    nombre_persona = st.text_input("Nombre:", placeholder="Ej: María José", label_visibility="collapsed")

    if st.button("🔍 Verificar Acceso"):
        if not nombre_persona.strip():
            st.markdown('<div class="status-err">⚠️ Ingresa el nombre de la persona.</div>', unsafe_allow_html=True)
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
                    st.markdown(f'<div class="status-err">⚠️ Autorizado, pero error MQTT: {msg}</div>', unsafe_allow_html=True)
            else:
                with st.spinner("Activando alarma..."):
                    ok, msg = publicar_mqtt({"Act1": "acceso denegado"})
                if not ok:
                    st.markdown(f'<div class="status-err">⚠️ Denegado, pero error MQTT: {msg}</div>', unsafe_allow_html=True)

    # Mostrar resultado
    if st.session_state["resultado_acceso"]:
        r  = st.session_state["resultado_acceso"]
        ts = st.session_state["ultimo_acceso"]
        es_auth = r["decision"] == "AUTORIZADO"
        color   = "#D8E2DC" if es_auth else "#FFCAD4"
        border  = "#9D8189" if es_auth else "#F4ACB7"
        icono   = "✅" if es_auth else "🚫"
        st.markdown(f"""
        <div style='background:{color};border:1px solid {border};border-left:5px solid {border};
                    border-radius:12px;padding:20px 24px;margin-top:16px;'>
            <h3 style='color:#5a4a4a;margin:0 0 8px 0;font-size:1.3rem;'>{icono} {r["decision"]}</h3>
            <p style='color:#5a4a4a;margin:0;font-size:0.9rem;'>
                <strong>Persona:</strong> {r["nombre"]}
            </p>
            <p style='color:#9D8189;margin:8px 0 0 0;font-size:0.78rem;'>Verificado a las {ts}</p>
        </div>
        """, unsafe_allow_html=True)

        if es_auth:
            st.markdown('<div class="status-ok">🚪 Puerta abierta automáticamente por 3 segundos (ESP32)</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="status-err">🚨 Alarma activada por 2 segundos (ESP32)</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
