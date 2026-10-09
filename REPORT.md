# Lab Report: Spatial Proximity & Graph Traversal Recommendation API

**System**: `stu9_sys4`  
**Host IP**: `10.1.75.51`  
**API Endpoint**: `http://10.1.75.51:3236/search/`  

---

## 1. Introduction & Objective

The objective of this assignment is to engineer a high-performance RESTful API capable of finding the 10 closest locations to a user-provided coordinate $(lat, long)$ from a 10,000-location dataset. 

The dataset is organized on a discrete $1.0 \times 1.0$ unit coordinate space arranged as a $100 \times 100$ regular grid. While the candidate search zone is constrained by a circular Euclidean radius, true proximity is governed by travel distance over a dynamic graph network representing roads or links. Straight-line distances do not accurately reflect traversability when direct road segments are missing. 

The API must:
1. Filter candidate points within a given circular search radius $r$ and matching target category $cat$.
2. Ingest per-query road linkage information provided via an uploaded text file.
3. Compute the shortest path distance across the network from the query's location.
4. Return the top 10 ranked location IDs by shortest network path distance.

---

## 2. System Architecture & Methodology

### 2.1 Dataset Exploration and Grid Snapping

The location dataset contains 10,000 entries with features `[ID, Latitude, Longitude, Category]`. An analysis of coordinate spacing reveals that:
- Latitude values range from $0.000000$ to $1.000000$ with step size $\Delta = \frac{1}{99} \approx 0.010101$.
- Longitude values follow an identical distribution.
- The 10,000 nodes form a uniform $100 \times 100$ lattice where node ID maps directly to grid indices:
  $$\text{ID} = \text{row} \times 100 + \text{col} + 1$$
  
When an arbitrary floating-point query $(lat_{query}, lon_{query})$ is received, it is snapped in $\mathcal{O}(1)$ time to the nearest grid node using uniform rounding:
$$i = \mathrm{clip}\left(\left\lfloor \frac{lat}{\Delta} + 0.5 \right\rfloor, 0, 99\right), \quad j = \mathrm{clip}\left(\left\lfloor \frac{lon}{\Delta} + 0.5 \right\rfloor, 0, 99\right)$$

### 2.2 Inverted Index for Categories & Spatial Pruning

To avoid iterating over all 10,000 entries on each request:
1. **Category Inverted Index**: During server startup, locations are partitioned into lookup lists keyed by category (`bank`, `store`, `cafe`, `hospital`, `school`, `pharmacy`, `park`, `restaurant`). There are exactly 1,250 locations per category.
2. **Radial Euclidean Pruning**: For any query with radius $r$, we filter candidate locations satisfying:
   $$(lat_k - lat_{query})^2 + (lon_k - lon_{query})^2 \le r^2$$
   By comparing squared Euclidean distances, the overhead of computing square roots is avoided during the candidate filtering pass.

### 2.3 Graph Construction from Linkage Data

Each incoming query supplies dynamic linkage data (`link` file) where each line denotes an undirected road link $u \leftrightarrow v$.
- The road network is modeled as an undirected weighted graph $G = (V, E)$, where edge weights equal the Euclidean distance between grid neighbors:
  $$w(u, v) = \sqrt{(lat_u - lat_v)^2 + (lon_u - lon_v)^2}$$
- The graph is instantiated using a contiguous array-based adjacency list of size 10,001, providing cache locality and eliminating dictionary hash lookups during traversal.

### 2.4 Shortest Path Traversal: Dijkstra's Algorithm

To compute the network traversal distance from the snapped source node $s$ to all candidates within the search radius:
- A min-heap priority queue ($O((|V| + |E|) \log |V|)$) is initialized with $(0.0, s)$.
- An array-backed distance vector `dist[1..10000]` initialized to $\infty$ tracks optimal travel costs.
- As nodes are relaxed, optimal distances are computed. Unreachable nodes retain distance $\infty$.

### 2.5 Ranking & Output Generation

Once traversal distances are determined:
1. Candidate nodes within the circular radius are associated with their computed graph distance $dist[v]$.
2. Nodes with finite distance are sorted primarily by graph distance in ascending order, with ID as a tie-breaker:
   $$\text{Sort key}: (dist[v], v)$$
3. The first 10 location IDs are extracted and formatted into the target JSON response structure:
   ```json
   {
     "recommended_locations": [id_1, id_2, ..., id_10]
   }
   ```

---

## 3. Complexity Analysis

| Stage | Algorithm / Data Structure | Time Complexity | Space Complexity |
|---|---|---|---|
| Startup Preprocessing | CSV Parsing & Hash Inverted Index | $\mathcal{O}(N)$ where $N=10000$ | $\mathcal{O}(N)$ |
| Query Snapping | Grid Index Rounding | $\mathcal{O}(1)$ | $\mathcal{O}(1)$ |
| Spatial Pruning | Category Filter + Squared Euclidean | $\mathcal{O}(N_{cat}) \approx 1250$ ops | $\mathcal{O}(N_{cat})$ |
| Graph Construction | Array Adjacency List Parsing | $\mathcal{O}(\|E\|) \approx 17000$ lines | $\mathcal{O}(\|V\| + \|E\|)$ |
| Path Traversal | Dijkstra with Min-Heap | $\mathcal{O}((\|V\| + \|E\|) \log \|V\|)$ | $\mathcal{O}(\|V\|)$ |
| Top-K Selection | QuickSort / TimSort on valid targets | $\mathcal{O}(K \log K)$ ($K \le 1250$) | $\mathcal{O}(K)$ |
| **Total Query Latency** | | **$\approx 50 - 80\text{ ms}$** | **$\approx 35\text{ MB RAM}$** |

---

## 4. API Specification & Deployment

### 4.1 Route Details

- **Route**: `POST /search/`
- **Host**: `http://10.1.75.51:3236/search/`
- **Payload Format**: `multipart/form-data`

| Parameter | Type | Description |
|---|---|---|
| `lat` | Float | Query latitude $[0.0, 1.0]$ |
| `long` | Float | Query longitude $[0.0, 1.0]$ |
| `cat` | String | Target category (e.g. `bank`, `hospital`, etc.) |
| `rad` | Float | Euclidean radius threshold |
| `link` | File | Text file containing space-separated edge pairs $(u, v)$ |

### 4.2 Deployment Architecture

1. **Remote Node**: Deployed on `stu9_sys4` (`10.1.75.51:2236`).
2. **Port Forwarding**: The Flask application binds internally to port `3000`. The container gateway forwards host port `3236` directly to container port `3000`.
3. **High-Availability Supervisor**: Managed via a persistent background watchdog loop (`run_server.sh`) ensuring continuous uptime and automatic resurrection upon process termination.

---

## 5. Verification & Test Results

The system was evaluated against multiple test queries. Example results:

### Test Case 1: Central Bank Query
- **Inputs**: `lat=0.5, long=0.5, cat=bank, rad=0.15`
- **Response Time**: `72 ms`
- **Recommended Locations**: `[4850, 4948, 5155, 5452, 5551, 4753, 5349, 4947, 5651, 5156]`

### Test Case 2: Corner Hospital Query
- **Inputs**: `lat=0.9, long=0.9, cat=hospital, rad=0.25`
- **Response Time**: `64 ms`
- **Recommended Locations**: `[8890, 8788, 8688, 8690, 8793, 8693, 8488, 8785, 8593, 8984]`

All returned candidate locations strictly conform to the required category, lie within the specified circular radius, and are sorted in ascending order of graph traversal distance.

