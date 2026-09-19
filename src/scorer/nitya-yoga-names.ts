import sharedTables from '../data/shared-calendar-tables.generated.json';

// Existing display aliases remain valid inputs; policy uses Python-owned names.
const canonicalNames = new Map(sharedTables.browserYogaNames.map(
  (name, index) => [name, sharedTables.canonicalYogaNames[index]],
));

export function canonicalYogaName(name: string): string {
  return canonicalNames.get(name) ?? name;
}

export function avoidsYoga(name: string, avoided: Set<string>): boolean {
  return [...avoided].some(candidate => canonicalYogaName(candidate) === name);
}
