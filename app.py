import os
import json
import logging
from typing import List, Optional
from pathlib import Path

import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# --- System B Imports ---
from samaan_engine import score_pair, extract_attributes
from cnmc_generator import generate_cnmc_for_material, OUTPUT_FILE, CLUSTERS_FILE, REGISTRY_FILE

app = FastAPI(title="SAMAAN — National Unified Material Master Platform | One Nation, One Material Code")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory store — populated by startup.py
db = {
    'materials': {},       # internal_id -> record dict
    'matches': [],         # list of match dicts
    'clusters': {},        # cluster_id -> cluster dict
    'cnmc': {},            # internal_id -> cnmc_code
    'matching_engine': None  # reference to MatchingEngine for live matching
}


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the SAMAAN dashboard HTML."""
    base_dir = os.path.dirname(__file__)
    for filename in ["index.html", "dashboard.html"]:
        html_path = os.path.join(base_dir, "templates", filename)
        if os.path.exists(html_path):
            with open(html_path, "r", encoding="utf-8") as f:
                return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>SAMAAN</h1><p>Dashboard not found. Visit <a href='/docs'>/docs</a></p>")


@app.get("/api/stats")
async def get_stats():
    materials = list(db['materials'].values())
    matches = db['matches']
    clusters = db['clusters']

    cpses = set(m.get('cpse') for m in materials if m.get('cpse'))
    cpse_breakdown = {c: len([m for m in materials if m.get('cpse') == c]) for c in cpses}

    match_types = {}
    for m in matches:
        mt = m.get('match_type', 'UNKNOWN')
        match_types[mt] = match_types.get(mt, 0) + 1

    total_matches = len(matches)
    identical = match_types.get('IDENTICAL', 0)
    auto_pct = round((identical / total_matches * 100) if total_matches > 0 else 0)

    return {
        "total_materials": len(materials),
        "total_matches": total_matches,
        "total_clusters": len(clusters),
        "duplicates_found": total_matches,
        "cpse_breakdown": cpse_breakdown,
        "match_type_breakdown": match_types,
        "auto_approved_pct": auto_pct
    }


@app.get("/api/materials")
async def get_materials(page: int = 1, size: int = 20, cpse: Optional[str] = None):
    materials = list(db['materials'].values())
    if cpse:
        materials = [m for m in materials if m.get('cpse') == cpse]

    total = len(materials)
    pages = max(1, (total + size - 1) // size)
    start = (page - 1) * size
    end = start + size

    items = []
    for m in materials[start:end]:
        # Count matches for this material
        mid = m.get('internal_id', '')
        match_count = sum(1 for mt in db['matches']
                          if mt.get('source_id') == mid or mt.get('target_id') == mid)
        items.append({
            "internal_id": mid,
            "cpse": m.get('cpse', ''),
            "code": str(m.get('material_code', '')),
            "desc": m.get('material_description', ''),
            "cleaned_desc": m.get('cleaned_description', ''),
            "category": m.get('attributes', {}).get('material_type', 'MISC').upper(),
            "attributes": m.get('attributes', {}),
            "cnmc": m.get('cnmc', ''),
            "match_count": match_count
        })

    return {"items": items, "total": total, "page": page, "pages": pages}


@app.get("/api/materials/{id}")
async def get_material(id: str):
    if id not in db['materials']:
        raise HTTPException(status_code=404, detail="Material not found")
    m = db['materials'][id]
    return {
        "internal_id": id,
        "cpse": m.get('cpse', ''),
        "code": str(m.get('material_code', '')),
        "desc": m.get('material_description', ''),
        "attributes": m.get('attributes', {}),
        "cnmc": m.get('cnmc', '')
    }


@app.get("/api/matches")
async def get_matches(type: Optional[str] = None, page: int = 1, limit: int = 10):
    matches = db['matches']
    if type:
        matches = [m for m in matches if m.get('match_type') == type]

    total = len(matches)
    start = (page - 1) * limit
    end = start + limit

    items = []
    for m in matches[start:end]:
        src = db['materials'].get(m['source_id'], {})
        tgt = db['materials'].get(m['target_id'], {})
        items.append({
            "match_id": f"{m['source_id'][:8]}_{m['target_id'][:8]}",
            "material_a": {
                "code": str(src.get('material_code', '')),
                "desc": src.get('material_description', ''),
                "cpse": src.get('cpse', '')
            },
            "material_b": {
                "code": str(tgt.get('material_code', '')),
                "desc": tgt.get('material_description', ''),
                "cpse": tgt.get('cpse', '')
            },
            "score": round(m.get('combined_score', 0) * 100, 1),
            "semantic_score": round(m.get('semantic_score', 0) * 100, 1),
            "attribute_score": round(m.get('attribute_score', 0) * 100, 1),
            "match_type": m.get('match_type', 'UNKNOWN'),
            "explanation": _generate_explanation(m, src, tgt)
        })

    return {"items": items, "total": total}


def _generate_explanation(match: dict, src: dict, tgt: dict) -> str:
    """Generate a human-readable explanation for a match."""
    reasons = []
    src_attr = src.get('attributes', {})
    tgt_attr = tgt.get('attributes', {})

    if src_attr.get('material_type') and src_attr.get('material_type') == tgt_attr.get('material_type'):
        reasons.append(f"Same material type: {src_attr['material_type']}")
    if src_attr.get('connector_type') and src_attr.get('connector_type') == tgt_attr.get('connector_type'):
        reasons.append(f"Same connector type: {src_attr['connector_type']}")
    if src_attr.get('pin_count') and src_attr.get('pin_count') == tgt_attr.get('pin_count'):
        reasons.append(f"Same pin count: {src_attr['pin_count']}")
    if src_attr.get('standard') and src_attr.get('standard') == tgt_attr.get('standard'):
        reasons.append(f"Same standard: {src_attr['standard']}")
    if src_attr.get('voltage_rating') and src_attr.get('voltage_rating') == tgt_attr.get('voltage_rating'):
        reasons.append(f"Same voltage: {src_attr['voltage_rating']}")
    if src_attr.get('dimensions') and tgt_attr.get('dimensions'):
        shared = set(src_attr['dimensions']) & set(tgt_attr['dimensions'])
        if shared:
            reasons.append(f"Shared dimensions: {', '.join(shared)}")

    sem = round(match.get('semantic_score', 0) * 100, 1)
    reasons.append(f"Semantic similarity: {sem}%")

    return "; ".join(reasons) if reasons else "Matched by semantic similarity"


@app.get("/api/matches/{material_id}")
async def get_matches_for_material(material_id: str):
    matches = [m for m in db['matches']
               if m['source_id'] == material_id or m['target_id'] == material_id]
    return {"matches": matches}


@app.get("/api/clusters")
async def get_clusters():
    clusters_list = list(db['clusters'].values())
    result = []
    for c in clusters_list:
        members = c.get('members', [])
        cpses_in_cluster = list(set(m.get('cpse', '') for m in members if m.get('cpse')))
        # Get CNMC code from first member
        first_id = members[0]['internal_id'] if members else ''
        cnmc_code = db['cnmc'].get(first_id, c.get('cluster_id', ''))

        result.append({
            "cluster_id": c.get('cluster_id', ''),
            "cnmc_code": cnmc_code,
            "category": db['materials'].get(first_id, {}).get('attributes', {}).get('material_type', 'MISC').upper(),
            "member_count": c.get('size', len(members)),
            "golden_description": c.get('golden_description', ''),
            "members": [
                {"cpse": m.get('cpse', ''), "code": str(m.get('material_code', '')), "desc": m.get('description', '')}
                for m in members
            ],
            "cpses": cpses_in_cluster
        })

    return {"clusters": result}


@app.get("/api/clusters/{cluster_id}")
async def get_cluster(cluster_id: str):
    if cluster_id not in db['clusters']:
        raise HTTPException(status_code=404, detail="Cluster not found")
    return db['clusters'][cluster_id]


@app.get("/api/cnmc")
async def get_cnmc():
    clusters = list(db['clusters'].values())
    mappings = []
    for c in clusters:
        members = c.get('members', [])
        if not members:
            continue
        first_id = members[0]['internal_id']
        cnmc_code = db['cnmc'].get(first_id, '')
        category = db['materials'].get(first_id, {}).get('attributes', {}).get('material_type', 'MISC').upper()

        cpse_codes = {}
        for m in members:
            cpse = m.get('cpse', '')
            if cpse:
                cpse_codes[cpse] = str(m.get('material_code', ''))

        mappings.append({
            "cnmc_code": cnmc_code,
            "category": category,
            "material_desc": c.get('golden_description', ''),
            "cpse_codes": cpse_codes
        })

    return {"mappings": mappings}


@app.get("/api/tsne")
async def get_tsne():
    return {"points": db.get('tsne', [])}


class MatchRequest(BaseModel):
    description: str = None
    query: str = None


@app.post("/api/match")
async def run_match(req: MatchRequest):
    query = req.description or req.query or ""
    if not query:
        raise HTTPException(status_code=400, detail="No description/query provided")

    engine = db.get('matching_engine')
    if engine is None:
        # Fallback: simple text search
        materials = list(db['materials'].values())
        query_lower = query.lower()
        scored = []
        for m in materials:
            desc = m.get('cleaned_description', '')
            # Simple word overlap score
            query_words = set(query_lower.split())
            desc_words = set(desc.split())
            overlap = len(query_words & desc_words)
            if overlap > 0:
                score = overlap / max(len(query_words), 1) * 100
                scored.append((m, score))
        scored.sort(key=lambda x: x[1], reverse=True)
        results = []
        for m, score in scored[:5]:
            results.append({
                "code": str(m.get('material_code', '')),
                "desc": m.get('material_description', ''),
                "cpse": m.get('cpse', ''),
                "score": round(score, 1),
                "match_type": "IDENTICAL" if score >= 85 else "EQUIVALENT" if score >= 70 else "SIMILAR"
            })
        return {"query": query, "results": results}

    # Use actual matching engine
    from ner_extractor import NERExtractor
    ner = NERExtractor()
    attrs = ner.extract(query.lower())

    query_emb = engine.model.encode([query.lower()])
    from sklearn.metrics.pairwise import cosine_similarity
    import numpy as np

    scores = []
    for mid, emb in engine.embeddings.items():
        sim = cosine_similarity(query_emb, emb.reshape(1, -1))[0][0]
        m = db['materials'].get(mid, {})
        attr_score = engine._attribute_score(attrs, m.get('attributes', {}))
        combined = 0.4 * sim + 0.6 * attr_score
        scores.append((mid, combined, sim))

    scores.sort(key=lambda x: x[1], reverse=True)
    results = []
    for mid, combined, sem in scores[:5]:
        m = db['materials'].get(mid, {})
        score_pct = float(round(float(combined) * 100, 1))
        results.append({
            "code": str(m.get('material_code', '')),
            "desc": str(m.get('material_description', '')),
            "cpse": str(m.get('cpse', '')),
            "score": score_pct,
            "match_type": "IDENTICAL" if score_pct >= 85 else "EQUIVALENT" if score_pct >= 70 else "SIMILAR"
        })

    return {"query": query, "results": results}


@app.post("/api/validate/{match_id}")
async def validate_match(match_id: str, action: str = Query(..., pattern="^(approve|reject)$")):
    return {"status": f"Match {match_id} {action}d.", "match_id": match_id, "action": action}


# ----------------------------------------------------------------------
# SYSTEM B - ADVANCED CNMC ENDPOINTS
# ----------------------------------------------------------------------
class CNMCPayload(BaseModel):
    description: str
    cpse: Optional[str] = "CPSE_ENTERPRISE"
    legacy_code: Optional[str] = "NEW_ITEM"
    save_to_master: Optional[bool] = False

@app.post("/api/generate-cnmc")
def api_generate_cnmc(payload: CNMCPayload):
    return generate_cnmc_for_material(
        description=payload.description,
        cpse=payload.cpse,
        legacy_code=payload.legacy_code,
        save_to_master=payload.save_to_master,
    )

@app.get("/api/cnmc/stats")
def api_cnmc_stats():
    if not OUTPUT_FILE.exists():
        return {"total_records": 0, "unique_cnmc": 0, "clusters": 0, "merged_items": 0}

    df = pd.read_csv(OUTPUT_FILE)
    clusters_df = pd.read_csv(CLUSTERS_FILE) if CLUSTERS_FILE.exists() else pd.DataFrame()
    cnmc_counts = df["CNMC"].value_counts()
    multi = cnmc_counts[cnmc_counts > 1]

    return {
        "total_records": int(len(df)),
        "unique_cnmc": int(df["CNMC"].nunique()),
        "multi_material_clusters": int(len(multi)),
        "deduplicated_materials": int(len(clusters_df)),
        "domains": df["Domain"].value_counts().to_dict(),
        "top_categories": df["Category"].value_counts().head(8).to_dict(),
    }

@app.get("/api/cnmc/master")
def api_cnmc_master(
    search: Optional[str] = None,
    category: Optional[str] = None,
    domain: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
):
    if not OUTPUT_FILE.exists():
        return {"total": 0, "data": []}

    df = pd.read_csv(OUTPUT_FILE)
    if search:
        s = search.upper()
        mask = (
            df["CNMC"].str.contains(s, na=False)
            | df["Legacy_Material_Code"].str.contains(s, na=False)
            | df["Original_Description"].str.contains(s, na=False)
            | df["Standardized_National_Description"].str.contains(s, na=False)
        )
        df = df[mask]
    if category:
        df = df[df["Category"] == category]
    if domain:
        df = df[df["Domain"] == domain]

    total = len(df)
    page_data = df.iloc[offset : offset + limit].fillna("").to_dict(orient="records")
    return {"total": total, "offset": offset, "limit": limit, "data": page_data}

@app.get("/api/cnmc/clusters")
def api_cnmc_clusters(limit: int = 20):
    if not CLUSTERS_FILE.exists():
        return []
    df = pd.read_csv(CLUSTERS_FILE)
    grouped = []
    for cnmc, grp in df.groupby("CNMC"):
        grouped.append({
            "cnmc": cnmc,
            "category": grp["Category"].iloc[0],
            "standardized_description": grp["Standardized_National_Description"].iloc[0],
            "count": len(grp),
            "materials": grp[["CPSE", "Legacy_Material_Code", "Original_Description"]].to_dict(orient="records"),
        })
    grouped.sort(key=lambda x: -x["count"])
    return grouped[:limit]

class ComparePayload(BaseModel):
    desc_a: str
    desc_b: str

@app.post("/api/compare")
def compare(payload: ComparePayload):
    return score_pair(payload.desc_a, payload.desc_b)

class ExtractPayload(BaseModel):
    description: str

@app.post("/api/extract")
def extract(payload: ExtractPayload):
    attrs = extract_attributes(payload.description)
    return {k: (list(v) if isinstance(v, set) else v) for k, v in attrs.items()}
