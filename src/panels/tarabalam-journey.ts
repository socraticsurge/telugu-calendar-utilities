import { selEl, inpEl } from '../lib/dom';
import { getSelection } from '../selection-store';
import { loadFeed } from '../lib/feed-loader';
import { parseDescription } from '../lib/parse-description';
import { fmtT, stampOf } from '../lib/format';
import { htmlEsc } from '../lib/html';
import { gcEvent } from '../lib/analytics';
import { NAKSHATRA_NAMES } from '../data/rasis';
import { tbTaraOf, tbTaraIsGood, tbTaraLabel, tbChandraOf } from '../scorer/tara-chandra';
export { tbTaraOf, tbTaraIsGood, tbTaraLabel, tbChandraOf, tbChandraVerdict } from '../scorer/tara-chandra';
import { getLoadedEvents } from './today';
import { tbProfiles } from './tarabalam-profile-controller';

const TB_NAKSHATRAS = NAKSHATRA_NAMES;

let TB_DAYS = null;    // last computed result rows
let TB_EVENTS = null;  // feed events used for the last calculation

export async function calcTarabalam() {
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
        const t = tbTaraOf(pr.nak, nak);
        const entry: {
          who: string;
          tara: number;
          label: string;
          good: boolean;
          chandra?: ReturnType<typeof tbChandraOf>;
        } =
          { who: pr.name, tara: t, label: tbTaraLabel(t), good: tbTaraIsGood(t) };
        if (pr.rasi && data.lunarSign) entry.chandra = tbChandraOf(pr.rasi, data.lunarSign);
        return entry;
      });
      TB_DAYS.push({ date: new Date(d), nak, nakUntil: data.nakshatra.end, nakEflag: data.nakshatra.eflag,
                     moonRasi: data.lunarSign || '', tithi: data.tithi ? data.tithi.name : '', taras });
    }
    renderTarabalam(profiles);
  } catch {
    // Feed details are intentionally withheld; the user gets a stable retry message.
    resBox.innerHTML = '<p class="preview-error">Could not load the feed. Try again.</p>';
  }
}

let TB_SHOW_ALL = false;  // default: only favourable days
let TB_MODE = (() => {
  try {
    return typeof window === 'undefined'
      ? 'stars'
      : window.localStorage?.getItem('tc-tb-mode') || 'stars';
  } catch {
    return 'stars';
  }
})();

export function tbSetMode(m, onInvalidate: () => void) {
  onInvalidate();
  TB_MODE = m;
  try { window.localStorage?.setItem('tc-tb-mode', m); } catch { /* session only */ }
  if (TB_DAYS) renderTarabalam();
}

function tbPersonGood(t) {
  if (!t.good) return false;
  if (!t.chandra) return true;
  if (TB_MODE === 'strict') return t.chandra.verdict === 'good';
  if (TB_MODE === 'puja_ok') return t.chandra.verdict !== 'bad';
  return true;  // stars: chandra annotates, never blocks
}

export function tbChandraPresentation(t): { chandraTag: string; cls: string } {
  const passes = tbPersonGood(t);
  let caveat = t.chandra?.verdict || null;
  if (caveat === 'good') caveat = null;
  const ord = n => n + (['st','nd','rd'][n-1] || 'th');
  let chandraTag = '';
  if (caveat === 'puja') chandraTag = ` · ° ${ord(t.chandra.pos)}`;
  else if (caveat) chandraTag = ` · ☾ ${ord(t.chandra.pos)}`;
  let cls = 'good';
  if (!passes) cls = 'bad';
  else if (TB_MODE === 'puja_ok' && caveat === 'puja') cls = 'puja';
  return { chandraTag, cls };
}

export function tbToggleShowAll() {
  TB_SHOW_ALL = inpEl('tb-show-all').checked;
  renderTarabalam();
}

function tbCycleHasGoodDay(profiles) {
  // Tarabalam repeats every 27 nakshatras. When rashis are also set the
  // real cycle is nakshatra x rashi, so only declare impossibility on the
  // star check alone — the look-ahead handles the rest.
  return TB_NAKSHATRAS.some(n =>
    profiles.every(pr => tbTaraIsGood(tbTaraOf(pr.nak, n))));
}

function tbDayGoodForAll(profiles, nak, moonRasi) {
  return profiles.every(pr => {
    if (!tbTaraIsGood(tbTaraOf(pr.nak, nak))) return false;
    if (TB_MODE !== 'stars' && pr.rasi && moonRasi) {
      const c = tbChandraOf(pr.rasi, moonRasi);
      if (c?.verdict === 'bad') return false;
      if (c?.verdict !== undefined && TB_MODE === 'strict' && c.verdict !== 'good') return false;
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
    const nak = data.nakshatra?.name;
    if (nak && tbDayGoodForAll(profiles, nak, data.lunarSign)) return d;
  }
  return null;
}

export function tbExtendTo(iso) {
  inpEl('tb-to').value = iso;
  calcTarabalam();
}

function tbTarabalamProfileHeader(profile): string {
  const parts = [htmlEsc(profile.nak)];
  if (profile.rasi) parts.push(`${htmlEsc(profile.rasi)} rashi`);
  if (profile.lagna) parts.push(`${htmlEsc(profile.lagna)} lagna`);
  return `<th>${htmlEsc(profile.name)}<div class="tb-sub">${parts.join(' · ')}</div></th>`;
}

function tbTarabalamChip(tara, row): string {
  const { chandraTag, cls } = tbChandraPresentation(tara);
  let chandraDetail = '';
  if (tara.chandra) {
    const verdict = tara.chandra.verdict === 'puja'
      ? 'needs puja'
      : tara.chandra.verdict;
    chandraDetail = ` · Chandra: ${tara.chandra.pos}${['st','nd','rd'][tara.chandra.pos-1] || 'th'} from rashi (${verdict})`;
  }
  const moonDetail = row.moonRasi ? ` · Moon in ${row.moonRasi}` : '';
  const detail = `Tara: ${tara.tara} ${tara.label} (${tara.good ? 'good' : 'avoid'})`
    + chandraDetail + moonDetail;
  return `<td><span class="tara-chip ${cls}" title="${detail}">${tara.tara} ${tara.label}${chandraTag}</span></td>`;
}

function tbTarabalamDesktopRow(row, profiles): string {
  const dlabel = row.date.toLocaleDateString('en-US', {
    weekday: 'short', month: 'short', day: 'numeric',
  });
  const chips = row.taras.map(tara => tbTarabalamChip(tara, row)).join('');
  let all = '';
  if (profiles.length > 1) {
    const allGood = row.allGood ? '<span class="tb-star">✦</span>' : '';
    all = `<td>${allGood}</td>`;
  }
  return `<tr class="${row.allGood && profiles.length > 1 ? 'tb-all' : ''}">
      <td class="tb-date-cell">${dlabel}</td>
      <td>${row.nak}<div class="tb-sub">till ${fmtT(row.nakUntil)}${row.nakEflag === '+1' ? ' +1' : ''}</div></td>
      <td>${row.tithi}</td>${chips}${all}</tr>`;
}

function tbTarabalamLegend(rows, group: boolean): string {
  const hasPuja = rows.some(row => row.taras.some(tara => tara.chandra?.verdict === 'puja'));
  const hasMoonBad = rows.some(row => row.taras.some(tara => tara.chandra?.verdict === 'bad'));
  const modeLabel = {
    stars: 'Stars only (classic)',
    puja_ok: 'Stars + Moon, puja ok',
    strict: 'Stars + Moon, strict',
  }[TB_MODE];
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
  return `${legend}</div>`;
}

function tbTarabalamPersonCard(tara, profile): string {
  const { chandraTag, cls } = tbChandraPresentation(tara);
  let subText = '';
  if (profile) {
    const extras = [htmlEsc(profile.nak)];
    if (profile.rasi) extras.push(`${htmlEsc(profile.rasi)} rashi`);
    if (profile.lagna) extras.push(`${htmlEsc(profile.lagna)} lagna`);
    subText = `<span class="tb-sub">${htmlEsc(profile.name)}<span style="color:#DDD2BC"> · ${extras.join(' · ')}</span></span>`;
  }
  return `<div class="tb-card-row">${subText}<span class="tara-chip ${cls}">${tara.tara} ${tara.label}${chandraTag}</span></div>`;
}

function tbTarabalamMobileCard(row, profiles): string {
  const dlabel = row.date.toLocaleDateString('en-US', {
    weekday: 'short', month: 'short', day: 'numeric',
  });
  const personRows = row.taras
    .map((tara, index) => tbTarabalamPersonCard(tara, profiles[index]))
    .join('');
  const goodForEveryone = row.allGood && profiles.length > 1;
  const star = goodForEveryone
    ? '<span class="tb-star">✦</span> good for everyone'
    : '&nbsp;';
  return `<div class="tb-card ${goodForEveryone ? 'tb-all' : ''}">
      <div class="tb-card-head">
        <span class="tb-date-cell">${dlabel}</span>
        <span class="tb-card-flag">${star}</span>
      </div>
      <div class="tb-card-sub">${row.nak} till ${fmtT(row.nakUntil)}${row.nakEflag === '+1' ? ' +1' : ''} · ${row.tithi}</div>
      ${personRows}
    </div>`;
}

function tbRenderNoFavourableRows(profiles, group: boolean, who: string): void {
  const result = document.getElementById('tb-result');
  if (!tbCycleHasGoodDay(profiles)) {
    result.innerHTML =
      `<p class="preview-error">This combination of birth stars never aligns; tarabalam repeats over the
         27 nakshatras, and no day is favourable for ${group ? 'all ' + profiles.length + ' people' : htmlEsc(who)} at once.
         Tick "show all days" to plan by individual taras, or consult your purohit.</p>`;
    return;
  }
  const nextGood = tbNextGoodBeyondRange(profiles);
  if (!nextGood) {
    result.innerHTML =
      `<p class="preview-error">No favourable days for ${htmlEsc(who)} in this range, and none found in the months ahead.
         Tick "show all days" to plan by individual taras.</p>`;
    return;
  }
  const iso = `${nextGood.getFullYear()}-${String(nextGood.getMonth()+1).padStart(2,'0')}-${String(nextGood.getDate()).padStart(2,'0')}`;
  const label = nextGood.toLocaleDateString('en-US', {
    weekday: 'short', month: 'short', day: 'numeric',
  });
  result.innerHTML =
    `<p class="preview-error">No favourable days for ${htmlEsc(who)} in this range.
         The next one is <strong>${label}</strong>:
         <button class="read-more" style="color:var(--indigo);" onclick="tbExtendTo('${iso}')">extend the range to include it</button>,
         or tick "show all days".</p>`;
}

function tbRenderSummary(goodDays, profiles, group: boolean, who: string): void {
  const next = goodDays[0];
  let summary = `<span class="count">${goodDays.length} of ${TB_DAYS.length}</span>&nbsp;days are favourable for ${htmlEsc(who)}`;
  if (next) {
    summary += ` · next: <span class="count">${next.date.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })}</span>`;
  }
  const share = goodDays.length
    ? `<button class="wa-share-mini" style="position:static;width:28px;height:28px;flex:none;" title="Share these good days on WhatsApp" aria-label="Share on WhatsApp" onclick="shareTarabalamOnWhatsApp()"><svg viewBox="0 0 24 24" width="15" height="15" fill="currentColor" aria-hidden="true"><path d="M12.04 2a9.9 9.9 0 0 0-8.46 15.1L2 22l5.05-1.55A9.9 9.9 0 1 0 12.04 2zm0 18.1a8.2 8.2 0 0 1-4.18-1.15l-.3-.18-3 .92.93-2.92-.2-.3a8.2 8.2 0 1 1 6.75 3.63zm4.5-6.14c-.25-.12-1.46-.72-1.69-.8-.22-.08-.39-.12-.55.13-.17.24-.64.8-.78.96-.14.16-.29.18-.53.06a6.7 6.7 0 0 1-3.35-2.93c-.25-.43.25-.4.72-1.34.08-.16.04-.3-.02-.43-.06-.12-.55-1.33-.76-1.82-.2-.48-.4-.42-.55-.43h-.47c-.16 0-.43.06-.65.3-.22.25-.85.84-.85 2.04 0 1.2.88 2.36 1 2.52.12.16 1.72 2.63 4.17 3.69.58.25 1.04.4 1.4.51.58.19 1.11.16 1.53.1.47-.07 1.46-.6 1.67-1.18.2-.58.2-1.07.14-1.18-.06-.1-.22-.16-.47-.28z"/></svg></button>`
    : '';
  const toggle = `<label class="tb-toggle"><input type="checkbox" id="tb-show-all" ${TB_SHOW_ALL ? 'checked' : ''} onchange="tbToggleShowAll()"> show all days</label>${share}`;
  document.getElementById('tb-summary').innerHTML =
    `<div class="tb-summary">${group ? '<span class="tb-star">✦</span>' : '🟢'} ${summary}${toggle}</div>`;
}

export function renderTarabalam(profiles?) {
  if (!TB_DAYS) return;
  const participants = profiles || tbProfiles();
  const group = participants.length > 1;
  const who = group ? 'everyone' : participants[0]?.name || 'you';
  TB_DAYS.forEach(row => { row.allGood = row.taras.every(tbPersonGood); });
  selEl('tb-mode').value = TB_MODE;
  const goodDays = TB_DAYS.filter(row => row.allGood);
  tbRenderSummary(goodDays, participants, group, who);
  const rows = TB_DAYS.filter(row => TB_SHOW_ALL || row.allGood);
  if (!rows.length) {
    tbRenderNoFavourableRows(participants, group, who);
    return;
  }
  const head = `<tr><th>Date</th><th>Moon in</th><th>Tithi</th>${participants.map(tbTarabalamProfileHeader).join('')}${group ? '<th title="Auspicious for everyone selected">All ✦</th>' : ''}</tr>`;
  const body = rows.map(row => tbTarabalamDesktopRow(row, participants)).join('');
  const cards = rows.map(row => tbTarabalamMobileCard(row, participants)).join('');
  const legend = tbTarabalamLegend(rows, group);
  document.getElementById('tb-result').innerHTML =
    `<div class="tb-table-wrap"><table class="tb-table">${head}${body}</table></div>` +
    `<div class="tb-cards">${cards}</div>${legend}`;
}

export function shareTarabalamOnWhatsApp() {
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
  lines.push(
    `✦ *Good days ${group ? 'for all of us' : 'for me'} (${anyRasi ? 'Tarabalam · Chandrabalam' : 'Tarabalam'})*`,
    `📍 ${cityLabel} · ${fmtD(TB_DAYS[0].date)} to ${fmtD(TB_DAYS[TB_DAYS.length-1].date)}`,
    'Saved profile names and birth-star details are intentionally omitted from this share.',
    `Standard: ${{ stars: 'Stars only (classic)', puja_ok: 'Stars + Moon, puja ok', strict: 'Stars + Moon, strict' }[TB_MODE]}`,
    '',
  );
  goodDays.forEach(r => lines.push(`✅ ${fmtD(r.date)} · ${r.nak} · ${r.tithi}`));
  lines.push(
    '',
    'Check your own birth star:',
    'https://panchangam.astrochaganti.com/?src=share-tarabalam#tarabalam',
  );
  gcEvent('share-tarabalam');
  window.open('https://wa.me/?text=' + encodeURIComponent(lines.join('\n')), '_blank');
}

// --- Gochara tool ---


export function tbMode(): string {
  return TB_MODE;
}

export function tbHasDays(): boolean {
  return Boolean(TB_DAYS);
}

export function clearTarabalamJourney(): void {
  TB_DAYS = null;
  TB_EVENTS = null;
}
