import { record, finite, nonEmpty, exactNonEmpty, withinRange, required, boundedArray } from './values';
import {
  BirthProfileApiError, type BirthPlaceCandidate, type BirthPlaceAttribution,
  type BirthPlaceSearchResult,
} from './contracts';

function parsePlace(value: unknown): BirthPlaceCandidate {
  const item = required(record(value), invalidResponse);
  const id = required(nonEmpty(item.id, 160), invalidResponse);
  const label = required(nonEmpty(item.label, 240), invalidResponse);
  const latitude = finite(item.latitude);
  const longitude = finite(item.longitude);
  const timezone = required(nonEmpty(item.timezone, 80), invalidResponse);
  if (!withinRange(latitude, -90, 90) || !withinRange(longitude, -180, 180)) throw invalidResponse();
  return { id, label, latitude, longitude, timezone };
}

const TRUSTED_ATTRIBUTION_URLS = new Set([
  'https://locationiq.com/',
  'https://www.geoapify.com/',
  'https://www.openstreetmap.org/copyright',
]);

function parseAttribution(value: unknown): BirthPlaceAttribution {
  const item = required(record(value), invalidResponse);
  const label = required(exactNonEmpty(item.label, 120), invalidResponse);
  const url = required(exactNonEmpty(item.url, 160), invalidResponse);
  if (!TRUSTED_ATTRIBUTION_URLS.has(url)) throw invalidResponse();
  return { label, url };
}

export function parsePlaceSearch(value: unknown): BirthPlaceSearchResult {
  const payload = required(record(value), invalidResponse);
  const data = required(record(payload.data), invalidResponse);
  const attribution = required(nonEmpty(data.attribution, 240), invalidResponse);
  const attributions = parseAttributions(data.attributions);
  const results = parseResults(data.results);
  return { results, attribution, attributions };
}

function parseAttributions(value: unknown): BirthPlaceAttribution[] {
  const items = required(boundedArray(value, 1, 3), invalidResponse).map(parseAttribution);
  if (new Set(items.map(({ url }) => url)).size !== items.length) throw invalidResponse();
  return items;
}

function parseResults(value: unknown): BirthPlaceCandidate[] {
  return required(boundedArray(value, 0, 5), invalidResponse).map(parsePlace);
}

function invalidResponse(): BirthProfileApiError {
  return new BirthProfileApiError('invalid-response', 'Place search returned an invalid response.');
}
