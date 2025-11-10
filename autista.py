import streamlit as st
import streamlit.components.v1 as components
import time
import requests
from database import inserisci_ticket, get_notifiche, aggiorna_posizione

# 🔧 CONFIGURA URL DEL BACKEND FASTAPI (deve essere HTTPS)
BACKEND_URL = "https://gestione-code-realtime.onrender.com/update_position"  # <-- cambia con il tuo dominio Render HTTPS

def main():
    st.set_page_config(
        page_title="Gestione Code - Autisti",
        page_icon="https://raw.githubusercontent.com/dull235/Gestione-code/main/static/icon.png",
        layout="wide"
    )

    st.markdown("""
    <style>
    .stApp {
        background: url("https://raw.githubusercontent.com/dull235/Gestione-code/main/static/sfondo.jpg") 
        no-repeat center center fixed;
        background-size: cover;
    }
    .main > div {
        background-color: rgba(255, 255, 255, 0.85) !important;
        padding: 20px;
        border-radius: 10px;
        color: black !important;
    }
    .stButton button {
        background-color: #1976d2;
        color: white;
        border-radius: 8px;
        border: none;
    }
    .notifica {
        background-color: rgba(255, 255, 255, 0.9);
        padding: 10px 15px;
        border-left: 6px solid #1976d2;
        margin-bottom: 10px;
        border-radius: 6px;
    }
    </style>
    """, unsafe_allow_html=True)

    st.title("🚛 Pagina Autisti")
    st.write("Compila i tuoi dati e ricevi aggiornamenti dall'ufficio in tempo reale.")

    # --- Stato iniziale ---
    if "ticket_id" not in st.session_state:
        st.session_state.ticket_id = None
    if "modalita" not in st.session_state:
        st.session_state.modalita = "iniziale"
    if "posizione_attuale" not in st.session_state:
        st.session_state.posizione_attuale = (0.0, 0.0)
    if "last_refresh_time" not in st.session_state:
        st.session_state.last_refresh_time = 0

    # --- Refresh automatico ogni 10 secondi ---
    refresh_interval = 10  # secondi
    if time.time() - st.session_state.last_refresh_time > refresh_interval:
        st.session_state.last_refresh_time = time.time()
        st.rerun()

    # --- Geolocalizzazione via componente HTML ---
    if st.session_state.ticket_id:  # attiva solo se c'è un ticket attivo
        st.subheader("📍 Geolocalizzazione in tempo reale")

        geo_html = """
        <script>
        const sendLocation = (lat, lon) => {
            const streamlitDoc = window.parent.document;
            const input = streamlitDoc.getElementById("geo-coords");
            input.value = `${lat},${lon}`;
            input.dispatchEvent(new Event("input", { bubbles: true }));
        };

        if (navigator.geolocation) {
            navigator.geolocation.watchPosition(
                pos => sendLocation(pos.coords.latitude, pos.coords.longitude),
                err => console.warn("⚠️ Errore GPS:", err.message),
                { enableHighAccuracy: true, maximumAge: 5000, timeout: 10000 }
            );
        } else {
            alert("Il tuo browser non supporta la geolocalizzazione.");
        }
        </script>
        <input type="text" id="geo-coords" style="display:none"/>
        """
        components.html(geo_html, height=0)

        geo_input = st.text_input("", key="geo-coords", label_visibility="collapsed")
        if geo_input:
            try:
                lat, lon = map(float, geo_input.split(","))
                st.session_state.posizione_attuale = (lat, lon)
                st.success(f"Posizione aggiornata: {lat:.5f}, {lon:.5f}")

                # Aggiorna posizione su Supabase via FastAPI
                try:
                    requests.post(BACKEND_URL, json={
                        "ticket_id": st.session_state.ticket_id,
                        "lat": lat,
                        "lon": lon
                    })
                except Exception as e:
                    st.warning(f"Errore invio posizione al server: {e}")
            except:
                st.warning("Errore nel parsing della posizione.")
    else:
        st.info("Attiva un ticket per iniziare il monitoraggio GPS.")

    # --- Logica modalità ---
    if st.session_state.modalita == "iniziale":
        st.info("Clicca su **Avvia** per creare una nuova richiesta di carico/scarico.")
        if st.button("🚀 Avvia"):
            st.session_state.modalita = "form"
            st.rerun()

    elif st.session_state.modalita == "form":
        st.subheader("📋 Compila i tuoi dati")
        nome = st.text_input("Nome e Cognome")
        azienda = st.text_input("Azienda")
        targa = st.text_input("Targa Motrice")
        rimorchio = st.checkbox("Hai un rimorchio?")
        targa_rim = st.text_input("Targa Rimorchio") if rimorchio else ""
        tipo = st.radio("Tipo Operazione", ["Carico", "Scarico"])
        destinazione = produttore = ""
        if tipo == "Carico":
            destinazione = st.text_input("Destinazione")
        else:
            produttore = st.text_input("Produttore")

        if st.button("📨 Invia Richiesta"):
            if not nome or not azienda or not targa:
                st.error("⚠️ Compila tutti i campi obbligatori prima di inviare.")
            else:
                try:
                    ticket_id = inserisci_ticket(
                        nome=nome,
                        azienda=azienda,
                        targa=targa,
                        tipo=tipo,
                        destinazione=destinazione,
                        produttore=produttore,
                        rimorchio=int(rimorchio),
                        lat=st.session_state.posizione_attuale[0],
                        lon=st.session_state.posizione_attuale[1]
                    )
                    st.session_state.ticket_id = ticket_id
                    st.session_state.modalita = "notifiche"
                    st.success("✅ Ticket inviato all'ufficio! Attendi notifiche.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Errore invio ticket: {e}")

    elif st.session_state.modalita == "notifiche":
        ticket_id = st.session_state.ticket_id
        st.success(f"📦 Ticket attivo ID: {ticket_id}")
        st.subheader("📢 Notifiche ricevute")

        st.markdown("<hr>", unsafe_allow_html=True)

        try:
            notifiche = get_notifiche(ticket_id)
        except Exception as e:
            st.error(f"Errore recupero notifiche: {e}")
            notifiche = []

        if notifiche:
            ultima = notifiche[0]
            testo = ultima.get("Testo") if isinstance(ultima, dict) else ultima[0]
            data = ultima.get("Data") if isinstance(ultima, dict) else ultima[1]
            st.markdown(f"### 🕓 Ultimo aggiornamento: `{data}`")
            st.markdown(f"#### 💬 **{testo}**")
            st.divider()
            st.write("🔁 Storico ultime notifiche:")
            for n in notifiche[1:5]:
                testo_n = n.get("Testo") if isinstance(n, dict) else n[0]
                data_n = n.get("Data") if isinstance(n, dict) else n[1]
                st.markdown(f"<div class='notifica'>🕓 <b>{data_n}</b><br>{testo_n}</div>", unsafe_allow_html=True)
        else:
            st.info("Nessuna notifica disponibile al momento.")

        col1, col2 = st.columns(2)
        if col1.button("🔄 Aggiorna ora"):
            st.rerun()
        if col2.button("❌ Chiudi ticket locale"):
            st.session_state.ticket_id = None
            st.session_state.modalita = "iniziale"
            st.rerun()


if __name__ == "__main__":
    main()
