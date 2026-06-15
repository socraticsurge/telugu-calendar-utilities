// Unit tests for the pure muhurta scoring helpers in
// docs/muhurta-scorer.js. Run with: node --test tests/js/
//
// These are JS-only tests: they verify the JS port matches the
// behaviour the Python suite already pins for telugu_panchangam/
// personal/{muhurta,lagna_position,chandrabalam}.py. Any drift
// between Python and JS must be caught by a failure HERE — that's
// the regression the tara_dosha JS-parity bug (PR 63) slipped
// through for months.

const test = require('node:test');
const assert = require('node:assert/strict');
const M = require('../../docs/muhurta-scorer.js');

// ── Lagna position math ─────────────────────────────────────────

test('muLagnaPosition: inclusive count from janma', () => {
  assert.equal(M.muLagnaPosition('Mesha', 'Mesha'), 1);
  assert.equal(M.muLagnaPosition('Mesha', 'Vrishabha'), 2);
  assert.equal(M.muLagnaPosition('Mesha', 'Karka'), 4);      // kendra
  assert.equal(M.muLagnaPosition('Mesha', 'Simha'), 5);      // trikona
  assert.equal(M.muLagnaPosition('Mesha', 'Tula'), 7);       // kendra
  assert.equal(M.muLagnaPosition('Mesha', 'Vrischika'), 8);  // Ashtama
  assert.equal(M.muLagnaPosition('Mesha', 'Makara'), 10);    // kendra
  assert.equal(M.muLagnaPosition('Mesha', 'Meena'), 12);
});

test('muLagnaPosition: wraps modulo 12 from non-Mesha', () => {
  assert.equal(M.muLagnaPosition('Meena', 'Meena'), 1);
  assert.equal(M.muLagnaPosition('Meena', 'Mesha'), 2);
  assert.equal(M.muLagnaPosition('Meena', 'Tula'), 8);  // Ashtama from Meena
});

test('muLagnaPosition: unknown rashi returns null', () => {
  assert.equal(M.muLagnaPosition('NotARashi', 'Mesha'), null);
  assert.equal(M.muLagnaPosition('Mesha', 'NotARashi'), null);
});

test('muLagnaVerdict: own / kendra / trikona / ashtama / neutral', () => {
  assert.equal(M.muLagnaVerdict(1), 'own');
  assert.equal(M.muLagnaVerdict(4), 'kendra');
  assert.equal(M.muLagnaVerdict(5), 'trikona');
  assert.equal(M.muLagnaVerdict(7), 'kendra');
  assert.equal(M.muLagnaVerdict(8), 'ashtama');
  assert.equal(M.muLagnaVerdict(9), 'trikona');
  assert.equal(M.muLagnaVerdict(10), 'kendra');
  assert.equal(M.muLagnaVerdict(6), 'neutral');
  assert.equal(M.muLagnaVerdict(12), 'neutral');
});

test('muIsFavourableLagna covers kendra OR trikona only', () => {
  const fav = new Set([1, 4, 5, 7, 9, 10]);
  for (let p = 1; p <= 12; p++) {
    assert.equal(M.muIsFavourableLagna(p), fav.has(p),
      `pos ${p}: expected fav=${fav.has(p)}`);
  }
});

test('muIsAshtamaLagna is only position 8', () => {
  for (let p = 1; p <= 12; p++) {
    assert.equal(M.muIsAshtamaLagna(p), p === 8);
  }
});

// ── Lagna lookup against day data ───────────────────────────────

const SAMPLE_DAY = {
  sunrise: '05:41',
  lagna0: 1,                                     // Vrishabha
  transitions: [[5, 2], [137, 3], [270, 4]],     // Mithuna, Karka, Simha starts
  cycleEnd: 396,                                 // (placeholder; Simha runs to here)
};

test('muLagnaAtMin returns the rashi rising at a slot start', () => {
  // sunrise 05:41 → first 5 min Vrishabha, then Mithuna until 137 min.
  // slotMin 06:00 (= 360 min) is 19 min after sunrise → Mithuna.
  assert.equal(M.muLagnaAtMin(SAMPLE_DAY, 360), 'Mithuna');
  // slotMin == sunrise → first window (Vrishabha).
  assert.equal(M.muLagnaAtMin(SAMPLE_DAY, 341), 'Vrishabha');
  // slotMin near end of last visible cell → Simha.
  assert.equal(M.muLagnaAtMin(SAMPLE_DAY, 341 + 350), 'Simha');
});

test('muLagnaAtMin returns null before sunrise or outside data', () => {
  assert.equal(M.muLagnaAtMin(SAMPLE_DAY, 0), null);   // before sunrise
  assert.equal(M.muLagnaAtMin(null, 360), null);       // no data
});

// ── Tier mapping ────────────────────────────────────────────────

test('muScoreTier maps fixed bands', () => {
  assert.equal(M.muScoreTier(8), 'Excellent');
  assert.equal(M.muScoreTier(7), 'Excellent');
  assert.equal(M.muScoreTier(6), 'Good');
  assert.equal(M.muScoreTier(4), 'Good');
  assert.equal(M.muScoreTier(3), 'Fair');
  assert.equal(M.muScoreTier(1), 'Fair');
  assert.equal(M.muScoreTier(0), 'Avoid');
  assert.equal(M.muScoreTier(-5), 'Avoid');
});

test('muRelativeTier buckets by position in [floor, ceiling]', () => {
  // ceiling=8, floor=0. Score 8 → rel=1.0 → Excellent. Score 6 → 0.75 → Excellent.
  assert.equal(M.muRelativeTier(8, 8, 0), 'Excellent');
  assert.equal(M.muRelativeTier(6, 8, 0), 'Excellent');
  // Score 4 → rel=0.5 → Good
  assert.equal(M.muRelativeTier(4, 8, 0), 'Good');
  // Score 2 → rel=0.25 → Fair
  assert.equal(M.muRelativeTier(2, 8, 0), 'Fair');
  // Score 1 → rel=0.125 → Avoid
  assert.equal(M.muRelativeTier(1, 8, 0), 'Avoid');
  // Degenerate spread → fall back to absolute tier.
  assert.equal(M.muRelativeTier(5, 5, 5), 'Good');
});

// ── personalDosha cascade ───────────────────────────────────────
// This is the cascade where the tara_dosha JS-parity bug (PR 63)
// lived for months. Every branch is tested here, plus precedence.

test('computePersonalDosha: clean slot returns null', () => {
  assert.equal(M.computePersonalDosha(), null);
  assert.equal(M.computePersonalDosha({}), null);
});

test('computePersonalDosha: ashtama_chandra beats everything else', () => {
  assert.equal(M.computePersonalDosha({
    chandraAvoidNames: ['#1'],
    hasAshtamaChandra: true,
    ashtamaLagnaNames: ['#1'],
    chandraPujaNames: ['#1'],
    taraUnfavNames: ['#1'],
  }), 'ashtama_chandra');
});

test('computePersonalDosha: chandra_avoid (non-Ashtama) when chandra is in 4/12', () => {
  assert.equal(M.computePersonalDosha({
    chandraAvoidNames: ['#1'],
    hasAshtamaChandra: false,
  }), 'chandra_avoid');
});

test('computePersonalDosha: ashtama_lagna beats chandra_remedial + tara', () => {
  assert.equal(M.computePersonalDosha({
    ashtamaLagnaNames: ['#1'],
    chandraPujaNames: ['#1'],
    taraUnfavNames: ['#1'],
  }), 'ashtama_lagna');
});

test('computePersonalDosha: chandra_remedial beats tara_dosha', () => {
  assert.equal(M.computePersonalDosha({
    chandraPujaNames: ['#1'],
    taraUnfavNames: ['#1'],
  }), 'chandra_remedial');
});

// THE one that broke (PR 63 fix):
test('computePersonalDosha: tara_dosha fires when no Siddhi rectifies', () => {
  assert.equal(M.computePersonalDosha({
    taraUnfavNames: ['#1'],
    siddhiYogas: [],
  }), 'tara_dosha');
});

test('computePersonalDosha: Siddhi yoga rectifies tara → null', () => {
  assert.equal(M.computePersonalDosha({
    taraUnfavNames: ['#1'],
    siddhiYogas: ['Sarvartha Siddhi Yoga'],
  }), null);
  assert.equal(M.computePersonalDosha({
    taraUnfavNames: ['#1'],
    siddhiYogas: ['Amrita Siddhi Yoga'],
  }), null);
});

// ── dayDosha ─────────────────────────────────────────────────────

test('computeDayDosha: clean day returns null', () => {
  assert.equal(M.computeDayDosha(), null);
});

test('computeDayDosha: Rikta tithi', () => {
  assert.equal(M.computeDayDosha({ tithiFamily: 'Rikta' }), 'rikta_tithi');
});

test('computeDayDosha: Amavasya', () => {
  assert.equal(M.computeDayDosha({ isAmavasya: true }), 'amavasya');
});

test('computeDayDosha: Rikta beats Amavasya in precedence', () => {
  assert.equal(M.computeDayDosha({
    tithiFamily: 'Rikta',
    isAmavasya: true,
  }), 'rikta_tithi');
});

test('computeDayDosha: Visha/Dagdha yoga', () => {
  assert.equal(M.computeDayDosha({ hasYogaPenalty: true }), 'visha_dagdha_yoga');
});

test('computeDayDosha: Vyatipata/Vaidhriti', () => {
  assert.equal(M.computeDayDosha({ nityaHardAvoid: true }), 'vyatipata_vaidhriti');
});

// ── Lagna classes (Chara / Sthira / Dvisvabhava) ────────────────

test('Lagna classes partition the 12 rashis cleanly', () => {
  const union = new Set([...M.MU_LAGNA_CHARA, ...M.MU_LAGNA_STHIRA, ...M.MU_LAGNA_DVISVABHAVA]);
  assert.equal(union.size, 12);
  assert.equal(M.MU_LAGNA_CHARA.size, 4);
  assert.equal(M.MU_LAGNA_STHIRA.size, 4);
  assert.equal(M.MU_LAGNA_DVISVABHAVA.size, 4);
  // No overlap
  for (const r of M.MU_LAGNA_CHARA) {
    assert.ok(!M.MU_LAGNA_STHIRA.has(r));
    assert.ok(!M.MU_LAGNA_DVISVABHAVA.has(r));
  }
});

test('muLagnaClassOf classical spot-checks', () => {
  // Movable: Mesha, Karka, Tula, Makara
  assert.equal(M.muLagnaClassOf('Mesha'), 'Chara');
  assert.equal(M.muLagnaClassOf('Makara'), 'Chara');
  // Fixed: Vrishabha, Simha, Vrischika, Kumbha
  assert.equal(M.muLagnaClassOf('Vrishabha'), 'Sthira');
  assert.equal(M.muLagnaClassOf('Simha'), 'Sthira');
  // Dual: Mithuna, Kanya, Dhanu, Meena
  assert.equal(M.muLagnaClassOf('Mithuna'), 'Dvisvabhava');
  assert.equal(M.muLagnaClassOf('Meena'), 'Dvisvabhava');
});

test('muLagnaClassOf unknown rashi returns null', () => {
  assert.equal(M.muLagnaClassOf('NotARashi'), null);
});

test('muLagnasInClass returns the right set', () => {
  assert.equal(M.muLagnasInClass('Chara'), M.MU_LAGNA_CHARA);
  assert.equal(M.muLagnasInClass('Sthira'), M.MU_LAGNA_STHIRA);
  assert.equal(M.muLagnasInClass('Dvisvabhava'), M.MU_LAGNA_DVISVABHAVA);
  assert.equal(M.muLagnasInClass('Bogus'), null);
});
