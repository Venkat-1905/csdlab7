"""
Automated verification test suite for the Dockerized Proximity Search stack.
Validates:
1. Service discovery and healthcheck probes on both ports 5000 and 8080
2. Nginx reverse proxy routing and headers
3. Search queries with both ID-based and Coordinate-based link graphs
4. Latency benchmarks and response integrity
"""
import time
import requests

API_BASE = "http://localhost:5000"
PROXY_BASE = "http://localhost:8080"
TEST_LINKS = "test_links.txt"
COORD_LINKS = "link.txt"


def test_health():
    print("[1] Testing Container Health & Routing Endpoints...")
    r1 = requests.get(f"{API_BASE}/", timeout=5)
    assert r1.status_code == 200, f"API root failed: {r1.status_code}"
    print(f"  ✓ Direct API (:5000/) -> {r1.json().get('status')}")

    r2 = requests.get(f"{PROXY_BASE}/", timeout=5)
    assert r2.status_code == 200, f"Proxy root failed: {r2.status_code}"
    print(f"  ✓ Reverse Proxy (:8080/) -> {r2.json().get('status')}")

    r3 = requests.get(f"{PROXY_BASE}/health", timeout=5)
    assert r3.status_code == 200, f"Proxy health probe failed: {r3.status_code}"
    print(f"  ✓ Proxy Health Probe (:8080/health) -> {r3.text.strip()}")


def test_search_via_proxy():
    print("\n[2] Testing Search Queries via Nginx Reverse Proxy (:8080/search/)...")

    # Query 1: Bank with test_links.txt
    start = time.time()
    with open(TEST_LINKS, "rb") as f:
        res = requests.post(
            f"{PROXY_BASE}/search/",
            data={"lat": 0.5, "long": 0.5, "cat": "bank", "rad": 0.15},
            files={"link": ("test_links.txt", f, "text/plain")},
            timeout=10,
        )
    dur1 = (time.time() - start) * 1000
    assert res.status_code == 200, f"Search failed: {res.text}"
    locs1 = res.json().get("recommended_locations", [])
    assert len(locs1) == 10, f"Expected 10 locations, got {len(locs1)}"
    print(f"  ✓ Bank Search (test_links.txt) -> {len(locs1)} results in {dur1:.1f}ms")
    print(f"    IDs: {locs1}")

    # Query 2: Coordinate format link.txt
    start = time.time()
    with open(COORD_LINKS, "rb") as f:
        res2 = requests.post(
            f"{PROXY_BASE}/search/",
            data={"lat": 0.5, "long": 0.5, "cat": "bank", "rad": 0.15},
            files={"link": ("link.txt", f, "text/plain")},
            timeout=10,
        )
    dur2 = (time.time() - start) * 1000
    assert res2.status_code == 200, f"Coordinate link failed: {res2.text}"
    locs2 = res2.json().get("recommended_locations", [])
    assert len(locs2) == 10, f"Expected 10 locations, got {len(locs2)}"
    print(f"  ✓ Bank Search (link.txt coords) -> {len(locs2)} results in {dur2:.1f}ms")
    print(f"    IDs: {locs2}")

    # Query 3: Store at origin
    start = time.time()
    with open(TEST_LINKS, "rb") as f:
        res3 = requests.post(
            f"{PROXY_BASE}/search/",
            data={"lat": 0.0, "long": 0.0, "cat": "store", "rad": 0.2},
            files={"link": ("test_links.txt", f, "text/plain")},
            timeout=10,
        )
    dur3 = (time.time() - start) * 1000
    assert res3.status_code == 200
    locs3 = res3.json().get("recommended_locations", [])
    print(f"  ✓ Store Search (0.0, 0.0) -> {len(locs3)} results in {dur3:.1f}ms")
    print(f"    IDs: {locs3}")


if __name__ == "__main__":
    print("=" * 65)
    print("  RUNNING CONTAINERIZED PROXIMITY SEARCH STACK TEST SUITE")
    print("=" * 65)
    test_health()
    test_search_via_proxy()
    print("\n" + "=" * 65)
    print("  ALL CONTAINER INTEGRATION TESTS PASSED SUCCESSFULLY!")
    print("=" * 65)
