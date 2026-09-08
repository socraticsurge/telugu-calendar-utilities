import { RASI_NAMES } from '../../data/rasis';
import type { ElectionChartSnapshot } from '../../lib/election-chart-api';
import type { PlanetPosition } from './contracts';

export function completePlanetPositions(
  chart: ElectionChartSnapshot,
  expectedPlanets: ReadonlySet<string>,
): ReadonlyMap<string, PlanetPosition> | null {
  if (chart.planets.length !== expectedPlanets.size) return null;
  const result = new Map<string, PlanetPosition>();
  for (const planet of chart.planets) {
    if (
      !expectedPlanets.has(planet.name) || result.has(planet.name)
      || !RASI_NAMES.includes(planet.rashi)
      || !Number.isFinite(planet.degree) || planet.degree < 0 || planet.degree >= 30
      || !Number.isInteger(planet.house) || planet.house < 1 || planet.house > 12
      || typeof planet.retrograde !== 'boolean'
    ) return null;
    result.set(planet.name, { ...planet });
  }
  return result.size === expectedPlanets.size ? result : null;
}
