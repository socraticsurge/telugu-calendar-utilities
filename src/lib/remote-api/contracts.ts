import {
  type BirthChartPlanet, type BirthPada, type BirthProfileEngine, BIRTH_PROFILE_CONTRACT_VERSION,
} from '../chart-contracts';
import {
  type RemoteCalculationLocation, type RemoteCalculationLocation as ElectionChartBrowserLocation,
} from '../remote-calculation-activation';

export interface BirthPlaceCandidate {
  id: string;
  label: string;
  latitude: number;
  longitude: number;
  timezone: string;
}

export interface BirthPlaceAttribution {
  label: string;
  url: string;
}

export interface BirthPlaceSearchResult {
  results: BirthPlaceCandidate[];
  attribution: string;
  attributions: BirthPlaceAttribution[];
}

export interface BirthProfileDerivationInput {
  dateOfBirth: string;
  timeOfBirth: string;
  latitude: number;
  longitude: number;
  timezone: string;
}

export interface BirthProfileDerivation {
  contractVersion: typeof BIRTH_PROFILE_CONTRACT_VERSION;
  engine: BirthProfileEngine;
  nakshatra: string;
  pada: BirthPada;
  janmaRashi: string;
  lagna: string;
  lagnaDegree: number;
  planets: BirthChartPlanet[];
}

export type BirthProfileApiErrorCode =
  | 'disabled'
  | 'invalid-response'
  | 'network'
  | 'rate-limited'
  | 'request-failed'
  | 'timeout';

export class BirthProfileApiError extends Error {
  constructor(
    public readonly code: BirthProfileApiErrorCode,
    message: string,
    public readonly status: number | null = null,
    public readonly retryAfterSeconds: number | null = null,
  ) {
    super(message);
    this.name = 'BirthProfileApiError';
  }
}

export interface BirthProfileApiOptions {
  activationFlag?: string;
  baseUrl?: string;
  fetcher?: typeof fetch;
  locationLike?: RemoteCalculationLocation;
  timeoutMs?: number;
}

export const ELECTION_CHART_CONTRACT_VERSION = '1.0' as const;
export const ELECTION_CHART_BATCH_LIMIT = 24;
export interface ElectionChartEngine extends Omit<BirthProfileEngine, 'ephemeris'> {
  ephemeris: BirthProfileEngine['ephemeris'] | 'mixed';
  nodeConvention: 'mean';
}

export interface ElectionChartLocation {
  latitude: number;
  longitude: number;
  timezone: string;
}

export interface ElectionChartSnapshot {
  instant: string;
  lagna: { rashi: string; degree: number };
  planets: BirthChartPlanet[];
}

export interface ElectionChartDerivation {
  contractVersion: typeof ELECTION_CHART_CONTRACT_VERSION;
  engine: ElectionChartEngine;
  houseSystem: 'whole_sign';
  location: ElectionChartLocation;
  charts: ElectionChartSnapshot[];
}

export interface ElectionChartRequest {
  location: ElectionChartLocation;
  instants: string[];
}

export type ElectionChartApiErrorCode =
  | 'disabled'
  | 'invalid-request'
  | 'invalid-response'
  | 'network'
  | 'rate-limited'
  | 'request-failed'
  | 'timeout';

export class ElectionChartApiError extends Error {
  constructor(
    public readonly code: ElectionChartApiErrorCode,
    message: string,
    public readonly status: number | null = null,
    public readonly retryAfterSeconds: number | null = null,
  ) {
    super(message);
    this.name = 'ElectionChartApiError';
  }
}

export interface ElectionChartApiOptions {
  activationFlag?: string;
  baseUrl?: string;
  fetcher?: typeof fetch;
  locationLike?: ElectionChartBrowserLocation;
  timeoutMs?: number;
  signal?: AbortSignal;
}
