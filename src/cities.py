from src.models.panchangam_day import Location

CITIES: list[Location] = [
    # Telugu Heartland — AP & Telangana
    Location('Hyderabad',      lat=17.3850,  lon=78.4867,  timezone='Asia/Kolkata'),
    Location('Vijayawada',     lat=16.5062,  lon=80.6480,  timezone='Asia/Kolkata'),
    Location('Visakhapatnam',  lat=17.6868,  lon=83.2185,  timezone='Asia/Kolkata'),
    Location('Tirupati',       lat=13.6288,  lon=79.4192,  timezone='Asia/Kolkata'),
    Location('Warangal',       lat=17.9689,  lon=79.5941,  timezone='Asia/Kolkata'),
    Location('Guntur',         lat=16.3067,  lon=80.4365,  timezone='Asia/Kolkata'),
    Location('Nizamabad',      lat=18.6726,  lon=78.0942,  timezone='Asia/Kolkata'),
    Location('Rajahmundry',    lat=17.0005,  lon=81.8040,  timezone='Asia/Kolkata'),
    Location('Kurnool',        lat=15.8281,  lon=78.0373,  timezone='Asia/Kolkata'),
    Location('Nellore',        lat=14.4426,  lon=79.9865,  timezone='Asia/Kolkata'),
    # Major Indian Metros
    Location('Bengaluru',      lat=12.9716,  lon=77.5946,  timezone='Asia/Kolkata'),
    Location('Chennai',        lat=13.0827,  lon=80.2707,  timezone='Asia/Kolkata'),
    Location('Mumbai',         lat=19.0760,  lon=72.8777,  timezone='Asia/Kolkata'),
    Location('Delhi',          lat=28.6139,  lon=77.2090,  timezone='Asia/Kolkata'),
    # International Diaspora
    Location('Dallas',         lat=32.7767,  lon=-96.7970, timezone='America/Chicago'),
    Location('San Jose',       lat=37.3382,  lon=-121.8863,timezone='America/Los_Angeles'),
    Location('San Francisco',  lat=37.7749,  lon=-122.4194,timezone='America/Los_Angeles'),
    Location('Edison',         lat=40.5187,  lon=-74.4121, timezone='America/New_York'),
    Location('New York',       lat=40.7128,  lon=-74.0060, timezone='America/New_York'),
    Location('London',         lat=51.5074,  lon=-0.1278,  timezone='Europe/London'),
    Location('Sydney',         lat=-33.8688, lon=151.2093, timezone='Australia/Sydney'),
    Location('Dubai',          lat=25.2048,  lon=55.2708,  timezone='Asia/Dubai'),
]
