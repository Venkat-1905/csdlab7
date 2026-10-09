"""
Generate a sample link file for testing.
Creates a grid with most adjacent links present but some missing (simulating a road network).
"""
import random
import os

random.seed(42)
ROWS = 100
COLS = 100

links = []
for i in range(ROWS):
    for j in range(COLS):
        node_id = i * COLS + j + 1
        # Right neighbor
        if j + 1 < COLS:
            right_id = i * COLS + (j + 1) + 1
            # Keep ~85% of horizontal links
            if random.random() < 0.85:
                links.append(f"{node_id} {right_id}")
        # Down neighbor
        if i + 1 < ROWS:
            down_id = (i + 1) * COLS + j + 1
            # Keep ~85% of vertical links
            if random.random() < 0.85:
                links.append(f"{node_id} {down_id}")

out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_links.txt")
with open(out_path, "w") as fh:
    fh.write("\n".join(links))

print(f"Generated {len(links)} links to {out_path}")

