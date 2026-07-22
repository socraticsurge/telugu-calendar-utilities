"""Product-surface catalogue for Muhurtam activities.

The calculation rules live in :mod:`activity_rules`. This module records which
of those rules the browser can evaluate from its generated feed data and how
the supported activities are grouped in the selector. Backend-only activities
remain valid MCP/Python activities; they are deliberately absent here until
the browser has the decisive inputs needed to evaluate them faithfully.
"""

BROWSER_ACTIVITY_GROUPS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ('General', ('any',)),
    ('Samskaras', (
        'wedding', 'engagement', 'naming', 'annaprasana', 'karnavedha',
        'mundana', 'upanayana', 'vidyarambha', 'seemantha',
        'gruhapravesha',
    )),
    ('Acquisitions', (
        'vehicle', 'property', 'house_purchase', 'gold', 'purchase',
    )),
    ('Construction & ventures', (
        'bhumi_puja', 'well_digging', 'home_repair', 'business', 'job',
    )),
    ('Spiritual', ('yajna', 'pilgrimage', 'ceremony')),
    ('Civil & medical', ('court', 'surgery')),
    ('Other', ('travel', 'beginning')),
)

BROWSER_ACTIVITIES: tuple[str, ...] = tuple(
    activity
    for _group, activities in BROWSER_ACTIVITY_GROUPS
    for activity in activities
)
