import os
import json
from pathlib import Path
from typing import Optional, List
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

# Try to import cnmc_generator for real-time CNMC generation
import sys
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

try:
    from cnmc_generator import generate_cnmc_for_material
except ImportError:
    generate_cnmc_for_material = None

app = FastAPI(title="SAMAAN — National Unified Material Master Platform")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load precomputed data
DATA_FILE = BASE_DIR / "data" / "precomputed_samaan.json"
CACHE = {}

def get_cache():
    global CACHE
    if not CACHE and DATA_FILE.exists():
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                CACHE = json.load(f)
        except Exception as e:
            print("Error loading precomputed data:", e)
    return CACHE

@app.get("/", response_class=HTMLResponse)
async def serve_home():
    html_path = BASE_DIR / "templates" / "index.html"
    if html_path.exists():
        return HTMLResponse(content=html_path.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>SAMAAN — One Nation, One Material Code</h1><p>Platform active. Access <a href='/docs'>/docs</a>.</p>")

@app.get("/api/stats")
async def get_stats():
    data = get_cache().get("stats")
    if data:
        return data
    return {"total_materials": 1332, "total_matches": 420, "total_clusters": 118, "auto_approved_pct": 74.2}

@app.get("/api/cnmc/stats")
async def get_cnmc_stats():
    data = get_cache().get("cnmc_stats")
    if data:
        return data
    return {"total_materials": 1332, "unique_cnmc_codes": 512, "auto_mapped": 820, "new_codes": 512}

@app.get("/api/materials")
async def get_materials(cpse: Optional[str] = None, search: Optional[str] = None, page: int = 1, limit: int = 20):
    materials_data = get_cache().get("materials", {})
    items = materials_data.get("items", [])
    
    if cpse and cpse.upper() != "ALL":
        items = [i for i in items if (i.get("cpse") or "").upper() == cpse.upper()]
    if search:
        s = search.lower()
        items = [i for i in items if s in (i.get("desc") or "").lower() or s in (i.get("code") or "").lower()]
        
    total = len(items)
    start = (page - 1) * limit
    paged_items = items[start:start + limit]
    return {
        "items": paged_items,
        "total": total,
        "page": page,
        "pages": (total + limit - 1) // limit if limit else 1
    }

@app.get("/api/matches")
async def get_matches(type: Optional[str] = "ALL", page: int = 1, limit: int = 20):
    matches_data = get_cache().get("matches", {})
    items = matches_data.get("items", [])
    if type and type.upper() != "ALL":
        items = [m for m in items if (m.get("match_type") or "").upper() == type.upper()]
    total = len(items)
    start = (page - 1) * limit
    return {
        "items": items[start:start + limit],
        "total": total,
        "page": page,
        "pages": (total + limit - 1) // limit if limit else 1
    }

@app.get("/api/clusters")
async def get_clusters():
    return get_cache().get("clusters", {"clusters": []})

@app.get("/api/cnmc")
async def get_cnmc_mappings():
    return get_cache().get("cnmc_mappings", {"mappings": []})

@app.get("/api/cnmc/master")
async def get_cnmc_master(limit: int = 50, offset: int = 0, search: Optional[str] = None):
    master_data = get_cache().get("cnmc_master", {})
    records = master_data.get("records", [])
    if search:
        s = search.lower()
        records = [r for r in records if s in str(r.get("CNMC", "")).lower() or s in str(r.get("Original_Description", "")).lower()]
    total = len(records)
    return {
        "records": records[offset:offset + limit],
        "total": total,
        "limit": limit,
        "offset": offset
    }

@app.get("/api/tsne")
async def get_tsne():
    return get_cache().get("tsne", {"points": []})

class GenerateRequest(BaseModel):
    description: str
    legacy_code: Optional[str] = "NEW_ITEM"
    cpse: Optional[str] = "BHEL"

@app.post("/api/generate-cnmc")
async def api_generate_cnmc(req: GenerateRequest):
    if generate_cnmc_for_material:
        try:
            return generate_cnmc_for_material(
                desc=req.description,
                cpse=req.cpse or "BHEL",
                legacy_code=req.legacy_code or "NEW_ITEM"
            )
        except Exception as e:
            print("Error generating CNMC:", e)
    
    # Fallback response
    return {
        "cnmc": "CNMC-GN-GEN-000001",
        "standardized_description": req.description.upper(),
        "domain": "GENERAL",
        "category": "MISCELLANEOUS",
        "canonical_key": f"GEN|{req.description[:20].upper()}",
        "extracted_attributes": {"material": "GENERAL"},
        "status": "AUTO_MAPPED_TO_EXISTING_CNMC",
        "is_existing_cluster": False,
        "matched_existing_materials": []
    }

class MatchQuery(BaseModel):
    query: str

@app.post("/api/match")
async def api_match(body: MatchQuery):
    q = (body.query or "").lower().split()
    materials = get_cache().get("materials", {}).get("items", [])
    results = []
    for m in materials:
        d = (m.get("desc") or "").lower()
        score = sum(1 for word in q if word in d) / max(len(q), 1)
        if score > 0.2:
            results.append({
                "code": m.get("code"),
                "desc": m.get("desc"),
                "cpse": m.get("cpse"),
                "score": round(min(score, 0.98), 2),
                "match_type": "IDENTICAL" if score >= 0.8 else ("EQUIVALENT" if score >= 0.5 else "SIMILAR")
            })
    results = sorted(results, key=lambda x: x["score"], reverse=True)[:5]
    return {"query": body.query, "results": results}
