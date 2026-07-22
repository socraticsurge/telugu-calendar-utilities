// typing lands with the component rewrite, not the move.
//
// Tarabalam panel + the nested Muhurta finder: profiles, good-day
// calculation, slot search (client-side mirror of the Python scorer),
// rendering and WhatsApp shares.

import {
  MU_RASHI_NAMES, MU_LAGNA_KENDRA, MU_LAGNA_TRIKONA,
  MU_LAGNA_CHARA, MU_LAGNA_STHIRA, MU_LAGNA_DVISVABHAVA, MU_LAGNA_CLASSES,
  MU_CHANDRA_GOOD, MU_CHANDRA_PUJA,
  MU_TIER_NAMES, MU_RELATIVE_BANDS,
  muLagnaPosition, muLagnaVerdict,
  muIsFavourableLagna, muIsAshtamaLagna, muLagnaAtMin,
  muLagnaClassOf, muLagnasInClass,
  muScoreTier, muRelativeTier, muCanonicalNakshatra, muScoreTithiClass,
  muEndsBySolarNoon, muCombustionDropReason,
  computePersonalDosha, computeDayDosha,
} from '../muhurta-scorer';
import { selEl, inpEl } from '../lib/dom';
import { getSelection } from '../selection-store';
import { loadFeed } from '../lib/feed-loader';
import { parseDescription, TIME_PART } from '../lib/parse-description';
import { fmtT, dayMark, fmtRange, fmtPlain, stampOf } from '../lib/format';
import { htmlEsc } from '../lib/html';
import { gcEvent } from '../lib/analytics';
import { loadLagna, lagnaDayFor } from '../lib/lagna-loader';
import { RASI_NAMES, NAKSHATRA_NAMES, rasiFromStar } from '../data/rasis';
import { MUHURTA_DAY } from '../data/muhurtas';
import activityContract from '../data/activity-rules.generated.json';
import { goHasData, goBuildViewSelect, renderGochara } from './gochara';
import { getLoadedEvents, selectedDate, ekadashiName, festivalNames } from './today';

// --- Tarabalam tool ---

const TB_NAKSHATRAS = NAKSHATRA_NAMES;
const TARA_NAMES = ['Janma','Sampat','Vipat','Kshema','Pratyak','Sadhana','Naidhana','Mitra','Parama Mitra'];
const TARA_GOOD = new Set([2,4,6,8,9]);
const TB_RASIS = RASI_NAMES;
const CHANDRA_GOOD = new Set([1,3,6,7,10,11]);
const CHANDRA_PUJA = new Set([2,5,9]);
let TB_DAYS = null;    // last computed result rows
let TB_EVENTS = null;  // feed events used for the last calculation

function taraOf(janmaName, dayName) {
  const j = TB_NAKSHATRAS.indexOf(janmaName), d = TB_NAKSHATRAS.indexOf(dayName);
  if (j < 0 || d < 0) return null;
  return ((d - j + 27) % 27) % 9 + 1;
}

function chandraOf(janmaRasi, dayRasi) {
  const j = TB_RASIS.indexOf(janmaRasi), d = TB_RASIS.indexOf(dayRasi);
  if (j < 0 || d < 0) return null;
  const pos = ((d - j + 12) % 12) + 1;
  return { pos, verdict: CHANDRA_GOOD.has(pos) ? 'good' : (CHANDRA_PUJA.has(pos) ? 'puja' : 'bad') };
}

function tbProfiles() {
  const out = [];
  for (let i = 0; i < TB_ROWS; i++) {
    const nak = selEl(`tb-nak-${i}`).value;
    if (!nak) continue;
    const name = inpEl(`tb-name-${i}`).value.trim() || (i === 0 ? 'You' : `Person ${i+1}`);
    const pada = Number(selEl(`tb-pada-${i}`).value) || null;
    const lagnaInput = selEl(`tb-lagna-${i}`);
    const lagna = (lagnaInput && lagnaInput.value) ? lagnaInput.value : null;
    out.push({ name, nak, pada, rasi: rasiFromStar(nak, pada), lagna });
  }
  return out;
}

function tbSaveProfiles() {
  const raw = [];
  for (let i = 0; i < TB_ROWS; i++) {
    const lagnaInput = selEl(`tb-lagna-${i}`);
    raw.push({ name: inpEl(`tb-name-${i}`).value,
               nak: selEl(`tb-nak-${i}`).value,
               pada: selEl(`tb-pada-${i}`).value,
               lagna: lagnaInput ? lagnaInput.value : '' });
  }
  localStorage.setItem('tc-tb-profiles', JSON.stringify(raw));
}

let TB_ROWS = 1;  // visible person rows (1..4)

function tbRenderProfileInputs() {
  const saved = JSON.parse(localStorage.getItem('tc-tb-profiles') || '[]');
  TB_ROWS = Math.max(TB_ROWS, Math.min(4, saved.filter(v => v && (v.nak || v.name)).length || 1));
  const wrap = document.getElementById('tb-profiles');
  let html = '';
  for (let i = 0; i < TB_ROWS; i++) {
    const v = saved[i] || { name: '', nak: '', pada: '', lagna: '' };
    const opts = ['<option value="">birth star</option>']
      .concat(TB_NAKSHATRAS.map(n => `<option value="${n}" ${n === v.nak ? 'selected' : ''}>${n}</option>`)).join('');
    const padaOpts = ['<option value="">padam?</option>']
      .concat([1,2,3,4].map(q => `<option value="${q}" ${String(q) === String(v.pada) ? 'selected' : ''}>${q}</option>`)).join('');
    const lagnaOpts = ['<option value="">lagna? (optional)</option>']
      .concat(TB_RASIS.map(r => `<option value="${r}" ${r === v.lagna ? 'selected' : ''}>${r}</option>`)).join('');
    const rasi = v.nak ? rasiFromStar(v.nak, Number(v.pada) || null) : null;
    const rasiNote = (v.nak && !rasi)
      ? '<span class="tb-you" style="color:#8A5518;">add padam for rashi</span>'
      : '';
    html += `<div class="tb-profile-row">
      <input type="text" id="tb-name-${i}" placeholder="${i === 0 ? 'Your name (optional)' : 'Name (optional)'}" value="${v.name || ''}" onchange="tbSaveProfiles()">
      <select id="tb-nak-${i}" onchange="tbSaveProfiles(); tbRenderProfileInputs();">${opts}</select>
      <select id="tb-pada-${i}" style="min-width:90px;" title="Padam (quarter) of the birth star, needed only when the star spans two rashis" onchange="tbSaveProfiles(); tbRenderProfileInputs();">${padaOpts}</select>
      <select id="tb-lagna-${i}" style="min-width:130px;" title="Janma Lagna: the rising sign at the moment of birth. Leave blank if you don't know it; we'll use your janma rashi instead for muhurta scoring." onchange="tbSaveProfiles();">${lagnaOpts}</select>
      ${rasiNote}
      ${i === 0 ? '' : `<button class="tb-remove" title="Remove" onclick="tbRemoveRow(${i})">✕</button>`}
    </div>`;
  }
  wrap.innerHTML = html;
  document.getElementById('tb-add-btn').style.display = TB_ROWS < 4 ? '' : 'none';
}

function tbResetProfiles() {
  if (!confirm('Forget all saved people and choices on this device?')) return;
  localStorage.removeItem('tc-tb-profiles');
  localStorage.removeItem('tc-go-view');
  localStorage.removeItem('tc-go-rasi');
  TB_ROWS = 1;
  TB_DAYS = null;
  tbRenderProfileInputs();
  document.getElementById('tb-summary').innerHTML = '';
  document.getElementById('tb-result').innerHTML = '';
  if (goHasData()) { goBuildViewSelect(); renderGochara(); }
}

function tbAddRow() {
  tbSaveProfiles();
  TB_ROWS = Math.min(4, TB_ROWS + 1);
  tbRenderProfileInputs();
}

function tbRemoveRow(i) {
  const saved = JSON.parse(localStorage.getItem('tc-tb-profiles') || '[]');
  saved.splice(i, 1);
  localStorage.setItem('tc-tb-profiles', JSON.stringify(saved));
  TB_ROWS = Math.max(1, TB_ROWS - 1);
  tbRenderProfileInputs();
}

async function calcTarabalam() {
  const profiles = tbProfiles();
  const resBox = document.getElementById('tb-result');
  if (!profiles.length) {
    resBox.innerHTML = '<p class="preview-error">Pick at least one birth star.</p>';
    return;
  }
  const from = new Date(inpEl('tb-from').value + 'T00:00:00');
  const to = new Date(inpEl('tb-to').value + 'T00:00:00');
  const span = Math.round((to.getTime() - from.getTime()) / 86400000) + 1;
  if (!(span >= 1 && span <= 60)) {
    resBox.innerHTML = '<p class="preview-error">Pick a range of 1 to 60 days.</p>';
    return;
  }
  resBox.innerHTML = '<p class="preview-error">Calculating…</p>';
  try {
    const city = getSelection().city;
    const system = getSelection().system;
    const events = getLoadedEvents() || await loadFeed(city, system);
    TB_EVENTS = events;
    TB_DAYS = [];
    for (let i = 0; i < span; i++) {
      const d = new Date(from); d.setDate(d.getDate() + i);
      const ev = events.get(stampOf(d));
      if (!ev) continue;
      const data = parseDescription(ev.description);
      const nak = data.nakshatra ? data.nakshatra.name : null;
      if (!nak) continue;
      const taras = profiles.map(pr => {
        const t = taraOf(pr.nak, nak);
        const entry: { who: any; tara: number; label: string; good: boolean; chandra?: any } =
          { who: pr.name, tara: t, label: TARA_NAMES[t-1], good: TARA_GOOD.has(t) };
        if (pr.rasi && data.lunarSign) entry.chandra = chandraOf(pr.rasi, data.lunarSign);
        return entry;
      });
      TB_DAYS.push({ date: new Date(d), nak, nakUntil: data.nakshatra.end, nakEflag: data.nakshatra.eflag,
                     moonRasi: data.lunarSign || '', tithi: data.tithi ? data.tithi.name : '', taras });
    }
    renderTarabalam(profiles);
  } catch (e) {
    resBox.innerHTML = '<p class="preview-error">Could not load the feed. Try again.</p>';
  }
}

let TB_SHOW_ALL = false;  // default: only favourable days
let TB_MODE = localStorage.getItem('tc-tb-mode') || 'stars';

function tbSetMode(m) {
  TB_MODE = m;
  localStorage.setItem('tc-tb-mode', m);
  if (TB_DAYS) renderTarabalam();
}

function tbPersonGood(t) {
  if (!t.good) return false;
  if (!t.chandra) return true;
  if (TB_MODE === 'strict') return t.chandra.verdict === 'good';
  if (TB_MODE === 'puja_ok') return t.chandra.verdict !== 'bad';
  return true;  // stars: chandra annotates, never blocks
}

function tbToggleShowAll() {
  TB_SHOW_ALL = inpEl('tb-show-all').checked;
  renderTarabalam();
}

function tbCycleHasGoodDay(profiles) {
  // Tarabalam repeats every 27 nakshatras. When rashis are also set the
  // real cycle is nakshatra x rashi, so only declare impossibility on the
  // star check alone — the look-ahead handles the rest.
  return TB_NAKSHATRAS.some(n =>
    profiles.every(pr => TARA_GOOD.has(taraOf(pr.nak, n))));
}

function tbDayGoodForAll(profiles, nak, moonRasi) {
  return profiles.every(pr => {
    if (!TARA_GOOD.has(taraOf(pr.nak, nak))) return false;
    if (TB_MODE !== 'stars' && pr.rasi && moonRasi) {
      const c = chandraOf(pr.rasi, moonRasi);
      if (c && c.verdict === 'bad') return false;
      if (c && TB_MODE === 'strict' && c.verdict !== 'good') return false;
    }
    return true;
  });
}

function tbNextGoodBeyondRange(profiles) {
  if (!TB_EVENTS || !TB_DAYS.length) return null;
  const after = new Date(TB_DAYS[TB_DAYS.length - 1].date);
  for (let i = 1; i <= 365; i++) {
    const d = new Date(after); d.setDate(d.getDate() + i);
    const ev = TB_EVENTS.get(stampOf(d));
    if (!ev) return null;  // feed horizon reached
    const data = parseDescription(ev.description);
    const nak = data.nakshatra && data.nakshatra.name;
    if (nak && tbDayGoodForAll(profiles, nak, data.lunarSign)) return d;
  }
  return null;
}

function tbExtendTo(iso) {
  inpEl('tb-to').value = iso;
  calcTarabalam();
}

function renderTarabalam(profiles?) {
  if (!TB_DAYS) return;
  profiles = profiles || tbProfiles();
  const group = profiles.length > 1;
  TB_DAYS.forEach(r => { r.allGood = r.taras.every(tbPersonGood); });
  selEl('tb-mode').value = TB_MODE;
  const goodDays = TB_DAYS.filter(r => r.allGood);
  const next = goodDays[0];
  const who = group ? 'everyone' : (profiles[0] ? profiles[0].name : 'you');
  let summary = `<span class="count">${goodDays.length} of ${TB_DAYS.length}</span>&nbsp;days are favourable for ${who}`;
  if (next) {
    summary += ` · next: <span class="count">${next.date.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })}</span>`;
  }
  const share = goodDays.length
    ? `<button class="wa-share-mini" style="position:static;width:28px;height:28px;flex:none;" title="Share these good days on WhatsApp" aria-label="Share on WhatsApp" onclick="shareTarabalamOnWhatsApp()"><svg viewBox="0 0 24 24" width="15" height="15" fill="currentColor" aria-hidden="true"><path d="M12.04 2a9.9 9.9 0 0 0-8.46 15.1L2 22l5.05-1.55A9.9 9.9 0 1 0 12.04 2zm0 18.1a8.2 8.2 0 0 1-4.18-1.15l-.3-.18-3 .92.93-2.92-.2-.3a8.2 8.2 0 1 1 6.75 3.63zm4.5-6.14c-.25-.12-1.46-.72-1.69-.8-.22-.08-.39-.12-.55.13-.17.24-.64.8-.78.96-.14.16-.29.18-.53.06a6.7 6.7 0 0 1-3.35-2.93c-.25-.43.25-.4.72-1.34.08-.16.04-.3-.02-.43-.06-.12-.55-1.33-.76-1.82-.2-.48-.4-.42-.55-.43h-.47c-.16 0-.43.06-.65.3-.22.25-.85.84-.85 2.04 0 1.2.88 2.36 1 2.52.12.16 1.72 2.63 4.17 3.69.58.25 1.04.4 1.4.51.58.19 1.11.16 1.53.1.47-.07 1.46-.6 1.67-1.18.2-.58.2-1.07.14-1.18-.06-.1-.22-.16-.47-.28z"/></svg></button>`
    : '';
  const toggle = `<label class="tb-toggle"><input type="checkbox" id="tb-show-all" ${TB_SHOW_ALL ? 'checked' : ''} onchange="tbToggleShowAll()"> show all days</label>${share}`;
  document.getElementById('tb-summary').innerHTML =
    `<div class="tb-summary">${group ? '<span class="tb-star">✦</span>' : '🟢'} ${summary}${toggle}</div>`;
  const rows = TB_DAYS.filter(r => TB_SHOW_ALL || r.allGood);
  if (!rows.length) {
    if (!tbCycleHasGoodDay(profiles)) {
      document.getElementById('tb-result').innerHTML =
        `<p class="preview-error">This combination of birth stars never aligns; tarabalam repeats over the
         27 nakshatras, and no day is favourable for ${group ? 'all ' + profiles.length + ' people' : htmlEsc(who)} at once.
         Tick "show all days" to plan by individual taras, or consult your purohit.</p>`;
      return;
    }
    const nextGood = tbNextGoodBeyondRange(profiles);
    if (nextGood) {
      const iso = `${nextGood.getFullYear()}-${String(nextGood.getMonth()+1).padStart(2,'0')}-${String(nextGood.getDate()).padStart(2,'0')}`;
      const label = nextGood.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
      document.getElementById('tb-result').innerHTML =
        `<p class="preview-error">No favourable days for ${htmlEsc(who)} in this range.
         The next one is <strong>${label}</strong>:
         <button class="read-more" style="color:var(--indigo);" onclick="tbExtendTo('${iso}')">extend the range to include it</button>,
         or tick "show all days".</p>`;
    } else {
      document.getElementById('tb-result').innerHTML =
        `<p class="preview-error">No favourable days for ${who} in this range, and none found in the months ahead.
         Tick "show all days" to plan by individual taras.</p>`;
    }
    return;
  }
  const head = `<tr><th>Date</th><th>Moon in</th><th>Tithi</th>${profiles.map(p => {
    // Sub-line surfaces nakshatra + derived rashi + (when set)
    // natal lagna so the user can see which Jyotisha frame each
    // column is being scored against. Lagna only appears when
    // the optional dropdown was filled for that profile.
    const parts = [htmlEsc(p.nak)];
    if (p.rasi) parts.push(`${htmlEsc(p.rasi)} rashi`);
    if (p.lagna) parts.push(`${htmlEsc(p.lagna)} lagna`);
    return `<th>${htmlEsc(p.name)}<div class="tb-sub">${parts.join(' · ')}</div></th>`;
  }).join('')}${profiles.length > 1 ? '<th title="Auspicious for everyone selected">All ✦</th>' : ''}</tr>`;
  const body = rows.map(r => {
    const dlabel = r.date.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
    const chips = r.taras.map(t => {
      // chip colour = verdict under the chosen ✦ standard; the Moon is a
      // marked caveat (° puja, ☾ moon-avoid), never a silent veto
      const passes = tbPersonGood(t);
      const caveat = t.chandra && t.chandra.verdict !== 'good' ? t.chandra.verdict : null;
      const ord = n => n + (['st','nd','rd'][n-1] || 'th');
      const chandraTag = t.chandra && t.chandra.verdict !== 'good'
        ? (caveat === 'puja' ? ` · ° ${ord(t.chandra.pos)}` : ` · ☾ ${ord(t.chandra.pos)}`)
        : '';
      const mark = '';
      // colour follows the chosen standard: under 'Stars only' the chips are
      // pure star verdicts; amber only when the standard admits a day on the
      // condition of a remedial puja
      const cls = !passes ? 'bad'
        : (TB_MODE === 'puja_ok' && caveat === 'puja' ? 'puja' : 'good');
      const detail = `Tara: ${t.tara} ${t.label} (${t.good ? 'good' : 'avoid'})` +
        (t.chandra ? ` · Chandra: ${t.chandra.pos}${['st','nd','rd'][t.chandra.pos-1] || 'th'} from rashi (${t.chandra.verdict === 'puja' ? 'needs puja' : t.chandra.verdict})` : '') +
        (r.moonRasi ? ` · Moon in ${r.moonRasi}` : '');
      return `<td><span class="tara-chip ${cls}" title="${detail}">${t.tara} ${t.label}${chandraTag}</span></td>`;
    }).join('');
    const all = profiles.length > 1 ? `<td>${r.allGood ? '<span class="tb-star">✦</span>' : ''}</td>` : '';
    return `<tr class="${r.allGood && profiles.length > 1 ? 'tb-all' : ''}">
      <td class="tb-date-cell">${dlabel}</td>
      <td>${r.nak}<div class="tb-sub">till ${fmtT(r.nakUntil)}${r.nakEflag === '+1' ? ' +1' : ''}</div></td>
      <td>${r.tithi}</td>${chips}${all}</tr>`;
  }).join('');
  const shown = TB_DAYS.filter(r => TB_SHOW_ALL || r.allGood);
  const hasPuja = shown.some(r => r.taras.some(t => t.chandra && t.chandra.verdict === 'puja'));
  const hasMoonBad = shown.some(r => r.taras.some(t => t.chandra && t.chandra.verdict === 'bad'));
  const modeLabel = { stars: 'Stars only (classic)', puja_ok: 'Stars + Moon, puja ok', strict: 'Stars + Moon, strict' }[TB_MODE];
  let legend = `<div class="tb-readme"><div class="tb-readme-title">How to read this table</div>
    <div><span class="tara-chip good">green</span> a good day for that person, under your standard (<em>${modeLabel}</em>).</div>
    <div><span class="tara-chip bad">red</span> not suitable for that person.</div>`;
  if (TB_MODE === 'puja_ok' && hasPuja) {
    legend += `<div><span class="tara-chip puja">amber</span> good: a small remedial puja is advised (°).</div>`;
  } else if (hasPuja) {
    legend += `<div><strong>°</strong> a small remedial puja is advised for the Moon's position.</div>`;
  }
  if (hasMoonBad) {
    legend += `<div><strong>☾</strong> the Moon's position is unfavourable that day.</div>`;
  }
  if (group) {
    legend += `<div><span class="tb-star">✦</span> the day is favourable for <strong>everyone</strong>, under your standard.</div>`;
  }
  legend += `</div>`;
  // Mobile-only stacked cards: same data, no horizontal swipe
  const cards = rows.map(r => {
    const dlabel = r.date.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
    const personRows = r.taras.map((t, i) => {
      const passes = tbPersonGood(t);
      const caveat = t.chandra && t.chandra.verdict !== 'good' ? t.chandra.verdict : null;
      const ord = n => n + (['st','nd','rd'][n-1] || 'th');
      const chandraTag = t.chandra && t.chandra.verdict !== 'good'
        ? (caveat === 'puja' ? ` · ° ${ord(t.chandra.pos)}` : ` · ☾ ${ord(t.chandra.pos)}`)
        : '';
      const cls = !passes ? 'bad'
        : (TB_MODE === 'puja_ok' && caveat === 'puja' ? 'puja' : 'good');
      // Mobile card sub-line: name · nak · optional rashi/lagna.
      const p = profiles[i];
      let subText = '';
      if (p) {
        const extras = [htmlEsc(p.nak)];
        if (p.rasi) extras.push(`${htmlEsc(p.rasi)} rashi`);
        if (p.lagna) extras.push(`${htmlEsc(p.lagna)} lagna`);
        subText = `<span class="tb-sub">${htmlEsc(p.name)}<span style="color:#DDD2BC"> · ${extras.join(' · ')}</span></span>`;
      }
      const sub = subText;
      return `<div class="tb-card-row">${sub}<span class="tara-chip ${cls}">${t.tara} ${t.label}${chandraTag}</span></div>`;
    }).join('');
    const star = (r.allGood && profiles.length > 1) ? '<span class="tb-star">✦</span> good for everyone' : '&nbsp;';
    return `<div class="tb-card ${r.allGood && profiles.length > 1 ? 'tb-all' : ''}">
      <div class="tb-card-head">
        <span class="tb-date-cell">${dlabel}</span>
        <span class="tb-card-flag">${star}</span>
      </div>
      <div class="tb-card-sub">${r.nak} till ${fmtT(r.nakUntil)}${r.nakEflag === '+1' ? ' +1' : ''} · ${r.tithi}</div>
      ${personRows}
    </div>`;
  }).join('');
  document.getElementById('tb-result').innerHTML =
    `<div class="tb-table-wrap"><table class="tb-table">${head}${body}</table></div>` +
    `<div class="tb-cards">${cards}</div>${legend}`;
}

function shareTarabalamOnWhatsApp() {
  if (!TB_DAYS) return;
  const profiles = tbProfiles();
  const group = profiles.length > 1;
  TB_DAYS.forEach(r => { r.allGood = r.taras.every(tbPersonGood); });
  selEl('tb-mode').value = TB_MODE;
  TB_DAYS.forEach(r => { r.allGood = r.taras.every(tbPersonGood); });
  const goodDays = TB_DAYS.filter(r => r.allGood);
  if (!goodDays.length) return;
  const citySel = selEl('tp-city');
  const cityLabel = citySel.options[citySel.selectedIndex].textContent;
  const fmtD = d => d.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
  const lines = [];
  const anyRasi = profiles.some(pr => pr.rasi);
  lines.push(`✦ *Good days ${group ? 'for all of us' : 'for me'} (${anyRasi ? 'Tarabalam · Chandrabalam' : 'Tarabalam'})*`);
  lines.push(`📍 ${cityLabel} · ${fmtD(TB_DAYS[0].date)} to ${fmtD(TB_DAYS[TB_DAYS.length-1].date)}`);
  lines.push(profiles.map(pr => `${pr.name}: ${pr.nak}`).join(' · '));
  lines.push(`Standard: ${{ stars: 'Stars only (classic)', puja_ok: 'Stars + Moon, puja ok', strict: 'Stars + Moon, strict' }[TB_MODE]}`);
  lines.push('');
  goodDays.forEach(r => lines.push(`✅ ${fmtD(r.date)} · ${r.nak} · ${r.tithi}`));
  lines.push('');
  lines.push('Check your own birth star:');
  lines.push('https://panchangam.astrochaganti.com/?src=share-tarabalam#tarabalam');
  gcEvent('share-tarabalam');
  window.open('https://wa.me/?text=' + encodeURIComponent(lines.join('\n')), '_blank');
}

// --- Gochara tool ---


// --- Muhurta finder (client-side, from the already-loaded feed) ---

const MU_GOOD_CHOG = { Amrit: 3, Shubh: 2, Labh: 2, Char: 1 };
const MU_YOGA_BONUS = { 'Sarvartha Siddhi Yoga': 2, 'Amrita Siddhi Yoga': 2,
                        'Dvipushkara Yoga': 1, 'Tripushkara Yoga': 1 };
const MU_YOGA_PENALTY = { 'Visha Yoga': -2, 'Dagdha Yoga': -2 };

// MU_TIER_NAMES, muScoreTier, muRelativeTier — imported from
// src/muhurta-scorer.ts (see the import block at the top of this
// file).
// Tier each slot relative to the min/max score in this batch — mirror
// telugu_panchangam/personal/muhurta.assign_tiers. "Excellent" means
// the best of what turned up in this search, not a fixed bar.
function muAssignTiers(slots) {
  if (!slots.length) return;
  let ceiling = -Infinity, floor = Infinity;
  for (const s of slots) {
    if (s.score > ceiling) ceiling = s.score;
    if (s.score < floor) floor = s.score;
  }
  for (const s of slots) {
    let tier = muRelativeTier(s.score, ceiling, floor);
    if ((s.personalDosha || s.dayDosha) && tier === 'Excellent') tier = 'Good';
    s.tier = tier;
  }
}

// Nitya Yoga scoring — mirror telugu_panchangam/personal/nitya_yoga.py
const MU_NITYA_HARD_AVOID = new Set(['Vyatipata', 'Vaidhriti']);
const MU_NITYA_HARD_PENALTY = -2;
const MU_NITYA_PARTIAL_WINDOW_MIN = {  // dosha-window minutes from yoga start
  'Vishkambha': 3 * 24, 'Atiganda': 6 * 24, 'Shoola': 5 * 24,
  'Ganda': 6 * 24, 'Vyaghata': 9 * 24, 'Parigha': 5 * 24,
};
const MU_NITYA_PARTIAL_PENALTY = -1;
const MU_NITYA_AUSPICIOUS = new Set([
  'Preeti', 'Ayushman', 'Saubhagya', 'Shobhana',
  'Sukarma', 'Dhriti', 'Vriddhi', 'Dhruva',
  'Harshana', 'Siddhi', 'Shiva', 'Siddha',
  'Sadhya', 'Shubha', 'Shukla', 'Brahma', 'Indra',
]);
const MU_NITYA_AUSPICIOUS_BONUS = 1;

function muMin(t, flag?) {
  const [h, m] = t.split(':').map(Number);
  return h * 60 + m + (flag === '+1' ? 1440 : flag === '-1' ? -1440 : 0);
}

function muSubtract(s, e, blocks) {
  let pieces = [[s, e]];
  for (const [b0, b1] of blocks) {
    const nxt = [];
    for (const [p0, p1] of pieces) {
      if (b1 <= p0 || b0 >= p1) { nxt.push([p0, p1]); continue; }
      if (p0 < b0) nxt.push([p0, b0]);
      if (b1 < p1) nxt.push([b1, p1]);
    }
    pieces = nxt;
  }
  return pieces;
}

// ---------- Slot-time astronomy (Batch F2) ----------------------------
//
// Meeus low-precision Sun/Moon longitudes + Lahiri ayanamsa. Lets us
// recompute the panchangam anga (nakshatra, tithi, yoga, karana, moon
// rashi, special yogas) at any datetime — matching the Python engine's
// facts_at() so the in-page muhurta finder gets slot-time precision
// instead of just the sunrise snapshot from the feed.
//
// Accuracy: Sun ~0.01°, Moon ~0.1-0.3°. Nakshatra boundaries are
// 13.33° wide and tithi boundaries 12° wide, so this is comfortably
// sufficient for slot-time scoring.

const MU_NAKSHATRA_LIST = TB_NAKSHATRAS;     // already defined above

const MU_TITHI_LIST_FULL = (() => {
  const last = ['Pratipat','Dwitiya','Tritiya','Chaturthi','Panchami',
                'Shashthi','Saptami','Ashtami','Navami','Dashami',
                'Ekadashi','Dwadashi','Trayodashi','Chaturdashi','Pournami'];
  const shukla = last.slice(0, 14).map(n => `Shukla ${n}`).concat(['Pournami']);
  const krishna = last.slice(0, 14).map(n => `Krishna ${n}`).concat(['Amavasya']);
  return shukla.concat(krishna);
})();

const MU_YOGA_NAMES_27 = [
  'Vishkambha','Priti','Ayushman','Saubhagya','Shobhana','Atiganda',
  'Sukarma','Dhriti','Shula','Ganda','Vriddhi','Dhruva','Vyaghata',
  'Harshana','Vajra','Siddhi','Vyatipata','Variyana','Parigha','Shiva',
  'Siddha','Sadhya','Shubha','Shukla','Brahma','Indra','Vaidhriti',
];

const MU_KARANA_REPEATING = ['Bava','Balava','Kaulava','Taitila','Garaja','Vanija','Vishti'];
const MU_KARANA_FIXED = { 0: 'Kinstughna', 57: 'Shakuni', 58: 'Chatushpada', 59: 'Naga' };

// Special yogas — mirror telugu_panchangam/special_yogas.py
const MU_SARVARTHA = {
  Adivaram:    new Set(['Hasta','Mula','Pushya','Ashvini','Punarvasu','Anuradha','Shravana','Revati']),
  Somavaram:   new Set(['Shravana','Rohini','Mrigashira','Pushya','Anuradha']),
  Mangalavaram:new Set(['Ashvini','Krittika','Ashlesha','Uttara Ashadha','Uttara Phalguni','Uttara Bhadrapada']),
  Budhavaram:  new Set(['Krittika','Rohini','Hasta','Anuradha','Mrigashira']),
  Guruvaram:   new Set(['Ashvini','Punarvasu','Anuradha','Revati','Pushya','Swati']),
  Shukravaram: new Set(['Revati','Anuradha','Ashvini','Pushya','Shravana','Punarvasu']),
  Shanivaram:  new Set(['Swati','Rohini','Shravana']),
};
const MU_AMRITA_SIDDHI = {
  Adivaram:'Hasta', Somavaram:'Mrigashira', Mangalavaram:'Ashvini',
  Budhavaram:'Anuradha', Guruvaram:'Pushya', Shukravaram:'Revati', Shanivaram:'Rohini',
};
const MU_VISHA_TITHI = { Adivaram:5, Somavaram:6, Mangalavaram:7, Budhavaram:8,
                         Guruvaram:9, Shukravaram:10, Shanivaram:11 };
const MU_DAGDHA_TITHI = { Adivaram:new Set([12]), Somavaram:new Set([11]),
                          Mangalavaram:new Set([5]), Budhavaram:new Set([2,3]),
                          Guruvaram:new Set([6]), Shukravaram:new Set([8]), Shanivaram:new Set([9]) };
const MU_PUSHKARA_VARAS = new Set(['Adivaram','Mangalavaram','Shanivaram']);
const MU_DVI_TITHIS = new Set([2,7,12]);
const MU_DVI_NAKS   = new Set(['Mrigashira','Chitra','Dhanishtha']);
const MU_TRI_TITHIS = new Set([2,7,12]);
const MU_TRI_NAKS   = new Set(['Krittika','Punarvasu','Uttara Phalguni',
                                'Vishakha','Uttara Ashadha','Purva Bhadrapada']);

function muSpecialYogasAt(vaaram, tithiName, nakshatraName) {
  const yogas = [];
  if (MU_SARVARTHA[vaaram] && MU_SARVARTHA[vaaram].has(nakshatraName))
    yogas.push('Sarvartha Siddhi Yoga');
  if (MU_AMRITA_SIDDHI[vaaram] === nakshatraName)
    yogas.push('Amrita Siddhi Yoga');
  const tithiBase = MU_TITHI_LIST_FULL.indexOf(tithiName) % 15 + 1;
  if (tithiBase === MU_VISHA_TITHI[vaaram]) yogas.push('Visha Yoga');
  if (MU_DAGDHA_TITHI[vaaram] && MU_DAGDHA_TITHI[vaaram].has(tithiBase))
    yogas.push('Dagdha Yoga');
  if (MU_PUSHKARA_VARAS.has(vaaram)) {
    if (MU_DVI_TITHIS.has(tithiBase) && MU_DVI_NAKS.has(nakshatraName))
      yogas.push('Dvipushkara Yoga');
    if (MU_TRI_TITHIS.has(tithiBase) && MU_TRI_NAKS.has(nakshatraName))
      yogas.push('Tripushkara Yoga');
  }
  return yogas;
}

// Julian Day from a JS Date (UTC)
function muJD(dt) { return dt.getTime() / 86400000 + 2440587.5; }

// Lahiri ayanamsa (linear approximation; ~0.01° accuracy in the
// current era — good enough for nakshatra/tithi boundaries).
function muLahiri(jd) {
  return 23.85 + ((jd - 2451545.0) / 365.25) * 0.01397;
}

// Sun apparent longitude, sidereal (Lahiri). Meeus low-precision.
function muSunLong(jd) {
  const T = (jd - 2451545.0) / 36525;
  const L = ((280.460 + 36000.770 * T) % 360 + 360) % 360;
  const g = ((357.528 + 35999.050 * T) % 360 + 360) % 360;
  const gr = g * Math.PI / 180;
  const tropical = L + 1.915 * Math.sin(gr) + 0.020 * Math.sin(2 * gr);
  return ((tropical - muLahiri(jd)) % 360 + 360) % 360;
}

// Moon apparent longitude, sidereal (Lahiri). Meeus 12 leading terms.
function muMoonLong(jd) {
  const T = (jd - 2451545.0) / 36525;
  const d2r = Math.PI / 180;
  const Lp = ((218.3164477 + 481267.88123421 * T) % 360 + 360) % 360;
  const D  = ((297.8501921 + 445267.1114034 * T) % 360 + 360) % 360;
  const M  = ((357.5291092 + 35999.0502909 * T) % 360 + 360) % 360;
  const Mp = ((134.9633964 + 477198.8675055 * T) % 360 + 360) % 360;
  const F  = (( 93.2720950 + 483202.0175233 * T) % 360 + 360) % 360;
  const s  = a => Math.sin(a * d2r);
  const tropical = Lp
    + 6.288774 * s(Mp)
    + 1.274027 * s(2*D - Mp)
    + 0.658314 * s(2*D)
    + 0.213618 * s(2*Mp)
    - 0.185116 * s(M)
    - 0.114332 * s(2*F)
    + 0.058793 * s(2*D - 2*Mp)
    + 0.057066 * s(2*D - M - Mp)
    + 0.053322 * s(2*D + Mp)
    + 0.045758 * s(2*D - M)
    - 0.040923 * s(M - Mp)
    - 0.034720 * s(D);
  return ((tropical - muLahiri(jd)) % 360 + 360) % 360;
}

// factsAt(dt, vaaram) — slot-time anga, mirroring Python engine.facts_at.
function muFactsAt(dt, vaaram) {
  const jd = muJD(dt);
  const sun = muSunLong(jd);
  const moon = muMoonLong(jd);
  const elong = ((moon - sun) % 360 + 360) % 360;
  const nakSize = 360 / 27;
  const nakIdx = Math.floor(moon / nakSize) % 27;
  const nakshatra = MU_NAKSHATRA_LIST[nakIdx];
  const tithiIdx = Math.floor(elong / 12) % 30;
  const tithi = MU_TITHI_LIST_FULL[tithiIdx];
  const yogaIdx = Math.floor(((sun + moon) % 360) / nakSize) % 27;
  const yoga = MU_YOGA_NAMES_27[yogaIdx];
  const htIdx = Math.floor(elong / 6) % 60;
  const karana = MU_KARANA_FIXED[htIdx] !== undefined
    ? MU_KARANA_FIXED[htIdx]
    : MU_KARANA_REPEATING[(htIdx - 1 + 7) % 7];
  const rashiIdx = Math.floor(moon / 30) % 12;
  const lunarSign = TB_RASIS[rashiIdx];
  const specialYogas = muSpecialYogasAt(vaaram, tithi, nakshatra);
  return { nakshatra, tithi, yoga, karana, lunarSign, vaaram, specialYogas };
}

// MU_CHANDRA_GOOD/MU_CHANDRA_PUJA, MU_LAGNA_KENDRA/MU_LAGNA_TRIKONA,
// MU_RASHI_NAMES, muLagnaPosition, muLagnaVerdict, muIsFavourableLagna,
// muLagnaAtMin — all live in src/muhurta-scorer.ts (imported at the
// top of this file) so they can be unit-tested under Vitest.
// CHANDRA bad = {4, 8, 12} (the complement).

// Tithi family — mirror telugu_panchangam/personal/tithi_class.py
const TITHI_NAMES_ORDER = [
  'Pratipat', 'Dwitiya', 'Tritiya', 'Chaturthi', 'Panchami',
  'Shashthi', 'Saptami', 'Ashtami', 'Navami',    'Dashami',
  'Ekadashi', 'Dwadashi','Trayodashi','Chaturdashi','Pournami',
];
const TITHI_ALIASES = { Pratipada: 1, Prathama: 1, Shashti: 6, Amavasya: 15 };
function activityTithiNumber(name) {
  if (!name) return null;
  const last = name.trim().split(/\s+/).pop();
  if (TITHI_ALIASES[last]) return TITHI_ALIASES[last];
  const idx = TITHI_NAMES_ORDER.indexOf(last);
  return idx >= 0 ? idx + 1 : null;
}

// Activity rules — mirror telugu_panchangam/personal/muhurta.py
// ACTIVITY_RULES. Only the fields the JS scorer consumes are duplicated
// here (label, prefer_tithi_class, prefer_vara). skip_on_yoga and
// avoid_karana are still enforced by the engine; the JS reads
// parsed-feed yogas and karanas to mirror behaviour for activities the
// user picks via the in-page dropdown.
const MU_ACTIVITY = activityContract.rules;
async function findMuhurta() {
  const box = document.getElementById('mu-result');
  box.innerHTML = '<p class="preview-error">Searching…</p>';
  const activity = selEl('mu-activity').value;
  const from = new Date(inpEl('tb-from').value + 'T00:00:00');
  const to = new Date(inpEl('tb-to').value + 'T00:00:00');
  const nDays = Math.min(60, Math.max(1, Math.round((to.getTime() - from.getTime()) / 86400000) + 1));
  const people = tbProfiles();
  const chandraMode = TB_MODE;  // 'stars' | 'puja_ok' | 'strict' — filters only, never scores
  document.getElementById('mu-context').innerHTML = people.length
    ? `Searching <strong>${inpEl('tb-from').value}</strong> to <strong>${inpEl('tb-to').value}</strong>, screened by the stars of <strong>${people.map(p => htmlEsc(p.name)).join(', ')}</strong> (set above).`
    : `Searching <strong>${inpEl('tb-from').value}</strong> to <strong>${inpEl('tb-to').value}</strong> · no people set above, so no star screening.`;
  try {
    const city = getSelection().city;
    const system = getSelection().system;
    const events = getLoadedEvents() || await loadFeed(city, system);
    // Lagna data is needed when (a) people are set — for the
    // per-person kendra/trikona/Ashtama check — OR (b) the chosen
    // activity has a preferred lagna class (Sthira/Chara/...).
    // Cached per session, shared with the day-card's lagna ribbon.
    const activityRules = MU_ACTIVITY[activity] || MU_ACTIVITY.any;
    const activityNeedsLagna = !!(
      activityRules.prefer_lagna_class || activityRules.required_lagna_class ||
      activityRules.allowed_lagnas?.length || activityRules.skip_on_combust?.length);
    const lagnaCityData = (people.length || activityNeedsLagna)
      ? await loadLagna(city) : null;
    const slots = [];
    let droppedEclipseDays = 0;
    let droppedModeDays = 0;
    let droppedModeSlots = 0;
    const droppedDays = [];
    const slotsPerDay = new Map();   // YYYY-MM-DD → count
    for (let i = 0; i < nDays; i++) {
      const d = new Date(from); d.setDate(d.getDate() + i);
      const ev = events.get(stampOf(d));
      if (!ev) continue;
      const data = parseDescription(ev.description);
      const isoDate = stampOf(d).replace(/^(\d{4})(\d{2})(\d{2})$/, '$1-$2-$3');

      // Eclipse: auspicious activities are deferred outright.
      if (data.eclipse) {
        droppedEclipseDays++;
        const kind = data.eclipse.kind || 'Eclipse';
        droppedDays.push({ date: isoDate, reason: `${kind} · auspicious activities deferred` });
        continue;
      }

      const rules = MU_ACTIVITY[activity] || MU_ACTIVITY.any;
      const skipYogas = new Set(rules.skip_on_yoga || []);
      const preferChog = rules.prefer_choghadiya || null;     // ['Block', bonus]
      const avoidKaranaNames = new Set(rules.avoid_karana || []);
      const preferTithiClass = rules.prefer_tithi_class || null;
      const avoidTithiClasses = rules.avoid_tithi_class || [];
      const preferVaras = new Set(rules.prefer_vara || []);
      const preferLagnaClass = rules.prefer_lagna_class || null;
      const requiredLagnaClass = rules.required_lagna_class || null;
      const allowedLagnas = new Set(rules.allowed_lagnas || []);
      const preferLagnas = new Set(rules.prefer_lagnas || []);
      const cautionLagnaSolar = !!rules.caution_lagna_solar;
      const allowedNakshatras = new Set(
        (rules.allowed_nakshatras || []).map(muCanonicalNakshatra));
      const avoidNakshatras = new Set(
        (rules.avoid_nakshatras || []).map(muCanonicalNakshatra));
      const avoidJanmaNakshatra = !!rules.avoid_janma_nakshatra;
      const preferNakshatras = new Set(
        (rules.prefer_nakshatras || []).map(muCanonicalNakshatra));
      const allowedTithiNumbers = new Set(rules.allowed_tithi_numbers || []);
      const preferTithiNumbers = new Set(rules.prefer_tithi_numbers || []);
      const allowedTithiNames = new Set(rules.allowed_tithi_names || []);
      const avoidTithiNumbers = new Set(rules.avoid_tithi_numbers || []);
      const manualChecks = rules.manual_checks || [];
      const activityLabel = rules.label;
      const combustionReason = muCombustionDropReason(
        lagnaCityData ? lagnaDayFor(lagnaCityData, isoDate) : null,
        rules.skip_on_combust || [], activityLabel);
      if (combustionReason) {
        droppedDays.push({ date: isoDate, reason: combustionReason });
        continue;
      }

      const normalizedMaasam = (data.maasam || '').replace(/^(?:Nija|Adhika)\s+/, '');
      if (rules.allowed_maasams?.length && !rules.allowed_maasams.includes(normalizedMaasam)) {
        droppedDays.push({ date: isoDate,
          reason: `${data.maasam} Maasa · ${activityLabel} source profile does not admit this lunar month` });
        continue;
      }
      if (rules.allowed_varas?.length && !rules.allowed_varas.includes(data.vaaram)) {
        droppedDays.push({ date: isoDate,
          reason: `${data.vaaram} · ${activityLabel} source profile does not admit this weekday` });
        continue;
      }
      if (rules.allowed_pakshams?.length && !rules.allowed_pakshams.includes(data.paksham)) {
        droppedDays.push({ date: isoDate,
          reason: `${data.paksham} Paksha · ${activityLabel} source profile does not admit this lunar fortnight` });
        continue;
      }
      if ((rules.avoid_vara_paksha || []).some(pair =>
        pair[0] === data.vaaram && pair[1] === data.paksham)) {
        droppedDays.push({ date: isoDate,
          reason: `${data.vaaram} during ${data.paksham} Paksha · ${activityLabel} source profile rejects this combination` });
        continue;
      }
      const solarClass = data.solarSign ? muLagnaClassOf(data.solarSign) : null;
      if (rules.allowed_solar_classes?.length &&
          (!solarClass || !rules.allowed_solar_classes.includes(solarClass))) {
        droppedDays.push({ date: isoDate,
          reason: `Surya in ${data.solarSign} (${solarClass}) · ${activityLabel} source profile does not admit this Rasi class` });
        continue;
      }
      if (rules.allowed_solar_signs?.length &&
          !rules.allowed_solar_signs.includes(data.solarSign)) {
        droppedDays.push({ date: isoDate,
          reason: `Surya in ${data.solarSign} · ${activityLabel} source profile does not admit this solar Rasi` });
        continue;
      }

      // Vara is sunrise-anchored — compute once per day.
      const varaBonus = (data.vaaram && preferVaras.has(data.vaaram)) ? 1 : 0;
      const varaReason = varaBonus
        ? `${data.vaaram} favoured for ${activityLabel} (+1)` : null;

      const bad = data.inauspicious.map(w => [muMin(w.start, w.sflag), muMin(w.end, w.eflag)]);
      if (avoidKaranaNames.size && data.karana) {
        for (const k of data.karana.split(/\s+\/\s+/)) {
          const m = k.match(new RegExp(`^(.*?)\\s+${TIME_PART}\\s*[–-]\\s*${TIME_PART}$`));
          if (m && avoidKaranaNames.has(m[1].trim())) bad.push([muMin(m[2], m[3]), muMin(m[4], m[5])]);
        }
      }
      const abhijit = data.auspicious.find(w => w.name === 'Abhijit Muhurta');
      const amrita = data.auspicious.filter(w => w.name === 'Amrita Kalam');

      // Day-context strip shown on every slot card for this day: the
      // sunrise-anchored anga (matches the Panchangam tab), a visible teaser
      // of the timings people cross-check most (Sunrise, Abhijit, Rahu
      // Kalam), and the full Panchangam auspicious/avoid window lists behind
      // an expand. Display only; computed once per day, shared by its slots.
      const fmtRange = (w) => `${muToT(muMin(w.start, w.sflag))} to ${muToT(muMin(w.end, w.eflag))}`;
      // Group by window name so multi-segment windows (e.g. two Durmuhurtham
      // spells) read as one entry with both ranges.
      const groupWins = (arr) => {
        const m = new Map();
        for (const w of arr) {
          if (!m.has(w.name)) m.set(w.name, []);
          m.get(w.name).push(fmtRange(w));
        }
        return [...m.entries()].map(([name, ranges]) => ({ name, ranges }));
      };
      const rahuWin = data.inauspicious.find(w => /Rahu/i.test(w.name));
      const dayCtx = {
        tithi: data.tithi?.name || null,
        nakshatra: data.nakshatra?.name || null,
        yoga: data.yoga?.name || null,
        sunrise: data.sunrise ? muToT(muMin(data.sunrise)) : null,
        abhijit: abhijit ? fmtRange(abhijit) : null,
        rahu: rahuWin ? fmtRange(rahuWin) : null,
        auspicious: groupWins(data.auspicious),
        avoid: groupWins(data.inauspicious),
      };

      const srMin = muMin(data.sunrise);
      const ssMin = muMin(data.sunset);
      const muLen = (ssMin - srMin) / 15;
      // Dominant choghadiya by overlap — a scoring attribute, not a gate;
      // straddle disclosed. Mirrors Python _dominant_choghadiya.
      const dominantChog = (s, e) => {
        let best = null, bestOv = 0; const touched = [];
        for (const blk of data.choghadiya) {
          const bs = muMin(blk.start), be = muMin(blk.end);
          const ov = Math.min(e, be) - Math.max(s, bs);
          if (ov > 0) { touched.push(blk.name); if (ov > bestOv) { best = blk; bestOv = ov; } }
        }
        return { block: best, straddle: best ? (touched.find(n => n !== best.name) || null) : null };
      };
      // Iterate the 15 named daytime muhurtas (sunrise->sunset /15). Mirrors
      // Python day_slots: exclude a muhurta overlapping any inauspicious
      // window, else score it by nature + dominant choghadiya + all factors.
      for (let mi = 0; mi < 15; mi++) {
          // Round muhurta bounds to whole minutes (display + integer-minute
          // math); contiguous because both edges round the same expression.
          const s0 = Math.round(srMin + mi * muLen);
          const e0 = Math.round(srMin + (mi + 1) * muLen);
          if (rules.forenoon_only && !muEndsBySolarNoon(e0, srMin, ssMin)) continue;
          if (bad.some(([b0, b1]) => s0 < b1 && b0 < e0)) continue;  // decision 1
          const dom = dominantChog(s0, e0);
          const c = dom.block;
          if (!c) continue;
          const base = MU_GOOD_CHOG[c.name] || 0;
          const muRow = MUHURTA_DAY[mi];
          const isAbhijit = mi === 7 && !!abhijit;   // no Abhijit on Wednesday (feed omits it)
          const natureBonus = isAbhijit ? 2 : (muRow[2] === 'auspicious' ? 1 : -2);

          // Compute slot-time facts via Meeus Sun/Moon longitudes.
          // s0 is minutes from local midnight of `d`. Convert to a Date
          // object in the same local timezone, then muFactsAt does the
          // UTC → JD conversion internally.
          const slotStart = new Date(d.getTime() + s0 * 60000);
          const facts = muFactsAt(slotStart, data.vaaram);
          if (allowedNakshatras.size && !allowedNakshatras.has(facts.nakshatra)) continue;
          if (avoidNakshatras.has(facts.nakshatra)) continue;
          if (avoidJanmaNakshatra && people.some(
              person => muCanonicalNakshatra(person.nak) === facts.nakshatra)) continue;
          if (allowedTithiNumbers.size &&
              !allowedTithiNumbers.has(activityTithiNumber(facts.tithi))) continue;
          if (allowedTithiNames.size && !allowedTithiNames.has(facts.tithi)) continue;
          if (avoidTithiNumbers.has(activityTithiNumber(facts.tithi))) continue;

          // Build reason groups as we score — slot_quality, day_quality,
          // group_fit, activity_match, notes — mirroring Python's
          // day_slots() reason_groups field.
          let score = base + natureBonus;
          const muLabel = muRow[0] + (isAbhijit ? ' (Abhijit)' : '');
          const muDeity = muRow[1] ? ` · ${muRow[1]}` : '';
          let chogDesc = `${c.name} choghadiya`;
          if (dom.straddle) chogDesc += ` (spans ${dom.straddle})`;
          const chogLine = base ? `${chogDesc} (+${base})` : chogDesc;
          // Middot separators (no em-dash); no "clear of inauspicious
          // windows" line — every surviving muhurta is clear by construction.
          const slotQuality = [
            `${muLabel} muhurta${muDeity} · ${muRow[2]} (${natureBonus >= 0 ? '+' : ''}${natureBonus})`,
            chogLine];
          const dayQuality = [];
          const groupFit = [];
          const activityMatch = [];
          const taraUnfavNames = [];
          const chandraAvoidNames = [];
          const chandraPujaNames = [];
          let hasAshtama = false;

          // Tarabalam — slot-time nakshatra (per-person)
          if (people.length) {
            const fav = [], unfav = [];
            for (let pi = 0; pi < people.length; pi++) {
              const pr = people[pi];
              const t = taroOf_safe(pr.nak, facts.nakshatra);
              const label = `#${pi + 1} (${htmlEsc(pr.name || pr.nak)})`;
              if (TARA_GOOD.has(t)) { fav.push(label); score += 1; }
              else { unfav.push(`${label} ${TARA_NAMES[t - 1]}`); taraUnfavNames.push(label); score -= 1; }
            }
            if (fav.length) groupFit.push(`Tarabalam favourable for ${fav.join(', ')} (+${fav.length})`);
            if (unfav.length) groupFit.push(`Tarabalam avoid for ${unfav.join(', ')} (-${unfav.length})`);
          }

          // Chandrabalam — slot-time moon rashi (per-person + mode filter)
          let dropSlot = false;
          if (people.length) {
            const good = [], puja = [], avoid = [];
            for (let pi = 0; pi < people.length; pi++) {
              const pr = people[pi];
              if (!pr.rasi) continue;
              const c2 = chandraOf(pr.rasi, facts.lunarSign);
              if (!c2) continue;
              const pos = c2.pos;
              const label = `#${pi + 1} (${htmlEsc(pr.name || pr.nak)})`;
              if (MU_CHANDRA_GOOD.has(pos)) { good.push(label); score += 1; }
              else if (MU_CHANDRA_PUJA.has(pos)) { puja.push(`${label} Moon@${pos}`); chandraPujaNames.push(label); }
              else {
                const ashtama = pos === 8 ? ' Ashtama' : '';
                if (pos === 8) hasAshtama = true;
                avoid.push(`${label}${ashtama} Moon@${pos}`); chandraAvoidNames.push(label); score -= 1;
              }
            }
            if (good.length) groupFit.push(`Chandrabalam favourable for ${good.join(', ')} (+${good.length})`);
            if (puja.length) groupFit.push(`Chandrabalam remedial for ${puja.join(', ')} (puja recommended)`);
            if (avoid.length) groupFit.push(`Chandrabalam avoid for ${avoid.join(', ')} (-${avoid.length})`);

            if (chandraMode === 'strict' && (puja.length || avoid.length)) dropSlot = true;
            else if (chandraMode === 'puja_ok' && avoid.length) dropSlot = true;
          }
          if (dropSlot) { droppedModeSlots++; continue; }

          // Lagna position vs janma rashi — kendra/trikona favour,
          // Ashtama is the rising-sign-axis personal dosha. Mirrors
          // telugu_panchangam/personal/muhurta._score_lagna. Only
          // runs when lagna data was loaded (people.length > 0).
          const ashtamaLagnaNames = [];
          if (people.length && lagnaCityData) {
            const lagnaDay = lagnaDayFor(lagnaCityData, isoDate);
            const slotLagna = lagnaDay ? muLagnaAtMin(lagnaDay, s0) : null;
            if (slotLagna) {
              // Two independent checks per person. Both run when both
              // references are set; each contributes its own +1/-1.
              // When the user opted into Lagna Shuddhi (provided lagna
              // too), we ALSO emit neutral chips so both lenses always
              // appear — no asymmetric silences across slots.
              const favRashi = [], ashRashi = [], neutRashi = [];
              const favLagna = [], ashLagna = [], neutLagna = [];
              const recordAshtama = (label) => {
                if (!ashtamaLagnaNames.includes(label)) ashtamaLagnaNames.push(label);
              };
              const ord = n => `${n}${ ({1:'st',2:'nd',3:'rd'})[n] || 'th' }`;
              for (let pi = 0; pi < people.length; pi++) {
                const pr = people[pi];
                const label = `#${pi + 1} (${htmlEsc(pr.name || pr.nak)})`;
                const hasLagna = !!pr.lagna;
                // Always: from janma rashi (Chandra-Rashi-as-lagna).
                if (pr.rasi) {
                  const pos = muLagnaPosition(pr.rasi, slotLagna);
                  if (pos === 8) {
                    ashRashi.push(`${label} lagna@8 from ${pr.rasi}`);
                    recordAshtama(label);
                    score -= 1;
                  } else if (pos && muIsFavourableLagna(pos)) {
                    favRashi.push(`${label} ${muLagnaVerdict(pos)}@${pos} from ${pr.rasi}`);
                    score += 1;
                  } else if (hasLagna && pos) {
                    // Symmetry chip — opt-in via janma_lagna.
                    neutRashi.push(`${label} ${ord(pos)} from ${pr.rasi}`);
                  }
                }
                // Additionally: from janma lagna (strict Lagna Shuddhi).
                if (hasLagna) {
                  const pos = muLagnaPosition(pr.lagna, slotLagna);
                  if (pos === 8) {
                    ashLagna.push(`${label} lagna@8 from ${pr.lagna} lagna`);
                    recordAshtama(label);
                    score -= 1;
                  } else if (pos && muIsFavourableLagna(pos)) {
                    favLagna.push(`${label} ${muLagnaVerdict(pos)}@${pos} from ${pr.lagna} lagna`);
                    score += 1;
                  } else if (pos) {
                    neutLagna.push(`${label} ${ord(pos)} from ${pr.lagna} lagna`);
                  }
                }
              }
              if (favRashi.length) groupFit.push(
                `${slotLagna} lagna favourable for ${favRashi.join(', ')} (+${favRashi.length})`);
              if (favLagna.length) groupFit.push(
                `${slotLagna} lagna favourable for ${favLagna.join(', ')} (+${favLagna.length})`);
              if (ashRashi.length) groupFit.push(
                `${slotLagna} lagna Ashtama for ${ashRashi.join(', ')} (-${ashRashi.length})`);
              if (ashLagna.length) groupFit.push(
                `${slotLagna} lagna Ashtama for ${ashLagna.join(', ')} (-${ashLagna.length})`);
              if (neutRashi.length) groupFit.push(
                `${slotLagna} lagna neutral for ${neutRashi.join(', ')} (no effect)`);
              if (neutLagna.length) groupFit.push(
                `${slotLagna} lagna neutral for ${neutLagna.join(', ')} (no effect)`);
            }
          }

          if (requiredLagnaClass) {
            const lagnaDay = lagnaCityData ? lagnaDayFor(lagnaCityData, isoDate) : null;
            const slotLagna = lagnaDay ? muLagnaAtMin(lagnaDay, s0) : null;
            const required = muLagnasInClass(requiredLagnaClass);
            if (!slotLagna || !required?.has(slotLagna)) continue;
            activityMatch.push(
              `${slotLagna} lagna satisfies required ${requiredLagnaClass} class`);
          }
          if (allowedLagnas.size) {
            const lagnaDay = lagnaCityData ? lagnaDayFor(lagnaCityData, isoDate) : null;
            const slotLagna = lagnaDay ? muLagnaAtMin(lagnaDay, s0) : null;
            if (!slotLagna || !allowedLagnas.has(slotLagna)) continue;
            activityMatch.push(`${slotLagna} lagna is admitted for ${activityLabel}`);
          }
          if (preferLagnas.size) {
            const lagnaDay = lagnaCityData ? lagnaDayFor(lagnaCityData, isoDate) : null;
            const slotLagna = lagnaDay ? muLagnaAtMin(lagnaDay, s0) : null;
            if (slotLagna && preferLagnas.has(slotLagna)) {
              score += 1;
              activityMatch.push(
                `${slotLagna} lagna specifically favoured for ${activityLabel} (+1)`);
            }
          }

          // Activity-class lagna preference (Muhurta Chintamani):
          // independent of any personal kendra/trikona check —
          // this is about the activity's nature (wedding wants
          // Sthira, travel wants Chara, learning rites want
          // Dvisvabhava). Mirrors _score_lagna_activity in Python.
          if (preferLagnaClass && lagnaCityData) {
            const lagnaDay = lagnaDayFor(lagnaCityData, isoDate);
            const slotLagna = lagnaDay ? muLagnaAtMin(lagnaDay, s0) : null;
            const favoured = muLagnasInClass(preferLagnaClass);
            if (slotLagna && favoured && favoured.has(slotLagna)) {
              score += 1;
              activityMatch.push(
                `${slotLagna} lagna (${preferLagnaClass}) favoured for ${activityLabel} (+1)`);
            }
          }

          // Tithi family — slot-time tithi (Rikta → day_quality penalty;
          // activity class match → activity_match bonus)
          const tithiScore = muScoreTithiClass(
            facts.tithi, preferTithiClass, activityLabel, facts.nakshatra,
            facts.specialYogas, avoidTithiClasses);
          const tFam = tithiScore.family;
          score += tithiScore.bonus;
          if (tithiScore.dayReason) dayQuality.push(tithiScore.dayReason);
          if (tithiScore.activityReason) activityMatch.push(tithiScore.activityReason);
          const activeTithiNumber = activityTithiNumber(facts.tithi);
          if (activeTithiNumber && preferTithiNumbers.has(activeTithiNumber)) {
            score += 1;
            activityMatch.push(
              `${facts.tithi} specifically favoured for ${activityLabel} (+1)`);
          }

          // Special yogas — slot-time
          let yogaSkip = false;
          for (const y of facts.specialYogas) {
            if (MU_YOGA_BONUS[y]) { score += MU_YOGA_BONUS[y]; dayQuality.push(`${y} day (+${MU_YOGA_BONUS[y]})`); }
            if (MU_YOGA_PENALTY[y] !== undefined) {
              if (skipYogas.has(y)) { yogaSkip = true; break; }
              score += MU_YOGA_PENALTY[y]; dayQuality.push(`${y} day (${MU_YOGA_PENALTY[y]})`);
            }
          }
          if (yogaSkip) continue;

          // Nitya yoga — slot-time (samskara skip on Vyatipata/Vaidhriti)
          const ny = facts.yoga;
          if (MU_NITYA_HARD_AVOID.has(ny)) {
            if (skipYogas.size) { continue; }
            score += MU_NITYA_HARD_PENALTY;
            dayQuality.push(`${ny} yoga (${MU_NITYA_HARD_PENALTY})`);
          } else if (MU_NITYA_PARTIAL_WINDOW_MIN[ny] !== undefined && data.yoga) {
            const windowMin = MU_NITYA_PARTIAL_WINDOW_MIN[ny];
            const yogaStartMin = (ny === data.yoga.name)
              ? muMin(data.yoga.start, data.yoga.sflag)
              : muMin(data.yoga.end, data.yoga.eflag);
            if (s0 - yogaStartMin <= windowMin) {
              score += MU_NITYA_PARTIAL_PENALTY;
              dayQuality.push(`${ny} yoga dosha-window (${MU_NITYA_PARTIAL_PENALTY})`);
            }
          } else if (MU_NITYA_AUSPICIOUS.has(ny)) {
            score += MU_NITYA_AUSPICIOUS_BONUS;
            dayQuality.push(`${ny} yoga (+${MU_NITYA_AUSPICIOUS_BONUS})`);
          }

          // Vara — activity_match (day-level)
          if (varaReason) { score += 1; activityMatch.push(varaReason); }
          if (preferNakshatras.has(facts.nakshatra)) {
            score += 1;
            activityMatch.push(`${facts.nakshatra} specifically favoured for ${activityLabel} (+1)`);
          }

          // Slot-overlap bonuses → slot_quality (Abhijit is now scored as
          // the 8th muhurta's nature above).
          if (amrita.some(a => s0 < muMin(a.end, a.eflag) && muMin(a.start, a.sflag) < e0)) {
            score += 2; slotQuality.push('overlaps Amrita Kalam (+2)');
          }
          if (preferChog && c.name === preferChog[0]) {
            score += preferChog[1];
            activityMatch.push(`${c.name} favoured for ${activityLabel} (+${preferChog[1]})`);
          }
          for (const kn of avoidKaranaNames) activityMatch.push(`${kn} karana avoided`);

          // Doctrinal notes — explanatory, no score effect
          const notes = [];
          for (const item of manualChecks) notes.push(`Manual check required · ${item}`);
          if (cautionLagnaSolar && lagnaCityData) {
            const lagnaDay = lagnaDayFor(lagnaCityData, isoDate);
            const slotLagna = lagnaDay ? muLagnaAtMin(lagnaDay, s0) : null;
            if (slotLagna && slotLagna === data.solarSign) {
              notes.push(`Source caution · ${slotLagna} Lagna is occupied by Surya; ` +
                         `Raman associates this with delay from hard rock.`);
            }
          }
          const siddhiYogas = facts.specialYogas.filter(y =>
            y === 'Sarvartha Siddhi Yoga' || y === 'Amrita Siddhi Yoga');
          const hasPushkara = facts.specialYogas.some(y =>
            y === 'Dvipushkara Yoga' || y === 'Tripushkara Yoga');
          if (siddhiYogas.length && taraUnfavNames.length) {
            notes.push(`${siddhiYogas.join(' + ')} traditionally rectifies tara dosha ` +
                       `(Muhurta Chintamani) · ${taraUnfavNames.join(', ')} mitigated.`);
          }
          if (siddhiYogas.length && chandraAvoidNames.length) {
            notes.push(`Chandra dosha is not rectified by Siddhi yogas · ` +
                       `${chandraAvoidNames.join(', ')} remains a personal caution.`);
          }
          if (hasPushkara && tFam === 'Rikta') {
            notes.push(`Pushkara amplifies the day's nature; combined with Rikta tithi, ` +
                       `even small inauspicious factors magnify.`);
          }

          const reasonGroups = {
            slot_quality: slotQuality, day_quality: dayQuality,
            group_fit: groupFit, activity_match: activityMatch, notes,
          };
          const reasons = [...slotQuality, ...groupFit, ...dayQuality, ...activityMatch];

          // Personal (chandra) dosha is never fully rectified by
          // group-level yogas — cap the tier below Excellent and flag
          // it so equally-scored clean slots sort first.
          let personalDosha = null;
          if (chandraAvoidNames.length) personalDosha = hasAshtama ? 'ashtama_chandra' : 'chandra_avoid';
          else if (ashtamaLagnaNames.length) personalDosha = 'ashtama_lagna';
          else if (chandraPujaNames.length) personalDosha = 'chandra_remedial';
          // tara_dosha: unrectified by Sarvartha/Amrita Siddhi. Last
          // in the cascade — matches the Python order in muhurta.py.
          else if (taraUnfavNames.length && !siddhiYogas.length) personalDosha = 'tara_dosha';

          // Day-level dosha (Rikta tithi, Visha/Dagdha yoga, Vyatipata/
          // Vaidhriti) — same "can't be Excellent" treatment as a
          // personal chandra dosha.
          let dayDosha = null;
          if (tFam === 'Rikta') dayDosha = 'rikta_tithi';
          else if (facts.specialYogas.some(y => MU_YOGA_PENALTY[y] !== undefined)) dayDosha = 'visha_dagdha_yoga';
          else if (MU_NITYA_HARD_AVOID.has(ny)) dayDosha = 'vyatipata_vaidhriti';
          else if (rules.manual_prerequisites) dayDosha = 'practitioner_review';

          slots.push({ d: new Date(d), s0, e0, score, reasons, reasonGroups, personalDosha, dayDosha, dayCtx });
          slotsPerDay.set(isoDate, (slotsPerDay.get(isoDate) || 0) + 1);
      }
      // Diagnose: if the day produced no slots and it wasn't an eclipse,
      // record the most likely reason (samskara skip, mode filter, etc.).
      if (!slotsPerDay.has(isoDate)) {
        let reason = null;
        // Samskara skip on Visha/Dagdha
        for (const y of data.yogas) {
          if (skipYogas.has(y)) {
            reason = `${y} · ${activityLabel} traditionally avoids this day`;
            break;
          }
        }
        // Samskara skip on Vyatipata/Vaidhriti (Nitya yoga at sunrise)
        if (!reason && skipYogas.size && data.yoga && MU_NITYA_HARD_AVOID.has(data.yoga.name)) {
          reason = `${data.yoga.name} yoga · samskaras traditionally defer`;
        }
        // chandra_mode filter at the day level
        if (!reason && people.length && chandraMode !== 'stars' && data.lunarSign) {
          let hasAvoid = false, hasRemedial = false;
          for (const pr of people) {
            if (!pr.rasi) continue;
            const c2 = chandraOf(pr.rasi, data.lunarSign);
            if (!c2) continue;
            if (!MU_CHANDRA_GOOD.has(c2.pos) && !MU_CHANDRA_PUJA.has(c2.pos)) hasAvoid = true;
            else if (MU_CHANDRA_PUJA.has(c2.pos)) hasRemedial = true;
          }
          if (chandraMode === 'strict' && (hasAvoid || hasRemedial)) {
            reason = 'chandra_mode=strict · Moon at sunrise fails for at least one person';
          } else if (chandraMode === 'puja_ok' && hasAvoid) {
            reason = 'chandra_mode=puja_ok · someone has Moon-avoid (4/8/12)';
          }
        }
        if (reason) droppedDays.push({ date: isoDate, reason });
      }
    }
    droppedModeDays = droppedModeSlots;
    // Re-tier across the whole search — "Excellent" means the best of
    // what turned up over the full date range, not a fixed bar.
    muAssignTiers(slots);
    slots.sort((a, b) => MU_TIER_NAMES.indexOf(b.tier) - MU_TIER_NAMES.indexOf(a.tier)
      || b.score - a.score
      || (Number(!!a.personalDosha) - Number(!!b.personalDosha)) || a.d - b.d || a.s0 - b.s0);
    MU_LAST = { top: slots.slice(0, 10), droppedEclipseDays, droppedModeDays, droppedDays, activity, people, chandraMode };
    renderMuhurta();
  } catch (e) {
    box.innerHTML = '<p class="preview-error">Could not load the feed. Try again.</p>';
  }
}

// taroOf-safe: gracefully handle the case where parseDescription returns
// a nakshatra string that's not in our table (shouldn't happen on canonical
// feeds, but defensive — return Janma (1) so the day reads as avoid).
function taroOf_safe(janma, dayNak) {
  try { return taraOf(janma, dayNak); } catch (e) { return 1; }
}

let MU_LAST = null;
const MU_ACT_LABEL = {
  any: 'anything auspicious',
  travel: 'travel', purchase: 'a purchase',
  ceremony: 'a ceremony', beginning: 'a new beginning',
  wedding: 'a wedding (Vivaha)', engagement: 'an engagement',
  naming: 'a naming ceremony', annaprasana: 'annaprasana (first feeding)',
  karnavedha: 'karnavedha (ear-piercing)', mundana: 'a mundana / chaula',
  upanayana: 'upanayana (sacred thread)', vidyarambha: 'vidyarambha (education start)',
  seemantha: 'seemantha (prenatal ceremony)',
  gruhapravesha: 'gruhapravesha (home entry)',
  vehicle: 'a vehicle purchase', property: 'a land purchase for building',
  house_purchase: 'a completed house purchase',
  gold: 'a gold / jewelry purchase',
  business_inventory_purchase: 'a trade inventory purchase',
  borrowing_money: 'borrowing money / taking a loan',
  bhumi_puja: 'bhumi puja (foundation laying)',
  well_digging: 'well digging',
  home_repair: 'a home repair / renovation start',
  business: 'a business launch', job: 'a job start / contract',
  yajna: 'a yajna / homam', pilgrimage: 'a pilgrimage',
  court: 'a court / legal matter', surgery: 'a surgery / medical procedure',
};

function muToT(mm) {
  const m = ((mm % 1440) + 1440) % 1440;
  return fmtT(`${String(Math.floor(m / 60)).padStart(2,'0')}:${String(m % 60).padStart(2,'0')}`);
}

function renderMuhurta() {
  if (!MU_LAST) return;
  const box = document.getElementById('mu-result');
  const { top, droppedEclipseDays = 0, droppedModeDays = 0, droppedDays = [] } = MU_LAST;
  const fmtD = d => d.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
  const fmtIso = iso => {
    const [y, mo, da] = iso.split('-').map(Number);
    return new Date(y, mo - 1, da).toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
  };
  const droppedHtml = droppedDays.length
    ? `<details class="mu-dropped"><summary>${droppedDays.length} day${droppedDays.length>1?'s':''} filtered · see why</summary>
         <ul>${droppedDays.map(dd => `<li><span class="dd-date">${fmtIso(dd.date)}</span> · ${htmlEsc(dd.reason)}</li>`).join('')}</ul>
       </details>`
    : '';
  if (!top.length) {
    const notes = [];
    if (droppedEclipseDays) notes.push(`${droppedEclipseDays} eclipse day(s) deferred`);
    if (droppedModeDays) notes.push(`${droppedModeDays} slot(s) filtered by chandra mode`);
    const suffix = notes.length ? ` · ${notes.join(', ')}` : '';
    box.innerHTML = `<p class="preview-error">No clear slots found${suffix}. Try more days, relax the standard, or clear the people above.</p>${droppedHtml}`;
    return;
  }
  const share = `<button class="wa-share-mini" style="position:static;width:28px;height:28px;flex:none;margin-left:auto;" title="Share these slots on WhatsApp" aria-label="Share on WhatsApp" onclick="shareMuhurtaOnWhatsApp()"><svg viewBox="0 0 24 24" width="15" height="15" fill="currentColor" aria-hidden="true"><path d="M12.04 2a9.9 9.9 0 0 0-8.46 15.1L2 22l5.05-1.55A9.9 9.9 0 1 0 12.04 2zm0 18.1a8.2 8.2 0 0 1-4.18-1.15l-.3-.18-3 .92.93-2.92-.2-.3a8.2 8.2 0 1 1 6.75 3.63zm4.5-6.14c-.25-.12-1.46-.72-1.69-.8-.22-.08-.39-.12-.55.13-.17.24-.64.8-.78.96-.14.16-.29.18-.53.06a6.7 6.7 0 0 1-3.35-2.93c-.25-.43.25-.4.72-1.34.08-.16.04-.3-.02-.43-.06-.12-.55-1.33-.76-1.82-.2-.48-.4-.42-.55-.43h-.47c-.16 0-.43.06-.65.3-.22.25-.85.84-.85 2.04 0 1.2.88 2.36 1 2.52.12.16 1.72 2.63 4.17 3.69.58.25 1.04.4 1.4.51.58.19 1.11.16 1.53.1.47-.07 1.46-.6 1.67-1.18.2-.58.2-1.07.14-1.18-.06-.1-.22-.16-.47-.28z"/></svg></button>`;
  const muLineClass = (item) => {
    if (/\(\+\d+\)\s*$/.test(item)) return 'mu-pos';
    if (/\(-\d+\)\s*$/.test(item)) return 'mu-neg';
    if (/rectifies/i.test(item)) return 'mu-pos';
    if (/not rectified|remains a personal caution|puja recommended/i.test(item)) return 'mu-caution';
    return '';
  };
  const muCapitalize = (item) => item.charAt(0).toUpperCase() + item.slice(1);
  const renderGroup = (label, items, extraClass = '') => {
    if (!items || !items.length) return '';
    const lis = items.map(it => `<li class="${muLineClass(it)}">${muCapitalize(it)}</li>`).join('');
    return `<div class="mu-rg ${extraClass}">
              <span class="mu-rg-label">${label}</span>
              <ul class="mu-rg-items">${lis}</ul>
            </div>`;
  };
  const renderSlot = (s, i) => {
    const rg = s.reasonGroups;
    const groupsHtml = rg
      ? `<div class="mu-rgroups">
           ${renderGroup('Slot quality', rg.slot_quality)}
           ${renderGroup('Day quality', rg.day_quality)}
           ${renderGroup('Group fit', rg.group_fit)}
           ${renderGroup('Activity', rg.activity_match)}
           ${renderGroup('Notes', rg.notes, 'mu-rg-notes')}
         </div>`
      : `<span class="mu-reasons">${s.reasons.join(' · ')}</span>`;
    const tier = s.tier || muScoreTier(s.score);
    const tierClass = `mu-tier-${tier.toLowerCase()}`;
    const dc = s.dayCtx;
    const winList = (wins) => wins.map(w =>
      `<span class="mu-tim"><b>${w.name}</b> ${w.ranges.join(', ')}</span>`).join('');
    const dayCtxHtml = dc ? `<div class="mu-dayctx">
              <div class="mu-anga">
                ${dc.tithi ? `<span class="mu-angachip">🌙 ${dc.tithi}</span>` : ''}
                ${dc.nakshatra ? `<span class="mu-angachip">⭐ ${dc.nakshatra}</span>` : ''}
                ${dc.yoga ? `<span class="mu-angachip">🧘 ${dc.yoga} yoga</span>` : ''}
              </div>
              <details class="mu-timings-d">
                <summary class="mu-timings">
                  ${dc.sunrise ? `<span>🌅 Sunrise ${dc.sunrise}</span>` : ''}
                  ${dc.abhijit ? `<span class="mu-t-aus">✨ Abhijit ${dc.abhijit}</span>` : ''}
                  ${dc.rahu ? `<span class="mu-t-warn">⛔ Rahu Kalam ${dc.rahu}</span>` : ''}
                  <span class="mu-tim-toggle">all timings</span>
                </summary>
                <div class="mu-timings-full">
                  ${dc.auspicious.length ? `<div class="mu-tim-row">
                    <span class="mu-tim-lbl mu-t-aus">🟢 Auspicious</span>
                    <span class="mu-tim-wins mu-t-aus">${winList(dc.auspicious)}</span></div>` : ''}
                  ${dc.avoid.length ? `<div class="mu-tim-row">
                    <span class="mu-tim-lbl mu-t-warn">🔴 Avoid</span>
                    <span class="mu-tim-wins mu-t-warn">${winList(dc.avoid)}</span></div>` : ''}
                </div>
              </details>
            </div>` : '';
    return `<div class="mu-slot">
              <span class="mu-when">${fmtD(s.d)} · ${muToT(s.s0)} to ${muToT(s.e0)}</span>
              <span class="mu-tier ${tierClass}">${tier}</span>
              <span class="mu-score">score ${s.score}</span>
              ${dayCtxHtml}
              ${groupsHtml}
            </div>`;
  };
  box.innerHTML =
    `<div class="tb-summary">⏱ <span class="count">${top.length}</span>&nbsp;slot${top.length > 1 ? 's' : ''} found · best first${share}</div>`
    + top.map(renderSlot).join('')
    + droppedHtml
    + `<p class="preview-note" style="margin-top:0.5rem;">Each slot's score is the sum of the (+n)/(-n) bonuses across
       Slot quality (choghadiya, Abhijit/Amrita overlap), Day quality (Siddhi yogas, Nitya yoga, Rikta tithi),
       Group fit (per-person tarabalam and chandrabalam), and Activity match (preferred tithi class / vara).
       Being clear of every inauspicious window is a requirement, not a bonus. The tier reflects this score's
       rank within this search, capped below Excellent whenever a named dosha is present; check that slot's
       notes either way, since a capped "Good" can carry a caution worth knowing about even if it's otherwise
       a workable time. Notes carry classical-doctrine context (e.g. Sarvartha Siddhi traditionally rectifies
       tara dosha) without changing the score.</p>`;
}

function shareMuhurtaOnWhatsApp() {
  if (!MU_LAST || !MU_LAST.top.length) return;
  const { top, activity, people } = MU_LAST;
  const citySel = selEl('tp-city');
  const cityLabel = citySel.options[citySel.selectedIndex].textContent;
  const fmtD = d => d.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
  const lines = [];
  lines.push(`⏱ *Good time slots · ${MU_ACT_LABEL[activity]}*`);
  lines.push(`📍 ${cityLabel} · ${inpEl('tb-from').value} to ${inpEl('tb-to').value}`);
  if (people.length) lines.push(`Screened for: ${people.map(p => `${p.name} (${p.nak})`).join(' · ')}`);
  lines.push('');
  top.slice(0, 5).forEach(s => {
    lines.push(`✅ ${fmtD(s.d)} · ${muToT(s.s0)} to ${muToT(s.e0)}`);
    lines.push(`   ${s.reasons.filter(r => r !== 'clear of all inauspicious windows').slice(0, 3).join(' · ')}`);
  });
  lines.push('');
  lines.push('Every slot is clear of Rahu Kalam, Varjyam and all inauspicious windows.');
  lines.push('Find your own: https://panchangam.astrochaganti.com/?src=share-slots#tarabalam');
  gcEvent('share-slots');
  window.open('https://wa.me/?text=' + encodeURIComponent(lines.join('\n')), '_blank');
}


export {
  calcTarabalam, renderTarabalam, tbRenderProfileInputs,
  tbAddRow, tbRemoveRow, tbResetProfiles, tbSaveProfiles,
  tbSetMode, tbToggleShowAll, tbExtendTo,
  findMuhurta, renderMuhurta,
  shareTarabalamOnWhatsApp, shareMuhurtaOnWhatsApp,
};

export function tbHasDays() { return !!TB_DAYS; }
export function muHasLast() { return typeof MU_LAST !== 'undefined' && !!MU_LAST; }

/** Wire panel-internal seeds; called once from Init. */
export function initTarabalamPanel(todayISO) {
  tbRenderProfileInputs();
  inpEl('tb-from').value = todayISO;
  const t2 = new Date(); t2.setDate(t2.getDate() + 13);
  inpEl('tb-to').value =
    `${t2.getFullYear()}-${String(t2.getMonth() + 1).padStart(2, '0')}-${String(t2.getDate()).padStart(2, '0')}`;
}
