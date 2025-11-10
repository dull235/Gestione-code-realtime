# backend/backend.py
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from database import aggiorna_posizione
import uvicorn

app = FastAPI(title="Gestione Code Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def home():
    return {"status": "ok", "message": "Backend FastAPI attivo"}

@app.post("/update_position")
async def update_position(request: Request):
    try:
        data = await request.json()
        ticket_id = data.get("ticket_id")
        lat = data.get("lat")
        lon = data.get("lon")

        if not ticket_id or lat is None or lon is None:
            return {"status": "error", "message": "Dati mancanti"}

        aggiorna_posizione(ticket_id, lat, lon)
        return {"status": "ok"}

    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=10000)
