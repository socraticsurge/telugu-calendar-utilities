from telugu_panchangam.models.panchangam_day import Location

_INDIA_TIMEZONE = 'Asia/Kolkata'

CITIES: list[Location] = [
    # Telugu Heartland — AP & Telangana
    Location('Hyderabad',      lat=17.3850,  lon=78.4867,  timezone=_INDIA_TIMEZONE,           alt=531),
    Location('Vijayawada',     lat=16.5062,  lon=80.6480,  timezone=_INDIA_TIMEZONE,           alt=27),
    Location('Visakhapatnam',  lat=17.6868,  lon=83.2185,  timezone=_INDIA_TIMEZONE,           alt=45),
    Location('Tirupati',       lat=13.6288,  lon=79.4192,  timezone=_INDIA_TIMEZONE,           alt=183),
    Location('Warangal',       lat=17.9689,  lon=79.5941,  timezone=_INDIA_TIMEZONE,           alt=304),
    Location('Guntur',         lat=16.3067,  lon=80.4365,  timezone=_INDIA_TIMEZONE,           alt=30),
    Location('Nizamabad',      lat=18.6726,  lon=78.0942,  timezone=_INDIA_TIMEZONE,           alt=396),
    Location('Rajahmundry',    lat=17.0005,  lon=81.8040,  timezone=_INDIA_TIMEZONE,           alt=7),
    Location('Kurnool',        lat=15.8281,  lon=78.0373,  timezone=_INDIA_TIMEZONE,           alt=268),
    Location('Nellore',        lat=14.4426,  lon=79.9865,  timezone=_INDIA_TIMEZONE,           alt=22),
    # Major Indian Metros
    Location('Bengaluru',      lat=12.9716,  lon=77.5946,  timezone=_INDIA_TIMEZONE,           alt=920),
    Location('Chennai',        lat=13.0827,  lon=80.2707,  timezone=_INDIA_TIMEZONE,           alt=6),
    Location('Mumbai',         lat=19.0760,  lon=72.8777,  timezone=_INDIA_TIMEZONE,           alt=11),
    Location('Delhi',          lat=28.6139,  lon=77.2090,  timezone=_INDIA_TIMEZONE,           alt=216),
    # International Diaspora
    Location('Dallas',         lat=32.7767,  lon=-96.7970, timezone='America/Chicago',        alt=141),
    Location('San Jose',       lat=37.3382,  lon=-121.8863,timezone='America/Los_Angeles',    alt=26),
    Location('San Francisco',  lat=37.7749,  lon=-122.4194,timezone='America/Los_Angeles',    alt=16),
    Location('Edison',         lat=40.5187,  lon=-74.4121, timezone='America/New_York',       alt=20),
    Location('New York',       lat=40.7128,  lon=-74.0060, timezone='America/New_York',       alt=10),
    Location('London',         lat=51.5074,  lon=-0.1278,  timezone='Europe/London',          alt=11),
    Location('Sydney',         lat=-33.8688, lon=151.2093, timezone='Australia/Sydney',       alt=58),
    Location('Dubai',          lat=25.2048,  lon=55.2708,  timezone='Asia/Dubai',             alt=5),
]
