import streamlit as st
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from threading import Thread
import uvicorn
from database import aggiorna_posizione, get_posizioni_attuali, get_notifiche
import pandas as pd

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
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def run_api():
    uvicorn.run(api, host="0.0.0.0", port=8000)

Thread(target=run_api, daemon=True).start()

# ========== STREAMLIT FRONTEND ==========
st.set_page_config(page_title="Gestione Code - Ufficio", layout="wide")
st.title("🚛 Gestione Code - Monitoraggio Autisti")

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
    for n in notifiche[:5]:
        st.write(f"🕓 {n['Data']}: **{n['Testo']}**")
except:
    st.info("Nessuna notifica recente.")

# Aggiornamento automatico
st.experimental_rerun()
