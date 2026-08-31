// Display grouping for the city selector. JS-only metadata: the
// engine's authoritative city table lives in telugu_panchangam/cities.py.

export const CITY_GROUPS: Array<[string, string[]]> = [
  ['Telugu Heartland', ['Hyderabad', 'Vijayawada', 'Visakhapatnam', 'Tirupati', 'Warangal', 'Guntur', 'Nizamabad', 'Rajahmundry', 'Kurnool', 'Nellore']],
  ['Major Indian Metros', ['Bengaluru', 'Chennai', 'Mumbai', 'Delhi']],
  ['International', ['Dallas', 'San Jose', 'San Francisco', 'Edison', 'New York', 'London', 'Sydney', 'Dubai']],
];

export interface CityLocation {
  latitude: number;
  longitude: number;
  timezone: string;
}

// Browser projection of telugu_panchangam.cities.CITIES. Exact coordinates
// are needed only for privacy-minimal election-chart requests; no participant
// or activity data accompanies them.
export const CITY_LOCATIONS: Readonly<Record<string, CityLocation>> = {
  Hyderabad: { latitude: 17.3850, longitude: 78.4867, timezone: 'Asia/Kolkata' },
  Vijayawada: { latitude: 16.5062, longitude: 80.6480, timezone: 'Asia/Kolkata' },
  Visakhapatnam: { latitude: 17.6868, longitude: 83.2185, timezone: 'Asia/Kolkata' },
  Tirupati: { latitude: 13.6288, longitude: 79.4192, timezone: 'Asia/Kolkata' },
  Warangal: { latitude: 17.9689, longitude: 79.5941, timezone: 'Asia/Kolkata' },
  Guntur: { latitude: 16.3067, longitude: 80.4365, timezone: 'Asia/Kolkata' },
  Nizamabad: { latitude: 18.6726, longitude: 78.0942, timezone: 'Asia/Kolkata' },
  Rajahmundry: { latitude: 17.0005, longitude: 81.8040, timezone: 'Asia/Kolkata' },
  Kurnool: { latitude: 15.8281, longitude: 78.0373, timezone: 'Asia/Kolkata' },
  Nellore: { latitude: 14.4426, longitude: 79.9865, timezone: 'Asia/Kolkata' },
  Bengaluru: { latitude: 12.9716, longitude: 77.5946, timezone: 'Asia/Kolkata' },
  Chennai: { latitude: 13.0827, longitude: 80.2707, timezone: 'Asia/Kolkata' },
  Mumbai: { latitude: 19.0760, longitude: 72.8777, timezone: 'Asia/Kolkata' },
  Delhi: { latitude: 28.6139, longitude: 77.2090, timezone: 'Asia/Kolkata' },
  Dallas: { latitude: 32.7767, longitude: -96.7970, timezone: 'America/Chicago' },
  'San Jose': { latitude: 37.3382, longitude: -121.8863, timezone: 'America/Los_Angeles' },
  'San Francisco': { latitude: 37.7749, longitude: -122.4194, timezone: 'America/Los_Angeles' },
  Edison: { latitude: 40.5187, longitude: -74.4121, timezone: 'America/New_York' },
  'New York': { latitude: 40.7128, longitude: -74.0060, timezone: 'America/New_York' },
  London: { latitude: 51.5074, longitude: -0.1278, timezone: 'Europe/London' },
  Sydney: { latitude: -33.8688, longitude: 151.2093, timezone: 'Australia/Sydney' },
  Dubai: { latitude: 25.2048, longitude: 55.2708, timezone: 'Asia/Dubai' },
};
