"""
Test the API with multiple queries to verify correctness and performance.
"""
import requests
import time
import json

BASE_URL = "http://127.0.0.1:5000"
LINK_FILE = "/home/venkat/Desktop/csdlab7/test_links.txt"

test_cases = [
    {"lat": 0.5, "long": 0.5, "cat": "bank", "rad": 0.15},
    {"lat": 0.0, "long": 0.0, "cat": "store", "rad": 0.2},
    {"lat": 1.0, "long": 1.0, "cat": "hospital", "rad": 0.3},
    {"lat": 0.25, "long": 0.75, "cat": "cafe", "rad": 0.25},
    {"lat": 0.505, "long": 0.505, "cat": "pharmacy", "rad": 0.4},
    {"lat": 0.3, "long": 0.3, "cat": "restaurant", "rad": 0.5},
    {"lat": 0.8, "long": 0.2, "cat": "school", "rad": 0.15},
    {"lat": 0.1, "long": 0.9, "cat": "park", "rad": 0.2},
]

for i, tc in enumerate(test_cases):
    start = time.time()
    with open(LINK_FILE, "rb") as f:
        resp = requests.post(
            f"{BASE_URL}/search/",
            data={
                "lat": tc["lat"],
                "long": tc["long"],
                "cat": tc["cat"],
                "rad": tc["rad"],
            },
            files={"link": ("links.txt", f, "text/plain")},
        )
    elapsed = time.time() - start

    if resp.status_code == 200:
        result = resp.json()
        locs = result.get("recommended_locations", [])
        print(f"Test {i+1}: lat={tc['lat']}, lon={tc['long']}, "
              f"cat={tc['cat']}, rad={tc['rad']}")
        print(f"  -> {len(locs)} results in {elapsed:.3f}s: {locs}")
    else:
        print(f"Test {i+1}: ERROR {resp.status_code} - {resp.text}")

print("\nAll tests completed.")

