"""FastAPI entrypoint.  Run:  uvicorn app.main:app --reload"""
from pathlib import Path

from fastapi import Body, FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

import service

app = FastAPI(title="Digital Risk Protection - Social & App Monitoring")
STATIC = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=STATIC), name="static")


@app.get("/")
def index():
    return FileResponse(STATIC / "index.html")


@app.get("/api/profile")
def read_profile():
    return service.get_profile()


@app.put("/api/profile")
def update_profile(payload: dict = Body(...)):
    profile, errors = service.validate_profile(payload)
    if errors:
        raise HTTPException(status_code=422, detail=errors)
    service.save_profile(profile)
    return profile


@app.post("/api/scan")
def scan(live: bool = False):
    """Run a scan. `live=true` also queries the live Apple App Store API;
    if that is unreachable the scan still completes and reports the source as unavailable."""
    profile = service.get_profile()
    return service.run_scan(profile, live=live)


@app.get("/api/scan/latest")
def latest():
    return service.latest_scan() or {}
