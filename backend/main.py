from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import datetime
import json
import os

from ml_inference import model_service
from live_marine_data import get_all_regions_data, REGIONS_COORDS

app = FastAPI(title="Indian Coastal Bloom Monitor API")

# Enable CORS for React development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

ALERTS_FILE = "alerts.json"

class Alert(BaseModel):
    id: int
    msg: str
    severity: str
    label: str
    time: str
    region_id: Optional[str] = "all"

# Initial base data mirroring the frontend REGIONS but with dynamic potential
BASE_REGIONS = [
    { "id": "mannar", "name": "Gulf of Mannar", "state": "Tamil Nadu", "risk": "High", "score": 78, "wqi": 42, "sst": 31.2, "nutrients": 78, "zoo": 4200, "hab": "PSP", "oilSpill": 7, "prob": 87, "conf": 91, "do_": 4.1, "ph": 7.2, "turbidity": 28, "tds": 780, "salinity": 35.8, "nitrate": 42, "coliform": 220, "biodiv": 52, "fish": ["Indian Mackerel", "Sardines", "Prawns"], "ec": "₹82 Cr", "safeFishing": False },
    { "id": "kerala", "name": "Arabian Sea – Kerala", "state": "Kerala", "risk": "Medium", "score": 55, "wqi": 71, "sst": 29.8, "nutrients": 61, "zoo": 2800, "hab": None, "oilSpill": 0, "prob": 61, "conf": 84, "do_": 6.8, "ph": 8.0, "turbidity": 12, "tds": 410, "salinity": 34.2, "nitrate": 18, "coliform": 45, "biodiv": 71, "fish": ["Sardines", "Anchovies", "Hilsa"], "ec": "₹31 Cr", "safeFishing": True },
    { "id": "odisha", "name": "Bay of Bengal – Odisha", "state": "Odisha/WB", "risk": "High", "score": 72, "wqi": 55, "sst": 30.5, "nutrients": 70, "zoo": 3600, "hab": "NSP", "oilSpill": 2, "prob": 79, "conf": 88, "do_": 5.2, "ph": 7.6, "turbidity": 35, "tds": 620, "salinity": 33.1, "nitrate": 28, "coliform": 120, "biodiv": 58, "fish": ["Hilsa", "Mackerel", "Anchovies"], "ec": "₹64 Cr", "safeFishing": False },
    { "id": "lakshadweep", "name": "Lakshadweep Sea", "state": "Lakshadweep UT", "risk": "Low", "score": 22, "wqi": 88, "sst": 27.8, "nutrients": 22, "zoo": 1200, "hab": None, "oilSpill": 0, "prob": 18, "conf": 95, "do_": 7.4, "ph": 8.2, "turbidity": 6, "tds": 290, "salinity": 36.1, "nitrate": 4, "coliform": 5, "biodiv": 88, "fish": ["Tuna", "Reef Fish", "Skipjack"], "ec": "₹4 Cr", "safeFishing": True },
    { "id": "palk", "name": "Palk Strait", "state": "Tamil Nadu/Sri Lanka border", "risk": "High", "score": 69, "wqi": 44, "sst": 30.1, "nutrients": 65, "zoo": 3100, "hab": "DSP", "oilSpill": 4, "prob": 74, "conf": 86, "do_": 3.8, "ph": 7.0, "turbidity": 44, "tds": 890, "salinity": 32.4, "nitrate": 38, "coliform": 310, "biodiv": 47, "fish": ["Shrimp", "Prawns", "Mackerel"], "ec": "₹57 Cr", "safeFishing": False },
    { "id": "andaman", "name": "Andaman Sea", "state": "Andaman & Nicobar", "risk": "Low", "score": 19, "wqi": 82, "sst": 28.2, "nutrients": 18, "zoo": 1800, "hab": None, "oilSpill": 0, "prob": 14, "conf": 97, "do_": 7.1, "ph": 8.1, "turbidity": 9, "tds": 320, "salinity": 35.5, "nitrate": 6, "coliform": 8, "biodiv": 83, "fish": ["Tuna", "Barracuda", "Snapper"], "ec": "₹2 Cr", "safeFishing": True },
    { "id": "andhra", "name": "Andhra Pradesh Coast", "state": "Andhra Pradesh", "risk": "Medium", "score": 58, "wqi": 62, "sst": 29.5, "nutrients": 55, "zoo": 2600, "hab": None, "oilSpill": 0, "prob": 63, "conf": 82, "do_": 5.9, "ph": 7.7, "turbidity": 22, "tds": 510, "salinity": 34.0, "nitrate": 22, "coliform": 75, "biodiv": 62, "fish": ["Pomfret", "Barramundi", "King Fish"], "ec": "₹38 Cr", "safeFishing": True },
    { "id": "karnataka", "name": "Karnataka Coast", "state": "Karnataka", "risk": "Low", "score": 28, "wqi": 79, "sst": 28.9, "nutrients": 28, "zoo": 1500, "hab": None, "oilSpill": 0, "prob": 22, "conf": 90, "do_": 7.0, "ph": 8.1, "turbidity": 10, "tds": 340, "salinity": 34.8, "nitrate": 8, "coliform": 18, "biodiv": 76, "fish": ["Sardines", "Mackerel", "Prawns"], "ec": "₹12 Cr", "safeFishing": True },
    { "id": "gujarat", "name": "Gulf of Kutch – Gujarat", "state": "Gujarat", "risk": "Low", "score": 31, "wqi": 74, "sst": 28.1, "nutrients": 31, "zoo": 1600, "hab": None, "oilSpill": 0, "prob": 26, "conf": 88, "do_": 6.8, "ph": 8.0, "turbidity": 15, "tds": 380, "salinity": 35.2, "nitrate": 10, "coliform": 22, "biodiv": 70, "fish": ["Pomfret", "Threadfin", "Bombay Duck"], "ec": "₹9 Cr", "safeFishing": True },
    { "id": "goa", "name": "Goa Coast", "state": "Goa", "risk": "Low", "score": 24, "wqi": 80, "sst": 28.5, "nutrients": 24, "zoo": 1400, "hab": None, "oilSpill": 0, "prob": 20, "conf": 93, "do_": 7.2, "ph": 8.1, "turbidity": 8, "tds": 310, "salinity": 35.0, "nitrate": 7, "coliform": 12, "biodiv": 78, "fish": ["Kingfish", "Pomfret", "Tuna"], "ec": "₹6 Cr", "safeFishing": True },
]

@app.get("/api/v1/regions")
async def get_regions():
    live_data = await get_all_regions_data()
    
    updated_regions = []
    for r_base in BASE_REGIONS:
        # Explicitly cast to dict to avoid inference issues with the constant list
        r = dict(r_base) 
        rid = str(r["id"])
        live = live_data.get(rid, {})
        
        # Override with live SST and Waves
        # Use .get with a default to avoid type errors if live data is missing
        sst_val = live.get("sst")
        if sst_val is not None:
            r["sst"] = float(sst_val)
        
        # Run ML Inference
        ml_input = {
            "sst": float(r.get("sst", 28.0)),
            "salinity": float(r.get("salinity", 34.0)),
            "nitrate": float(r.get("nitrate", 20.0)),
            "do": float(r.get("do_", 6.0)),
            "turbidity": float(r.get("turbidity", 10.0))
        }
        prediction = model_service.predict(ml_input)
        
        r["prob"] = float(prediction.get("probability", 50.0))
        r["risk"] = str(prediction.get("prediction", "Medium"))
        r["score"] = float(r["prob"])
        r["safeFishing"] = bool(r["risk"] != "High")
        
        sync_time = live.get("last_sync")
        r["last_sync"] = str(sync_time) if sync_time else datetime.datetime.now().isoformat()
        updated_regions.append(r)
        
    return updated_regions

@app.get("/api/v1/alerts")
async def get_alerts():
    if not os.path.exists(ALERTS_FILE):
        return []
    try:
        with open(ALERTS_FILE, "r") as f:
            content = f.read()
            if not content: return []
            return json.loads(content)
    except Exception:
        return []

@app.post("/api/v1/broadcast")
async def post_alert(alert: Alert):
    alerts = []
    if os.path.exists(ALERTS_FILE):
        try:
            with open(ALERTS_FILE, "r") as f:
                content = f.read()
                if content:
                    alerts = json.loads(content)
        except Exception:
            alerts = []
    
    alerts.insert(0, alert.dict())
    try:
        with open(ALERTS_FILE, "w") as f:
            # Slicing is standard for lists in Python, if the linter complains, 
            # we can use a loop or just ignore if it's a false positive.
            # But let's try a very explicit slice.
            to_save = alerts[0:50] 
            json.dump(to_save, f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
    return {"status": "success", "alert": alert}

@app.get("/")
def read_root():
    return {"status": "online", "message": "Indian Coastal Bloom Monitor API v1"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
