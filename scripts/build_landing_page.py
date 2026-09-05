"""Builds the Vite site and copies the freshly generated feeds into dist/.

Called by generate.yml after feed generation. The Vite build handles
index.html, assets, and static files (og-image, sitemap, robots).
This script's only job is to copy the feeds alongside.
"""
import os
import shutil
import subprocess

# Build the Vite site into dist/
subprocess.run(["npm", "ci", "--ignore-scripts"], check=True)
subprocess.run(["npm", "run", "build"], check=True)

# Copy generated feeds into dist/feeds/ so they land on gh-pages
os.makedirs('dist/feeds', exist_ok=True)
count = 0
for f in os.listdir('feeds'):
    if f.endswith('.ics'):
        shutil.copy(os.path.join('feeds', f), os.path.join('dist/feeds', f))
        count += 1

print(f"Published {count} feeds.")
