"""Web API and static page for Ketana Drishti.

Run:  uvicorn ketana_drishti.api:app --reload      (then open http://127.0.0.1:8000)
"""
import datetime as dt
import logging
from dataclasses import asdict
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, model_validator

from .chart import build_chart
from .facts import build_facts

log = logging.getLogger("ketana_drishti.api")
WEB_DIR = Path(__file__).resolve().parents[2] / "web"

app = FastAPI(title="Ketana Drishti", version="0.2.0")


class ChartRequest(BaseModel):
    datetime: str = Field(description="Birth moment, local time, e.g. 1998-05-14T08:30:21")
    place: str | None = Field(default=None, max_length=120)
    lat: float | None = Field(default=None, ge=-90, le=90)
    lon: float | None = Field(default=None, ge=-180, le=180)
    name: str | None = Field(default=None, max_length=80)
    as_of: dt.date | None = None

    @model_validator(mode="after")
    def need_place_or_coordinates(self):
        has_place = bool(self.place and self.place.strip())
        has_coords = self.lat is not None and self.lon is not None
        if not (has_place or has_coords):
            raise ValueError("Give a place name, or both latitude and longitude.")
        return self


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/chart")
def chart(req: ChartRequest):
    try:
        when = dt.datetime.fromisoformat(req.datetime)
    except ValueError:
        raise HTTPException(400, "Birth date and time must look like 1998-05-14T08:30:21.")
    if when.year < 1900 or when > dt.datetime.now() + dt.timedelta(days=366):
        raise HTTPException(400, "Birth date must be between 1900 and today.")
    try:
        result = build_chart(when, place=(req.place or None), lat=req.lat, lon=req.lon, name=req.name)
    except Exception:
        log.exception("chart calculation failed")
        raise HTTPException(400, "Could not find that place or calculate the chart. "
                                 "Check the spelling, or enter latitude and longitude instead.")
    as_of = req.as_of or dt.date.today()
    facts = [asdict(f) for f in build_facts(result, as_of)]
    return {"chart": result, "facts": facts}


if WEB_DIR.is_dir():
    app.mount("/", StaticFiles(directory=WEB_DIR, html=True), name="web")
