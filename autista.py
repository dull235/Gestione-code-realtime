import streamlit as st
from database import inserisci_ticket, get_notifiche, aggiorna_posizione
from streamlit_autorefresh import st_autorefresh
import base64

# Compatibilità Streamlit vecchie versioni
if not hasattr(st, "rerun"):
    st.rerun = st.experimental_rerun

# --- Funzione per riprodurre suono locale ---
def play_local_sound(file_path):
    with open(file_path, "rb") as f:
        audio_bytes = f.read()
    audio_base64 = base64.b64encode(audio_bytes).decode()
    st.markdown(f"""
    <audio autoplay>
        <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
    </audio>
    """, unsafe_allow_html=True)


def main():
    st.set_page_config(
        page_title="Gestione Code - Autisti",
        page_icon="https://raw.githubusercontent.com/dull235/Gestione-code/main/static/icon.png",
        layout="wide"
    )

    # --- Aggiornamento automatico ogni 10 secondi ---
    st_autorefresh(interval=10000, key="refresh_autista")

    # --- Stile CSS personalizzato + overlay footer ---
    st.markdown("""
    <style>

    /* 🔥 NASCONDI TUTTO STREAMLIT (100% effettivo su Render) */
    #MainMenu {visibility: hidden !important; display: none !important;}
    footer {visibility: hidden !important; display: none !important;}
    header {visibility: hidden !important; display: none !important;}

    [data-testid="stDecoration"] {visibility: hidden !important; display: none !important;}
    [data-testid="stToolbar"] {visibility: hidden !important; height: 0 !important; display: none !important;}
    [data-testid="stActionButton"] {visibility: hidden !important; display: none !important;}
    [data-testid="stStatusWidget"] {visibility: hidden !important; display: none !important;}

    .css-1rs6os.edgvbvh3,
    .css-yemjua,
    .stApp > div > div:nth-child(3) {
        visibility: hidden !important;
        display: none !important;
    }

    /* 🔵 Sfondi */
    .stApp {
        background: linear-gradient(rgba(179, 217, 255, 0.6), rgba(179, 217, 255, 0.6)),
                    url("https://raw.githubusercontent.com/dull235/Gestione-code/main/static/sfondo.png");
        background-size: cover;
        background-position: center;
        min-height: 100vh;
        padding: 0 !important;
        margin: 0 !important;
    }

    /* Contenitore */
    .main > div {
        background-color: rgba(173, 216, 230, 0.85) !important;
        padding: 20px;
        border-radius: 10px;
        color: black !important;
        max-width: 600px;
        margin: 10px auto !important;
    }

    /* Pulsanti */
    .stButton button {
        background-color: #1976d2 !important;
        color: white !important;
        border-radius: 8px !important;
        border: none !important;
        font-weight: 600 !important;
    }

    /* Input */
    div[data-baseweb="input"] > div > input,
    div[data-baseweb="textarea"] > textarea,
    input, textarea, select {
        background-color: white !important;
        color: black !important;
        border: 1px solid black !important;
        border-radius: 5px !important;
        padding: 5px !important;
    }

    /* Radio */
    div[role="radiogroup"] > label {
        background-color: white !important;
        border: 1px solid black;
        color: black !important;
        border-radius: 5px;
        padding: 5px;
        margin-right: 5px;
        transition: 0.2s;
    }
    div[role="radiogroup"] > label:has(input:checked) {
        background-color: #e3f2fd !important;
        border: 2px solid #1976d2 !important;
        font-weight: 600 !important;
    }

    /* Notifiche */
    .notifica {
        background-color: rgba(255,255,255,0.9);
        padding: 10px 15px;
        border-left: 6px solid #1976d2;
        margin-bottom: 10px;
        border-radius: 6px;
    }

    /* Logo splash */
    .custom-logo {
        display: flex;
        justify-content: center;
        margin-top: 20px;
        margin-bottom: 15px;
    }
    .custom-logo img {
        height: 100px;
        border-radius: 15px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.2);
    }
    @media (max-width: 600px) {
        .custom-logo img { height: 70px; }
    }

    </style>

    <!-- LOGO SUPERIORE -->
    <div class="custom-logo">
        <img src="https://raw.githubusercontent.com/dull235/Gestione-code/main/static/icon.png">
    </div>

    """, unsafe_allow_html=True)


    # --- Contenuto app ---
    st.title("🚛 Pagina Autisti")
    st.write("Compila i tuoi dati e ricevi aggiornamenti dall'ufficio in tempo reale.")

    # --- Stato sessione ---
    if "ticket_id" not in st.session_state:
        st.session_state.ticket_id = None
    if "modalita" not in st.session_state:
        st.session_state.modalita = "iniziale"
    if "posizione_attuale" not in st.session_state:
        st.session_state.posizione_attuale = (0.0, 0.0)
    if "ultima_notifica_id" not in st.session_state:
        st.session_state.ultima_notifica_id = None

    # --- Ottieni lat/lon dalla query string ---
    params = st.query_params
    if "lat" in params and "lon" in params:
        try:
            lat = float(params["lat"])
            lon = float(params["lon"])
            st.session_state.posizione_attuale = (lat, lon)
        except Exception:
            pass

    # --- Se la posizione non è disponibile ---
    if st.session_state.posizione_attuale == (0.0, 0.0):
        gps_url = "https://dull235.github.io/gps-sender/gps_sender.html"
        st.warning("📡 Posizione non rilevata.")
        st.markdown(f"[👉 Clicca qui per attivare il GPS]({gps_url})", unsafe_allow_html=True)
    else:
        lat, lon = st.session_state.posizione_attuale
        st.markdown(f"**📍 Posizione attuale:** Lat {lat:.6f}, Lon {lon:.6f}")
        if st.session_state.ticket_id:
            try:
                aggiorna_posizione(st.session_state.ticket_id, lat, lon)
            except Exception as e:
                st.warning(f"Errore aggiornamento posizione: {e}")

    # --- Modalità iniziale ---
    if st.session_state.modalita == "iniziale":
        st.info("Clicca su **Avvia** per creare una nuova richiesta di carico/scarico.")
        if st.button("🚀 Avvia"):
            st.session_state.modalita = "form"
            st.rerun()

    # --- Form ---
    elif st.session_state.modalita == "form":
        st.subheader("📋 Compila i tuoi dati")
        nome = st.text_input("Nome e Cognome", value=st.session_state.get("nome", ""), key="nome")
        azienda = st.text_input("Azienda", value=st.session_state.get("azienda", ""), key="azienda")
        targa = st.text_input("Targa Motrice", value=st.session_state.get("targa", ""), key="targa")
        rimorchio = st.checkbox("Hai un rimorchio?", value=st.session_state.get("rimorchio", False), key="rimorchio")
        if rimorchio:
            targa_rim = st.text_input("Targa Rimorchio", value=st.session_state.get("targa_rim", ""), key="targa_rim")
        else:
            st.session_state["targa_rim"] = ""
        tipo = st.radio("Tipo Operazione", ["Carico", "Scarico"], key="tipo")
        if tipo == "Carico":
            destinazione = st.text_input("Destinazione", value=st.session_state.get("destinazione", ""), key="destinazione")
            st.session_state["produttore"] = ""
        else:
            produttore = st.text_input("Produttore", value=st.session_state.get("produttore", ""), key="produttore")
            st.session_state["destinazione"] = ""
        if st.button("📨 Invia Richiesta"):
            if not st.session_state.nome or not st.session_state.azienda or not st.session_state.targa:
                st.error("⚠️ Compila tutti i campi obbligatori prima di inviare.")
            else:
                try:
                    ticket_id = inserisci_ticket(
                        nome=st.session_state.nome,
                        azienda=st.session_state.azienda,
                        targa=st.session_state.targa,
                        tipo=st.session_state.tipo,
                        destinazione=st.session_state.get("destinazione", ""),
                        produttore=st.session_state.get("produttore", ""),
                        rimorchio_targa=st.session_state.get("targa_rim", ""),
                        rimorchio=int(st.session_state.rimorchio),
                        lat=st.session_state.posizione_attuale[0],
                        lon=st.session_state.posizione_attuale[1]
                    )
                    st.session_state.ticket_id = ticket_id
                    st.session_state.modalita = "notifiche"
                    st.success("✅ Ticket inviato all'ufficio! Attendi notifiche.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Errore invio ticket: {e}")

    # --- Modalità notifiche ---
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
            if st.session_state.ultima_notifica_id != data:
                st.session_state.ultima_notifica_id = data
                play_local_sound("notifica.mp3")
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
