import { describe, expect, test } from 'vitest';

import {
  evaluateAllPlanetsInHouses as directAllPlanets,
  evaluateFullAspect as directFullAspect,
  evaluateWellSituated as directWellSituated,
  goldTransitionUncertainty as directTransitionUncertainty,
  navamsaRashi as directNavamsaRashi,
} from '../election-assessors/chart-geometry';
import { completePlanetPositions as directCompletePositions } from '../election-assessors/event-admission';
import { evaluateHouseFreeOfNaturalMalefics as directNaturalMalefics } from '../election-assessors/graha-nature';
import {
  completePlanetPositions,
  evaluateAllPlanetsInHouses,
  evaluateFullAspect,
  evaluateHouseFreeOfNaturalMalefics,
  evaluateWellSituated,
  goldTransitionUncertainty,
  navamsaRashi,
} from '../election-assessors/primitives';

describe('election primitive module boundaries', () => {
  test('legacy TypeScript exports remain exact compatibility aliases', () => {
    expect(evaluateAllPlanetsInHouses).toBe(directAllPlanets);
    expect(evaluateFullAspect).toBe(directFullAspect);
    expect(evaluateWellSituated).toBe(directWellSituated);
    expect(goldTransitionUncertainty).toBe(directTransitionUncertainty);
    expect(navamsaRashi).toBe(directNavamsaRashi);
    expect(completePlanetPositions).toBe(directCompletePositions);
    expect(evaluateHouseFreeOfNaturalMalefics).toBe(directNaturalMalefics);
  });
});
