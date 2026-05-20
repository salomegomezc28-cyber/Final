import streamlit as st
import paho.mqtt.client as mqtt
import json
import time
import threading
import streamlit.components.v1 as components

st.set_page_config(
    page_title="Casa Inteligente",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.stApp { background-color: #FFE5D9; color: #5a4a4a; }
[data-testid="stSidebar"] { background-color: #D8E2DC !important; border-right: 1px solid #FFCAD4; }
[data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
    color: #9D8189 !important; font-weight: 700 !important;
    font-size: 0.95rem !important; text-transform: uppercase !important;
}
[data-testid="stSidebar"] label { color: #5a4a4a !important; font-size: 0.85rem !important; }
h1 { color: #fefcfb !important; font-weight: 700 !important; }
h2, h3 { color: #9D8189 !important; font-weight: 600 !important; }
.stButton > button {
    background: #F4ACB7 !important; color: #ffffff !important;
    border: none !important; border-radius: 8px !important;
    font-weight: 600 !important; width: 100% !important;
    padding: 0.6rem 1.4rem !important; transition: background 0.2s ease !important;
}
.stButton > button:hover { background: #9D8189 !important; }
.device-card { background: #FFCAD4; border: 1px solid #F4ACB7; border-radius: 12px; padding: 24px 28px; margin-bottom: 16px; }
.device-card h4 { color: #9D8189 !important; margin: 0 0 16px 0 !important; font-size: 1.05rem !important; font-weight: 600 !important; }
.header-card { background: #FFCAD4; border: 1px solid #F4ACB7; border-left: 5px solid #9D8189; border-radius: 8px; padding: 28px 36px; margin-bottom: 24px; }
.status-ok { background: #D8E2DC; border: 1px solid #9D8189; border-left: 4px solid #9D8189; border-radius: 8px; padding: 12px 18px; margin: 8px 0; font-size: 0.88rem; color: #5a4a4a; font-weight: 500; }
.status-err { background: #FFCAD4; border: 1px solid #F4ACB7; border-left: 4px solid #F4ACB7; border-radius: 8px; padding: 12px 18px; margin: 8px 0; font-size: 0.88rem; color: #9D8189; font-weight: 500; }
hr { border-color: #FFCAD4 !important; }
textarea, input[type="text"] { background-color: #FFE5D9 !important; border: 1px solid #F4ACB7 !important; border-radius: 6px !important; color: #5a4a4a !important; }
div[data-testid="stExpander"] { border: 1px solid #FFCAD4 !important; border-radius: 8px !important; background: #FFE5D9 !important; }
</style>
""", unsafe_allow_html=True)

# ── MQTT ─────────────────────────────────────
BROKER = "broker.mqttdashboard.com"
PORT   = 1883
TOPIC  = "casaIM/control"

def publicar_mqtt(payload: dict) -> tuple[bool, str]:
    """
    Publica un mensaje MQTT esperando el CONNACK antes de publicar.

    Flujo correcto para paho 1.6.1:
      connect_async()  → abre el socket TCP y envía el CONNECT
      loop_start()     → arranca el hilo de red que procesa paquetes
      on_connect       → señal de que el broker aceptó (CONNACK recibido)
      publish()        → ahora sí el broker está listo para recibir
      on_publish       → confirmación de que el broker recibió (QoS 1)
      loop_stop() + disconnect()

    Sin esperar on_connect, publish() se llama con la conexión aún en
    handshake y el broker descarta el mensaje silenciosamente.
    """
    evt_conectado = threading.Event()
    evt_publicado  = threading.Event()
    error = [None]

    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            evt_conectado.set()
        else:
            codigos = {1:"versión de protocolo incorrecta", 2:"client_id rechazado",
                       3:"broker no disponible", 4:"credenciales incorrectas", 5:"no autorizado"}
            error[0] = f"Broker rechazó conexión: {codigos.get(rc, f'rc={rc}')}"
            evt_conectado.set()

    def on_publish(client, userdata, mid):
        evt_publicado.set()

    try:
        c = mqtt.Client(
            client_id=f"streamlit_{int(time.time() * 1000)}",
            clean_session=True,
            protocol=mqtt.MQTTv311,
        )
        c.on_connect = on_connect
        c.on_publish  = on_publish

        c.connect_async(BROKER, PORT, keepalive=10)
        c.loop_start()

        # 1. Esperar CONNACK (el broker aceptó la conexión)
        if not evt_conectado.wait(timeout=6):
            c.loop_stop(); c.disconnect()
            return False, "Timeout: el broker no respondió en 6s"
        if error[0]:
            c.loop_stop(); c.disconnect()
            return False, error[0]

        # 2. Publicar ahora que la conexión está establecida
        c.publish(TOPIC, json.dumps(payload), qos=1)

        # 3. Esperar que el broker confirme recepción (QoS 1 PUBACK)
        if not evt_publicado.wait(timeout=5):
            c.loop_stop(); c.disconnect()
            return False, "Timeout: el broker no confirmó la publicación"

        c.loop_stop()
        c.disconnect()
        return True, ""

    except Exception as e:
        return False, str(e)


# ── Session state ─────────────────────────────
for key, default in {
    "luz":        False,
    "alarma":     False,
    "puerta":     "cerrada",
    "mqtt_msg":   "",    # mensaje de estado del último comando
    "mqtt_ok":    None,  # True/False del último comando
    "historial":  [],
    "voz_texto":  "",
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ── Procesar comando de voz via query param ───
query_params = st.query_params
if "voz" in query_params:
    texto_voz = query_params["voz"].strip().lower()
    if texto_voz and texto_voz != st.session_state.get("voz_texto", ""):
        st.session_state["voz_texto"] = texto_voz
        comandos = {
            "enciende las luces":  {"luz": 1},
            "apaga las luces":     {"luz": 0},
            "abre la puerta":      {"puerta": "abre"},
            "cierra la puerta":    {"puerta": "cierra"},
            "activa la alarma":    {"alarma": 1},
            "desactiva la alarma": {"alarma": 0},
        }
        for cmd, payload in comandos.items():
            if cmd in texto_voz:
                ok, msg = publicar_mqtt(payload)
                if ok:
                    if "luz"    in payload: st.session_state["luz"]    = (payload["luz"] == 1)
                    if "puerta" in payload: st.session_state["puerta"] = "abierta" if payload["puerta"] == "abre" else "cerrada"
                    if "alarma" in payload: st.session_state["alarma"] = (payload["alarma"] == 1)
                    st.session_state["historial"].append({"ts": time.strftime("%H:%M:%S"), "cmd": f'Voz: "{texto_voz}"'})
                break
    st.query_params.clear()

# ── Sidebar ───────────────────────────────────
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
    st.markdown("📡 [Monitoreo y Acceso](Monitoreo)")

# ── Header ────────────────────────────────────
st.markdown("""
<div class="header-card">
    <h1 style="margin:0; font-size:2rem;">🏠 Panel de Control</h1>
    <p style="margin:6px 0 0 0; color:#9D8189; font-size:0.97rem;">
        Casa Inteligente — Control por voz y botones · ESP32 vía MQTT
    </p>
</div>
""", unsafe_allow_html=True)

# Mostrar resultado del último comando MQTT
if st.session_state["mqtt_ok"] is True:
    st.markdown(f'<div class="status-ok">✅ {st.session_state["mqtt_msg"]}</div>', unsafe_allow_html=True)
elif st.session_state["mqtt_ok"] is False:
    st.markdown(f'<div class="status-err">❌ Error MQTT: {st.session_state["mqtt_msg"]}</div>', unsafe_allow_html=True)

col1, col2 = st.columns(2, gap="large")

# ════════════════════════════════════════════
# Columna 1 — Control manual
# ════════════════════════════════════════════
with col1:
    st.markdown("### 🎛️ Control Manual")

    # ── Luz ──
    st.markdown('<div class="device-card"><h4>💡 Luz de la Sala</h4>', unsafe_allow_html=True)
    lc1, lc2 = st.columns(2)
    with lc1:
        if st.button("Encender 💡", key="luz_on"):
            with st.spinner("Enviando al ESP32..."):
                ok, msg = publicar_mqtt({"luz": 1})
            if ok:
                st.session_state["luz"] = True
                st.session_state["historial"].append({"ts": time.strftime("%H:%M:%S"), "cmd": "Luz encendida"})
                st.session_state["mqtt_ok"]  = True
                st.session_state["mqtt_msg"] = "Luz encendida — ESP32 confirmó recepción"
            else:
                st.session_state["mqtt_ok"]  = False
                st.session_state["mqtt_msg"] = msg
            st.rerun()
    with lc2:
        if st.button("Apagar 💡", key="luz_off"):
            with st.spinner("Enviando al ESP32..."):
                ok, msg = publicar_mqtt({"luz": 0})
            if ok:
                st.session_state["luz"] = False
                st.session_state["historial"].append({"ts": time.strftime("%H:%M:%S"), "cmd": "Luz apagada"})
                st.session_state["mqtt_ok"]  = True
                st.session_state["mqtt_msg"] = "Luz apagada — ESP32 confirmó recepción"
            else:
                st.session_state["mqtt_ok"]  = False
                st.session_state["mqtt_msg"] = msg
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Puerta ──
    st.markdown('<div class="device-card"><h4>🚪 Puerta Principal</h4>', unsafe_allow_html=True)
    pc1, pc2 = st.columns(2)
    with pc1:
        if st.button("Abrir 🔓", key="puerta_open"):
            with st.spinner("Enviando al ESP32..."):
                ok, msg = publicar_mqtt({"puerta": "abre"})
            if ok:
                st.session_state["puerta"] = "abierta"
                st.session_state["historial"].append({"ts": time.strftime("%H:%M:%S"), "cmd": "Puerta abierta"})
                st.session_state["mqtt_ok"]  = True
                st.session_state["mqtt_msg"] = "Puerta abierta — ESP32 confirmó recepción"
            else:
                st.session_state["mqtt_ok"]  = False
                st.session_state["mqtt_msg"] = msg
            st.rerun()
    with pc2:
        if st.button("Cerrar 🔒", key="puerta_close"):
            with st.spinner("Enviando al ESP32..."):
                ok, msg = publicar_mqtt({"puerta": "cierra"})
            if ok:
                st.session_state["puerta"] = "cerrada"
                st.session_state["historial"].append({"ts": time.strftime("%H:%M:%S"), "cmd": "Puerta cerrada"})
                st.session_state["mqtt_ok"]  = True
                st.session_state["mqtt_msg"] = "Puerta cerrada — ESP32 confirmó recepción"
            else:
                st.session_state["mqtt_ok"]  = False
                st.session_state["mqtt_msg"] = msg
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Alarma ──
    st.markdown('<div class="device-card"><h4>🚨 Alarma</h4>', unsafe_allow_html=True)
    ac1, ac2 = st.columns(2)
    with ac1:
        if st.button("Activar 🚨", key="alarma_on"):
            with st.spinner("Enviando al ESP32..."):
                ok, msg = publicar_mqtt({"alarma": 1})
            if ok:
                st.session_state["alarma"] = True
                st.session_state["historial"].append({"ts": time.strftime("%H:%M:%S"), "cmd": "Alarma activada"})
                st.session_state["mqtt_ok"]  = True
                st.session_state["mqtt_msg"] = "Alarma activada — ESP32 confirmó recepción"
            else:
                st.session_state["mqtt_ok"]  = False
                st.session_state["mqtt_msg"] = msg
            st.rerun()
    with ac2:
        if st.button("Desactivar 🚨", key="alarma_off"):
            with st.spinner("Enviando al ESP32..."):
                ok, msg = publicar_mqtt({"alarma": 0})
            if ok:
                st.session_state["alarma"] = False
                st.session_state["historial"].append({"ts": time.strftime("%H:%M:%S"), "cmd": "Alarma desactivada"})
                st.session_state["mqtt_ok"]  = True
                st.session_state["mqtt_msg"] = "Alarma desactivada — ESP32 confirmó recepción"
            else:
                st.session_state["mqtt_ok"]  = False
                st.session_state["mqtt_msg"] = msg
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# ════════════════════════════════════════════
# Columna 2 — Control por voz
# ════════════════════════════════════════════
with col2:
    st.markdown("### 🎙️ Control por Voz")
    st.markdown('<div class="device-card"><h4>🎙️ Habla un comando</h4>', unsafe_allow_html=True)
    st.markdown("""
    <p style='color:#9D8189;font-size:0.9rem;margin-bottom:16px;'>
    Toca el botón, habla uno de estos comandos y se enviará automáticamente al ESP32:
    </p>
    <div style='display:flex;flex-wrap:wrap;gap:8px;margin-bottom:16px;'>
        <span style='background:#FFE5D9;border:1px solid #9D8189;border-radius:20px;padding:4px 12px;font-size:0.82rem;color:#9D8189;'>"enciende las luces"</span>
        <span style='background:#FFE5D9;border:1px solid #9D8189;border-radius:20px;padding:4px 12px;font-size:0.82rem;color:#9D8189;'>"apaga las luces"</span>
        <span style='background:#FFE5D9;border:1px solid #9D8189;border-radius:20px;padding:4px 12px;font-size:0.82rem;color:#9D8189;'>"abre la puerta"</span>
        <span style='background:#FFE5D9;border:1px solid #9D8189;border-radius:20px;padding:4px 12px;font-size:0.82rem;color:#9D8189;'>"cierra la puerta"</span>
        <span style='background:#FFE5D9;border:1px solid #9D8189;border-radius:20px;padding:4px 12px;font-size:0.82rem;color:#9D8189;'>"activa la alarma"</span>
        <span style='background:#FFE5D9;border:1px solid #9D8189;border-radius:20px;padding:4px 12px;font-size:0.82rem;color:#9D8189;'>"desactiva la alarma"</span>
    </div>
    """, unsafe_allow_html=True)

    components.html("""
    <style>
      body { margin:0; background:transparent; font-family:'Inter',sans-serif; }
      #btn { background:#F4ACB7; color:#fff; border:none; border-radius:8px; font-weight:700; font-size:1rem; padding:14px 0; width:100%; cursor:pointer; transition:background 0.2s; }
      #btn:hover { background:#9D8189; }
      #btn.listening { background:#9D8189; animation:pulse 1s infinite; }
      @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.6} }
      #status { margin-top:10px; font-size:0.88rem; color:#9D8189; min-height:24px; text-align:center; }
      #result { margin-top:8px; background:#FFE5D9; border:1px solid #F4ACB7; border-radius:8px; padding:10px 14px; font-size:0.95rem; color:#5a4a4a; display:none; }
    </style>
    <button id="btn" onclick="startListening()">🎙 Iniciar escucha</button>
    <div id="status">Listo para escuchar</div>
    <div id="result"></div>
    <script>
      const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
      if (!SR) {
        document.getElementById('status').innerText = '❌ Tu navegador no soporta reconocimiento de voz. Usa Chrome.';
        document.getElementById('btn').disabled = true;
      }
      function startListening() {
        const btn = document.getElementById('btn');
        const status = document.getElementById('status');
        const result = document.getElementById('result');
        const recognition = new SR();
        recognition.lang = 'es-ES'; recognition.continuous = false; recognition.interimResults = false;
        btn.classList.add('listening'); btn.innerText = '🔴 Escuchando...';
        status.innerText = 'Habla ahora...'; result.style.display = 'none';
        recognition.onresult = function(e) {
          const texto = e.results[0][0].transcript.toLowerCase().trim();
          result.style.display = 'block';
          result.innerHTML = '🎙 <strong>"' + texto + '"</strong>';
          status.innerText = 'Enviando comando...';
          const url = new URL(window.parent.location.href);
          url.searchParams.set('voz', texto);
          window.parent.location.href = url.toString();
        };
        recognition.onerror = function(e) {
          status.innerText = '❌ Error: ' + e.error + '. Intenta de nuevo.';
          btn.classList.remove('listening'); btn.innerText = '🎙 Iniciar escucha';
        };
        recognition.onend = function() { btn.classList.remove('listening'); btn.innerText = '🎙 Iniciar escucha'; };
        recognition.start();
      }
    </script>
    """, height=160)

    if st.session_state["voz_texto"]:
        texto = st.session_state["voz_texto"]
        validos = ["enciende las luces","apaga las luces","abre la puerta","cierra la puerta","activa la alarma","desactiva la alarma"]
        if any(c in texto for c in validos):
            st.markdown(f'<div class="status-ok">✅ Ejecutado: <strong>"{texto}"</strong></div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="status-err">⚠️ No reconocido: "{texto}"</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

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
