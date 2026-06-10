"""Copies feeds/ and docs/index.html into public/ for GitHub Pages deployment."""
import os
import shutil

os.makedirs('public/feeds', exist_ok=True)

for f in os.listdir('feeds'):
    if f.endswith('.ics'):
        shutil.copy(os.path.join('feeds', f), os.path.join('public/feeds', f))

shutil.copy('docs/index.html', 'public/index.html')

print(f"Published {len(os.listdir('public/feeds'))} feeds.")
