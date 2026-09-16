/** Browser-side Tara/Chandra rules, independent of presentation and storage. */
import { RASI_NAMES, NAKSHATRA_NAMES } from '../data/rasis';

const TARA_NAMES = ['Janma', 'Sampat', 'Vipat', 'Kshema', 'Pratyak', 'Sadhana', 'Naidhana', 'Mitra', 'Parama Mitra'];
const TARA_GOOD = new Set([2, 4, 6, 8, 9]);
const CHANDRA_GOOD = new Set([1, 3, 6, 7, 10, 11]);
const CHANDRA_PUJA = new Set([2, 5, 9]);
type ChandraVerdict = 'good' | 'puja' | 'bad';

function nameIndex(names: readonly string[], name: unknown): number {
  return typeof name === 'string' ? names.indexOf(name) : -1;
}

export function tbTaraOf(janmaName: unknown, dayName: unknown): number | null {
  const j = nameIndex(NAKSHATRA_NAMES, janmaName), d = nameIndex(NAKSHATRA_NAMES, dayName);
  if (j < 0 || d < 0) return null;
  return ((d - j + 27) % 27) % 9 + 1;
}

export function tbTaraIsGood(tara: number): boolean {
  return TARA_GOOD.has(tara);
}

export function tbTaraLabel(tara: number): string | undefined {
  return TARA_NAMES[tara - 1];
}

export function tbChandraVerdict(pos: number): ChandraVerdict {
  if (CHANDRA_GOOD.has(pos)) return 'good';
  if (CHANDRA_PUJA.has(pos)) return 'puja';
  return 'bad';
}

export function tbChandraOf(
  janmaRasi: unknown, dayRasi: unknown,
): { pos: number; verdict: ChandraVerdict } | null {
  const j = nameIndex(RASI_NAMES, janmaRasi), d = nameIndex(RASI_NAMES, dayRasi);
  if (j < 0 || d < 0) return null;
  const pos = ((d - j + 12) % 12) + 1;
  return { pos, verdict: tbChandraVerdict(pos) };
}
