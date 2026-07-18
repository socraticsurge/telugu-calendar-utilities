// @ts-nocheck — verbatim lift from main.ts (one-shell decomposition);
// typing lands with the component rewrite, not the move.
//
// Today panel: the daily panchangam preview (day header, anga rows,
// windows, choghadiya, horas, lagna strip), the festivals/observances
// accordion, and the WhatsApp share.

import { getSelection } from '../selection-store';
import { parseDescription, TIME_PART } from '../lib/parse-description';
import { loadFeed } from '../lib/feed-loader';
import { fmtT, dayMark, fmtRange, fmtPlain, stampOf } from '../lib/format';
import { htmlEsc } from '../lib/html';
import { gcEvent } from '../lib/analytics';
import { loadLagna, lagnaDayFor } from '../lib/lagna-loader';

// --- Ekadashi naming (Amanta maasam + paksham) ---

const EKADASHI_NAMES = {
  Chaitra:    { Shukla: 'Kamada',      Krishna: 'Varuthini' },
  Vaishakha:  { Shukla: 'Mohini',      Krishna: 'Apara' },
  Jyeshtha:   { Shukla: 'Nirjala',     Krishna: 'Yogini' },
  Ashadha:    { Shukla: 'Shayani',     Krishna: 'Kamika' },
  Shravana:   { Shukla: 'Putrada',     Krishna: 'Aja' },
  Bhadrapada: { Shukla: 'Parivartini', Krishna: 'Indira' },
  Ashvina:    { Shukla: 'Papankusha',  Krishna: 'Rama' },
  Kartika:    { Shukla: 'Prabodhini',  Krishna: 'Utpanna' },
  Margashira: { Shukla: 'Mokshada',    Krishna: 'Saphala' },
  Pushya:     { Shukla: 'Putrada',     Krishna: 'Shattila' },
  Magha:      { Shukla: 'Jaya',        Krishna: 'Vijaya' },
  Phalguna:   { Shukla: 'Amalaki',     Krishna: 'Papamochani' },
};

function ekadashiName(maasam, paksham, solarSign) {
  if (!maasam || !paksham) return null;
  if (maasam.startsWith('Adhika')) return paksham === 'Shukla' ? 'Padmini' : 'Parama';
  const name = (EKADASHI_NAMES[maasam.replace(/^Nija /, '')] || {})[paksham];
  if (!name) return null;
  // Vaikunta (Mukkoti) Ekadashi is the Shukla Ekadashi of Dhanurmasa.
  if (paksham === 'Shukla' && solarSign === 'Dhanu') return `${name} (Vaikunta)`;
  return name;
}

function festivalNames(summary) {
  const m = summary.match(/^🪔 (.+?) — /);
  return m ? m[1].split(' · ') : [];
}

function chipEmoji(s, summary) {
  if (festivalNames(summary).some(f => s.startsWith(f))) return '🪔';
  if (s.startsWith('Ganda Moola')) return '⚠️';
  return '⚡';
}

function specialLabel(s, data) {
  if (/^Ekadashi/.test(s)) {
    const name = ekadashiName(data.maasam, data.paksham, data.solarSign);
    if (name) return s.replace(/^Ekadashi/, `${name} Ekadashi`);
  }
  return s;
}

// --- Choghadiya tables (standard weekday sequences, Sun..Sat) ---

const CHOG_NIGHT_START = ['Shubh', 'Char', 'Kaal', 'Udveg', 'Amrit', 'Rog', 'Labh'];
const CHOG_NIGHT_SEQ = ['Amrit', 'Char', 'Rog', 'Kaal', 'Labh', 'Udveg', 'Shubh'];

function nightChoghadiya(weekday, sunset, nextSunrise) {
  const toMin = t => { const [h, m] = t.split(':').map(Number); return h * 60 + m; };
  const toT = mm => { const m = Math.round(mm) % 1440; return `${String(Math.floor(m / 60)).padStart(2, '0')}:${String(m % 60).padStart(2, '0')}`; };
  const s = toMin(sunset);
  const e = toMin(nextSunrise) + 1440;
  const idx = CHOG_NIGHT_SEQ.indexOf(CHOG_NIGHT_START[weekday]);
  const blocks = [];
  for (let i = 0; i < 8; i++) {
    blocks.push({
      name: CHOG_NIGHT_SEQ[(idx + i) % 7],
      start: toT(s + (e - s) * i / 8),
      end: toT(s + (e - s) * (i + 1) / 8),
    });
  }
  return blocks;
}

// --- Horas (planetary hours) + Lagna (rising sign) ---
//
// Horas: computed purely client-side. Sequence is fixed by the
// weekday lord; 12 day horas span sunrise→sunset and 12 night horas
// span sunset→next sunrise. Mirrors telugu_panchangam/personal/lagna_hora.py.
//
// Lagna: requires Swiss Ephemeris, so it's precomputed by
// scripts/build_lagna_json.py and served as feeds/<slug>-lagna.json.

const HORA_LORDS = ['Sun', 'Venus', 'Mercury', 'Moon', 'Saturn', 'Jupiter', 'Mars'];
const HORA_GLYPH = { Sun: '☉', Venus: '♀', Mercury: '☿', Moon: '☽', Saturn: '♄', Jupiter: '♃', Mars: '♂' };
const HORA_PALETTE_CLASS = { Sun: 'sun', Venus: 'venus', Mercury: 'mercury', Moon: 'moon', Saturn: 'saturn', Jupiter: 'jupiter', Mars: 'mars' };
// Benefic / neutral / malefic — used by the site palette to encode
// favourability rather than planetary identity. Sun is neutral
// because its hora is benefic for some activities and malefic for
// others; the classical scheme is more nuanced and is opt-in.
const HORA_FAVOURABILITY = { Sun: '', Venus: 'benefic', Mercury: 'benefic', Moon: 'benefic', Jupiter: 'benefic', Saturn: 'malefic', Mars: 'malefic' };
// JS Date.getDay() index -> starting hora lord. Order matches
// _WEEKDAY_TO_LORD_START in telugu_panchangam/personal/lagna_hora.py.
const WEEKDAY_TO_LORD_IDX = [0, 3, 6, 2, 5, 1, 4];  // Sun, Mon, Tue, Wed, Thu, Fri, Sat

const RASHI_ELEMENT = ['fire','earth','air','water','fire','earth','air','water','fire','earth','air','water'];
const RASHI_NAMES_JS = ['Mesha','Vrishabha','Mithuna','Karka','Simha','Kanya','Tula','Vrischika','Dhanu','Makara','Kumbha','Meena'];

function computeHoras(weekday, sunrise, sunset, nextSunrise) {
  // weekday: 0..6 (Sun..Sat). All times are 'HH:MM'.
  const toMin = t => { const [h, m] = t.split(':').map(Number); return h * 60 + m; };
  const toT = mm => { const m = ((Math.round(mm) % 1440) + 1440) % 1440;
                      return `${String(Math.floor(m / 60)).padStart(2,'0')}:${String(m % 60).padStart(2,'0')}`; };
  const sr = toMin(sunrise), ss = toMin(sunset);
  const dayLen = ss - sr;
  const nextSrAbs = toMin(nextSunrise) + 1440;
  const nightLen = nextSrAbs - ss;
  const lordStart = WEEKDAY_TO_LORD_IDX[weekday];
  const day = [], night = [];
  for (let i = 0; i < 12; i++) {
    const lord = HORA_LORDS[(lordStart + i) % 7];
    day.push({ lord, start: toT(sr + dayLen * i / 12), end: toT(sr + dayLen * (i + 1) / 12) });
  }
  for (let i = 0; i < 12; i++) {
    const lord = HORA_LORDS[(lordStart + 12 + i) % 7];
    night.push({ lord, start: toT(ss + nightLen * i / 12), end: toT(ss + nightLen * (i + 1) / 12) });
  }
  return { day, night };
}

// Walk a sequence of HH:MM start/end pairs and mark the first cell
// whose end is the FIRST time past midnight. Subsequent cells that
// already live past midnight don't get a flag — the convention is
// "mark only the crossing", and after that the next-day-ness is
// visually obvious. Matches Choghadiya night.
function markFirstMidnightCrossing(cells, anchorStartTime) {
  const toMin = t => { const [h, m] = t.split(':').map(Number); return h * 60 + m; };
  const anchor = toMin(anchorStartTime);
  let prevMin = anchor;
  let marked = false;
  return cells.map(c => {
    const startMin = toMin(c.start);
    const endMin = toMin(c.end);
    const sflag = !marked && startMin < prevMin ? '+1' : '';
    // The "crossing" cell is the one whose end wraps backward.
    const crosses = !marked && endMin < startMin;
    const eflag = crosses ? '+1' : '';
    if (sflag || crosses) marked = true;
    prevMin = endMin;
    return { ...c, sflag, eflag };
  });
}

function horaCell(h) {
  // Defense-in-depth: every interpolation goes through htmlEsc even
  // though h.lord / h.start / h.end come from hard-coded arrays and
  // arithmetic on HH:MM strings. Matches the pattern PR #59 set.
  // Times go through fmtRange so the 12/24 hour toggle and the
  // <wbr> break behaviour match the rest of the day card.
  const fav = HORA_FAVOURABILITY[h.lord] || 'neutral';
  const palClass = HORA_PALETTE_CLASS[h.lord] || '';
  const cls = `hora-cell ${palClass} ${fav}`;
  const glyph = HORA_GLYPH[h.lord] || '';
  const range = fmtRange(h.start, h.end, '–<wbr>', h.sflag, h.eflag);
  return `<div class="${cls}" title="${htmlEsc(h.lord)} hora · ${htmlEsc(h.start)}–${htmlEsc(h.end)}">`
    + `<div class="hora-glyph">${htmlEsc(glyph)}</div>`
    + `<div class="hora-lord">${htmlEsc(h.lord)}</div>`
    + `<div class="hora-time">${range}</div></div>`;
}

function lagnaSegments(dayData) {
  // dayData: { sunrise: 'HH:MM', lagna0: int,
  //            transitions: [[minOffset, newIdx], ...],
  //            cycleEnd: int }   // minute-offset from sunrise to next sunrise
  if (!dayData) return [];
  const fmt = m => {
    const w = ((m % 1440) + 1440) % 1440;
    return `${String(Math.floor(w / 60)).padStart(2,'0')}:${String(w % 60).padStart(2,'0')}`;
  };
  const [srH, srM] = dayData.sunrise.split(':').map(Number);
  const baseMin = srH * 60 + srM;
  // Build raw (rashi, startOffset) entries so we can derive ends.
  const raw = [{ rashi: dayData.lagna0, off: 0 }];
  for (const [off, idx] of dayData.transitions) {
    raw.push({ rashi: idx, off });
  }
  const cycleEnd = typeof dayData.cycleEnd === 'number' ? dayData.cycleEnd : (24 * 60);
  return raw.map((r, i) => {
    const endOff = i < raw.length - 1 ? raw[i + 1].off : cycleEnd;
    return {
      rashi: r.rashi,
      start: fmt(baseMin + r.off),
      end: fmt(baseMin + endOff),
    };
  });
}

function lagnaCell(seg) {
  // seg.rashi is a JSON-supplied integer 0..11; we look up the name
  // from a hard-coded array. Defense-in-depth: escape anyway.
  const name = RASHI_NAMES_JS[seg.rashi] || '?';
  const elem = RASHI_ELEMENT[seg.rashi] || '';
  const range = fmtRange(seg.start, seg.end, '–<wbr>', seg.sflag, seg.eflag);
  return `<div class="lagna-seg ${elem}" title="${htmlEsc(name)} lagna · ${htmlEsc(seg.start)}–${htmlEsc(seg.end)}">`
    + `<div class="lagna-name">${htmlEsc(name)}</div>`
    + `<div class="lagna-time">${range}</div></div>`;
}

// (Removed: site/classical palette toggle. Classical-only now —
// see the CSS block above for the rationale.)

let _tpDateVal = null;
function selectedDate() {
  return _tpDateVal ? new Date(_tpDateVal + 'T00:00:00') : new Date();
}

function formatToday() {
  return selectedDate().toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' });
}

function eclipseChip(e) {
  const emoji = e.kind === 'Solar' ? '🌒' : '🌕';
  let txt = `${emoji} ${e.kind} Eclipse (${e.subtype}) — ${e.visible ? 'visible here' : 'not visible here'}`;
  if (e.visible && e.window) txt += ` · ${fmtRange(e.window.start, e.window.end)}`;
  if (e.visible && e.sutak) txt += ` · Sutak ${fmtRange(e.sutak.start, e.sutak.end)}`;
  return `<span class="special-chip">${txt}</span>`;
}

function renderPreview(container, event, events) {
  const data = parseDescription(event.description);
  const special = event.summary.includes('🪔')
    ? '<span class="badge">Festival</span>'
    : (event.summary.includes('⚡') ? '<span class="badge">Special day</span>' : '');
  // 1 · Why today is special — flags right under the header, with the reason.
  let flags = '';
  data.special
    .filter(s => !(data.eclipse && /Eclipse/.test(s)))
    .forEach(s => { flags += `<span class="special-chip">${chipEmoji(s, event.summary)} ${specialLabel(s, data)}</span>`; });
  if (data.eclipse) flags += eclipseChip(data.eclipse);
  data.yogas.forEach(y => { flags += `<span class="yoga-chip">✨ ${y}</span>`; });
  const flagStrip = flags ? `<div class="flag-strip">${flags}</div>` : '';

  // 2 · What the day is — Pancha Anga as hero tiles, sky as a slim strip.
  const angaTile = (label, kind, entry) => entry
    ? `<div class="anga-cell" data-kind="${kind}"><div class="anga-label">${label}</div><div class="anga-name">${entry.name}</div><div class="anga-time">${fmtRange(entry.start, entry.end, undefined, entry.sflag, entry.eflag)}</div></div>`
    : '';
  // Older feeds carry the bare paksham tithi ("Krishna Ekadashi") — name it
  // here; regenerated feeds arrive already named ("Parama Ekadashi").
  let tithiEntry = data.tithi;
  if (tithiEntry && /^(Shukla|Krishna) Ekadashi$/.test(tithiEntry.name)) {
    const name = ekadashiName(data.maasam, data.paksham, data.solarSign);
    if (name) tithiEntry = { ...tithiEntry, name: `${name} Ekadashi` };
  }
  let anga = angaTile('Tithi', 'tithi', tithiEntry) + angaTile('Nakshatra', 'nakshatra', data.nakshatra) + angaTile('Nitya Yoga', 'yoga', data.yoga);
  if (data.karana) {
    const karanas = data.karana.split(/\s+\/\s+/).map(k => {
      const m = k.match(new RegExp(`^(.*?)\\s+${TIME_PART}\\s*[–-]\\s*${TIME_PART}$`));
      return m ? `<div class="anga-time"><b>${m[1]}</b> ${fmtRange(m[2], m[4], '–', m[3], m[5])}</div>` : `<div class="anga-time">${k}</div>`;
    }).join('');
    anga += `<div class="anga-cell" data-kind="karana"><div class="anga-label">Karana</div>${karanas}</div>`;
  }
  const angaGrid = anga ? `<div class="anga-grid">${anga}</div>` : '';

  // Header context lines: year context · month context · today's sky frame.
  const metaLines = data.samvatsara
    ? `<div class="meta">${data.samvatsara} Nama Samvatsara${data.ayanam ? ` · ${data.ayanam} · ${data.rituvu} Rituvu` : ''}</div>
       <div class="meta">${data.maasam} Maasam · ${data.paksham} Paksham · ${data.vaaram}</div>
       <div class="meta sky">🌅 ${fmtT(data.sunrise)} – ${fmtT(data.sunset)} &nbsp;·&nbsp; 🌙 ${fmtT(data.moonrise)} – ${fmtT(data.moonset)}</div>`
    : `<div class="meta">${data.meta}</div>`;

  // 3 · When to act or avoid — tile strips in the same language as Choghadiya,
  // in clock order so the day scans morning → evening.
  // An observance occurring twice (e.g. Durmuhurtham) is one tile, two windows.
  const groupWins = list => {
    const order = [];
    const byName = new Map();
    [...list].sort((a, b) => a.start.localeCompare(b.start)).forEach(e => {
      if (!byName.has(e.name)) { byName.set(e.name, []); order.push(e.name); }
      byName.get(e.name).push(fmtRange(e.start, e.end, '–', e.sflag, e.eflag));
    });
    return order.map(name => ({ name, times: byName.get(name) }));
  };
  const winCell = (e, cls) =>
    `<div class="chog-cell ${cls}"><div class="chog-name">${e.name}</div>${e.times.map(t => `<div class="chog-time">${t}</div>`).join('')}</div>`;
  let windows = '';
  if (data.auspicious.length) {
    windows += `<div class="tile-strip"><div class="strip-title good-t">🟢 Auspicious</div><div class="win-grid">${groupWins(data.auspicious).map(e => winCell(e, 'good')).join('')}</div></div>`;
  }
  if (data.inauspicious.length) {
    windows += `<div class="tile-strip avoid-strip"><div class="strip-title bad-t">🔴 Avoid</div><div class="win-grid">${groupWins(data.inauspicious).map(e => winCell(e, 'bad')).join('')}</div></div>`;
  }

  // 4 · The day's timeline — Choghadiya as full-width colour-coded strips,
  // day from the feed, night computed from sunset → tomorrow's sunrise.
  const CHOG_GOOD = new Set(['Amrit', 'Shubh', 'Labh', 'Char']);
  const chogCell = c =>
    `<div class="chog-cell ${CHOG_GOOD.has(c.name) ? 'good' : 'bad'}"><div class="chog-name">${c.name}</div><div class="chog-time">${fmtRange(c.start, c.end, '–<wbr>')}</div></div>`;
  let chog = '';
  if (data.choghadiya.length) {
    chog = `<div class="tile-strip"><div class="strip-title">🕐 Choghadiya — day in 8 blocks</div><div class="chog-grid">${data.choghadiya.map(chogCell).join('')}</div></div>`;
  }
  // Prefer the feed's night section; compute it locally only for older feeds.
  let night = data.nightChoghadiya;
  if (!night.length && data.sunset && events) {
    const tomorrow = new Date(selectedDate());
    tomorrow.setDate(tomorrow.getDate() + 1);
    const next = events.get(stampOf(tomorrow));
    const m = next && next.description.match(/Sunrise (\d{2}:\d{2})/);
    if (m) night = nightChoghadiya(selectedDate().getDay(), data.sunset, m[1]);
  }
  if (night.length) {
    chog += `<div class="tile-strip"><div class="strip-title">🌙 Choghadiya — night in 8 blocks</div><div class="chog-grid">${night.map(chogCell).join('')}</div></div>`;
  }

  // Horas + lagna — horas are derived client-side from sunrise/sunset/
  // tomorrow's sunrise; lagna is fetched asynchronously and injected
  // into the placeholder once it loads.
  let tomorrowSr = null;
  if (data.sunset && events) {
    const tomorrow = new Date(selectedDate());
    tomorrow.setDate(tomorrow.getDate() + 1);
    const next = events.get(stampOf(tomorrow));
    const m = next && next.description.match(/Sunrise (\d{2}:\d{2})/);
    if (m) tomorrowSr = m[1];
  }
  let horaHtml = '';
  if (data.sunrise && data.sunset && tomorrowSr) {
    const horas = computeHoras(selectedDate().getDay(), data.sunrise, data.sunset, tomorrowSr);
    // Day horas live entirely within one calendar day; night horas
    // cross midnight, so feed them through the marker pass with
    // sunset as the "today" anchor.
    const nightFlagged = markFirstMidnightCrossing(horas.night, data.sunset);
    horaHtml = `<div class="tile-strip"><div class="strip-title">🕒 Horas — day</div><div class="hora-grid">${horas.day.map(horaCell).join('')}</div></div>`;
    horaHtml += `<div class="tile-strip"><div class="strip-title">🌙 Horas — night</div><div class="hora-grid">${nightFlagged.map(horaCell).join('')}</div></div>`;
  }
  const isoDate = `${selectedDate().getFullYear()}-${String(selectedDate().getMonth()+1).padStart(2,'0')}-${String(selectedDate().getDate()).padStart(2,'0')}`;
  const lagnaPlaceholder = `<div class="tile-strip" id="lagna-strip" data-iso="${isoDate}">`
    + `<div class="strip-title">🌅 Lagna — rising sign</div>`
    + `<div class="lagna-ribbon" id="lagna-ribbon">`
    + `<div class="preview-note" style="grid-column:1/-1;margin:0;padding:0.4rem;text-align:center;">Loading lagna data…</div>`
    + `</div>`
    + `<p class="preview-note" style="margin:0.5rem 0 0;">`
    + `Cells span sunrise to next sunrise. The first and last cells are often the `
    + `<em>same rashi</em> — a short partial at sunrise and a longer wrap before `
    + `next sunrise, because the lagna cycle (~23h 56m) is slightly shorter than `
    + `the panchangam day (24h).`
    + `</p></div>`;

  container.innerHTML = `
    <div class="preview-card">
      <div class="preview-head">
        <button class="wa-share-mini" onclick="shareTodayOnWhatsApp()"
                title="Share this day's panchangam on WhatsApp" aria-label="Share on WhatsApp">
          <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor" aria-hidden="true"><path d="M12.04 2a9.9 9.9 0 0 0-8.46 15.1L2 22l5.05-1.55A9.9 9.9 0 1 0 12.04 2zm0 18.1a8.2 8.2 0 0 1-4.18-1.15l-.3-.18-3 .92.93-2.92-.2-.3a8.2 8.2 0 1 1 6.75 3.63zm4.5-6.14c-.25-.12-1.46-.72-1.69-.8-.22-.08-.39-.12-.55.13-.17.24-.64.8-.78.96-.14.16-.29.18-.53.06a6.7 6.7 0 0 1-3.35-2.93c-.25-.43.25-.4.72-1.34.08-.16.04-.3-.02-.43-.06-.12-.55-1.33-.76-1.82-.2-.48-.4-.42-.55-.43h-.47c-.16 0-.43.06-.65.3-.22.25-.85.84-.85 2.04 0 1.2.88 2.36 1 2.52.12.16 1.72 2.63 4.17 3.69.58.25 1.04.4 1.4.51.58.19 1.11.16 1.53.1.47-.07 1.46-.6 1.67-1.18.2-.58.2-1.07.14-1.18-.06-.1-.22-.16-.47-.28z"/></svg>
        </button>
        <div class="date">${formatToday()}${special}<span style="position:relative;display:inline-block;vertical-align:middle;margin-left:0.4em;"><input type="date" class="tp-date-input" value="${_tpDateVal||''}" style="position:absolute;inset:0;opacity:0;cursor:pointer;width:100%;height:100%;border:none;padding:0;" aria-label="Change date"><span aria-hidden="true" style="display:inline-block;background:rgba(255,255,255,0.15);border:1px solid rgba(255,255,255,0.3);border-radius:5px;padding:2px 6px;font-size:0.75rem;pointer-events:none;">📅</span></span></div>
        ${metaLines}
      </div>
      ${flagStrip}
      ${angaGrid}
      ${windows}
      ${chog}
      ${horaHtml}
      ${lagnaPlaceholder}
    </div>
  `;

  // Async lagna fetch — guarded by the strip's data-iso so a quick
  // date change before the fetch resolves doesn't paint stale data.
  const cityForLagna = getSelection().city;
  if (cityForLagna) {
    loadLagna(cityForLagna).then(d => {
      const ribbon = document.getElementById('lagna-ribbon');
      const strip = document.getElementById('lagna-strip');
      if (!ribbon || !strip || strip.dataset.iso !== isoDate) return;
      const dayData = lagnaDayFor(d, isoDate);
      const segs = lagnaSegments(dayData);
      if (segs.length) {
        // Anchor midnight detection on sunrise — the first cell that
        // crosses past midnight gets *+1 and subsequent cells stay
        // unmarked (matches the existing Choghadiya convention).
        const flagged = markFirstMidnightCrossing(segs, dayData.sunrise);
        ribbon.innerHTML = flagged.map(lagnaCell).join('');
      } else {
        // Date is outside the generated lagna window (we precompute
        // ~18 months ahead per city). Keep the strip visible with a
        // clear explanation instead of vanishing silently. Built via
        // DOM API + textContent so no string ever reaches innerHTML.
        const note = document.createElement('div');
        note.className = 'preview-note';
        note.style.cssText = 'grid-column:1/-1;margin:0;padding:0.5rem;text-align:center;';
        note.textContent = d
          ? 'Lagna data is generated ~18 months ahead. This date is outside the current window — it will appear once the next monthly build runs.'
          : 'Lagna data is loading from a separate feed. If this persists, the feed may be unreachable from your network.';
        ribbon.replaceChildren(note);
      }
    });
  }
}

// --- Festivals & observances — full calendar year, accordion by month ---

function renderUpcoming(events) {
  const container = document.getElementById('upcoming-result');
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const year = today.getFullYear();
  const currentMonth = today.getMonth();

  const MONTH_NAMES = ['January','February','March','April','May','June',
                       'July','August','September','October','November','December'];

  const buckets: Map<number, string[]> = new Map();

  const d = new Date(year, 0, 1);
  const yearEnd = new Date(year, 11, 31);
  while (d <= yearEnd) {
    const ev = events.get(stampOf(d));
    if (ev && (ev.summary.includes('⚡') || ev.summary.includes('🪔'))) {
      const data = parseDescription(ev.description);
      let chips = '';
      data.special
        .filter(s => !(data.eclipse && /Eclipse/.test(s)))
        .forEach(s => { chips += `<span class="special-chip">${chipEmoji(s, ev.summary)} ${specialLabel(s, data)}</span>`; });
      if (data.eclipse) chips += eclipseChip(data.eclipse);
      if (chips) {
        const m = d.getMonth();
        if (!buckets.has(m)) buckets.set(m, []);
        const isToday = d.getTime() === today.getTime();
        const isFestival = ev.summary.includes('🪔');
        const dow = d.toLocaleDateString('en-US', { weekday: 'short' });
        const day = d.getDate();
        const monthAbbr = MONTH_NAMES[m].slice(0, 3);
        let cls = 'upcoming-row';
        if (isFestival) cls += ' upcoming-festival';
        if (isToday)   cls += ' upcoming-today';
        buckets.get(m).push(
          `<div class="${cls}">
            <span class="upcoming-date"><span class="dow">${dow}</span> ${monthAbbr} ${day}${isToday ? '<span class="upcoming-today-badge">today</span>' : ''}</span>
            <span class="upcoming-chips">${chips}</span>
          </div>`
        );
      }
    }
    d.setDate(d.getDate() + 1);
  }

  if (!buckets.size) {
    container.innerHTML = `<p class="preview-note">No festivals found for ${year}.</p>`;
    return;
  }

  let html = '';
  for (const [m, rows] of buckets) {
    const isOpen = m === currentMonth;
    html += `<div class="upcoming-month${isOpen ? ' open' : ''}">
      <button class="upcoming-month-header" onclick="toggleFestivalMonth(this)" aria-expanded="${isOpen}">
        <span>${MONTH_NAMES[m]} ${year}</span>
        <span class="upcoming-chevron" aria-hidden="true"></span>
      </button>
      <div class="upcoming-month-body">
        <div class="upcoming-list">${rows.join('')}</div>
      </div>
    </div>`;
  }
  container.innerHTML = html;
}

function toggleFestivalMonth(btn) {
  const month = btn.closest('.upcoming-month');
  const isOpen = month.classList.toggle('open');
  btn.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
}

let LAST_EVENTS = null;

function renderAll() {
  if (!LAST_EVENTS) return;
  const container = document.getElementById('tp-result');
  const event = LAST_EVENTS.get(stampOf(selectedDate()));
  if (event) {
    renderPreview(container, event, LAST_EVENTS);
  } else {
    container.innerHTML = '<p class="preview-error">Preview unavailable for this date — try the subscription link below.</p>';
  }
  renderUpcoming(LAST_EVENTS);
}
window.renderAll = renderAll;

async function loadPreview() {
  const city = getSelection().city;
  const system = getSelection().system;
  document.getElementById('tp-result').innerHTML = '<p class="preview-error">Loading…</p>';
  try {
    LAST_EVENTS = await loadFeed(city, system);
    renderAll();
  } catch (e) {
    // Surface the real failure: this catch also swallows render bugs,
    // not just fetch errors, and a silent one masks regressions.
    console.error('loadPreview failed:', e);
    LAST_EVENTS = null;
    document.getElementById('tp-result').innerHTML = '<p class="preview-error">Preview unavailable — try the subscription link below.</p>';
    document.getElementById('upcoming-result').innerHTML = '<p class="preview-error">Unavailable — try the subscription link below.</p>';
  }
}

// --- Share today's panchangam on WhatsApp (plain-text forward) ---

function buildShareText(event) {
  const data = parseDescription(event.description);
  const d = selectedDate();
  const dateLabel = d.toLocaleDateString('en-US', { weekday: 'short', day: 'numeric', month: 'short', year: 'numeric' });
  const citySel = document.getElementById('tp-city');
  const sysSel = document.getElementById('tp-system');
  const cityLabel = citySel.options[citySel.selectedIndex].textContent;
  const sysLabel = sysSel.options[sysSel.selectedIndex].textContent;
  const lines = [];
  const fests = festivalNames(event.summary);
  if (fests.length) lines.push(`🪔 *${fests.join(' · ')}*`);
  lines.push(`*Panchangam — ${dateLabel}*`);
  lines.push(`📍 ${cityLabel} · ${sysLabel}`);
  lines.push('');
  if (data.samvatsara) {
    const yearBits = [data.samvatsara + ' Nama Samvatsara', data.ayanam, data.rituvu ? data.rituvu + ' Rituvu' : null].filter(Boolean);
    lines.push(yearBits.join(' · '));
    lines.push(`${data.maasam} Maasam · ${data.paksham} Paksham · ${data.vaaram}`);
  }
  const anga = (label, e) => e && lines.push(`*${label}:* ${e.name} — ${fmtPlain(e.start, e.sflag)} to ${fmtPlain(e.end, e.eflag)}`);
  let tithi = data.tithi;
  if (tithi && /^(Shukla|Krishna) Ekadashi$/.test(tithi.name)) {
    const name = ekadashiName(data.maasam, data.paksham, data.solarSign);
    if (name) tithi = { ...tithi, name: `${name} Ekadashi` };
  }
  anga('Tithi', tithi);
  anga('Nakshatra', data.nakshatra);
  anga('Yoga', data.yoga);
  if (data.karana) {
    const karana = data.karana.split(/\s+\/\s+/).map(k => {
      const m = k.match(new RegExp(`^(.*?)\\s+${TIME_PART}\\s*[–-]\\s*${TIME_PART}$`));
      return m ? `${m[1]} ${fmtPlain(m[2], m[3])}–${fmtPlain(m[4], m[5])}` : k;
    }).join(' / ');
    lines.push(`*Karana:* ${karana}`);
  }
  if (data.sunrise) lines.push(`🌅 Sunrise ${fmtT(data.sunrise)} · Sunset ${fmtT(data.sunset)}`);
  if (data.moonrise) lines.push(`🌙 Moonrise ${fmtT(data.moonrise)} · Moonset ${fmtT(data.moonset)}`);
  const winList = (title, list) => {
    if (!list.length) return;
    lines.push('');
    lines.push(title);
    list.forEach(w => lines.push(`• ${w.name} ${fmtPlain(w.start, w.sflag)}–${fmtPlain(w.end, w.eflag)}`));
  };
  winList('⚠️ *Avoid:*', data.inauspicious);
  winList('✅ *Good times:*', data.auspicious);
  const extras = data.special.filter(sp => !fests.some(f => sp.startsWith(f)));
  if (extras.length) {
    lines.push('');
    lines.push(`⚡ ${extras.map(sp => specialLabel(sp, data)).join(' · ')}`);
  }
  if (data.yogas.length) lines.push(`✨ ${data.yogas.join(' · ')}`);
  if (data.eclipse) {
    lines.push(`🌒 ${data.eclipse.kind} Eclipse (${data.eclipse.subtype}) — ${data.eclipse.visible ? 'visible here, Sutak applies' : 'not visible from this location'}`);
  }
  lines.push('');
  lines.push('📅 Full panchangam & free calendar feeds:');
  lines.push('https://panchangam.astrochaganti.com/?src=share-today');
  gcEvent('share-today');
  return lines.join('\n');
}

function shareTodayOnWhatsApp() {
  const event = LAST_EVENTS && LAST_EVENTS.get(stampOf(selectedDate()));
  if (!event) return;
  window.open('https://wa.me/?text=' + encodeURIComponent(buildShareText(event)), '_blank');
}


export {
  loadPreview, renderAll, renderUpcoming, toggleFestivalMonth,
  shareTodayOnWhatsApp, selectedDate, ekadashiName, festivalNames,
};

/** Events map of the currently loaded feed (null before first load). */
export function getLoadedEvents() { return LAST_EVENTS; }

/** Wire panel-internal listeners; called once from Init. */
export function initTodayPanel(todayISO) {
  _tpDateVal = todayISO;
  document.getElementById('tp-result').addEventListener('change', function (e) {
    if (e.target.matches('input.tp-date-input')) { _tpDateVal = e.target.value; loadPreview(); }
  });
}
