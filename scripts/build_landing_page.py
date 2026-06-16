"""Copies feeds/ and docs/index.html into public/ for GitHub Pages deployment."""
import os
import shutil

os.makedirs('public/feeds', exist_ok=True)

for f in os.listdir('feeds'):
    if f.endswith('.ics'):
        shutil.copy(os.path.join('feeds', f), os.path.join('public/feeds', f))

shutil.copy('docs/index.html', 'public/index.html')
shutil.copy('docs/og-image.png', 'public/og-image.png')
# muhurta-scorer.js — sidecar loaded by index.html via <script src>.
# Must be staged alongside index.html or the muhurta finder errors
# out on every search (ReferenceError on muLagnaPosition etc.).
shutil.copy('docs/muhurta-scorer.js', 'public/muhurta-scorer.js')
# SEO static files — referenced by search engines, never by JS at
# runtime. Deploy-drift guard parametrises over both.
shutil.copy('docs/sitemap.xml', 'public/sitemap.xml')
shutil.copy('docs/robots.txt', 'public/robots.txt')

print(f"Published {len(os.listdir('public/feeds'))} feeds.")
