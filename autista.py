import streamlit as st
import requests
import time
import streamlit.components.v1 as components

# =========================
# CONFIGURAZIONE BASE
# =========================
st.set_page_config(page_title="Tracker Autista", page_icon="🚚", layout="centered")

API_URL = "https://gestione-code-realtime.onrender.com"
REFRESH_INTERVAL = 10  # secondi

# =========================
# INIZIALIZZAZIONE SESSIONE
# =========================
if "posizione_attuale" not in st.session_state:
    st.session_state.posizione_attuale = (0.0, 0.0)
if "ticket_id" not in st.session_state:
    st.session_state.ticket_id = None
if "last_refresh_time" not in st.session_state:
    st.session_state.last_refresh_time = time.time()

# =========================
# FUNZIONI DI SUPPORTO
# =========================
def apri_ticket(nome_autista):
    try:
        r = requests.post(f"{API_URL}/crea_ticket", json={"nome_autista": nome_autista})
        if r.status_code == 200:
            st.session_state.ticket_id = r.json().get("ticket_id")
            return st.session_state.ticket_id
        else:
            st.error("Errore nel creare il ticket.")
    except Exception as e:
        st.error(f"Errore di connessione: {e}")

def aggiorna_posizione(ticket_id, lat, lon):
    try:
        r = requests.post(f"{API_URL}/aggiorna_posizione", json={
            "ticket_id": ticket_id,
            "lat": lat,
            "lon": lon
        })
        if r.status_code != 200:
            st.warning("⚠️ Impossibile aggiornare la posizione sul server.")
    except Exception as e:
        st.warning(f"Errore aggiornamento posizione: {e}")

# =========================
# UI PRINCIPALE
# =========================
st.title("🚚 Tracker Autista")
st.markdown("Questa app invia la posizione dell’autista in tempo reale all’ufficio.")

nome_autista = st.text_input("👤 Inserisci il tuo nome:")

# --- Creazione ticket ---
if st.button("🎫 Apri Ticket"):
    if nome_autista.strip():
        ticket = apri_ticket(nome_autista)
        if ticket:
            st.success(f"✅ Ticket creato correttamente (ID: {ticket})")
            st.rerun()
    else:
        st.warning("Inserisci il tuo nome prima di aprire il ticket.")

# --- Mostra ticket aperto ---
if st.session_state.ticket_id:
    st.info(f"🎟️ Ticket attivo: {st.session_state.ticket_id}")

# --- Lettura coordinate da URL (inviate da JS) ---
query_params = st.query_params
if "lat" in query_params and "lon" in query_params:
    try:
        lat = float(query_params["lat"])
        lon = float(query_params["lon"])
        st.session_state.posizione_attuale = (lat, lon)
        # Aggiorna posizione sul server
        if st.session_state.ticket_id:
            aggiorna_posizione(st.session_state.ticket_id, lat, lon)
    except Exception:
        pass

# =========================
# GEOLOCALIZZAZIONE
# =========================
if st.session_state.posizione_attuale == (0.0, 0.0):
    st.markdown("**📡 Geolocalizzazione attiva:** in attesa di coordinate GPS...")

    components.html(
        """
        <script>
        (function() {
            console.log("🔍 Tentativo di ottenere coordinate GPS...");

            function inviaPosizione(lat, lon) {
                console.log("✅ Coordinate trovate:", lat, lon);
                const query = new URLSearchParams(window.location.search);
                query.set("lat", lat);
                query.set("lon", lon);
                window.location.search = query.toString();
            }

            function success(pos) {
                inviaPosizione(pos.coords.latitude, pos.coords.longitude);
            }

            function error(err) {
                console.error("❌ Errore geolocalizzazione:", err);
                const msg = document.createElement('p');
                msg.style.color = 'red';
                msg.innerText = "⚠️ Errore GPS: " + err.message;
                document.body.appendChild(msg);

                // Coordinate di test (Milano)
                if (window.location.search.indexOf("lat=") === -1) {
                    console.log("🌍 Uso coordinate simulate (Milano)...");
                    inviaPosizione(45.4642, 9.19);
                }
            }

            if (navigator.geolocation) {
                navigator.geolocation.getCurrentPosition(success, error, {
                    enableHighAccuracy: true,
                    timeout: 10000,
                    maximumAge: 0
                });
            } else {
                const msg = document.createElement('p');
                msg.style.color = 'red';
                msg.innerText = "❌ Geolocalizzazione non supportata dal browser.";
                document.body.appendChild(msg);
            }
        })();
        </script>
        """,
        height=0,
    )
else:
    lat, lon = st.session_state.posizione_attuale
    st.success(f"**📍 Posizione attuale:** Lat {lat:.6f}, Lon {lon:.6f}")
    if st.session_state.ticket_id:
        try:
            aggiorna_posizione(st.session_state.ticket_id, lat, lon)
        except Exception as e:
            st.warning(f"Errore aggiornamento posizione: {e}")

# =========================
# REFRESH PERIODICO
# =========================
if time.time() - st.session_state.last_refresh_time > REFRESH_INTERVAL:
    st.session_state.last_refresh_time = time.time()
    st.rerun()
