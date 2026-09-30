import urllib.request
import json
import os

BASE_URL = "http://127.0.0.1:8000"

def fetch_json(endpoint):
    url = f"{BASE_URL}{endpoint}"
    print(f"Fetching {url}...")
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'VercelExporter/1.0'})
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except Exception as e:
        print(f"Error fetching {endpoint}: {e}")
        return None

def main():
    out_dir = os.path.join(os.path.dirname(__file__), "data")
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, "precomputed_samaan.json")

    export_data = {
        "stats": fetch_json("/api/stats"),
        "cnmc_stats": fetch_json("/api/cnmc/stats"),
        "materials": fetch_json("/api/materials?limit=2000"),
        "matches": fetch_json("/api/matches?limit=1000"),
        "clusters": fetch_json("/api/clusters"),
        "cnmc_mappings": fetch_json("/api/cnmc"),
        "cnmc_master": fetch_json("/api/cnmc/master?limit=2000"),
        "tsne": fetch_json("/api/tsne"),
    }

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(export_data, f, indent=2)

    size_mb = os.path.getsize(out_file) / (1024 * 1024)
    print(f"✅ Precomputed data exported successfully to {out_file} ({size_mb:.2f} MB)")

if __name__ == "__main__":
    main()
