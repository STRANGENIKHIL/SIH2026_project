"""
AIS Vessel Attribution & Drift Intelligence Engine Launcher
Nikhil — AI/ML Lead for Vessel Attribution + Drift Intelligence (SIH PS 26143)
Starts FastAPI service on http://127.0.0.1:8000
"""

import sys
import os
import uvicorn

def main():
    print("=" * 75)
    print(" 🚢 AIS VESSEL ATTRIBUTION & DRIFT INTELLIGENCE ENGINE (SIH PS 26143)")
    print(" 👤 Lead: Nikhil (AI/ML Lead for Vessel Attribution + Drift Intelligence)")
    print("=" * 75)
    print(" FastAPI Service Running at: http://127.0.0.1:8000")
    print(" OpenAPI Docs (Swagger UI):  http://127.0.0.1:8000/docs")
    print(" Health Endpoint:            http://127.0.0.1:8000/api/health")
    print("=" * 75)

    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)

if __name__ == "__main__":
    main()
