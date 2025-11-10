import streamlit as st
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from threading import Thread
import uvicorn
from database import aggiorna_posizione, get_posizioni_attuali, get_notifiche
import pandas as pd
import time

# ========== FASTAPI BACKEND ==========
api = FastAPI()

api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@api.post("/update_position")
async def update_position(request: Request):
    data = await request.json()
    ticket_id = data.get("ticket_id")
    lat = data.get("lat")
    lon = data.get("lon")
    if not ticket_id or lat is None or lon is None:
        return {"status": "error", "message": "Dati mancanti"}
    try:
        aggiorna_posizione(ticket_id, lat, lon)
        return {"status": "ok", "ticket_id": ticket_id}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def run_api():
    uvicorn.run(api, host="0.0.0.0", port=8000)

# Avvia l’API in thread parallelo
Thread(target=run_api, daemon=True).start()

# ========== STREAMLIT FRONTEND ==========
st.set_page_config(page_title="Gestione Code - Ufficio", layout="wide")
st.title("🏢 Gestione Code - Monitoraggio Autisti")

# Refresh automatico ogni 10 secondi
refresh_interval = 10
last_refresh_time = st.session_state.get("last_refresh_time", 0)

if time.time() - last_refresh_time > refresh_interval:
    st.session_state["last_refresh_time"] = time.time()
    st.experimental_rerun()

# Mostra posizioni
try:
    dati = get_posizioni_attuali()
    if dati:
        df = pd.DataFrame(dati)
        st.map(df)
        st.dataframe(df)
    else:
        st.info("Nessuna posizione disponibile al momento.")
except Exception as e:
    st.error(f"Errore caricamento posizioni: {e}")

st.markdown("---")
st.subheader("📢 Ultime notifiche")
try:
    notifiche = get_notifiche()
    if notifiche:
        for n in notifiche[:5]:
            st.write(f"🕓 {n['Data']}: **{n['Testo']}**")
    else:
        st.info("Nessuna notifica recente.")
except Exception as e:
    st.error(f"Errore recupero notifiche: {e}")
