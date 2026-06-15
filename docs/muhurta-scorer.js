// Pure muhurta scoring helpers — extracted from docs/index.html so
// they can be loaded both in the browser (assigns to window) and from
// Node (`require()` for tests). The inline scoring loop in index.html
// uses these via the window globals; tests import them as a module.
//
// Mirrors telugu_panchangam/personal/{muhurta,lagna_position,chandrabalam}.py
// — the parity must hold between this file and the Python module.
//
// Add new pure functions here when extracting from the inline loop.
// DOM-touching code must stay in index.html.
(function (root) {

  // ────────────────────────────────────────────────────────────────
  // Constants
  // ────────────────────────────────────────────────────────────────
  const MU_RASHI_NAMES = ['Mesha','Vrishabha','Mithuna','Karka','Simha',
                          'Kanya','Tula','Vrischika','Dhanu','Makara',
                          'Kumbha','Meena'];

  // Lagna position classification (mirrors lagna_position.py).
  const MU_LAGNA_KENDRA = new Set([1, 4, 7, 10]);
  const MU_LAGNA_TRIKONA = new Set([1, 5, 9]);

  // Lagna classes (Chara / Sthira / Dvisvabhava) — Muhurta Chintamani
  // groupings. Used by per-activity lagna preferences.
  const MU_LAGNA_CHARA = new Set(['Mesha', 'Karka', 'Tula', 'Makara']);
  const MU_LAGNA_STHIRA = new Set(['Vrishabha', 'Simha', 'Vrischika', 'Kumbha']);
  const MU_LAGNA_DVISVABHAVA = new Set(['Mithuna', 'Kanya', 'Dhanu', 'Meena']);
  const MU_LAGNA_CLASSES = {
    Chara: MU_LAGNA_CHARA,
    Sthira: MU_LAGNA_STHIRA,
    Dvisvabhava: MU_LAGNA_DVISVABHAVA,
  };
  function muLagnaClassOf(rashi) {
    for (const k of Object.keys(MU_LAGNA_CLASSES)) {
      if (MU_LAGNA_CLASSES[k].has(rashi)) return k;
    }
    return null;
  }
  function muLagnasInClass(className) {
    return MU_LAGNA_CLASSES[className] || null;
  }

  // Chandrabalam (mirrors chandrabalam.py). Used by the dosha cascade.
  const MU_CHANDRA_GOOD = new Set([1, 3, 6, 7, 10, 11]);
  const MU_CHANDRA_PUJA = new Set([2, 5, 9]);

  // Tier bucketing (mirrors muhurta.score_tier / relative_tier).
  const MU_TIER_NAMES = ['Avoid', 'Fair', 'Good', 'Excellent'];
  const MU_RELATIVE_BANDS = [0.75, 0.5, 0.25];

  // ────────────────────────────────────────────────────────────────
  // Lagna position math
  // ────────────────────────────────────────────────────────────────

  function muLagnaPosition(janmaRashi, lagnaRashi) {
    const j = MU_RASHI_NAMES.indexOf(janmaRashi);
    const l = MU_RASHI_NAMES.indexOf(lagnaRashi);
    if (j < 0 || l < 0) return null;
    return ((l - j) % 12 + 12) % 12 + 1;
  }

  function muLagnaVerdict(pos) {
    if (pos === 1) return 'own';
    if (pos === 8) return 'ashtama';
    if (MU_LAGNA_TRIKONA.has(pos)) return 'trikona';
    if (MU_LAGNA_KENDRA.has(pos)) return 'kendra';
    return 'neutral';
  }

  function muIsFavourableLagna(pos) {
    return MU_LAGNA_KENDRA.has(pos) || MU_LAGNA_TRIKONA.has(pos);
  }

  function muIsAshtamaLagna(pos) { return pos === 8; }

  // Find the rashi rising at slotMin (minutes from midnight) using the
  // pre-computed lagna.json day data (with lagna0 + transitions[] +
  // cycleEnd). Returns null if slot is before sunrise or data missing.
  function muLagnaAtMin(lagnaDayData, slotMin) {
    if (!lagnaDayData) return null;
    const [srH, srM] = lagnaDayData.sunrise.split(':').map(Number);
    const sunriseMin = srH * 60 + srM;
    const offset = slotMin - sunriseMin;
    if (offset < 0) return null;
    const starts = [[0, lagnaDayData.lagna0], ...lagnaDayData.transitions];
    for (let i = 0; i < starts.length; i++) {
      const [startOff, rashiIdx] = starts[i];
      const endOff = (i + 1 < starts.length) ? starts[i + 1][0] : lagnaDayData.cycleEnd;
      if (startOff <= offset && offset < endOff) {
        return MU_RASHI_NAMES[rashiIdx];
      }
    }
    return null;
  }

  // ────────────────────────────────────────────────────────────────
  // Tier mapping
  // ────────────────────────────────────────────────────────────────

  function muScoreTier(score) {
    if (score >= 7) return 'Excellent';
    if (score >= 4) return 'Good';
    if (score >= 1) return 'Fair';
    return 'Avoid';
  }

  function muRelativeTier(score, ceiling, floor) {
    const spread = ceiling - floor;
    if (spread <= 0) return muScoreTier(score);
    const rel = (score - floor) / spread;
    if (rel >= MU_RELATIVE_BANDS[0]) return 'Excellent';
    if (rel >= MU_RELATIVE_BANDS[1]) return 'Good';
    if (rel >= MU_RELATIVE_BANDS[2]) return 'Fair';
    return 'Avoid';
  }

  // ────────────────────────────────────────────────────────────────
  // Dosha cascades — match telugu_panchangam/personal/muhurta.py
  // ────────────────────────────────────────────────────────────────

  // Determines the slot's personal_dosha label given the per-person
  // flag-name lists already accumulated by the scoring loop. Mirrors
  // Python's elif cascade in _evaluate_slot. Returns null when clean.
  //
  // Order is load-bearing: ashtama_chandra > ashtama_lagna >
  // chandra_avoid > chandra_remedial > tara_dosha. The tara_dosha
  // JS-parity bug (PR 63) was a missing branch here.
  function computePersonalDosha({
    chandraAvoidNames = [],
    hasAshtamaChandra = false,
    ashtamaLagnaNames = [],
    chandraPujaNames = [],
    taraUnfavNames = [],
    siddhiYogas = [],
  } = {}) {
    if (chandraAvoidNames.length) {
      return hasAshtamaChandra ? 'ashtama_chandra' : 'chandra_avoid';
    }
    if (ashtamaLagnaNames.length) return 'ashtama_lagna';
    if (chandraPujaNames.length) return 'chandra_remedial';
    if (taraUnfavNames.length && !siddhiYogas.length) return 'tara_dosha';
    return null;
  }

  // Day-level dosha (Rikta tithi, Amavasya, Visha/Dagdha yoga,
  // Vyatipata/Vaidhriti) — same "can't be Excellent" treatment as a
  // personal dosha. Mirrors Python's _evaluate_slot day_dosha block.
  function computeDayDosha({
    tithiFamily = null,
    isAmavasya = false,
    hasYogaPenalty = false,
    nityaHardAvoid = false,
  } = {}) {
    if (tithiFamily === 'Rikta') return 'rikta_tithi';
    if (isAmavasya) return 'amavasya';
    if (hasYogaPenalty) return 'visha_dagdha_yoga';
    if (nityaHardAvoid) return 'vyatipata_vaidhriti';
    return null;
  }

  // ────────────────────────────────────────────────────────────────
  // Exports — dual-context (window in browser, module.exports in Node)
  // ────────────────────────────────────────────────────────────────
  const api = {
    MU_RASHI_NAMES,
    MU_LAGNA_KENDRA, MU_LAGNA_TRIKONA,
    MU_LAGNA_CHARA, MU_LAGNA_STHIRA, MU_LAGNA_DVISVABHAVA, MU_LAGNA_CLASSES,
    MU_CHANDRA_GOOD, MU_CHANDRA_PUJA,
    MU_TIER_NAMES, MU_RELATIVE_BANDS,
    muLagnaPosition, muLagnaVerdict,
    muIsFavourableLagna, muIsAshtamaLagna, muLagnaAtMin,
    muLagnaClassOf, muLagnasInClass,
    muScoreTier, muRelativeTier,
    computePersonalDosha, computeDayDosha,
  };
  if (typeof module !== 'undefined' && module.exports) {
    module.exports = api;
  } else {
    Object.assign(root, api);
  }
})(typeof window !== 'undefined' ? window : globalThis);
