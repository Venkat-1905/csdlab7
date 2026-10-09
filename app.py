import csv
import heapq
import math
import os

from flask import Flask, request, jsonify

app = Flask(__name__)

# ---------------------------------------------------------------------------
# Pre-load the locations data at startup
# ---------------------------------------------------------------------------
LOCATIONS = {}        # id -> (lat, lon, category)
LAT_VALS = []         # sorted list of unique latitudes
LON_VALS = []         # sorted list of unique longitudes
GRID_ROWS = 0
GRID_COLS = 0
STEP = 0.0


def load_locations():
    """Read locations.csv and build lookup structures."""
    global LOCATIONS, LAT_VALS, LON_VALS, GRID_ROWS, GRID_COLS, STEP

    csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "locations.csv")
    lat_set = set()
    lon_set = set()

    with open(csv_path, "r", newline="") as fh:
        reader = csv.reader(fh)
        next(reader)  # skip header
        for row in reader:
            loc_id = int(row[0].strip())
            lat = float(row[1].strip())
            lon = float(row[2].strip())
            cat = row[3].strip().lower()
            LOCATIONS[loc_id] = (lat, lon, cat)
            lat_set.add(lat)
            lon_set.add(lon)

    LAT_VALS = sorted(lat_set)
    LON_VALS = sorted(lon_set)
    GRID_ROWS = len(LAT_VALS)
    GRID_COLS = len(LON_VALS)
    STEP = LAT_VALS[1] - LAT_VALS[0] if GRID_ROWS > 1 else 1.0


load_locations()

# Build fast index mappings
LAT_TO_IDX = {round(v, 8): i for i, v in enumerate(LAT_VALS)}
LON_TO_IDX = {round(v, 8): i for i, v in enumerate(LON_VALS)}

# Map (lat_idx, lon_idx) -> location_id and vice versa
GRID_TO_ID = {}
ID_TO_GRID = {}
for _lid, (_la, _lo, _c) in LOCATIONS.items():
    _ri = LAT_TO_IDX[round(_la, 8)]
    _ci = LON_TO_IDX[round(_lo, 8)]
    GRID_TO_ID[(_ri, _ci)] = _lid
    ID_TO_GRID[_lid] = (_ri, _ci)

# Category index: category -> list of location ids
CAT_INDEX = {}
for _lid, (_la, _lo, _c) in LOCATIONS.items():
    CAT_INDEX.setdefault(_c, []).append(_lid)

# Pre-compute arrays for fast access
LOC_LAT = {}   # id -> lat
LOC_LON = {}   # id -> lon
for _lid, (_la, _lo, _c) in LOCATIONS.items():
    LOC_LAT[_lid] = _la
    LOC_LON[_lid] = _lo


def snap_to_grid(lat, lon):
    """Find the closest grid point indices to (lat, lon)."""
    li = round(lat / STEP) if STEP > 0 else 0
    lj = round(lon / STEP) if STEP > 0 else 0
    li = max(0, min(li, GRID_ROWS - 1))
    lj = max(0, min(lj, GRID_COLS - 1))
    return int(li), int(lj)


def euclidean_sq(lat1, lon1, lat2, lon2):
    """Squared Euclidean distance (avoids sqrt for radius comparison)."""
    return (lat1 - lat2) ** 2 + (lon1 - lon2) ** 2


def euclidean(lat1, lon1, lat2, lon2):
    """Euclidean distance on the unit grid."""
    return math.sqrt((lat1 - lat2) ** 2 + (lon1 - lon2) ** 2)


def build_graph(link_text):
    """
    Build an adjacency list from the link file content.
    Each line: "a b" meaning an undirected edge between location a and b.
    Edge weight = Euclidean distance between the two grid points.
    """
    # Pre-allocate adjacency lists
    adj = [[] for _ in range(10001)]  # index 0 unused, ids 1..10000

    for line in link_text.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) < 2:
            continue
        a = int(parts[0])
        b = int(parts[1])
        if a < 1 or a > 10000 or b < 1 or b > 10000:
            continue
        lat_a = LOC_LAT[a]
        lon_a = LOC_LON[a]
        lat_b = LOC_LAT[b]
        lon_b = LOC_LON[b]
        w = math.sqrt((lat_a - lat_b) ** 2 + (lon_a - lon_b) ** 2)
        adj[a].append((b, w))
        adj[b].append((a, w))

    return adj


def dijkstra_full(adj, source_id):
    """
    Run Dijkstra from source_id over the full graph.
    Returns dist array indexed by node id (1..10000).
    """
    INF = float("inf")
    dist = [INF] * 10001
    dist[source_id] = 0.0
    heap = [(0.0, source_id)]

    while heap:
        d, u = heapq.heappop(heap)
        if d > dist[u]:
            continue
        for v, w in adj[u]:
            nd = d + w
            if nd < dist[v]:
                dist[v] = nd
                heapq.heappush(heap, (nd, v))

    return dist


@app.route("/search/", methods=["POST", "GET"])
def search():
    """
    API endpoint for location search.
    Accepts: lat, long, cat, rad, link (file)
    Returns: JSON list of 10 closest location IDs.
    """
    # ---- Parse inputs ----
    if request.method == "POST":
        lat = float(request.form.get("lat", 0))
        lon = float(request.form.get("long", 0))
        cat = request.form.get("cat", "").strip().lower()
        rad = float(request.form.get("rad", 0))
        link_file = request.files.get("link")
    else:
        lat = float(request.args.get("lat", 0))
        lon = float(request.args.get("long", 0))
        cat = request.args.get("cat", "").strip().lower()
        rad = float(request.args.get("rad", 0))
        link_file = None

    # Read link file content
    if link_file is not None:
        link_text = link_file.read().decode("utf-8", errors="ignore")
    else:
        link_text = request.form.get("link", "")
        if not link_text:
            link_text = request.args.get("link", "")

    # ---- Step 1: Filter by category ----
    candidates = CAT_INDEX.get(cat, [])
    if not candidates:
        return jsonify({"error":
                        f"No locations found for category '{cat}'"}), 404

    # ---- Step 2: Filter by Euclidean radius ----
    rad_sq = rad * rad
    in_radius = []
    for loc_id in candidates:
        dsq = euclidean_sq(lat, lon, LOC_LAT[loc_id], LOC_LON[loc_id])
        if dsq <= rad_sq:
            in_radius.append(loc_id)

    if not in_radius:
        return jsonify({"error":
                        "No locations within the specified radius "
                        "and category"}), 404

    # ---- Step 3: Build graph from link data ----
    adj = build_graph(link_text)

    # ---- Step 4: Find the source node ----
    si, sj = snap_to_grid(lat, lon)
    source_id = GRID_TO_ID.get((si, sj))

    if source_id is None:
        # Fallback: find nearest grid node by brute force
        best_id = 1
        best_dsq = float("inf")
        for loc_id in range(1, 10001):
            dsq = euclidean_sq(lat, lon, LOC_LAT[loc_id], LOC_LON[loc_id])
            if dsq < best_dsq:
                best_dsq = dsq
                best_id = loc_id
        source_id = best_id

    # ---- Step 5: Dijkstra to find graph distances ----
    dist = dijkstra_full(adj, source_id)

    # ---- Step 6: Rank by graph distance, return top 10 ----
    INF = float("inf")
    reachable = []
    for loc_id in in_radius:
        d = dist[loc_id]
        if d < INF:
            reachable.append((d, loc_id))

    # Sort by distance, then by ID for tie-breaking
    reachable.sort(key=lambda x: (x[0], x[1]))

    top10_ids = [loc_id for _, loc_id in reachable[:10]]

    return jsonify({"recommended_locations": top10_ids})


@app.route("/", methods=["GET"])
def index():
    return jsonify({
        "status": "running",
        "endpoints": {
            "/search/": {
                "method": "POST",
                "params": "lat, long, cat, rad, link (file)",
                "description": ("Find 10 closest locations by grid distance "
                                "within radius for a given category")
            }
        }
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
