import { element } from './elements';
import { type BirthProfileDerivation } from '../../lib/birth-profile-api';
import { type GuestProfile } from '../../lib/guest-profile-store';

export const SOUTH_INDIAN_RASHI_GRID = [
  'Meena', 'Mesha', 'Vrishabha', 'Mithuna',
  'Kumbha', null, null, 'Karka',
  'Makara', null, null, 'Simha',
  'Dhanu', 'Vrischika', 'Tula', 'Kanya',
] as const;

export interface NatalProfileDetails {
  contractVersion: string;
  engine: BirthProfileDerivation['engine'];
  nakshatra: string;
  pada: 1 | 2 | 3 | 4;
  janmaRashi: string;
  lagna: string;
  lagnaDegree: number;
  planets: BirthProfileDerivation['planets'];
}

export interface NatalDetailsPresentation {
  titleId: string;
  eyebrow: string;
  title: string;
  intro: string;
}

export function savedNatalDetails(profile: Readonly<GuestProfile>): NatalProfileDetails | null {
  if (profile.source !== 'birth-details') return null;
  if (!profile.nakshatra) return null;
  if (!profile.pada) return null;
  if (!profile.janmaRasi) return null;
  if (!profile.lagna) return null;
  if (!profile.natalChart) return null;
  if (!profile.calculation) return null;

  return {
    contractVersion: profile.calculation.contractVersion,
    engine: { ...profile.calculation.engine },
    nakshatra: profile.nakshatra,
    pada: profile.pada,
    janmaRashi: profile.janmaRasi,
    lagna: profile.lagna,
    lagnaDegree: profile.natalChart.lagnaDegree,
    planets: profile.natalChart.planets.map(planet => ({ ...planet })),
  };
}

export function renderNatalFacts(result: NatalProfileDetails): HTMLDListElement {
  const facts = element('dl', 'profiles-birth-facts');
  const factRows: Array<[string, string]> = [
    ['Nakshatra', result.nakshatra],
    ['Padam', String(result.pada)],
    ['Janma Rashi', result.janmaRashi],
    ['Lagna', `${result.lagna} · ${result.lagnaDegree.toFixed(2)}°`],
  ];
  for (const [label, value] of factRows) {
    const group = element('div', 'profiles-birth-facts__item');
    group.append(
      element('dt', 'profiles-birth-facts__label', label),
      element('dd', 'profiles-birth-facts__value', value),
    );
    facts.append(group);
  }
  return facts;
}

export function renderNatalChartContent(result: NatalProfileDetails): DocumentFragment {
  const fragment = document.createDocumentFragment();
  const chart = element('div', 'profiles-chart');
  chart.setAttribute('role', 'img');
  chart.setAttribute('aria-label', 'South Indian D1 Rashi chart. A complete accessible table follows.');
  for (const rashi of SOUTH_INDIAN_RASHI_GRID) {
    if (!rashi) {
      const center = element('div', 'profiles-chart__center');
      center.setAttribute('aria-hidden', 'true');
      chart.append(center);
      continue;
    }
    const cell = element('div', 'profiles-chart__cell');
    cell.dataset.rashi = rashi;
    cell.append(element('span', 'profiles-chart__rashi', rashi));
    const occupants = result.planets
      .filter(planet => planet.rashi === rashi)
      .map(planet => `${planet.name}${planet.retrograde ? ' ℞' : ''}`);
    if (result.lagna === rashi) occupants.unshift('Lagna');
    cell.append(element('span', 'profiles-chart__occupants', occupants.join(' · ') || '—'));
    chart.append(cell);
  }

  const tableWrap = element('div', 'profiles-chart-table-wrap');
  const scrollHint = element(
    'p',
    'profiles-chart-table__hint',
    'Scroll sideways to view every column on a small screen.',
  );
  scrollHint.id = 'profiles-chart-table-hint';
  const table = element('table', 'profiles-chart-table');
  table.setAttribute('aria-describedby', scrollHint.id);
  const caption = element('caption', 'profiles-chart-table__caption', 'Planet positions in the D1 Rashi chart');
  const head = element('thead');
  const headRow = element('tr');
  for (const label of ['Graha', 'Rashi', 'Degree', 'House']) {
    const cell = element('th', undefined, label);
    cell.scope = 'col';
    headRow.append(cell);
  }
  head.append(headRow);
  const body = element('tbody');
  for (const planet of result.planets) {
    const row = element('tr');
    const values = [
      `${planet.name}${planet.retrograde ? ' (retrograde)' : ''}`,
      planet.rashi,
      `${planet.degree.toFixed(2)}°`,
      String(planet.house),
    ];
    values.forEach(value => row.append(element('td', undefined, value)));
    body.append(row);
  }
  table.append(caption, head, body);
  tableWrap.append(scrollHint, table);

  const method = element(
    'p',
    'profiles-birth-review__method',
    `${result.engine.name} ${result.engine.version} · ${result.engine.ayanamsha} ayanamsha · ${result.engine.ephemeris} ephemeris · contract ${result.contractVersion}`,
  );
  const reference = element(
    'a',
    'profiles-birth-review__reference',
    'How this is calculated and verified',
  );
  reference.href = '/docs/reference/53-birth-profile-calculation';
  fragment.append(chart, tableWrap, method, reference);
  return fragment;
}

export function renderNatalDetails(
  result: NatalProfileDetails,
  presentation: NatalDetailsPresentation,
): HTMLElement {
  const section = element('section', 'profiles-birth-review');
  section.setAttribute('aria-labelledby', presentation.titleId);
  const eyebrow = element('p', 'profiles-birth-review__eyebrow', presentation.eyebrow);
  const title = element('h2', 'profiles-birth-review__title', presentation.title);
  title.id = presentation.titleId;
  title.tabIndex = -1;
  const intro = element(
    'p',
    'profiles-birth-review__intro',
    presentation.intro,
  );
  const facts = renderNatalFacts(result);
  const chartTitle = element('h3', 'profiles-chart__title', 'D1 Rashi chart');
  section.append(eyebrow, title, intro, facts, chartTitle, renderNatalChartContent(result));
  return section;
}

export function renderNatalReview(result: BirthProfileDerivation): HTMLElement {
  return renderNatalDetails(result, {
    titleId: 'profile-review-title',
    eyebrow: 'Calculated profile',
    title: 'Review before saving',
    intro: 'These facts will power Daily Horoscope and Muhurtam. Confirm that the birth details above are correct before saving.',
  });
}
