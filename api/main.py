import json
import statistics
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from pathlib import Path

app = FastAPI()

# Enable CORS for POST from any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST"],
    allow_headers=["*"],
)

# Load telemetry safely
BASE_DIR = Path(__file__).parent.parent
with open(BASE_DIR / "telemetry.json") as f:
    telemetry = json.load(f)

class RequestBody(BaseModel):
    regions: List[str]
    threshold_ms: int

def percentile(values, p):
    values = sorted(values)
    k = int(len(values) * p / 100)
    return values[min(k, len(values) - 1)]

@app.get("/")
def root():
    return {"status": "ok"}

@app.post("/api")
def check_latency(data: RequestBody):
    result = {}

    for region in data.regions:
        records = [r for r in telemetry if r["region"] == region]

        if not records:
            # REQUIRED: handle missing regions safely
            result[region] = {
                "avg_latency": 0,
                "p95_latency": 0,
                "avg_uptime": 0,
                "breaches": 0
            }
            continue

        latencies = [r["latency_ms"] for r in records]
        uptimes = [r["uptime_pct"] for r in records]


        result[region] = {
            "avg_latency": statistics.mean(latencies),
            "p95_latency": percentile(latencies, 95),
            "avg_uptime": statistics.mean(uptimes),
            "breaches": sum(l > data.threshold_ms for l in latencies)
        }

    return result
