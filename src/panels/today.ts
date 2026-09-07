// typing lands with the component rewrite, not the move.
//
// Today panel: the daily panchangam preview (day header, anga rows,
// windows, choghadiya, horas, lagna strip), the festivals/observances
// accordion, and the WhatsApp share.

import { getSelection } from '../selection-store';
import { selEl } from '../lib/dom';
import { parseDescription, TIME_PART } from '../lib/parse-description';
import { loadFeed } from '../lib/feed-loader';
import { fmtT, fmtRange, fmtPlain, stampOf } from '../lib/format';
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
  const name = EKADASHI_NAMES[maasam.replace(/^Nija /, '')]?.[paksham];
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
  if (s.startsWith('Ekadashi')) {
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

const KARANA_RANGE_PATTERN = new RegExp(String.raw`${TIME_PART}\s*[–-]\s*${TIME_PART}$`);

function parseKaranaRange(value) {
  const match = KARANA_RANGE_PATTERN.exec(value);
  if (!match) return null;
  return {
    name: value.slice(0, match.index).trimEnd(),
    start: match[1],
    sflag: match[2],
    end: match[3],
    eflag: match[4],
  };
}

function eclipseChip(e) {
  const emoji = e.kind === 'Solar' ? '🌒' : '🌕';
  let txt = `${emoji} ${e.kind} Eclipse (${e.subtype}) — ${e.visible ? 'visible here' : 'not visible here'}`;
  if (e.visible && e.window) txt += ` · ${fmtRange(e.window.start, e.window.end)}`;
  if (e.visible && e.sutak) txt += ` · Sutak ${fmtRange(e.sutak.start, e.sutak.end)}`;
  return `<span class="special-chip">${txt}</span>`;
}

function specialBadge(summary) {
  if (summary.includes('🪔')) return '<span class="badge">Festival</span>';
  if (summary.includes('⚡')) return '<span class="badge">Special day</span>';
  return '';
}

function renderFlagStrip(data, summary) {
  const specialChips = data.special
    .filter(s => !(data.eclipse && s.includes('Eclipse')))
    .map(s => `<span class="special-chip">${chipEmoji(s, summary)} ${specialLabel(s, data)}</span>`);
  const eclipseChips = data.eclipse ? [eclipseChip(data.eclipse)] : [];
  const yogaChips = data.yogas.map(y => `<span class="yoga-chip">✨ ${y}</span>`);
  const flags = [...specialChips, ...eclipseChips, ...yogaChips].join('');
  return flags ? `<div class="flag-strip">${flags}</div>` : '';
}

function namedTithi(data) {
  const tithi = data.tithi;
  if (!tithi || !/^(Shukla|Krishna) Ekadashi$/.test(tithi.name)) return tithi;
  const name = ekadashiName(data.maasam, data.paksham, data.solarSign);
  return name ? { ...tithi, name: `${name} Ekadashi` } : tithi;
}

function angaTile(label, kind, entry) {
  if (!entry) return '';
  return `<div class="anga-cell" data-kind="${kind}"><div class="anga-label">${label}</div><div class="anga-name">${entry.name}</div><div class="anga-time">${fmtRange(entry.start, entry.end, undefined, entry.sflag, entry.eflag)}</div></div>`;
}

function karanaTile(karana) {
  if (!karana) return '';
  const rows = karana.split('/').map(value => value.trim()).map(value => {
    const range = parseKaranaRange(value);
    if (!range) return `<div class="anga-time">${value}</div>`;
    return `<div class="anga-time"><b>${range.name}</b> ${fmtRange(range.start, range.end, '–', range.sflag, range.eflag)}</div>`;
  }).join('');
  return `<div class="anga-cell" data-kind="karana"><div class="anga-label">Karana</div>${rows}</div>`;
}

function renderAngaGrid(data) {
  const anga = [
    angaTile('Tithi', 'tithi', namedTithi(data)),
    angaTile('Nakshatra', 'nakshatra', data.nakshatra),
    angaTile('Nitya Yoga', 'yoga', data.yoga),
    karanaTile(data.karana),
  ].join('');
  return anga ? `<div class="anga-grid">${anga}</div>` : '';
}

function renderMetaLines(data) {
  if (!data.samvatsara) return `<div class="meta">${data.meta}</div>`;
  const season = data.ayanam ? ` · ${data.ayanam} · ${data.rituvu} Rituvu` : '';
  return `<div class="meta">${data.samvatsara} Nama Samvatsara${season}</div>
       <div class="meta">${data.maasam} Maasam · ${data.paksham} Paksham · ${data.vaaram}</div>`;
}

function renderSkyCycle(data) {
  if (!(data.sunrise || data.sunset || data.moonrise || data.moonset)) return '';
  const skyValue = value => value ? fmtT(value) : '—';
  return `<div class="day-cycle" aria-label="Sun and Moon timings">
         <div class="day-cycle-group day-cycle-sun">
           <span class="day-cycle-icon" aria-hidden="true">
             <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"><circle cx="12" cy="12" r="3.5"/><path d="M12 2v2M12 20v2M4.93 4.93l1.42 1.42M17.65 17.65l1.42 1.42M2 12h2M20 12h2M4.93 19.07l1.42-1.42M17.65 6.35l1.42-1.42"/></svg>
           </span>
           <dl class="day-cycle-time"><dt>Sunrise</dt><dd>${skyValue(data.sunrise)}</dd></dl>
           <dl class="day-cycle-time"><dt>Sunset</dt><dd>${skyValue(data.sunset)}</dd></dl>
         </div>
         <div class="day-cycle-group day-cycle-moon">
           <span class="day-cycle-icon" aria-hidden="true">
             <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M19.2 15.4A8 8 0 0 1 8.6 4.8a8 8 0 1 0 10.6 10.6z"/></svg>
           </span>
           <dl class="day-cycle-time"><dt>Moonrise</dt><dd>${skyValue(data.moonrise)}</dd></dl>
           <dl class="day-cycle-time"><dt>Moonset</dt><dd>${skyValue(data.moonset)}</dd></dl>
         </div>
       </div>`;
}

function groupWindows(list) {
  const order = [];
  const byName = new Map();
  [...list].sort((a, b) => a.start.localeCompare(b.start)).forEach(entry => {
    if (!byName.has(entry.name)) {
      byName.set(entry.name, []);
      order.push(entry.name);
    }
    byName.get(entry.name).push(fmtRange(entry.start, entry.end, '–', entry.sflag, entry.eflag));
  });
  return order.map(name => ({ name, times: byName.get(name) }));
}

function windowCell(entry, className) {
  const times = entry.times.map(time => `<div class="chog-time">${time}</div>`).join('');
  return `<div class="chog-cell ${className}"><div class="chog-name">${entry.name}</div>${times}</div>`;
}

function windowStrip(list, title, className, stripClass = '') {
  if (!list.length) return '';
  const cells = groupWindows(list).map(entry => windowCell(entry, className)).join('');
  return `<div class="tile-strip${stripClass}"><div class="strip-title ${className}-t">${title}</div><div class="win-grid">${cells}</div></div>`;
}

function renderWindows(data) {
  return windowStrip(data.auspicious, '🟢 Auspicious', 'good')
    + windowStrip(data.inauspicious, '🔴 Avoid', 'bad', ' avoid-strip');
}

function nextSunrise(events) {
  if (!events) return null;
  const tomorrow = new Date(selectedDate());
  tomorrow.setDate(tomorrow.getDate() + 1);
  return events.get(stampOf(tomorrow))?.description.match(/Sunrise (\d{2}:\d{2})/)?.[1] ?? null;
}

function choghadiyaCell(entry) {
  const good = new Set(['Amrit', 'Shubh', 'Labh', 'Char']).has(entry.name);
  const className = good ? 'good' : 'bad';
  return `<div class="chog-cell ${className}"><div class="chog-name">${entry.name}</div><div class="chog-time">${fmtRange(entry.start, entry.end, '–<wbr>')}</div></div>`;
}

function renderChoghadiya(data, events, tomorrowSr, atSunrise) {
  let dayHtml = '';
  if (data.choghadiya.length) {
    atSunrise.push(`${data.choghadiya[0].name} Choghadiya`);
    dayHtml = `<div class="tile-strip"><div class="strip-title">🕐 Choghadiya — day in 8 blocks</div><div class="chog-grid">${data.choghadiya.map(choghadiyaCell).join('')}</div></div>`;
  }
  let night = data.nightChoghadiya;
  if (!night.length && data.sunset && tomorrowSr && events) {
    night = nightChoghadiya(selectedDate().getDay(), data.sunset, tomorrowSr);
  }
  const nightHtml = night.length
    ? `<div class="tile-strip"><div class="strip-title">🌙 Choghadiya — night in 8 blocks</div><div class="chog-grid">${night.map(choghadiyaCell).join('')}</div></div>`
    : '';
  return dayHtml + nightHtml;
}

function renderHoras(data, tomorrowSr, atSunrise) {
  if (!(data.sunrise && data.sunset && tomorrowSr)) return '';
  const horas = computeHoras(selectedDate().getDay(), data.sunrise, data.sunset, tomorrowSr);
  if (horas.day.length) atSunrise.push(`${horas.day[0].lord} Hora`);
  const nightFlagged = markFirstMidnightCrossing(horas.night, data.sunset);
  const day = `<div class="tile-strip"><div class="strip-title">🕒 Horas — day</div><div class="hora-grid">${horas.day.map(horaCell).join('')}</div></div>`;
  const night = `<div class="tile-strip"><div class="strip-title">🌙 Horas — night</div><div class="hora-grid">${nightFlagged.map(horaCell).join('')}</div></div>`;
  return day + night;
}

function selectedIsoDate() {
  const date = selectedDate();
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
}

function lagnaPlaceholder(isoDate, renderSequence) {
  return `<div class="tile-strip" id="lagna-strip" data-iso="${isoDate}" data-render-sequence="${renderSequence}">`
    + '<div class="strip-title">🌅 Lagna — rising sign</div>'
    + '<div class="lagna-ribbon" id="lagna-ribbon">'
    + '<div class="preview-note" style="grid-column:1/-1;margin:0;padding:0.4rem;text-align:center;">Loading lagna data…</div>'
    + '</div></div>';
}

function renderDetailedTimings(data, events, renderSequence, isoDate) {
  const atSunrise = [];
  const tomorrowSr = data.sunset ? nextSunrise(events) : null;
  const choghadiya = renderChoghadiya(data, events, tomorrowSr, atSunrise);
  const horas = renderHoras(data, tomorrowSr, atSunrise);
  const content = choghadiya + horas + lagnaPlaceholder(isoDate, renderSequence);
  const meta = atSunrise.length
    ? `At sunrise · ${htmlEsc(atSunrise.join(' · '))}`
    : 'Choghadiya · Hora · Lagna';
  return `<details class="daily-details">
         <summary>
           <span class="daily-details-title">Detailed timings</span>
           <span class="daily-details-meta">${meta}</span>
           <span class="daily-details-chevron" aria-hidden="true"></span>
         </summary>
         <div class="daily-details-body">${content}</div>
       </details>`;
}

function renderLagnaResult(data, isoDate) {
  const ribbon = document.getElementById('lagna-ribbon');
  const dayData = lagnaDayFor(data, isoDate);
  const segments = lagnaSegments(dayData);
  if (segments.length) {
    const flagged = markFirstMidnightCrossing(segments, dayData.sunrise);
    ribbon.innerHTML = flagged.map(lagnaCell).join('');
    return;
  }
  const note = document.createElement('div');
  note.className = 'preview-note';
  note.style.cssText = 'grid-column:1/-1;margin:0;padding:0.5rem;text-align:center;';
  note.textContent = data
    ? 'Lagna data is generated ~18 months ahead. This date is outside the current window — it will appear once the next monthly build runs.'
    : 'Lagna data is loading from a separate feed. If this persists, the feed may be unreachable from your network.';
  ribbon.replaceChildren(note);
}

function loadLagnaRibbon(city, isoDate, renderSequence, renderKey) {
  if (!city) return;
  loadLagna(city).then(data => {
    const strip = document.getElementById('lagna-strip');
    if (
      !document.getElementById('lagna-ribbon')
      || strip?.dataset.iso !== isoDate
      || strip.dataset.renderSequence !== String(renderSequence)
      || currentPreviewKey() !== renderKey
    ) return;
    renderLagnaResult(data, isoDate);
  });
}

function renderPreview(container, event, events, renderSequence, renderKey) {
  const data = parseDescription(event.description);
  const isoDate = selectedIsoDate();
  const special = specialBadge(event.summary);
  const metaLines = renderMetaLines(data);
  const skyCycle = renderSkyCycle(data);
  const flagStrip = renderFlagStrip(data, event.summary);
  const angaGrid = renderAngaGrid(data);
  const windows = renderWindows(data);
  const detailedTimings = renderDetailedTimings(data, events, renderSequence, isoDate);

  container.innerHTML = `
    <div class="preview-card">
      <div class="preview-head">
        <button class="wa-share-mini" onclick="shareTodayOnWhatsApp()"
                title="Share this day's panchangam on WhatsApp" aria-label="Share on WhatsApp">
          <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor" aria-hidden="true"><path d="M12.04 2a9.9 9.9 0 0 0-8.46 15.1L2 22l5.05-1.55A9.9 9.9 0 1 0 12.04 2zm0 18.1a8.2 8.2 0 0 1-4.18-1.15l-.3-.18-3 .92.93-2.92-.2-.3a8.2 8.2 0 1 1 6.75 3.63zm4.5-6.14c-.25-.12-1.46-.72-1.69-.8-.22-.08-.39-.12-.55.13-.17.24-.64.8-.78.96-.14.16-.29.18-.53.06a6.7 6.7 0 0 1-3.35-2.93c-.25-.43.25-.4.72-1.34.08-.16.04-.3-.02-.43-.06-.12-.55-1.33-.76-1.82-.2-.48-.4-.42-.55-.43h-.47c-.16 0-.43.06-.65.3-.22.25-.85.84-.85 2.04 0 1.2.88 2.36 1 2.52.12.16 1.72 2.63 4.17 3.69.58.25 1.04.4 1.4.51.58.19 1.11.16 1.53.1.47-.07 1.46-.6 1.67-1.18.2-.58.2-1.07.14-1.18-.06-.1-.22-.16-.47-.28z"/></svg>
        </button>
        <div class="date">${formatToday()}${special}<span class="tp-date-picker"><input type="date" class="tp-date-input" value="${_tpDateVal||''}" style="position:absolute;inset:0;opacity:0;cursor:pointer;width:100%;height:100%;border:none;padding:0;" aria-label="Change date"><span class="tp-date-picker__trigger" aria-hidden="true">📅</span></span></div>
        ${metaLines}
      </div>
      ${skyCycle}
      ${flagStrip}
      ${angaGrid}
      ${windows}
      ${detailedTimings}
    </div>
  `;

  loadLagnaRibbon(getSelection().city, isoDate, renderSequence, renderKey);
}

// --- Festivals & observances — full calendar year, accordion by month ---

const MONTH_NAMES = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December',
];

function observanceChips(event, data) {
  const special = data.special
    .filter(item => !(data.eclipse && item.includes('Eclipse')))
    .map(item => `<span class="special-chip">${chipEmoji(item, event.summary)} ${specialLabel(item, data)}</span>`);
  const eclipse = data.eclipse ? [eclipseChip(data.eclipse)] : [];
  return [...special, ...eclipse].join('');
}

function observanceEntry(events, date, today, year) {
  const event = events.get(stampOf(date));
  if (!event || !(event.summary.includes('⚡') || event.summary.includes('🪔'))) return null;
  const chips = observanceChips(event, parseDescription(event.description));
  if (!chips) return null;
  const month = date.getMonth();
  const isToday = date.getTime() === today.getTime();
  const rowClasses = [
    'upcoming-row',
    ...(event.summary.includes('🪔') ? ['upcoming-festival'] : []),
    ...(isToday ? ['upcoming-today'] : []),
  ].join(' ');
  const weekday = date.toLocaleDateString('en-US', { weekday: 'short' });
  const day = date.getDate();
  const monthAbbr = MONTH_NAMES[month].slice(0, 3);
  const todayBadge = isToday ? '<span class="upcoming-today-badge">today</span>' : '';
  const isoDate = `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
  const row = `<div class="${rowClasses}">
            <span class="upcoming-date"><span class="dow">${weekday}</span> ${monthAbbr} ${day}${todayBadge}</span>
            <span class="upcoming-chips">${chips}</span>
          </div>`;
  const next = `<section class="upcoming-next" aria-labelledby="upcoming-next-title">
            <div class="upcoming-next-copy">
              <p class="upcoming-next-kicker">Next observance</p>
              <h3 id="upcoming-next-title">${weekday}, ${monthAbbr} ${day}</h3>
              <div class="upcoming-chips">${chips}</div>
            </div>
            <button class="upcoming-next-action" onclick="switchTool('today'); openFestivalDate('${isoDate}')">View Panchangam</button>
          </section>`;
  return { month, row, next };
}

function collectObservances(events, today, year) {
  const buckets: Map<number, string[]> = new Map();
  let nextObservance = '';
  const date = new Date(year, 0, 1);
  const yearEnd = new Date(year, 11, 31);
  while (date <= yearEnd) {
    const entry = observanceEntry(events, date, today, year);
    if (entry) {
      const rows = buckets.get(entry.month);
      if (rows) rows.push(entry.row);
      else buckets.set(entry.month, [entry.row]);
      if (!nextObservance && date >= today) nextObservance = entry.next;
    }
    date.setDate(date.getDate() + 1);
  }
  return { buckets, nextObservance };
}

function renderObservanceMonths(buckets, currentMonth, year) {
  let html = '';
  for (const [month, rows] of buckets) {
    const isOpen = month === currentMonth;
    html += `<div class="upcoming-month${isOpen ? ' open' : ''}">
      <button class="upcoming-month-header" onclick="toggleFestivalMonth(this)" aria-expanded="${isOpen}">
        <span>${MONTH_NAMES[month]} ${year}</span>
        <span class="upcoming-chevron" aria-hidden="true"></span>
      </button>
      <div class="upcoming-month-body">
        <div class="upcoming-list">${rows.join('')}</div>
      </div>
    </div>`;
  }
  return html;
}

function renderUpcoming(events) {
  const container = document.getElementById('upcoming-result');
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const year = today.getFullYear();
  const currentMonth = today.getMonth();
  const { buckets, nextObservance } = collectObservances(events, today, year);
  if (!buckets.size) {
    container.innerHTML = `<p class="preview-note">No festivals found for ${year}.</p>`;
    return;
  }
  container.innerHTML = nextObservance + renderObservanceMonths(buckets, currentMonth, year);
}

function toggleFestivalMonth(btn) {
  const month = btn.closest('.upcoming-month');
  const isOpen = month.classList.toggle('open');
  btn.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
}

function openFestivalDate(isoDate) {
  _tpDateVal = isoDate;
  const input = document.querySelector('input.tp-date-input') as HTMLInputElement | null;
  if (input) input.value = isoDate;
  loadPreview();
}

let LAST_EVENTS = null;
let LAST_EVENTS_KEY = null;
let PREVIEW_REQUEST_SEQUENCE = 0;
let PREVIEW_RENDER_SEQUENCE = 0;

function currentFeedKey() {
  const { city, system } = getSelection();
  return `${city}|${system}`;
}

function currentPreviewKey() {
  return `${currentFeedKey()}|${_tpDateVal || ''}`;
}

function renderAll() {
  if (!LAST_EVENTS || LAST_EVENTS_KEY !== currentFeedKey()) return;
  const container = document.getElementById('tp-result');
  const event = LAST_EVENTS.get(stampOf(selectedDate()));
  if (event) {
    const renderSequence = ++PREVIEW_RENDER_SEQUENCE;
    const renderKey = currentPreviewKey();
    renderPreview(container, event, LAST_EVENTS, renderSequence, renderKey);
  } else {
    container.innerHTML = '<p class="preview-error" role="status">Preview unavailable for this date — try the subscription link below.</p>';
  }
  renderUpcoming(LAST_EVENTS);
}
(window as Window & { renderAll?: typeof renderAll }).renderAll = renderAll;

async function loadPreview() {
  const city = getSelection().city;
  const system = getSelection().system;
  const requestSequence = ++PREVIEW_REQUEST_SEQUENCE;
  const requestKey = currentPreviewKey();
  const feedKey = `${city}|${system}`;
  const result = document.getElementById('tp-result');
  const upcoming = document.getElementById('upcoming-result');
  result.setAttribute('aria-busy', 'true');
  result.innerHTML = '<p class="preview-error" role="status">Loading…</p>';
  upcoming.setAttribute('aria-busy', 'true');
  upcoming.innerHTML = '<p class="preview-note" role="status">Updating upcoming dates…</p>';
  try {
    const events = await loadFeed(city, system);
    if (requestSequence !== PREVIEW_REQUEST_SEQUENCE || requestKey !== currentPreviewKey()) return;
    LAST_EVENTS = events;
    LAST_EVENTS_KEY = feedKey;
    renderAll();
  } catch (e) {
    if (requestSequence !== PREVIEW_REQUEST_SEQUENCE || requestKey !== currentPreviewKey()) return;
    // Surface the real failure: this catch also swallows render bugs,
    // not just fetch errors, and a silent one masks regressions.
    console.error('loadPreview failed:', e);
    LAST_EVENTS = null;
    LAST_EVENTS_KEY = null;
    document.getElementById('tp-result').innerHTML = '<p class="preview-error" role="status">Preview unavailable — try the subscription link below.</p>';
    upcoming.innerHTML = '<p class="preview-error" role="status">Unavailable — try the subscription link below.</p>';
  } finally {
    if (requestSequence === PREVIEW_REQUEST_SEQUENCE && requestKey === currentPreviewKey()) {
      result.setAttribute('aria-busy', 'false');
      upcoming.setAttribute('aria-busy', 'false');
    }
  }
}

// --- Share today's panchangam on WhatsApp (plain-text forward) ---

function shareYearLines(data) {
  if (!data.samvatsara) return [];
  const yearBits = [
    `${data.samvatsara} Nama Samvatsara`,
    data.ayanam,
    data.rituvu ? `${data.rituvu} Rituvu` : null,
  ].filter(Boolean);
  return [
    yearBits.join(' · '),
    `${data.maasam} Maasam · ${data.paksham} Paksham · ${data.vaaram}`,
  ];
}

function shareAngaLine(label, entry) {
  if (!entry) return [];
  return [`*${label}:* ${entry.name} — ${fmtPlain(entry.start, entry.sflag)} to ${fmtPlain(entry.end, entry.eflag)}`];
}

function shareKaranaLines(karana) {
  if (!karana) return [];
  const ranges = karana.split('/').map(value => value.trim()).map(value => {
    const range = parseKaranaRange(value);
    if (!range) return value;
    return `${range.name} ${fmtPlain(range.start, range.sflag)}–${fmtPlain(range.end, range.eflag)}`;
  });
  return [`*Karana:* ${ranges.join(' / ')}`];
}

function shareWindowLines(title, list) {
  if (!list.length) return [];
  const windows = list.map(entry => (
    `• ${entry.name} ${fmtPlain(entry.start, entry.sflag)}–${fmtPlain(entry.end, entry.eflag)}`
  ));
  return ['', title, ...windows];
}

function shareExtraLines(data, festivals) {
  const extras = data.special.filter(item => !festivals.some(festival => item.startsWith(festival)));
  return extras.length
    ? ['', `⚡ ${extras.map(item => specialLabel(item, data)).join(' · ')}`]
    : [];
}

function buildShareText(event) {
  const data = parseDescription(event.description);
  const d = selectedDate();
  const dateLabel = d.toLocaleDateString('en-US', { weekday: 'short', day: 'numeric', month: 'short', year: 'numeric' });
  const citySel = selEl('tp-city');
  const sysSel = selEl('tp-system');
  const cityLabel = citySel.options[citySel.selectedIndex].textContent;
  const sysLabel = sysSel.options[sysSel.selectedIndex].textContent;
  const fests = festivalNames(event.summary);
  const lines = [
    ...(fests.length ? [`🪔 *${fests.join(' · ')}*`] : []),
    `*Panchangam — ${dateLabel}*`,
    `📍 ${cityLabel} · ${sysLabel}`,
    '',
    ...shareYearLines(data),
    ...shareAngaLine('Tithi', namedTithi(data)),
    ...shareAngaLine('Nakshatra', data.nakshatra),
    ...shareAngaLine('Yoga', data.yoga),
    ...shareKaranaLines(data.karana),
    ...(data.sunrise ? [`🌅 Sunrise ${fmtT(data.sunrise)} · Sunset ${fmtT(data.sunset)}`] : []),
    ...(data.moonrise ? [`🌙 Moonrise ${fmtT(data.moonrise)} · Moonset ${fmtT(data.moonset)}`] : []),
    ...shareWindowLines('⚠️ *Avoid:*', data.inauspicious),
    ...shareWindowLines('✅ *Good times:*', data.auspicious),
    ...shareExtraLines(data, fests),
    ...(data.yogas.length ? [`✨ ${data.yogas.join(' · ')}`] : []),
    ...(data.eclipse
      ? [`🌒 ${data.eclipse.kind} Eclipse (${data.eclipse.subtype}) — ${data.eclipse.visible ? 'visible here, Sutak applies' : 'not visible from this location'}`]
      : []),
    '',
    '📅 Full panchangam & free calendar feeds:',
    'https://panchangam.astrochaganti.com/?src=share-today',
  ];
  gcEvent('share-today');
  return lines.join('\n');
}

function shareTodayOnWhatsApp() {
  const event = LAST_EVENTS?.get(stampOf(selectedDate()));
  if (!event) return;
  window.open('https://wa.me/?text=' + encodeURIComponent(buildShareText(event)), '_blank');
}


export {
  loadPreview, renderAll, renderUpcoming, toggleFestivalMonth, openFestivalDate,
  shareTodayOnWhatsApp, selectedDate, ekadashiName, festivalNames,
};

/** Events map of the currently loaded feed (null before first load). */
export function getLoadedEvents() {
  return LAST_EVENTS_KEY === currentFeedKey() ? LAST_EVENTS : null;
}

/** Wire panel-internal listeners; called once from Init. */
export function initTodayPanel(todayISO) {
  _tpDateVal = todayISO;
  document.getElementById('tp-result').addEventListener('change', function (e) {
    const tgt = e.target as HTMLInputElement;
    if (tgt.matches('input.tp-date-input')) { _tpDateVal = tgt.value; loadPreview(); }
  });
}
