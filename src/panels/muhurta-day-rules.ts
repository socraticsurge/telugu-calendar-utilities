import {
  MU_CHANDRA_GOOD,
  MU_CHANDRA_PUJA,
  muLagnaClassOf,
  muCombustionDropReason,
} from '../muhurta-scorer';
import { lagnaDayFor } from '../lib/lagna-loader';
import {
  evaluateConfiguredKarnavedhaDaylight,
  karnavedhaDaylightDropReason,
} from '../scorer/election-assessors/karnavedha-daylight';
import { muAvoidKaranaWindows, muMin } from './muhurta-astronomy';
import { tbChandraOf } from './tarabalam-journey';

const MU_NITYA_HARD_AVOID = new Set(['Vyatipata', 'Vaidhriti']);

export function muConfiguredDaylightPolicy(activity, data, rules) {
  return activity === 'karnavedha'
    ? evaluateConfiguredKarnavedhaDaylight(
      data,
      rules.require_single_daylight_tithi,
      rules.require_single_daylight_nakshatra,
    )
    : null;
}

export function muPrimaryDayDrop(
  data,
  rules,
  activityLabel: string,
  daylightPolicy,
  lagnaCityData,
  isoDate: string,
) {
  if (data.eclipse) {
    const kind = data.eclipse.kind || 'Eclipse';
    return {
      eclipse: true,
      entry: { date: isoDate, reason: `${kind} · auspicious activities deferred` },
    };
  }
  if (daylightPolicy && !daylightPolicy.admissible) {
    return {
      eclipse: false,
      entry: {
        date: isoDate,
        reason: karnavedhaDaylightDropReason(daylightPolicy),
        daylightOutcomes: daylightPolicy.outcomes,
      },
    };
  }
  if (rules.skip_on_sankramana && data.special.some(
      item => /Sankraman/i.test(item))) {
    return {
      eclipse: false,
      entry: {
        date: isoDate,
        reason: `Sankramana · ${activityLabel} source profile avoids this day`,
      },
    };
  }
  const combustionReason = muCombustionDropReason(
    lagnaCityData ? lagnaDayFor(lagnaCityData, isoDate) : null,
    rules.skip_on_combust || [], activityLabel,
  );
  return combustionReason
    ? { eclipse: false, entry: { date: isoDate, reason: combustionReason } }
    : null;
}

export function muCalendarDayDrop(data, rules, activityLabel: string, isoDate: string) {
  const normalizedMaasam = (data.maasam || '').replace(/^(?:Nija|Adhika)\s+/, '');
  const maasaSolarAdmitted = (rules.allowed_maasa_solar_pairs || []).some(pair =>
    pair[0] === normalizedMaasam && pair[1] === data.solarSign);
  if ((rules.allowed_maasams?.length || rules.allowed_maasa_solar_pairs?.length) &&
      !rules.allowed_maasams?.includes(normalizedMaasam) && !maasaSolarAdmitted) {
    return { date: isoDate,
      reason: `${data.maasam} Maasa · ${activityLabel} source profile does not admit this lunar month` };
  }
  if (rules.allowed_varas?.length && !rules.allowed_varas.includes(data.vaaram)) {
    return { date: isoDate,
      reason: `${data.vaaram} · ${activityLabel} source profile does not admit this weekday` };
  }
  if (rules.allowed_pakshams?.length && !rules.allowed_pakshams.includes(data.paksham)) {
    return { date: isoDate,
      reason: `${data.paksham} Paksha · ${activityLabel} source profile does not admit this lunar fortnight` };
  }
  if ((rules.avoid_vara_paksha || []).some(pair =>
    pair[0] === data.vaaram && pair[1] === data.paksham)) {
    return { date: isoDate,
      reason: `${data.vaaram} during ${data.paksham} Paksha · ${activityLabel} source profile rejects this combination` };
  }
  return null;
}

export function muSolarDayDrop(data, rules, activityLabel: string, isoDate: string) {
  const solarClass = data.solarSign ? muLagnaClassOf(data.solarSign) : null;
  if (rules.allowed_solar_classes?.length &&
      (!solarClass || !rules.allowed_solar_classes.includes(solarClass))) {
    return { date: isoDate,
      reason: `Surya in ${data.solarSign} (${solarClass}) · ${activityLabel} source profile does not admit this Rasi class` };
  }
  if (rules.allowed_solar_signs?.length &&
      !rules.allowed_solar_signs.includes(data.solarSign)) {
    return { date: isoDate,
      reason: `Surya in ${data.solarSign} · ${activityLabel} source profile does not admit this solar Rasi` };
  }
  return null;
}

export function muDayDrop(
  data,
  rules,
  activityLabel: string,
  daylightPolicy,
  lagnaCityData,
  isoDate: string,
) {
  const primary = muPrimaryDayDrop(
    data, rules, activityLabel, daylightPolicy, lagnaCityData, isoDate,
  );
  if (primary) return primary;
  const entry = muCalendarDayDrop(data, rules, activityLabel, isoDate)
    || muSolarDayDrop(data, rules, activityLabel, isoDate);
  return entry ? { eclipse: false, entry } : null;
}

export function muBadWindows(data, avoidKaranaNames) {
  const windows = data.inauspicious.map(
    window => [muMin(window.start, window.sflag), muMin(window.end, window.eflag)],
  );
  if (avoidKaranaNames.size && data.karana) {
    windows.push(...muAvoidKaranaWindows(data.karana, avoidKaranaNames));
  }
  return windows;
}

export function muYogaDayDropReason(data, skipYogas, activityLabel: string): string | null {
  for (const yoga of data.yogas) {
    if (skipYogas.has(yoga)) {
      return `${yoga} · ${activityLabel} traditionally avoids this day`;
    }
  }
  if (skipYogas.size && data.yoga && MU_NITYA_HARD_AVOID.has(data.yoga.name)) {
    return `${data.yoga.name} yoga · samskaras traditionally defer`;
  }
  return null;
}

export function muChandraModeDayDropReason(data, people, chandraMode): string | null {
  if (!people.length || chandraMode === 'stars' || !data.lunarSign) return null;
  let hasAvoid = false;
  let hasRemedial = false;
  for (const person of people) {
    if (!person.rasi) continue;
    const chandra = tbChandraOf(person.rasi, data.lunarSign);
    if (!chandra) continue;
    if (!MU_CHANDRA_GOOD.has(chandra.pos) && !MU_CHANDRA_PUJA.has(chandra.pos)) {
      hasAvoid = true;
    } else if (MU_CHANDRA_PUJA.has(chandra.pos)) {
      hasRemedial = true;
    }
  }
  if (chandraMode === 'strict' && (hasAvoid || hasRemedial)) {
    return 'chandra_mode=strict · Moon at sunrise fails for at least one person';
  }
  return chandraMode === 'puja_ok' && hasAvoid
    ? 'chandra_mode=puja_ok · someone has Moon-avoid (4/8/12)'
    : null;
}

export function muNoSlotDayReason(data, skipYogas, activityLabel, people, chandraMode) {
  return muYogaDayDropReason(data, skipYogas, activityLabel)
    || muChandraModeDayDropReason(data, people, chandraMode);
}

export function muRecordNoSlotDay(options): void {
  const {
    slotsPerDay, droppedDays, isoDate, data, skipYogas,
    activityLabel, people, chandraMode,
  } = options;
  if (slotsPerDay.has(isoDate)) return;
  const reason = muNoSlotDayReason(
    data, skipYogas, activityLabel, people, chandraMode,
  );
  if (reason) droppedDays.push({ date: isoDate, reason });
}
