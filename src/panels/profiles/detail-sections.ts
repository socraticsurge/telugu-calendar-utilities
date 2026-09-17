import { type ProfilesPanelOptions } from './contracts';
import { element, button } from './elements';
import { type NatalProfileDetails, renderNatalFacts, renderNatalChartContent } from './natal-view';
import { guestProfileReadiness, type GuestProfile } from '../../lib/guest-profile-store';

export type DetailFactsRenderer = (
  rows: ReadonlyArray<readonly [string, string]>,
) => HTMLDListElement;

export function profileFactsSection(
  profile: GuestProfile,
  renderFacts: DetailFactsRenderer,
): HTMLElement {
  if (profile.birthDetails) {
    const section = element('section', 'profiles-detail__section');
    section.setAttribute('aria-labelledby', 'profile-detail-birth-title');
    const title = element('h2', 'profiles-detail__section-title', 'Saved birth details');
    title.id = 'profile-detail-birth-title';
    section.append(title, renderFacts([
      ['Date of birth', profile.birthDetails.dateOfBirth],
      ['Time of birth', profile.birthDetails.timeOfBirth],
      ['Place of birth', profile.birthDetails.placeLabel],
      ['Time zone', profile.birthDetails.timezone],
    ]));
    return section;
  }
  const section = element('section', 'profiles-detail__section');
  section.setAttribute('aria-labelledby', 'profile-detail-facts-title');
  const title = element('h2', 'profiles-detail__section-title', 'Saved astrology details');
  title.id = 'profile-detail-facts-title';
  section.append(title, renderFacts([
    ['Nakshatra', profile.nakshatra || 'Not added'],
    ['Padam', profile.pada ? String(profile.pada) : 'Not added'],
    ['Janma Rashi', profile.janmaRasi || 'Not available'],
    ['Lagna', profile.lagna || 'Not added'],
  ]));
  return section;
}

export function savedAstrologySection(details: NatalProfileDetails | null): HTMLElement | null {
  if (!details) return null;
  const section = element('section', 'profiles-birth-review profiles-detail__natal');
  section.setAttribute('aria-labelledby', 'profile-detail-astrology-title');
  const title = element('h2', 'profiles-birth-review__title', 'Astrology details');
  title.id = 'profile-detail-astrology-title';
  section.append(
    element('p', 'profiles-birth-review__eyebrow', 'Saved calculation'),
    title,
    element(
      'p',
      'profiles-birth-review__intro',
      'These results were saved from the birth calculation. The original inputs remain visible above so you can verify them before reviewing the chart.',
    ),
    renderNatalFacts(details),
  );
  return section;
}

export function journeyReadinessSection(
  profile: GuestProfile,
  renderReadiness: (profile: GuestProfile) => HTMLDListElement,
  options: ProfilesPanelOptions,
): HTMLElement {
  const section = element('section', 'profiles-detail__section profiles-detail__readiness');
  section.setAttribute('aria-labelledby', 'profile-detail-readiness-title');
  const title = element('h2', 'profiles-detail__section-title', 'Ready to use');
  title.id = 'profile-detail-readiness-title';
  section.append(
    title,
    element(
      'p',
      'profiles-detail__section-copy',
      'These checks show which personalized journeys can use the saved details as they are.',
    ),
    renderReadiness(profile),
  );
  const readiness = guestProfileReadiness(profile);
  const actions = element('div', 'profiles-form__actions');
  if (readiness.horoscope) {
    const horoscope = button('View Daily Horoscope', 'profiles-button profiles-button--primary');
    horoscope.dataset.action = 'view-daily-horoscope';
    horoscope.addEventListener('click', () => {
      openHoroscope(options, profile.id);
    });
    actions.append(horoscope);
  }
  if (readiness.muhurta) {
    const muhurta = button('Find Muhurtam', 'profiles-button profiles-button--secondary');
    muhurta.dataset.action = 'find-muhurtam';
    muhurta.addEventListener('click', () => {
      openMuhurtam(options, profile.id);
    });
    actions.append(muhurta);
  }
  if (actions.childElementCount > 0) section.append(actions);
  return section;
}

export function natalChartSection(details: NatalProfileDetails | null): HTMLElement {
  const sectionClass = details
    ? 'profiles-detail__section profiles-detail__chart'
    : 'profiles-detail__section profiles-detail__unavailable';
  const section = element('section', sectionClass);
  section.setAttribute('aria-labelledby', 'profile-detail-chart-title');
  const title = element(
    'h2',
    'profiles-detail__section-title',
    details ? 'D1 Rashi chart' : 'Natal chart and calculation',
  );
  title.id = 'profile-detail-chart-title';
  const copy = details
    ? 'The South Indian chart and accessible planet table below are the saved result; opening this page does not calculate them again.'
    : 'Natal chart and calculation details are available only for profiles calculated from birth details.';
  section.append(title, element('p', 'profiles-detail__section-copy', copy));
  if (details) section.append(renderNatalChartContent(details));
  return section;
}

function openHoroscope(options: ProfilesPanelOptions, id: string): void {
  if (options.onViewDailyHoroscope) options.onViewDailyHoroscope(id);
  else options.navigate('gochara');
}

function openMuhurtam(options: ProfilesPanelOptions, id: string): void {
  if (options.onFindMuhurtam) options.onFindMuhurtam(id);
  else options.navigate('tarabalam');
}
export const renderReadiness = (profile: GuestProfile): HTMLDListElement => {
  const readiness = guestProfileReadiness(profile);
  const list = element('dl', 'profiles-readiness');

  const muhurtaTerm = element('dt', 'profiles-readiness__term', 'Muhurtam');
  const muhurtaValue = element(
    'dd',
    `profiles-readiness__value ${readiness.muhurta ? 'profiles-readiness__value--ready' : 'profiles-readiness__value--needs-details'}`,
    readiness.muhurta ? 'Ready' : 'Needs Nakshatra',
  );
  const horoscopeTerm = element('dt', 'profiles-readiness__term', 'Daily Horoscope');
  let horoscopeText = 'Ready';
  if (readiness.missingForHoroscope === 'nakshatra') horoscopeText = 'Needs Nakshatra';
  if (readiness.missingForHoroscope === 'pada') horoscopeText = 'Needs Padam';
  if (readiness.horoscope && readiness.janmaRasi) {
    horoscopeText = `Ready · ${readiness.janmaRasi} Janma Rashi`;
  }
  const horoscopeValue = element(
    'dd',
    `profiles-readiness__value ${readiness.horoscope ? 'profiles-readiness__value--ready' : 'profiles-readiness__value--needs-details'}`,
    horoscopeText,
  );
  list.append(muhurtaTerm, muhurtaValue, horoscopeTerm, horoscopeValue);
  return list;
};
