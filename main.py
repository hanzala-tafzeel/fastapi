import json
import statistics
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import numpy as np

app = FastAPI()

# Enable CORS for POST from any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST"],
    allow_headers=["*"],
)

# Load telemetry once
with open("telemetry.json") as f:
    telemetry = json.load(f)

class RequestBody(BaseModel):
    regions: List[str]
    threshold_ms: int


@app.post("/api")
def check_latency(data: RequestBody):
    result = {}

    for region in data.regions:
        records = [r for r in telemetry if r["region"] == region]

        latencies = [r["latency_ms"] for r in records]
        uptimes = [r["uptime"] for r in records]

        result[region] = {
            "avg_latency": statistics.mean(latencies),
            "p95_latency": float(np.percentile(latencies, 95)),
            "avg_uptime": statistics.mean(uptimes),
            "breaches": sum(1 for l in latencies if l > data.threshold_ms)
        }

    return result
