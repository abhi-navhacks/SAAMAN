import time
import logging
from data_loader import DataLoader
from ner_extractor import NERExtractor
from matching_engine import MatchingEngine
from graph_clusterer import GraphClusterer
from app import db, app
import uvicorn
import os


from cnmc_generator import (
    load_registry, save_registry, normalize_text, extract_category,
    extract_attributes as cnmc_extract_attrs, generate_canonical_key,
    generate_standardized_description, assign_cnmc
)


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def run_pipeline():
    pipeline_start = time.time()
    logger.info("=" * 60)
    logger.info("  MaterialNet Pipeline — Starting...")
    logger.info("=" * 60)

    # ── Step 1: Load Data ────────────────────────────────────────
    t = time.time()
    bhel_path = r"C:\Users\bit\Downloads\bhel_material_codes_descriptions_868_clean (1).csv"
    cpse_path = r"C:\Users\bit\Downloads\cpse_150_verified_material_codes.csv"
    multi_path = r"C:\Users\bit\Downloads\cpse_multi_sector_distinct_materials.csv"

    dl = DataLoader(bhel_path, cpse_path, multi_path)
    df = dl.load_data()
    records = df.to_dict('records')
    logger.info(f"✅ Step 1: Data loaded — {len(records)} materials in {time.time()-t:.1f}s")

    # ── Step 2: NER Extraction ──────────────────────────────────
    t = time.time()
    ner = NERExtractor()
    for r in records:
        r['attributes'] = ner.extract(r['cleaned_description'])
    
    # Stats on extracted attributes
    type_counts = {}
    for r in records:
        mt = r['attributes'].get('material_type', 'unknown')
        type_counts[mt] = type_counts.get(mt, 0) + 1
    logger.info(f"✅ Step 2: NER extraction done in {time.time()-t:.1f}s")
    logger.info(f"   Material types found: {dict(sorted(type_counts.items(), key=lambda x: -x[1]))}")

    # ── Step 3: Build Index & Compute Embeddings ────────────────
    t = time.time()
    matcher = MatchingEngine()
    matcher.build_index(records)
    logger.info(f"✅ Step 3: Embeddings computed & LSH index built in {time.time()-t:.1f}s")

    # ── Step 4: Run Matching Pipeline ───────────────────────────
    t = time.time()
    matches = matcher.run_all_matches()
    
    match_type_counts = {}
    for m in matches:
        mt = m.get('match_type', 'UNKNOWN')
        match_type_counts[mt] = match_type_counts.get(mt, 0) + 1
    logger.info(f"✅ Step 4: Matching done — {len(matches)} matches in {time.time()-t:.1f}s")
    logger.info(f"   Match types: {match_type_counts}")

    # ── Step 5: Graph Clustering ────────────────────────────────
    t = time.time()
    clusterer = GraphClusterer()
    clusters = clusterer.build_clusters(records, matches)
    
    multi_cpse = sum(1 for c in clusters if len(set(m.get('cpse','') for m in c['members'])) > 1)
    logger.info(f"✅ Step 5: Clustering done — {len(clusters)} clusters in {time.time()-t:.1f}s")
    logger.info(f"   Cross-CPSE clusters: {multi_cpse}")

    # ── Step 6: CNMC Code Generation (SAMAAN Engine) ───────────
    t = time.time()
    registry_data = load_registry()
    cnmc_map = {}
    for r in records:
        desc = r.get('material_description', '')
        norm = normalize_text(desc)
        dom, cat, name = extract_category(norm)
        attrs = cnmc_extract_attrs(norm, name)
        canonical_key = generate_canonical_key(dom, cat, attrs)
        code, _ = assign_cnmc(canonical_key, dom, cat, registry_data)
        r['cnmc'] = code
        r['standardized_description'] = generate_standardized_description(name, attrs)
        r['domain'] = dom
        r['category'] = name
        cnmc_map[r['internal_id']] = code
    save_registry(registry_data)
    logger.info(f"✅ Step 6: CNMC codes generated in {time.time()-t:.1f}s")

    # ── Populate In-Memory DB ──────────────────────────────────
    for r in records:
        db['materials'][r['internal_id']] = r

    db['matches'] = matches
    db['cnmc'] = cnmc_map
    db['matching_engine'] = matcher

    for c in clusters:
        db['clusters'][c['cluster_id']] = c

    # ── Step 7: t-SNE Visualization ─────────────────────────────
    t = time.time()
    logger.info("Computing t-SNE coordinates for visualization...")
    import numpy as np
    from sklearn.manifold import TSNE
    
    ids = list(matcher.embeddings.keys())
    if len(ids) > 0:
        X = np.array([matcher.embeddings[i] for i in ids])
        tsne = TSNE(n_components=2, random_state=42, perplexity=30)
        X_2d = tsne.fit_transform(X)
        
        db['tsne'] = []
        for idx, mid in enumerate(ids):
            r = db['materials'][mid]
            c_id = next((c['cluster_id'] for c in clusters if any(m['internal_id'] == mid for m in c['members'])), None)
            db['tsne'].append({
                'id': mid,
                'x': float(X_2d[idx, 0]),
                'y': float(X_2d[idx, 1]),
                'desc': str(r.get('material_description', '')),
                'code': str(r.get('material_code', '')),
                'cpse': str(r.get('cpse', '')),
                'category': str(r.get('attributes', {}).get('material_type', 'misc').upper()),
                'cluster': c_id
            })
        logger.info(f"✅ Step 7: t-SNE coordinates computed in {time.time()-t:.1f}s")
    else:
        db['tsne'] = []

    # ── Summary ────────────────────────────────────────────────
    logger.info("=" * 60)
    logger.info(f"  Pipeline completed in {time.time()-pipeline_start:.1f}s")
    logger.info(f"  📦 Total Materials:  {len(records)}")
    logger.info(f"  🔗 Total Matches:    {len(matches)}")
    logger.info(f"  🧩 Total Clusters:   {len(clusters)}")
    logger.info(f"  🏷️  CNMC Codes:       {len(cnmc_map)}")
    
    cpse_counts = {}
    for r in records:
        c = r.get('cpse', 'UNKNOWN')
        cpse_counts[c] = cpse_counts.get(c, 0) + 1
    logger.info(f"  🏭 Per CPSE: {cpse_counts}")
    logger.info("=" * 60)


if __name__ == "__main__":
    logger.info("🚀 SAMAAN — National Unified Material Master Platform")
    logger.info("   One Nation, One Material Code | Smart India Hackathon 2026")
    logger.info("")

    run_pipeline()

    logger.info("")
    logger.info("🌐 SAMAAN Dashboard: http://localhost:8000")
    logger.info("📚 API Docs:         http://localhost:8000/docs")
    logger.info("")

    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="warning")
