"""Web API and static page for Ketana Drishti.

Run:  uvicorn ketana_drishti.api:app --reload      (then open http://127.0.0.1:8000)
"""
import datetime as dt
import logging
import os
from dataclasses import asdict, dataclass
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, model_validator

from .chart import build_chart
from .facts import build_facts
from .places import PlacesUnavailable, search_places
from .llm import ClaudeClient, FakeClient, LLMError
from . import i18n
from .classic import classic_payload
from .reading import LANGUAGES, ReadingError, check, generate_reading
from .retrieval import DEFAULT_LIMIT, load_corpus, retrieve

load_dotenv()
log = logging.getLogger("ketana_drishti.api")
WEB_DIR = Path(__file__).resolve().parents[2] / "web"

app = FastAPI(title="Ketana Drishti", version="0.3.0")


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
    ai = demo_enabled() or bool(os.environ.get("ANTHROPIC_API_KEY"))
    return {"status": "ok", "ai": ai}


@app.get("/api/places")
def places(q: str = Query("", max_length=120), limit: int = Query(6, ge=1, le=10)):
    """Type-ahead suggestions for the place of birth. Never an error page: if the
    lookup service is down, `unavailable` is true and the page falls back to typing."""
    try:
        return {"results": search_places(q, limit), "unavailable": False}
    except PlacesUnavailable:
        return {"results": [], "unavailable": True}


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


class FactIn(BaseModel):
    id: str = Field(min_length=1, max_length=80)
    text: str = Field(min_length=1, max_length=500)
    values: dict[str, str | int | float | None] = Field(default_factory=dict)


class ReadingRequest(BaseModel):
    facts: list[FactIn] = Field(min_length=1, max_length=400)
    language: str = "en"
    question: str | None = Field(default=None, max_length=200)
    mode: str = "classic"  # "classic" (no model, free) or "ai"


@dataclass
class _F:
    id: str
    text: str
    values: dict


def demo_enabled() -> bool:
    return os.environ.get("KETANA_DEMO", "").strip() == "1"


def make_client(facts, passages=None):
    """Real Claude client, or a free scripted one when KETANA_DEMO=1."""
    if demo_enabled():
        picked = [f for f in facts][:3]
        stmts = []
        for f in picked:
            pids = [p.id for p in (passages or []) if f.id in p.because][:1]
            stmts.append({"text": "Demo mode (no AI used): " + f.text, "fact_ids": [f.id], "passage_ids": pids})
        return FakeClient([{"statements": stmts}])
    return ClaudeClient()


_CORPUS = None


def _corpus():
    global _CORPUS
    if _CORPUS is None:
        _CORPUS = load_corpus()
    return _CORPUS


def get_passages(facts, limit=None):
    """Passages for these facts; an unreadable corpus means a reading without passages."""
    global _CORPUS
    try:
        if _CORPUS is None:
            _CORPUS = load_corpus()
        return retrieve(facts, _CORPUS, limit=limit or DEFAULT_LIMIT)
    except Exception:
        log.exception("could not load the passage corpus")
        return []


@app.post("/api/reading")
def reading(req: ReadingRequest):
    if req.language not in LANGUAGES:
        raise HTTPException(400, "Language must be one of: " + ", ".join(sorted(LANGUAGES)) + ".")
    if req.mode not in ("classic", "ai"):
        raise HTTPException(400, 'Mode must be "classic" or "ai".')
    facts = [_F(f.id, f.text, f.values) for f in req.facts]
    # A model prompt needs a size cap; the classic reading does not, so it uses every passage.
    passages = get_passages(facts, limit=500 if req.mode == "classic" else None)
    if req.mode == "classic":
        payload = classic_payload(facts, passages, lang=req.language, corpus=_corpus())
        valid, problems = check(payload, facts, passages)
        if not valid:
            raise HTTPException(502, "Could not build a classic reading from these facts.")
        used = {i for s in valid for i in s.passage_ids}
        return {
            "mode": "classic",
            "statements": [{"text": s.text, "fact_ids": s.fact_ids, "passage_ids": s.passage_ids} for s in valid],
            "passages": [{"id": p.id, "text": p.text, "because": p.because} for p in passages if p.id in used],
            "disclaimer": i18n.DISCLAIMERS[req.language],
            "language": req.language,
            "note": i18n.NOTES[req.language],
            "notice": "",
            "model": "", "demo": False, "retried": False, "dropped": 0,
        }
    try:
        client = make_client(facts, passages)
        r = generate_reading(client, facts, language=req.language, question=req.question,
                             passages=passages)
    except LLMError as e:
        raise HTTPException(503, str(e))
    except ReadingError as e:
        raise HTTPException(502, str(e))
    return {
        "mode": "ai",
        "notice": "",
        "statements": [{"text": s.text, "fact_ids": s.fact_ids, "passage_ids": s.passage_ids}
                       for s in r.statements],
        "passages": [{"id": p.id, "text": p.text, "because": p.because} for p in r.passages],
        "disclaimer": r.disclaimer,
        "language": r.language,
        "model": r.model,
        "demo": demo_enabled(),
        "retried": r.retried,
        "dropped": r.dropped,
    }


if WEB_DIR.is_dir():
    app.mount("/", StaticFiles(directory=WEB_DIR, html=True), name="web")
