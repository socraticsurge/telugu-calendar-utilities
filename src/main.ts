// @ts-nocheck
import {
  MU_RASHI_NAMES, MU_LAGNA_KENDRA, MU_LAGNA_TRIKONA,
  MU_LAGNA_CHARA, MU_LAGNA_STHIRA, MU_LAGNA_DVISVABHAVA, MU_LAGNA_CLASSES,
  MU_CHANDRA_GOOD, MU_CHANDRA_PUJA,
  MU_TIER_NAMES, MU_RELATIVE_BANDS,
  muLagnaPosition, muLagnaVerdict,
  muIsFavourableLagna, muIsAshtamaLagna, muLagnaAtMin,
  muLagnaClassOf, muLagnasInClass,
  muScoreTier, muRelativeTier,
  computePersonalDosha, computeDayDosha,
} from './muhurta-scorer';

  const FEED_BASE_URL = 'https://panchangam.astrochaganti.com/feeds/';

  const CITY_GROUPS = [
    ['Telugu Heartland', ['Hyderabad', 'Vijayawada', 'Visakhapatnam', 'Tirupati', 'Warangal', 'Guntur', 'Nizamabad', 'Rajahmundry', 'Kurnool', 'Nellore']],
    ['Major Indian Metros', ['Bengaluru', 'Chennai', 'Mumbai', 'Delhi']],
    ['International', ['Dallas', 'San Jose', 'San Francisco', 'Edison', 'New York', 'London', 'Sydney', 'Dubai']],
  ];
  const SYSTEMS = [['drik', 'Drik Ganita'], ['surya-siddhanta', 'Surya Siddhanta'], ['vakya', 'Vakya']];

  function slug(name) {
    return name.toLowerCase().replace(/\s+/g, '-').replace(/,/g, '');
  }

  function feedFilename(city, system) {
    return `${slug(city)}-${system}.ics`;
  }

  function populateCitySelect(select) {
    CITY_GROUPS.forEach(([label, cities]) => {
      const og = document.createElement('optgroup');
      og.label = label;
      cities.forEach(name => {
        const opt = document.createElement('option');
        opt.value = name;
        opt.textContent = name;
        og.appendChild(opt);
      });
      select.appendChild(og);
    });
  }

  function populateSystemSelect(select) {
    SYSTEMS.forEach(([value, label]) => {
      const opt = document.createElement('option');
      opt.value = value;
      opt.textContent = label;
      select.appendChild(opt);
    });
  }

  // --- Subscribe card ---

  function updateSubscribeUrl() {
    const city = document.getElementById('sub-city').value;
    const system = document.getElementById('sub-system').value;
    const url = `webcal://${FEED_BASE_URL.replace('https://', '')}${feedFilename(city, system)}`;
    document.getElementById('sub-url').textContent = url;
  }

  function copyUrl() {
    if (typeof gcEvent === 'function') gcEvent('subscribe-copy');
    const url = document.getElementById('sub-url').textContent;
    navigator.clipboard.writeText(url).then(() => {
      const el = document.getElementById('copy-confirm');
      el.style.display = 'inline';
      setTimeout(() => { el.style.display = 'none'; }, 2000);
    });
  }

  function showAppTab(name) {
    document.querySelectorAll('.app-tab').forEach(t => t.classList.toggle('active', t.dataset.app === name));
    document.querySelectorAll('.app-panel').forEach(p => p.classList.toggle('active', p.dataset.app === name));
  }

  // --- Choosing a system card ---

  function toggleReadMore(id, btn) {
    const el = document.getElementById(id);
    const open = el.classList.toggle('open');
    btn.textContent = open ? btn.dataset.less : btn.dataset.more;
  }

  // --- Today's Panchangam preview ---

  function unfoldICS(text) {
    return text.replace(/\r\n/g, '\n').split('\n').reduce((lines, line) => {
      if (line.startsWith(' ') && lines.length) {
        lines[lines.length - 1] += line.slice(1);
      } else {
        lines.push(line);
      }
      return lines;
    }, []);
  }

  // Parse every VEVENT into a Map keyed by YYYYMMDD — the preview, night
  // choghadiya (needs tomorrow's sunrise) and upcoming list all read from it.
  function parseEvents(text) {
    const lines = unfoldICS(text);
    const events = new Map();
    let current = null;
    for (const line of lines) {
      if (line === 'BEGIN:VEVENT') { current = []; continue; }
      if (line === 'END:VEVENT') {
        if (current) {
          const dtstart = current.find(l => l.startsWith('DTSTART;VALUE=DATE:'));
          if (dtstart) {
            const summary = (current.find(l => l.startsWith('SUMMARY:')) || '').slice('SUMMARY:'.length);
            const descLine = current.find(l => l.startsWith('DESCRIPTION:')) || '';
            const description = descLine.slice('DESCRIPTION:'.length)
              .replace(/\\n/g, '\n')
              .replace(/\\,/g, ',')
              .replace(/\\;/g, ';')
              .replace(/\\\\/g, '\\');
            events.set(dtstart.slice('DTSTART;VALUE=DATE:'.length), { summary, description });
          }
        }
        current = null;
        continue;
      }
      if (current) current.push(line);
    }
    return events;
  }

  // --- Time formatting (12h/24h toggle) ---

  let TIME_FMT = localStorage.getItem('tc-time-fmt') || '12';

  function fmtT(t) {
    if (TIME_FMT === '24') return t;
    const m = t.match(/^(\d{2}):(\d{2})$/);
    if (!m) return t;
    const h = Number(m[1]);
    return `${h % 12 || 12}:${m[2]}${h < 12 ? 'am' : 'pm'}`;
  }

  // The feed marks times falling outside the event's date with (+1)/(-1);
  // render those as superscripts. Old feeds without markers fall back to the
  // end-reads-earlier-than-start heuristic for the +1 case.
  function dayMark(flag) {
    if (!flag) return '';
    const title = flag === '+1' ? 'after midnight, on the next day' : 'on the previous day';
    return `<sup class="plus1" title="${title}">${flag === '+1' ? '+1' : '−1'}</sup>`;
  }
  function fmtRange(start, end, sep, sflag, eflag) {
    if (!sflag && !eflag && end <= start) eflag = '+1';
    return `${fmtT(start)}${dayMark(sflag)}${sep || ' – '}${fmtT(end)}${dayMark(eflag)}`;
  }

  function setTimeFmt(f) {
    TIME_FMT = f;
    localStorage.setItem('tc-time-fmt', f);
    document.getElementById('fmt-12').classList.toggle('active', f === '12');
    document.getElementById('fmt-24').classList.toggle('active', f === '24');
    renderAll();
    if (typeof TB_DAYS !== 'undefined' && TB_DAYS) renderTarabalam();
    if (typeof GO_DATA !== 'undefined' && GO_DATA) renderGochara();
    if (typeof MU_LAST !== 'undefined' && MU_LAST) renderMuhurta();
  }

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

  // --- Lagna data layer: cached per-session, per-city fetch ---
  const LAGNA_CACHE = new Map();
  async function loadLagna(city) {
    if (LAGNA_CACHE.has(city)) return LAGNA_CACHE.get(city);
    const filename = `${slug(city)}-lagna.json`;
    let promise = fetch(`feeds/${filename}`).then(r => r.ok ? r.json() : null).catch(() => null);
    promise = promise.then(d => d || fetch(`${FEED_BASE_URL}${filename}`).then(r => r.ok ? r.json() : null).catch(() => null));
    LAGNA_CACHE.set(city, promise);
    return promise;
  }

  function lagnaDayFor(data, isoDate) {
    if (!data || !data.days || !data.days.length) return null;
    const direct = data.days.find(d => d.date === isoDate);
    if (direct) return direct;
    // Fallback for older formats without 'date': offset from data.start.
    const start = new Date(`${data.start}T00:00:00`);
    const target = new Date(`${isoDate}T00:00:00`);
    const idx = Math.round((target - start) / 86400000);
    return data.days[idx] || null;
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

  // A time plus optional (+1)/(-1) relative-day marker, as emitted by the feed.
  const TIME_PART = '(\\d{2}:\\d{2})(?:\\s*\\(([+-]1)\\))?';
  // \s+ not \s{2,}: long names (Krishna Chaturdashi, named Ekadashis) overflow the column padding
  const ANGA_RE = new RegExp(`^(Tithi|Nakshatra|Yoga):\\s+(.+?)\\s+${TIME_PART}\\s*[–-]\\s*${TIME_PART}$`);
  const WINDOW_RE = new RegExp(`^\\s+(.+?)\\s{2,}${TIME_PART}\\s*[–-]\\s*${TIME_PART}\\s*$`);
  const CHOG_RE = new RegExp(`^\\s+${TIME_PART}\\s*[–-]\\s*${TIME_PART}\\s+(.+)$`);

  function parseDescription(description) {
    const data = {
      meta: '', tithi: null, nakshatra: null, yoga: null, karana: null,
      sunrise: null, sunset: null, moonrise: null, moonset: null,
      auspicious: [], inauspicious: [], choghadiya: [], nightChoghadiya: [],
      eclipse: null, yogas: [], ayanam: null, rituvu: null, special: [],
    };
    let section = null;
    for (const raw of description.split('\n')) {
      const line = raw.trimEnd();
      if (!line.trim()) { section = null; continue; }

      let m;
      // Header: "<year> [Nama Samvatsara]  ·  Maasam  ·  Paksham  ·  Vaaram".
      // The " Nama Samvatsara" suffix is the new (devotee-preferred)
      // form; older deployed feeds still have just "<year>" — strip
      // whichever shows up so data.samvatsara is always the bare year.
      if ((m = line.match(/^(.+?)\s+·\s+(.+?) Maasam\s+·\s+(.+?) Paksham\s+·\s+(.+)$/))) {
        const yearRaw = m[1].trim().replace(/\s+Nama Samvatsara$/i, '').replace(/\s+Samvatsara$/i, '');
        data.samvatsara = yearRaw;
        data.maasam = m[2].trim();
        data.paksham = m[3].trim();
        data.vaaram = m[4].trim();
        data.meta = `${yearRaw} Nama Samvatsara · ${m[2]} Maasam · ${m[3]} Paksham · ${m[4].trim()}`;
        continue;
      }
      // Sky: "Sunrise HH:MM  ·  Sunset HH:MM  ·  Moonrise HH:MM  ·  Moonset HH:MM"
      if ((m = line.match(/^Sunrise (\d{2}:\d{2})\s+·\s+Sunset (\d{2}:\d{2})\s+·\s+Moonrise (\d{2}:\d{2})\s+·\s+Moonset (\d{2}:\d{2})$/))) {
        [, data.sunrise, data.sunset, data.moonrise, data.moonset] = m;
        continue;
      }
      // Ayanam / Rituvu: "Ayanam: X  ·  Rituvu: Y"
      if ((m = line.match(/^Ayanam:\s+(.+?)\s+·\s+Rituvu:\s+(.+)$/))) {
        data.ayanam = m[1].trim();
        data.rituvu = m[2].trim();
        continue;
      }
      // Signs: "Solar sign: X  ·  Lunar sign: Y" (solar sign drives Vaikunta Ekadashi naming)
      if ((m = line.match(/^Solar sign:\s+(.+?)\s+·\s+Lunar sign:\s+(.+)$/))) {
        data.solarSign = m[1].trim();
        data.lunarSign = m[2].trim();
        continue;
      }
      // Pancha anga rows
      if ((m = line.match(ANGA_RE))) {
        data[m[1].toLowerCase()] = { name: m[2].trim(), start: m[3], sflag: m[4] || null, end: m[5], eflag: m[6] || null };
        continue;
      }
      if ((m = line.match(/^Karana:\s+(.+)$/))) {
        data.karana = m[1].trim();
        continue;
      }
      // Section headers
      if (line === '─ Auspicious ─') { section = 'auspicious'; continue; }
      if (line === '─ Inauspicious ─') { section = 'inauspicious'; continue; }
      if (line === '─ Choghadiya ─') { section = 'choghadiya'; continue; }
      if (line === '─ Night Choghadiya ─') { section = 'nightChoghadiya'; continue; }
      if (line === '─ Eclipse ─') { section = 'eclipse'; continue; }
      if (line === '─ Special Yogas ─') { section = 'specialyogas'; continue; }
      // Auspicious / inauspicious entries: "  Name           HH:MM – HH:MM (+1)"
      if ((section === 'auspicious' || section === 'inauspicious') && (m = line.match(WINDOW_RE))) {
        data[section].push({ name: m[1].trim(), start: m[2], sflag: m[3] || null, end: m[4], eflag: m[5] || null });
        continue;
      }
      // Choghadiya entries: "  HH:MM – HH:MM  Name"
      if ((section === 'choghadiya' || section === 'nightChoghadiya') && (m = line.match(CHOG_RE))) {
        data[section].push({ start: m[1], end: m[3], name: m[5].trim() });
        continue;
      }
      // Eclipse detail line: "  🌒 Solar Eclipse (Total) — visible/not visible..."
      if (section === 'eclipse' && (m = line.match(/^\s*\S+\s+(Solar|Lunar) Eclipse \((.+?)\)\s*[—-]\s*(.+)$/))) {
        data.eclipse = { kind: m[1], subtype: m[2], visible: !m[3].includes('not visible'), window: null, sutak: null };
        continue;
      }
      if (section === 'eclipse' && data.eclipse && (m = line.match(/^\s+Window:\s+(.+?)\s*[–-]\s*(.+)$/))) {
        data.eclipse.window = { start: m[1].trim(), end: m[2].trim() };
        continue;
      }
      if (section === 'eclipse' && data.eclipse && (m = line.match(/^\s+Sutak:\s+(.+?)\s*[–-]\s*(.+)$/))) {
        data.eclipse.sutak = { start: m[1].trim(), end: m[2].trim() };
        continue;
      }
      // Special yoga entries: "  Yoga Name" (new format)
      if (section === 'specialyogas' && (m = line.match(/^\s+(.+)$/))) {
        data.yogas.push(m[1].trim());
        continue;
      }
      // Backward compat: old "Yogas: X, Y" single-line format
      if ((m = line.match(/^Yogas:\s+(.+)$/))) {
        data.yogas = m[1].trim().split(/,\s*/);
        continue;
      }
      // Trailing special-day line: "⚡ Ekadashi — fasting day  ·  Pradosham"
      if ((m = line.match(/^⚡\s*(.+)$/))) {
        data.special = m[1].split(/\s+·\s+/).map(s => s.trim());
        continue;
      }
    }
    return data;
  }

  let _tpDateVal = null;
  function selectedDate() {
    return _tpDateVal ? new Date(_tpDateVal + 'T00:00:00') : new Date();
  }

  function formatToday() {
    return selectedDate().toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' });
  }

  function stampOf(d) {
    return `${d.getFullYear()}${String(d.getMonth() + 1).padStart(2, '0')}${String(d.getDate()).padStart(2, '0')}`;
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
    const cityForLagna = document.getElementById('tp-city')?.value;
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

  // --- Upcoming special days (next 30 days, same city/system as preview) ---

  function renderUpcoming(events) {
    const container = document.getElementById('upcoming-result');
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const rows = [];
    for (let i = 1; i <= 30; i++) {
      const d = new Date(today);
      d.setDate(d.getDate() + i);
      const ev = events.get(stampOf(d));
      if (!ev || !(ev.summary.includes('⚡') || ev.summary.includes('🪔'))) continue;
      const data = parseDescription(ev.description);
      let chips = '';
      data.special
        .filter(s => !(data.eclipse && /Eclipse/.test(s)))
        .forEach(s => { chips += `<span class="special-chip">${chipEmoji(s, ev.summary)} ${specialLabel(s, data)}</span>`; });
      if (data.eclipse) chips += eclipseChip(data.eclipse);
      if (!chips) continue;
      const dow = d.toLocaleDateString('en-US', { weekday: 'short' });
      const md = d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
      rows.push(`<div class="upcoming-row">
        <span class="upcoming-date"><span class="dow">${dow}</span> ${md}<span class="upcoming-in"> · in ${i} day${i > 1 ? 's' : ''}</span></span>
        <span class="upcoming-chips">${chips}</span>
      </div>`);
    }
    container.innerHTML = rows.length
      ? `<div class="upcoming-list">${rows.join('')}</div>`
      : '<p class="preview-note">No special days in the next 30 days.</p>';
  }

  const FEED_CACHE = new Map();
  let LAST_EVENTS = null;

  async function loadFeed(city, system) {
    const key = `${city}|${system}`;
    if (FEED_CACHE.has(key)) return FEED_CACHE.get(key);
    // Relative path on the deployed site; fall back to the live feed URL
    // so the page also works when previewed locally without a feeds/ dir.
    let res = await fetch(`feeds/${feedFilename(city, system)}`).catch(() => null);
    if (!res || !res.ok) res = await fetch(`${FEED_BASE_URL}${feedFilename(city, system)}`);
    if (!res.ok) throw new Error('fetch failed');
    const events = parseEvents(await res.text());
    FEED_CACHE.set(key, events);
    return events;
  }

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
    const city = document.getElementById('tp-city').value;
    const system = document.getElementById('tp-system').value;
    document.getElementById('tp-result').innerHTML = '<p class="preview-error">Loading…</p>';
    try {
      LAST_EVENTS = await loadFeed(city, system);
      renderAll();
    } catch (e) {
      LAST_EVENTS = null;
      document.getElementById('tp-result').innerHTML = '<p class="preview-error">Preview unavailable — try the subscription link below.</p>';
      document.getElementById('upcoming-result').innerHTML = '<p class="preview-error">Unavailable — try the subscription link below.</p>';
    }
  }

  // --- Share today's panchangam on WhatsApp (plain-text forward) ---

  function fmtPlain(t, flag) {
    return fmtT(t) + (flag === '+1' ? ' (next day)' : flag === '-1' ? ' (prev day)' : '');
  }

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

  // --- Tarabalam tool ---

  const TB_NAKSHATRAS = ['Ashvini','Bharani','Krittika','Rohini','Mrigashira','Ardra','Punarvasu','Pushya','Ashlesha','Magha','Purva Phalguni','Uttara Phalguni','Hasta','Chitra','Swati','Vishakha','Anuradha','Jyeshtha','Mula','Purva Ashadha','Uttara Ashadha','Shravana','Dhanishtha','Shatabhisha','Purva Bhadrapada','Uttara Bhadrapada','Revati'];
  const TARA_NAMES = ['Janma','Sampat','Vipat','Kshema','Pratyak','Sadhana','Naidhana','Mitra','Parama Mitra'];
  const TARA_GOOD = new Set([2,4,6,8,9]);
  const TB_RASIS = ['Mesha','Vrishabha','Mithuna','Karka','Simha','Kanya','Tula','Vrischika','Dhanu','Makara','Kumbha','Meena'];
  const CHANDRA_GOOD = new Set([1,3,6,7,10,11]);
  const CHANDRA_PUJA = new Set([2,5,9]);
  let TB_DAYS = null;    // last computed result rows
  let TB_EVENTS = null;  // feed events used for the last calculation

  function taraOf(janmaName, dayName) {
    const j = TB_NAKSHATRAS.indexOf(janmaName), d = TB_NAKSHATRAS.indexOf(dayName);
    if (j < 0 || d < 0) return null;
    return ((d - j + 27) % 27) % 9 + 1;
  }

  function rasiFromStar(nakName, pada) {
    const k = TB_NAKSHATRAS.indexOf(nakName);
    if (k < 0) return null;
    if (pada) return TB_RASIS[Math.floor((k * 4 + pada - 1) / 9)];
    const first = Math.floor((k * 4) / 9), last = Math.floor((k * 4 + 3) / 9);
    return first === last ? TB_RASIS[first] : null;  // straddler needs padam
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
      const nak = document.getElementById(`tb-nak-${i}`).value;
      if (!nak) continue;
      const name = document.getElementById(`tb-name-${i}`).value.trim() || (i === 0 ? 'You' : `Person ${i+1}`);
      const pada = Number(document.getElementById(`tb-pada-${i}`).value) || null;
      const lagnaInput = document.getElementById(`tb-lagna-${i}`);
      const lagna = (lagnaInput && lagnaInput.value) ? lagnaInput.value : null;
      out.push({ name, nak, pada, rasi: rasiFromStar(nak, pada), lagna });
    }
    return out;
  }

  function tbSaveProfiles() {
    const raw = [];
    for (let i = 0; i < TB_ROWS; i++) {
      const lagnaInput = document.getElementById(`tb-lagna-${i}`);
      raw.push({ name: document.getElementById(`tb-name-${i}`).value,
                 nak: document.getElementById(`tb-nak-${i}`).value,
                 pada: document.getElementById(`tb-pada-${i}`).value,
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
      const opts = ['<option value="">— birth star —</option>']
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
        <select id="tb-pada-${i}" style="min-width:90px;" title="Padam (quarter) of the birth star — needed only when the star spans two rashis" onchange="tbSaveProfiles(); tbRenderProfileInputs();">${padaOpts}</select>
        <select id="tb-lagna-${i}" style="min-width:130px;" title="Janma Lagna — the rising sign at the moment of birth. Leave blank if you don't know it; we'll use your janma rashi instead for muhurta scoring." onchange="tbSaveProfiles();">${lagnaOpts}</select>
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
    if (GO_DATA) { goBuildViewSelect(); renderGochara(); }
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
    const from = new Date(document.getElementById('tb-from').value + 'T00:00:00');
    const to = new Date(document.getElementById('tb-to').value + 'T00:00:00');
    const span = Math.round((to - from) / 86400000) + 1;
    if (!(span >= 1 && span <= 60)) {
      resBox.innerHTML = '<p class="preview-error">Pick a range of 1 to 60 days.</p>';
      return;
    }
    resBox.innerHTML = '<p class="preview-error">Calculating…</p>';
    try {
      const city = document.getElementById('tp-city').value;
      const system = document.getElementById('tp-system').value;
      const events = LAST_EVENTS || await loadFeed(city, system);
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
          const entry = { who: pr.name, tara: t, label: TARA_NAMES[t-1], good: TARA_GOOD.has(t) };
          if (pr.rasi && data.lunarSign) entry.chandra = chandraOf(pr.rasi, data.lunarSign);
          return entry;
        });
        TB_DAYS.push({ date: new Date(d), nak, nakUntil: data.nakshatra.end, nakEflag: data.nakshatra.eflag,
                       moonRasi: data.lunarSign || '', tithi: data.tithi ? data.tithi.name : '', taras });
      }
      renderTarabalam(profiles);
    } catch (e) {
      resBox.innerHTML = '<p class="preview-error">Could not load the feed — try again.</p>';
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
    TB_SHOW_ALL = document.getElementById('tb-show-all').checked;
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
    document.getElementById('tb-to').value = iso;
    calcTarabalam();
  }

  function renderTarabalam(profiles) {
    if (!TB_DAYS) return;
    profiles = profiles || tbProfiles();
    const group = profiles.length > 1;
    TB_DAYS.forEach(r => { r.allGood = r.taras.every(tbPersonGood); });
    document.getElementById('tb-mode').value = TB_MODE;
    const goodDays = TB_DAYS.filter(r => r.allGood);
    const next = goodDays[0];
    const who = group ? 'everyone' : (profiles[0] ? profiles[0].name : 'you');
    let summary = `<span class="count">${goodDays.length} of ${TB_DAYS.length}</span>&nbsp;days are favourable for ${who}`;
    if (next) {
      summary += ` — next: <span class="count">${next.date.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })}</span>`;
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
          `<p class="preview-error">This combination of birth stars never aligns — tarabalam repeats over the
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
           The next one is <strong>${label}</strong> —
           <button class="read-more" style="color:var(--indigo);" onclick="tbExtendTo('${iso}')">extend the range to include it</button>,
           or tick "show all days".</p>`;
      } else {
        document.getElementById('tb-result').innerHTML =
          `<p class="preview-error">No favourable days for ${who} in this range, and none found in the months ahead
           — tick "show all days" to plan by individual taras.</p>`;
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
      legend += `<div><span class="tara-chip puja">amber</span> good — a small remedial puja is advised (°).</div>`;
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
    document.getElementById('tb-mode').value = TB_MODE;
    TB_DAYS.forEach(r => { r.allGood = r.taras.every(tbPersonGood); });
    const goodDays = TB_DAYS.filter(r => r.allGood);
    if (!goodDays.length) return;
    const citySel = document.getElementById('tp-city');
    const cityLabel = citySel.options[citySel.selectedIndex].textContent;
    const fmtD = d => d.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
    const lines = [];
    const anyRasi = profiles.some(pr => pr.rasi);
    lines.push(`✦ *Good days ${group ? 'for all of us' : 'for me'} (${anyRasi ? 'Tarabalam · Chandrabalam' : 'Tarabalam'})*`);
    lines.push(`📍 ${cityLabel} · ${fmtD(TB_DAYS[0].date)} – ${fmtD(TB_DAYS[TB_DAYS.length-1].date)}`);
    lines.push(profiles.map(pr => `${pr.name}: ${pr.nak}`).join(' · '));
    lines.push(`Standard: ${{ stars: 'Stars only (classic)', puja_ok: 'Stars + Moon, puja ok', strict: 'Stars + Moon, strict' }[TB_MODE]}`);
    lines.push('');
    goodDays.forEach(r => lines.push(`✅ ${fmtD(r.date)} — ${r.nak} · ${r.tithi}`));
    lines.push('');
    lines.push('Check your own birth star:');
    lines.push('https://panchangam.astrochaganti.com/?src=share-tarabalam#tarabalam');
    gcEvent('share-tarabalam');
    window.open('https://wa.me/?text=' + encodeURIComponent(lines.join('\n')), '_blank');
  }

  // mobile: expand / collapse the "Find a time slot" section. Desktop CSS
  // ignores the .expanded toggle, so this is a no-op there.
  function muToggleMobile() {
    const sec = document.getElementById('mu-section');
    if (sec) sec.classList.toggle('mu-open');
  }

  // mobile: contextual help bottom-sheet. Pulls in the guide for the active
  // tab — Today has its own hidden source; Gochara and Tarabalam reuse the
  // existing #go-help and #tb-help guides verbatim.
  const HELP_TITLES = {
    today:     'How to read Today',
    gochara:   'How to read Gochara · Rasi Phalalu',
    tarabalam: 'How to use Tarabalam · Muhurtam',
  };
  const PAGE_TITLES = {
    today:     ["Today's Panchangam", 'What is the day?'],
    gochara:   ['Gochara · Rasi Phalalu', 'What does it mean for me?'],
    tarabalam: ['Tarabalam · Muhurtam', 'When should we act?'],
    festivals: ['Festivals', 'Special days — next 30 days'],
    subscribe: ['Subscribe', 'Get panchangam in your calendar'],
    useinai:   ['Use in AI', 'MCP server for AI assistants'],
    about:     ['About', 'What this is and how it works'],
  };
  function openHelpSheet() {
    const active = document.querySelector('#m-bottomnav .m-tab.active');
    const tab = active ? active.dataset.tab : 'today';
    const src = tab === 'today'   ? document.getElementById('today-help-src')
              : tab === 'gochara' ? document.getElementById('go-help')
              :                     document.getElementById('tb-help');
    document.getElementById('m-help-title').textContent = HELP_TITLES[tab];
    document.getElementById('m-help-body').innerHTML = src ? src.innerHTML : '';
    document.body.classList.add('m-help-open');
    document.getElementById('m-help-sheet').setAttribute('aria-hidden', 'false');
    document.querySelectorAll('.m-page-help-btn').forEach(b => b.setAttribute('aria-expanded', 'true'));
    if (typeof gcEvent === 'function') gcEvent('help-' + tab);
  }
  function closeHelpSheet() {
    document.body.classList.remove('m-help-open');
    document.getElementById('m-help-sheet').setAttribute('aria-hidden', 'true');
    document.querySelectorAll('.m-page-help-btn').forEach(b => b.setAttribute('aria-expanded', 'false'));
  }

  const TOOL_PANELS = ['today', 'tarabalam', 'gochara'];

  function switchTool(which) {
    // Tool panels: show/hide the three original panels
    for (const t of TOOL_PANELS) {
      document.getElementById('panel-' + t).style.display = t === which ? '' : 'none';
      document.getElementById('tab-' + t).classList.toggle('active', t === which);
      document.getElementById('tab-' + t).setAttribute('aria-selected', t === which ? 'true' : 'false');
    }
    document.body.dataset.tool = which;
    // sidebar stays in sync on desktop
    document.querySelectorAll('#sidebar .sidebar-item[id]').forEach(b => {
      b.classList.toggle('active', b.id === 'sidebar-' + which);
    });
    // mobile bottom-nav stays in sync (only meaningful for the 3 tool panels)
    document.querySelectorAll('#m-bottomnav .m-tab').forEach(b => {
      const on = b.dataset.tab === which;
      b.classList.toggle('active', on);
      b.setAttribute('aria-selected', on ? 'true' : 'false');
    });
    const titles = PAGE_TITLES[which];
    document.getElementById('m-page-title-main').textContent = titles ? titles[0] : '';
    document.getElementById('m-page-title-sub').textContent = titles ? titles[1] : '';
    if (history.replaceState) history.replaceState(null, '', which === 'today' ? '#' : '#' + which);
    if (typeof gcEvent === 'function') gcEvent('tab-' + which);
    if (which === 'gochara') loadGochara();
  }

  // --- Gochara tool ---

  const GO_FAV = { Surya:[3,6,10,11], Chandra:[1,3,6,7,10,11], Kuja:[3,6,11],
    Budha:[2,4,6,8,10,11], Guru:[2,5,7,9,11], Shukra:[1,2,3,4,5,8,9,11,12],
    Shani:[3,6,11], Rahu:[3,6,11], Ketu:[3,6,11] };
  const GO_VEDHA = { Surya:{3:9,6:12,10:4,11:5}, Chandra:{1:5,3:9,6:12,7:2,10:4,11:8},
    Kuja:{3:12,6:9,11:5}, Budha:{2:5,4:3,6:9,8:1,10:8,11:12},
    Guru:{2:12,5:4,7:3,9:10,11:8}, Shukra:{1:8,2:7,3:1,4:10,5:9,8:5,9:11,11:6,12:3},
    Shani:{3:12,6:9,11:5} };
  const GO_EXEMPT = new Set(['Surya|Shani','Shani|Surya','Chandra|Budha','Budha|Chandra']);
  const GO_NODES = new Set(['Rahu','Ketu']);
  let GO_DATA = null;

  async function loadGochara() {
    const firstLoad = !GO_DATA;
    if (firstLoad) {
      try {
        const r = await fetch('gochara.json', { cache: 'no-cache' });
        GO_DATA = await r.json();
      } catch (e) {
        document.getElementById('go-chart').innerHTML =
          '<p class="preview-error">Sky data unavailable — try again later.</p>';
        return;
      }
      const di = document.getElementById('go-date');
      di.min = GO_DATA.start;
      const last = new Date(GO_DATA.start + 'T00:00:00');
      last.setDate(last.getDate() + GO_DATA.days.length - 1);
      di.max = `${last.getFullYear()}-${String(last.getMonth()+1).padStart(2,'0')}-${String(last.getDate()).padStart(2,'0')}`;
      di.value = todayISO;
    }
    // people may have changed in the Tarabalam tab — rebuild, keep selection
    const sel = document.getElementById('go-view');
    let keep = firstLoad ? localStorage.getItem('tc-go-view') : sel.value;
    // An earlier iteration of this PR had separate 'p<i>r' / 'p<i>l'
    // options; we collapsed those into a single 'p<i>' combined
    // option. Strip the suffix on load so test users who saved a
    // suffixed value during the iteration don't end up unselected.
    if (keep && /^p\d+[rl]$/.test(keep)) keep = keep.slice(0, -1);
    goBuildViewSelect();
    if (keep && [...sel.options].some(o => o.value === keep)) sel.value = keep;
    renderGochara();
  }

  function goDateIndex() {
    const start = new Date(GO_DATA.start + 'T00:00:00');
    const val = document.getElementById('go-date').value;
    const chosen = val ? new Date(val + 'T00:00:00') : new Date(new Date().setHours(0,0,0,0));
    const i = Math.round((chosen - start) / 86400000);
    return Math.max(0, Math.min(i, GO_DATA.days.length - 1));
  }

  function goTill(idx, gi) {
    const cur = GO_DATA.days[idx][gi];
    for (let j = idx + 1; j < GO_DATA.days.length; j++) {
      if (GO_DATA.days[j][gi] !== cur) {
        const d = new Date(GO_DATA.start + 'T00:00:00');
        d.setDate(d.getDate() + j);
        return { date: d, next: GO_DATA.rasis[GO_DATA.days[j][gi]] };
      }
    }
    return null;
  }

  function goSavedPeople() {
    const saved = JSON.parse(localStorage.getItem('tc-tb-profiles') || '[]');
    return saved.map((v, i) => {
      if (!v || !v.nak) return null;
      const rasi = rasiFromStar(v.nak, Number(v.pada) || null);
      if (!rasi) return null;
      // Janma lagna is optional — only surfaced as a separate view
      // option when the user has filled it on the Tarabalam profile.
      const lagna = v.lagna || null;
      return {
        name: (v.name || (i === 0 ? 'You' : `Person ${i+1}`)),
        rasi,
        lagna,
      };
    }).filter(Boolean);
  }

  function goBuildViewSelect() {
    const sel = document.getElementById('go-view');
    const people = goSavedPeople();
    let html = '<option value="">Transits only — whole sky</option>';
    if (people.length) {
      // One row per person — when janma lagna is also on the profile,
      // the row label says so. The chart then uses BOTH references to
      // verdict each graha; you don't pick rashi-or-lagna, you get
      // the personalised combined view.
      const rows = people.map((k, i) => {
        const refs = k.lagna
          ? `${htmlEsc(k.rasi)} rashi + ${htmlEsc(k.lagna)} lagna`
          : `${htmlEsc(k.rasi)} rashi`;
        return `<option value="p${i}">${htmlEsc(k.name)} · ${refs}</option>`;
      });
      html += '<optgroup label="Your saved people">' + rows.join('') + '</optgroup>';
    }
    html += '<optgroup label="Any rashi">' +
      GO_DATA.rasis.map((r, i) => `<option value="${i}">${r}</option>`).join('') + '</optgroup>';
    sel.innerHTML = html;
  }

  function goCurrentView() {
    const val = document.getElementById('go-view').value;
    if (val === '') return { jr: null, jl: null, label: null };
    // 'p<i>' — profile-keyed combined view. We carry BOTH the rashi
    // index (jr, used to lay out the chart and number houses) AND the
    // optional lagna index (jl, used as a second reference for graha
    // verdicts and the conditions banner).
    const profMatch = val.match(/^p(\d+)$/);
    if (profMatch) {
      const k = goSavedPeople()[Number(profMatch[1])];
      if (!k) return { jr: null, jl: null, label: null };
      const jr = TB_RASIS.indexOf(k.rasi);
      const jl = k.lagna ? TB_RASIS.indexOf(k.lagna) : null;
      const refLabel = k.lagna
        ? `${k.rasi} rashi + ${k.lagna} lagna (${k.name})`
        : `${k.rasi} rashi (${k.name})`;
      return { jr, jl, label: refLabel };
    }
    // Bare rashi-index option from the "Any rashi" group.
    return { jr: Number(val), jl: null, label: GO_DATA.rasis[Number(val)] + ' rashi' };
  }

  // South Indian chart: fixed rasi positions on a 4x4 grid (row, col)
  const GO_LAYOUT = { 11:[1,1], 0:[1,2], 1:[1,3], 2:[1,4], 3:[2,4], 4:[3,4],
                      5:[4,4], 6:[4,3], 7:[4,2], 8:[4,1], 9:[3,1], 10:[2,1] };

  function renderGochara() {
    if (!GO_DATA) return;
    const idx = goDateIndex();
    const row = GO_DATA.days[idx], retro = GO_DATA.retro[idx];
    const view = goCurrentView();
    const jr = view.jr;
    const jl = (typeof view.jl === 'number') ? view.jl : null;
    localStorage.setItem('tc-go-view', document.getElementById('go-view').value);

    const dateShown = new Date(GO_DATA.start + 'T00:00:00');
    dateShown.setDate(dateShown.getDate() + idx);
    const fmtD = d => d.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric', year: 'numeric' });

    // Per-graha verdicts using a chosen reference index (rashi index
    // 0..11). Works for both janma rashi and janma lagna — same
    // Brihat Samhita rules, different reference frame.
    const houseFrom = (gi, ref) => ((row[gi] - ref + 12) % 12) + 1;
    const occupantsFor = (ref) => {
      const o = {};
      GO_DATA.grahas.forEach((g, gi) => {
        const h = houseFrom(gi, ref);
        (o[h] = o[h] || []).push(g);
      });
      return o;
    };
    const verdictFrom = (gi, ref, occ) => {
      const g = GO_DATA.grahas[gi], pos = houseFrom(gi, ref);
      if (!GO_FAV[g].includes(pos)) return 'bad';
      if (!GO_NODES.has(g)) {
        const vh = GO_VEDHA[g][pos];
        for (const other of (occ[vh] || [])) {
          if (other !== g && !GO_NODES.has(other) && !GO_EXEMPT.has(g + '|' + other)) return 'blocked';
        }
      }
      return 'good';
    };

    // Pre-compute occupants for each reference we'll use.
    const occRashi = (jr !== null) ? occupantsFor(jr) : null;
    const occLagna = (jl !== null) ? occupantsFor(jl) : null;

    // House numbering for the chart stays anchored to janma RASHI —
    // that's what users have always seen. The lagna lens is an extra
    // verdict layer, not a chart re-anchoring.
    const houseOf = gi => jr === null ? null : houseFrom(gi, jr);

    // Chart colour is anchored to the janma RASHI verdict — the
    // traditional Brihat Samhita gochara frame. The lagna lens is
    // surfaced separately (tooltip + prose) without judgement;
    // classical texts don't prescribe a single rule for merging the
    // two into one verdict, so we don't invent one.
    const verdictOf = gi => {
      if (jr === null) return null;
      return verdictFrom(gi, jr, occRashi);
    };
    const verdictsBoth = gi => {
      if (jr === null) return null;
      const vr = verdictFrom(gi, jr, occRashi);
      const vl = (jl !== null) ? verdictFrom(gi, jl, occLagna) : null;
      return { vr, vl };
    };

    // Conditions banner — Sade Sati / Ashtama / Ardhastama Shani.
    // Checked from BOTH references when both are set, so users see
    // conditions that fire on only one lens (a common Jyotisha case).
    const condBox = document.getElementById('go-conditions');
    const shaniIdx = GO_DATA.grahas.indexOf('Shani');
    const shaniCondFor = (sp) => {
      if (sp === 12) return 'Sade Sati (rising phase)';
      if (sp === 1) return 'Sade Sati (peak phase)';
      if (sp === 2) return 'Sade Sati (setting phase)';
      if (sp === 8) return 'Ashtama Shani';
      if (sp === 4) return 'Ardhastama Shani';
      return null;
    };
    let conds = [];
    if (jr !== null) {
      const cR = shaniCondFor(houseFrom(shaniIdx, jr));
      if (cR) conds.push(jl !== null ? `${cR} — from rashi` : cR);
    }
    if (jl !== null) {
      const cL = shaniCondFor(houseFrom(shaniIdx, jl));
      if (cL) conds.push(`${cL} — from lagna`);
    }
    condBox.innerHTML = conds.length
      ? `<div class="go-cond">${conds.map(c => `<span class="chip">⚠️ ${htmlEsc(c)}</span>`).join('')}
         <div class="tb-sub" style="margin-top:0.25rem;">Running ${conds[0].split(' — ')[0].split(' (')[0]}? Personalised guidance:
         <a href="https://astrochaganti.com" target="_blank" rel="noopener" style="color:var(--indigo);font-weight:600;">astrochaganti.com</a></div></div>` : '';

    // chart
    const byRasi = {};
    GO_DATA.grahas.forEach((g, gi) => { (byRasi[row[gi]] = byRasi[row[gi]] || []).push(gi); });
    const ord = n => `${n}${['st','nd','rd'][n-1] || 'th'}`;
    const verdictLabel = v => v === 'good' ? 'favourable' : v === 'blocked' ? 'vedha' : 'adverse';
    let boxes = '';
    for (let r = 0; r < 12; r++) {
      const [gr, gc] = GO_LAYOUT[r];
      const grahas = (byRasi[r] || []).map(gi => {
        const v = verdictOf(gi);
        const both = verdictsBoth(gi);
        const t = goTill(idx, gi);
        // Tooltip surfaces BOTH references when lagna is set so the
        // user can see exactly why a combined verdict landed where it
        // did (e.g. "good from rashi · adverse from lagna" → adverse).
        let perRef = '';
        if (both) {
          const hr = houseFrom(gi, jr);
          const partR = `${ord(hr)} from rashi (${verdictLabel(both.vr)})`;
          if (both.vl !== null) {
            const hl = houseFrom(gi, jl);
            perRef = ` — ${partR} · ${ord(hl)} from lagna (${verdictLabel(both.vl)})`;
          } else {
            perRef = ` — ${partR}`;
          }
        }
        const tip = `${GO_DATA.grahas[gi]} in ${GO_DATA.rasis[r]}${perRef}` +
          (t ? ` · till ${t.date.toLocaleDateString('en-US',{month:'short',day:'numeric'})}` : '');
        return `<span class="go-g ${v || ''}" title="${htmlEsc(tip)}">${GO_DATA.grahas[gi]}${retro[gi] ? '<span class="go-retro">℞</span>' : ''}</span>`;
      }).join('');
      const house = jr !== null ? `<span class="house">${((r - jr + 12) % 12) + 1}</span>` : '';
      // Highlight both natal cells when known. When they coincide
      // (janma rashi == janma lagna) we render a single combined
      // label rather than 'janma · lagna' which would look odd.
      const isJanma = (jr === r);
      const isLagna = (jl !== null && jl === r);
      const classes = ['go-box'];
      if (isJanma) classes.push('janma');
      if (isLagna) classes.push('lagna');
      let label = '';
      if (isJanma && isLagna) label = ' · janma + lagna';
      else if (isJanma) label = ' · janma';
      else if (isLagna) label = ' · lagna';
      boxes += `<div class="${classes.join(' ')}" style="grid-row:${gr};grid-column:${gc};">
        <span class="rname">${GO_DATA.rasis[r]}${label}</span>${house}<br>${grahas}</div>`;
    }
    const typed = document.getElementById('go-date').value;
    const shownISO = `${dateShown.getFullYear()}-${String(dateShown.getMonth()+1).padStart(2,'0')}-${String(dateShown.getDate()).padStart(2,'0')}`;
    document.getElementById('go-note').innerHTML = typed && typed !== shownISO
      ? `<p class="preview-note" style="color:#8A5518;">That date is outside this chart's data window
         (${GO_DATA.start} to ${document.getElementById('go-date').max}) — showing the nearest covered day,
         ${fmtD(dateShown)}. For any date, past or future, ask via the MCP server below.</p>` : '';
    const center = `<div class="go-center"><div class="d1">🪐 Gochara</div>
      <div class="d2">${fmtD(dateShown)}</div>
      <div class="d2">${jr !== null ? 'from ' + htmlEsc(view.label) : 'transits — choose a person or rashi above to personalise'}</div></div>`;
    document.getElementById('go-chart').innerHTML = boxes + center;

    // upcoming moves, soonest first
    const moves = GO_DATA.grahas.map((g, gi) => ({ g, t: goTill(idx, gi) }))
      .filter(m => m.t).sort((a, b) => a.t.date - b.t.date).slice(0, 5);
    document.getElementById('go-moves').innerHTML = moves.length
      ? `<div class="go-moves"><b>Coming up:</b> ` + moves.map(m =>
          `<span class="go-move">${m.g} → ${m.t.next} <b>${m.t.date.toLocaleDateString('en-US',{month:'short',day:'numeric'})}</b></span>`)
          .join('<span class="go-move-sep"> &nbsp;·&nbsp; </span>') + `</div>` : '';

    // rasi phalalu (daily reading from the same computed verdicts)
    const phBox = document.getElementById('go-phalalu');
    if (jr === null) { phBox.innerHTML = ''; }
    else {
      const ph = buildPhalalu(jr, jl, row, view, idx);
      const phShare = `<button class="wa-share-mini" style="position:static;width:26px;height:26px;margin-left:auto;flex:none;" title="Share this reading on WhatsApp" aria-label="Share on WhatsApp" onclick="shareGocharaOnWhatsApp()"><svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor" aria-hidden="true"><path d="M12.04 2a9.9 9.9 0 0 0-8.46 15.1L2 22l5.05-1.55A9.9 9.9 0 1 0 12.04 2zm0 18.1a8.2 8.2 0 0 1-4.18-1.15l-.3-.18-3 .92.93-2.92-.2-.3a8.2 8.2 0 1 1 6.75 3.63zm4.5-6.14c-.25-.12-1.46-.72-1.69-.8-.22-.08-.39-.12-.55.13-.17.24-.64.8-.78.96-.14.16-.29.18-.53.06a6.7 6.7 0 0 1-3.35-2.93c-.25-.43.25-.4.72-1.34.08-.16.04-.3-.02-.43-.06-.12-.55-1.33-.76-1.82-.2-.48-.4-.42-.55-.43h-.47c-.16 0-.43.06-.65.3-.22.25-.85.84-.85 2.04 0 1.2.88 2.36 1 2.52.12.16 1.72 2.63 4.17 3.69.58.25 1.04.4 1.4.51.58.19 1.11.16 1.53.1.47-.07 1.46-.6 1.67-1.18.2-.58.2-1.07.14-1.18-.06-.1-.22-.16-.47-.28z"/></svg></button>`;
      phBox.innerHTML = `<div class="go-phalalu"><h4 style="display:flex;align-items:center;gap:0.4rem;">Rasi Phalalu — ${htmlEsc(view.label)}
        <span class="go-quality ${ph.quality}">${ph.quality} day</span>${phShare}</h4>` +
        ph.lines.map(l => `<p>${l}</p>`).join('') +
        `<p style="font-size:0.72rem;color:#B5AC9C;">Every line above is rendered from the chart's computed verdicts — nothing is invented.</p></div>`;
    }

    // legend
    document.getElementById('go-legend').innerHTML = jr === null ? '' :
      `<div class="tb-legend" style="margin-top:0.5rem;">
        <span class="tb-legend-item"><span class="go-g good">favourable</span></span>
        <span class="tb-legend-item"><span class="go-g blocked">blocked by vedha</span></span>
        <span class="tb-legend-item"><span class="go-g bad">adverse</span></span>
        <span class="tb-legend-item"><span class="go-g">℞ retrograde</span></span>
        </div>`;
  }

  const HOUSE_MEANINGS = { 1:'self and health', 2:'wealth and family', 3:'courage and effort',
    4:'home and comfort', 5:'children and learning', 6:'health and rivals', 7:'partnerships',
    8:'obstacles', 9:'fortune and dharma', 10:'career and standing', 11:'gains and income', 12:'expenses and rest' };
  const PHALALU_OPENERS = {
    good: 'The Moon stands well for your rashi today — a day that supports initiative.',
    puja: "The Moon's position asks for a small remedial prayer; proceed gently after it.",
    bad: 'The Moon sits heavily for your rashi today — keep the day light and routine.' };
  const PHALALU_ORDER = ['Shani','Guru','Rahu','Ketu','Kuja','Surya','Shukra','Budha'];
  const ordinal = n => n + (['st','nd','rd'][n-1] || 'th');

  function buildPhalalu(jr, jl, row, view, idx) {
    // Two independent verdicts per graha — one from each reference.
    // No "combine into one" judgement; classical Jyotisha doesn't
    // prescribe a merge rule, so we surface both lenses side by side
    // when janma lagna is set. Chart colour and the count tally
    // stay anchored to janma rashi (matches the chart visual).
    const houseFromRef = (gi, ref) => ((row[gi] - ref + 12) % 12) + 1;
    const occFor = (ref) => {
      const o = {};
      GO_DATA.grahas.forEach((g, gi) => {
        const h = houseFromRef(gi, ref);
        (o[h] = o[h] || []).push(g);
      });
      return o;
    };
    const verdictForRef = (gi, ref, occ) => {
      const g = GO_DATA.grahas[gi], pos = houseFromRef(gi, ref);
      if (!GO_FAV[g].includes(pos)) return { v: 'adverse' };
      if (!GO_NODES.has(g)) {
        const vh = GO_VEDHA[g][pos];
        for (const other of (occ[vh] || [])) {
          if (other !== g && !GO_NODES.has(other) && !GO_EXEMPT.has(g + '|' + other)) return { v: 'blocked', by: other };
        }
      }
      return { v: 'favourable' };
    };
    const occR = occFor(jr);
    const occL = (jl !== null) ? occFor(jl) : null;
    const houseOf = gi => houseFromRef(gi, jr);     // chart anchor stays rashi
    const moonPos = houseOf(GO_DATA.grahas.indexOf('Chandra'));
    const mv = CHANDRA_GOOD.has(moonPos) ? 'good' : (CHANDRA_PUJA.has(moonPos) ? 'puja' : 'bad');
    let fav = 0, blocked = 0;
    const detail = {};
    GO_DATA.grahas.forEach((g, gi) => {
      // Rashi verdict drives the tally (and the chart colours).
      const r = verdictForRef(gi, jr, occR);
      const l = (occL !== null) ? verdictForRef(gi, jl, occL) : null;
      detail[g] = { ...r, lagna: l, posR: houseOf(gi),
                    posL: (jl !== null) ? houseFromRef(gi, jl) : null };
      if (r.v === 'favourable') fav++; else if (r.v === 'blocked') blocked++;
    });
    const quality = (mv === 'good' && fav >= 4) ? 'good' : (mv === 'bad' && fav <= 2) ? 'difficult' : 'mixed';
    const lines = [PHALALU_OPENERS[mv]];

    // Shani condition checked from BOTH references (matches the
    // chart's conditions banner). Each hit gets its own line so the
    // reader sees which lens triggered it.
    const shaniIdx = GO_DATA.grahas.indexOf('Shani');
    const shaniCondText = (sp) => sp === 12 ? 'Sade Sati (rising phase)' : sp === 1 ? 'Sade Sati (peak phase)'
      : sp === 2 ? 'Sade Sati (setting phase)' : sp === 8 ? 'Ashtama Shani'
      : sp === 4 ? 'Ardhastama Shani' : null;
    const shaniLineFor = (cond, refLabel) => {
      const suffix = refLabel ? ` (from ${refLabel})` : '';
      return cond.startsWith('Sade Sati')
        ? `${cond}${suffix} is running — Shani asks for patience, discipline and steady work.`
        : `${cond}${suffix} is running — avoid risks and keep commitments minimal.`;
    };
    const condR = shaniCondText(houseFromRef(shaniIdx, jr));
    const condL = (jl !== null) ? shaniCondText(houseFromRef(shaniIdx, jl)) : null;
    if (condR) lines.push(shaniLineFor(condR, jl !== null ? 'rashi' : null));
    if (condL) lines.push(shaniLineFor(condL, 'lagna'));

    const verdictClause = (v, pos, m) => v === 'favourable' ? `favours ${m}`
      : v === 'blocked' ? `is under vedha — ${m} arrives with friction`
      : `tests ${m}; don't force matters there`;
    for (const g of PHALALU_ORDER) {
      const d = detail[g];
      if (d.lagna === null) {
        const m = HOUSE_MEANINGS[d.posR];
        lines.push(d.v === 'favourable' ? `${g} in your ${ordinal(d.posR)} house favours ${m}.`
          : d.v === 'blocked' ? `${g}'s good ${ordinal(d.posR)}-house transit is under vedha by ${d.by} — gains in ${m} may arrive with friction.`
          : `${g} in the ${ordinal(d.posR)} house tests ${m}; avoid forcing matters there.`);
        continue;
      }
      // Both lenses set. If they agree, one clean line. If they
      // differ, two clauses: "X from your rashi … and from your lagna …".
      const mR = HOUSE_MEANINGS[d.posR];
      const mL = HOUSE_MEANINGS[d.posL];
      if (d.v === d.lagna.v && d.posR === d.posL) {
        // Same house, same verdict → one line.
        lines.push(`${g} in your ${ordinal(d.posR)} house ${verdictClause(d.v, d.posR, mR)}.`);
      } else {
        lines.push(`${g}: from your rashi, ${ordinal(d.posR)} house — ${verdictClause(d.v, d.posR, mR)}; from your lagna, ${ordinal(d.posL)} house — ${verdictClause(d.lagna.v, d.posL, mL)}.`);
      }
    }
    lines.push(`${fav} of 9 grahas favour you today${blocked ? `, ${blocked} under vedha` : ''} (from your rashi).`);
    return { quality, lines };
  }

  function shareGocharaOnWhatsApp() {
    if (!GO_DATA) return;
    const view = goCurrentView();
    if (view.jr === null) return;
    const jr = view.jr;
    const jl = (typeof view.jl === 'number') ? view.jl : null;
    const idx = goDateIndex();
    const row = GO_DATA.days[idx], retro = GO_DATA.retro[idx];
    const fmtD = d => d.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
    const ord = n => n + (['st','nd','rd'][n-1] || 'th');
    const ph = buildPhalalu(jr, jl, row, view, idx);
    const lines = [];
    const shown = new Date(GO_DATA.start + 'T00:00:00'); shown.setDate(shown.getDate() + idx);
    lines.push(`📜 *Rasi Phalalu — ${fmtD(shown)}*`);
    lines.push(`${view.label} · ${ph.quality} day`);
    lines.push('');
    ph.lines.forEach(l => lines.push('• ' + l));
    lines.push('');
    lines.push('Check your rashi:');
    lines.push('https://panchangam.astrochaganti.com/?src=share-phalalu#gochara');
    gcEvent('share-phalalu');
    window.open('https://wa.me/?text=' + encodeURIComponent(lines.join('\n')), '_blank');
  }

  // --- Muhurta finder (client-side, from the already-loaded feed) ---

  const MU_GOOD_CHOG = { Amrit: 3, Shubh: 2, Labh: 2, Char: 1 };
  const MU_YOGA_BONUS = { 'Sarvartha Siddhi Yoga': 2, 'Amrita Siddhi Yoga': 2,
                          'Dvipushkara Yoga': 1, 'Tripushkara Yoga': 1 };
  const MU_YOGA_PENALTY = { 'Visha Yoga': -2, 'Dagdha Yoga': -2 };

  // MU_TIER_NAMES, muScoreTier, muRelativeTier — moved to
  // docs/muhurta-scorer.js (loaded via <script> below the existing
  // tarabalam panel). The script tag assigns them to window so
  // existing references in this file keep working unchanged.
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

  function muMin(t, flag) {
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
  // muLagnaAtMin — all moved to docs/muhurta-scorer.js so they can be
  // unit-tested under Node. Loaded via <script src> below; assigned to
  // window so the inline references in this file still resolve.
  // CHANDRA bad = {4, 8, 12} (the complement).

  // Tithi family — mirror telugu_panchangam/personal/tithi_class.py
  const TITHI_NAMES_ORDER = [
    'Pratipat', 'Dwitiya', 'Tritiya', 'Chaturthi', 'Panchami',
    'Shashthi', 'Saptami', 'Ashtami', 'Navami',    'Dashami',
    'Ekadashi', 'Dwadashi','Trayodashi','Chaturdashi','Pournami',
  ];
  const TITHI_ALIASES = { Pratipada: 1, Prathama: 1, Shashti: 6, Amavasya: 15 };
  const TITHI_NUMBER_FAMILY = {
    1:'Nanda',  6:'Nanda',  11:'Nanda',
    2:'Bhadra', 7:'Bhadra', 12:'Bhadra',
    3:'Jaya',   8:'Jaya',   13:'Jaya',
    4:'Rikta',  9:'Rikta',  14:'Rikta',
    5:'Purna', 10:'Purna',  15:'Purna',
  };
  function tithiFamily(name) {
    if (!name) return null;
    const last = name.trim().split(/\s+/).pop();
    if (TITHI_ALIASES[last]) return TITHI_NUMBER_FAMILY[TITHI_ALIASES[last]];
    const idx = TITHI_NAMES_ORDER.indexOf(last);
    return idx >= 0 ? TITHI_NUMBER_FAMILY[idx + 1] : null;
  }

  // Activity rules — mirror telugu_panchangam/personal/muhurta.py
  // ACTIVITY_RULES. Only the fields the JS scorer consumes are duplicated
  // here (label, prefer_tithi_class, prefer_vara). skip_on_yoga and
  // avoid_karana are still enforced by the engine; the JS reads
  // parsed-feed yogas and karanas to mirror behaviour for activities the
  // user picks via the in-page dropdown.
  const MU_ACTIVITY = {
    any:           { label: 'Anything auspicious' },
    travel:        { label: 'Travel / journey', avoid_karana: ['Vishti'],
                     prefer_lagna_class: 'Chara' },
    purchase:      { label: 'Purchase (general)', prefer_choghadiya: ['Labh', 1] },
    ceremony:      { label: 'Ceremony / puja (general)',
                     skip_on_yoga: ['Visha Yoga','Dagdha Yoga'],
                     prefer_vara: ['Somavaram','Guruvaram'] },
    beginning:     { label: 'New beginning (general)',
                     prefer_choghadiya: ['Amrit', 1],
                     prefer_tithi_class: 'Nanda',
                     prefer_vara: ['Budhavaram','Guruvaram'] },
    wedding:       { label: 'Wedding (Vivaha)',
                     skip_on_yoga: ['Visha Yoga','Dagdha Yoga'],
                     prefer_tithi_class: 'Purna',
                     prefer_vara: ['Guruvaram','Somavaram'],
                     prefer_lagna_class: 'Sthira' },
    engagement:    { label: 'Engagement (Nischayam)',
                     skip_on_yoga: ['Visha Yoga','Dagdha Yoga'],
                     prefer_tithi_class: 'Purna',
                     prefer_vara: ['Guruvaram','Somavaram'],
                     prefer_lagna_class: 'Sthira' },
    naming:        { label: 'Naming (Namakaranam)',
                     skip_on_yoga: ['Visha Yoga','Dagdha Yoga'],
                     prefer_choghadiya: ['Shubh', 1],
                     prefer_tithi_class: 'Nanda',
                     prefer_vara: ['Budhavaram','Guruvaram'],
                     prefer_lagna_class: 'Dvisvabhava' },
    annaprasana:   { label: 'Annaprasana (First feeding)',
                     skip_on_yoga: ['Visha Yoga','Dagdha Yoga'],
                     prefer_choghadiya: ['Shubh', 1],
                     prefer_tithi_class: 'Bhadra',
                     prefer_vara: ['Somavaram','Guruvaram'],
                     prefer_lagna_class: 'Dvisvabhava' },
    karnavedha:    { label: 'Karnavedha (Ear-piercing)',
                     skip_on_yoga: ['Visha Yoga','Dagdha Yoga'],
                     prefer_tithi_class: 'Bhadra',
                     prefer_vara: ['Budhavaram','Shukravaram'],
                     prefer_lagna_class: 'Dvisvabhava' },
    mundana:       { label: 'Mundana / Chaula (First head-shave)',
                     skip_on_yoga: ['Visha Yoga','Dagdha Yoga'],
                     prefer_tithi_class: 'Nanda',
                     prefer_vara: ['Budhavaram','Guruvaram'],
                     prefer_lagna_class: 'Dvisvabhava' },
    upanayana:     { label: 'Upanayana (Sacred thread)',
                     skip_on_yoga: ['Visha Yoga','Dagdha Yoga'],
                     prefer_tithi_class: 'Nanda',
                     prefer_vara: ['Budhavaram','Guruvaram'],
                     prefer_lagna_class: 'Dvisvabhava' },
    vidyarambha:   { label: 'Education start (Vidyarambha)',
                     skip_on_yoga: ['Visha Yoga','Dagdha Yoga'],
                     prefer_choghadiya: ['Amrit', 1],
                     prefer_tithi_class: 'Nanda',
                     prefer_vara: ['Budhavaram'],
                     prefer_lagna_class: 'Dvisvabhava' },
    gruhapravesha: { label: 'Gruhapravesha (Home entry)',
                     skip_on_yoga: ['Visha Yoga','Dagdha Yoga'],
                     prefer_tithi_class: 'Bhadra',
                     prefer_vara: ['Guruvaram','Somavaram'],
                     prefer_lagna_class: 'Sthira' },
    vehicle:       { label: 'Vehicle purchase',
                     prefer_choghadiya: ['Labh', 1],
                     prefer_tithi_class: 'Bhadra',
                     prefer_vara: ['Shukravaram'],
                     prefer_lagna_class: 'Sthira' },
    property:      { label: 'Property / Land purchase',
                     prefer_choghadiya: ['Labh', 1],
                     prefer_tithi_class: 'Bhadra',
                     prefer_vara: ['Guruvaram','Shukravaram'],
                     prefer_lagna_class: 'Sthira' },
    gold:          { label: 'Gold / Jewelry purchase',
                     prefer_choghadiya: ['Labh', 1],
                     prefer_tithi_class: 'Bhadra',
                     prefer_vara: ['Shukravaram','Guruvaram'],
                     prefer_lagna_class: 'Sthira' },
    bhumi_puja:    { label: 'Bhumi Puja / Foundation laying',
                     skip_on_yoga: ['Visha Yoga','Dagdha Yoga'],
                     prefer_tithi_class: 'Bhadra',
                     prefer_vara: ['Guruvaram','Somavaram'],
                     prefer_lagna_class: 'Sthira' },
    business:      { label: 'Business launch',
                     prefer_choghadiya: ['Amrit', 1],
                     prefer_tithi_class: 'Nanda',
                     prefer_vara: ['Guruvaram','Budhavaram'],
                     prefer_lagna_class: 'Sthira' },
    job:           { label: 'Job start / Contract signing',
                     prefer_choghadiya: ['Amrit', 1],
                     prefer_tithi_class: 'Nanda',
                     prefer_vara: ['Guruvaram','Budhavaram'],
                     prefer_lagna_class: 'Sthira' },
    yajna:         { label: 'Yajna / Homam',
                     skip_on_yoga: ['Visha Yoga','Dagdha Yoga'],
                     prefer_tithi_class: 'Purna',
                     prefer_vara: ['Guruvaram','Somavaram'],
                     prefer_lagna_class: 'Sthira' },
    pilgrimage:    { label: 'Pilgrimage (Tirtha Yatra)', avoid_karana: ['Vishti'],
                     prefer_lagna_class: 'Chara' },
    court:         { label: 'Court / legal matter',
                     prefer_tithi_class: 'Jaya',
                     prefer_vara: ['Mangalavaram'] },
    surgery:       { label: 'Surgery / medical procedure',
                     avoid_karana: ['Vishti'],
                     prefer_vara: ['Mangalavaram'] },
  };

  // HTML-escape user-typed values (profile names) before they enter the
  // `reasons` strings that renderMuhurta concatenates via innerHTML.
  function htmlEsc(s) {
    return String(s).replace(/[&<>"']/g, c => (
      { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]
    ));
  }

  async function findMuhurta() {
    const box = document.getElementById('mu-result');
    box.innerHTML = '<p class="preview-error">Searching…</p>';
    const activity = document.getElementById('mu-activity').value;
    const from = new Date(document.getElementById('tb-from').value + 'T00:00:00');
    const to = new Date(document.getElementById('tb-to').value + 'T00:00:00');
    const nDays = Math.min(60, Math.max(1, Math.round((to - from) / 86400000) + 1));
    const people = tbProfiles();
    const chandraMode = TB_MODE;  // 'stars' | 'puja_ok' | 'strict' — filters only, never scores
    document.getElementById('mu-context').innerHTML = people.length
      ? `Searching <strong>${document.getElementById('tb-from').value}</strong> to <strong>${document.getElementById('tb-to').value}</strong>, screened by the stars of <strong>${people.map(p => htmlEsc(p.name)).join(', ')}</strong> (set above).`
      : `Searching <strong>${document.getElementById('tb-from').value}</strong> to <strong>${document.getElementById('tb-to').value}</strong> — no people set above, so no star screening.`;
    try {
      const city = document.getElementById('tp-city').value;
      const system = document.getElementById('tp-system').value;
      const events = LAST_EVENTS || await loadFeed(city, system);
      // Lagna data is needed when (a) people are set — for the
      // per-person kendra/trikona/Ashtama check — OR (b) the chosen
      // activity has a preferred lagna class (Sthira/Chara/...).
      // Cached per session, shared with the day-card's lagna ribbon.
      const activityRules = MU_ACTIVITY[activity] || MU_ACTIVITY.any;
      const activityNeedsLagna = !!activityRules.prefer_lagna_class;
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
          droppedDays.push({ date: isoDate, reason: `${kind} — auspicious activities deferred` });
          continue;
        }

        const rules = MU_ACTIVITY[activity] || MU_ACTIVITY.any;
        const skipYogas = new Set(rules.skip_on_yoga || []);
        const preferChog = rules.prefer_choghadiya || null;     // ['Block', bonus]
        const avoidKaranaNames = new Set(rules.avoid_karana || []);
        const preferTithiClass = rules.prefer_tithi_class || null;
        const preferVaras = new Set(rules.prefer_vara || []);
        const preferLagnaClass = rules.prefer_lagna_class || null;
        const activityLabel = rules.label;

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

        for (const c of data.choghadiya) {
          const base = MU_GOOD_CHOG[c.name];
          if (base === undefined) continue;
          for (const [s0, e0] of muSubtract(muMin(c.start), muMin(c.end), bad)) {
            if (e0 - s0 < 24) continue;

            // Compute slot-time facts via Meeus Sun/Moon longitudes.
            // s0 is minutes from local midnight of `d`. Convert to a Date
            // object in the same local timezone, then muFactsAt does the
            // UTC → JD conversion internally.
            const slotStart = new Date(d.getTime() + s0 * 60000);
            const facts = muFactsAt(slotStart, data.vaaram);

            // Build reason groups as we score — slot_quality, day_quality,
            // group_fit, activity_match, notes — mirroring Python's
            // day_slots() reason_groups field.
            let score = base;
            const slotQuality = [`${c.name} choghadiya (+${base})`,
                                  'clear of all inauspicious windows'];
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
            const tFam = tithiFamily(facts.tithi);
            if (tFam === 'Rikta') {
              score -= 2;
              dayQuality.push(`${facts.tithi} (Rikta tithi) (-2)`);
            } else if (tFam && preferTithiClass && tFam === preferTithiClass) {
              score += 1;
              activityMatch.push(`${facts.tithi} (${preferTithiClass}) favoured for ${activityLabel} (+1)`);
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

            // Slot-overlap bonuses → slot_quality
            if (abhijit && s0 < muMin(abhijit.end, abhijit.eflag) && muMin(abhijit.start, abhijit.sflag) < e0) {
              score += 2; slotQuality.push('overlaps Abhijit Muhurta (+2)');
            }
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
            const siddhiYogas = facts.specialYogas.filter(y =>
              y === 'Sarvartha Siddhi Yoga' || y === 'Amrita Siddhi Yoga');
            const hasPushkara = facts.specialYogas.some(y =>
              y === 'Dvipushkara Yoga' || y === 'Tripushkara Yoga');
            if (siddhiYogas.length && taraUnfavNames.length) {
              notes.push(`${siddhiYogas.join(' + ')} traditionally rectifies tara dosha ` +
                         `(Muhurta Chintamani) — ${taraUnfavNames.join(', ')} mitigated.`);
            }
            if (siddhiYogas.length && chandraAvoidNames.length) {
              notes.push(`Chandra dosha is not rectified by Siddhi yogas — ` +
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

            slots.push({ d: new Date(d), s0, e0, score, reasons, reasonGroups, personalDosha, dayDosha });
            slotsPerDay.set(isoDate, (slotsPerDay.get(isoDate) || 0) + 1);
          }
        }
        // Diagnose: if the day produced no slots and it wasn't an eclipse,
        // record the most likely reason (samskara skip, mode filter, etc.).
        if (!slotsPerDay.has(isoDate)) {
          let reason = null;
          // Samskara skip on Visha/Dagdha
          for (const y of data.yogas) {
            if (skipYogas.has(y)) {
              reason = `${y} — ${activityLabel} traditionally avoids this day`;
              break;
            }
          }
          // Samskara skip on Vyatipata/Vaidhriti (Nitya yoga at sunrise)
          if (!reason && skipYogas.size && data.yoga && MU_NITYA_HARD_AVOID.has(data.yoga.name)) {
            reason = `${data.yoga.name} yoga — samskaras traditionally defer`;
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
              reason = 'chandra_mode=strict — Moon at sunrise fails for at least one person';
            } else if (chandraMode === 'puja_ok' && hasAvoid) {
              reason = 'chandra_mode=puja_ok — someone has Moon-avoid (4/8/12)';
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
        || (!!a.personalDosha - !!b.personalDosha) || a.d - b.d || a.s0 - b.s0);
      MU_LAST = { top: slots.slice(0, 10), droppedEclipseDays, droppedModeDays, droppedDays, activity, people, chandraMode };
      renderMuhurta();
    } catch (e) {
      box.innerHTML = '<p class="preview-error">Could not load the feed — try again.</p>';
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
    gruhapravesha: 'gruhapravesha (home entry)',
    vehicle: 'a vehicle purchase', property: 'a property purchase',
    gold: 'a gold / jewelry purchase',
    bhumi_puja: 'bhumi puja (foundation laying)',
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
      ? `<details class="mu-dropped"><summary>${droppedDays.length} day${droppedDays.length>1?'s':''} filtered — see why</summary>
           <ul>${droppedDays.map(dd => `<li><span class="dd-date">${fmtIso(dd.date)}</span> — ${htmlEsc(dd.reason)}</li>`).join('')}</ul>
         </details>`
      : '';
    if (!top.length) {
      const notes = [];
      if (droppedEclipseDays) notes.push(`${droppedEclipseDays} eclipse day(s) deferred`);
      if (droppedModeDays) notes.push(`${droppedModeDays} slot(s) filtered by chandra mode`);
      const suffix = notes.length ? ` — ${notes.join(', ')}` : '';
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
      return `<div class="mu-slot">
                <span class="mu-when">${fmtD(s.d)} · ${muToT(s.s0)} – ${muToT(s.e0)}</span>
                <span class="mu-tier ${tierClass}">${tier}</span>
                <span class="mu-score">score ${s.score}</span>
                ${groupsHtml}
              </div>`;
    };
    box.innerHTML =
      `<div class="tb-summary">⏱ <span class="count">${top.length}</span>&nbsp;slot${top.length > 1 ? 's' : ''} found — best first${share}</div>`
      + top.map(renderSlot).join('')
      + droppedHtml
      + `<p class="preview-note" style="margin-top:0.5rem;">Each slot's score is the sum of the (+n)/(-n) bonuses across
         Slot quality (choghadiya, Abhijit/Amrita overlap), Day quality (Siddhi yogas, Nitya yoga, Rikta tithi),
         Group fit (per-person tarabalam and chandrabalam), and Activity match (preferred tithi class / vara).
         Being clear of every inauspicious window is a requirement, not a bonus. The tier reflects this score's
         rank within this search, capped below Excellent whenever a named dosha is present — check that slot's
         notes either way, since a capped "Good" can carry a caution worth knowing about even if it's otherwise
         a workable time. Notes carry classical-doctrine context (e.g. Sarvartha Siddhi traditionally rectifies
         tara dosha) without changing the score.</p>`;
  }

  function shareMuhurtaOnWhatsApp() {
    if (!MU_LAST || !MU_LAST.top.length) return;
    const { top, activity, people } = MU_LAST;
    const citySel = document.getElementById('tp-city');
    const cityLabel = citySel.options[citySel.selectedIndex].textContent;
    const fmtD = d => d.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
    const lines = [];
    lines.push(`⏱ *Good time slots — ${MU_ACT_LABEL[activity]}*`);
    lines.push(`📍 ${cityLabel} · ${document.getElementById('tb-from').value} to ${document.getElementById('tb-to').value}`);
    if (people.length) lines.push(`Screened for: ${people.map(p => `${p.name} (${p.nak})`).join(' · ')}`);
    lines.push('');
    top.slice(0, 5).forEach(s => {
      lines.push(`✅ ${fmtD(s.d)} · ${muToT(s.s0)} – ${muToT(s.e0)}`);
      lines.push(`   ${s.reasons.filter(r => r !== 'clear of all inauspicious windows').slice(0, 3).join(' · ')}`);
    });
    lines.push('');
    lines.push('Every slot is clear of Rahu Kalam, Varjyam and all inauspicious windows.');
    lines.push('Find your own: https://panchangam.astrochaganti.com/?src=share-slots#tarabalam');
    gcEvent('share-slots');
    window.open('https://wa.me/?text=' + encodeURIComponent(lines.join('\n')), '_blank');
  }

  // --- Init ---

  populateCitySelect(document.getElementById('tp-city'));
  populateSystemSelect(document.getElementById('tp-system'));
  populateCitySelect(document.getElementById('sub-city'));
  populateSystemSelect(document.getElementById('sub-system'));

  document.getElementById('tp-city').addEventListener('change', loadPreview);
  document.getElementById('tp-system').addEventListener('change', loadPreview);
  const _d = new Date();
  const todayISO = `${_d.getFullYear()}-${String(_d.getMonth()+1).padStart(2,'0')}-${String(_d.getDate()).padStart(2,'0')}`;
  _tpDateVal = todayISO;
  document.getElementById('tp-result').addEventListener('change', function(e) {
    if (e.target.matches('input.tp-date-input')) { _tpDateVal = e.target.value; loadPreview(); }
  });
  document.getElementById('sub-city').addEventListener('change', updateSubscribeUrl);
  document.getElementById('sub-system').addEventListener('change', updateSubscribeUrl);

  setTimeFmt(TIME_FMT);

  tbRenderProfileInputs();
  document.getElementById('tb-from').value = todayISO;
  const _t2 = new Date(); _t2.setDate(_t2.getDate() + 13);
  document.getElementById('tb-to').value = `${_t2.getFullYear()}-${String(_t2.getMonth()+1).padStart(2,'0')}-${String(_t2.getDate()).padStart(2,'0')}`;
  document.body.dataset.tool = 'today';
  if (location.hash === '#tarabalam') switchTool('tarabalam');
  if (location.hash === '#gochara') switchTool('gochara');
  if (location.hash === '#muhurta') switchTool('tarabalam');  // muhurtam lives there now
  if (location.hash === '#festivals') switchTool('festivals');
  if (location.hash === '#subscribe') switchTool('subscribe');
  if (location.hash === '#useinai') switchTool('useinai');
  if (location.hash === '#about') switchTool('about');
  updateSubscribeUrl();
  loadPreview();

  // ---------- Mobile shell — matchMedia, two drawers, swipe, card relocation ----------
  (function mobileShell() {
    const mq = window.matchMedia('(max-width: 620px)');

    // Each drawer has its own body and its own list of elements to host.
    // On mobile, those elements move into the drawer body in array order.
    // On resize back to desktop, they return to their original DOM position.
    const MORE = {
      bodyEl: document.getElementById('m-more-body'),
      drawerEl: document.getElementById('m-more-drawer'),
      btnEl: document.getElementById('m-more-btn'),
      anchorBefore: document.getElementById('m-about'),  // insert before the about blurb
      moveIds: ['sel-tp-city', 'sel-tp-system', 'sel-fmt-toggle', 'card-system', 'subscribe', 'card-mcp'],
      openClass: 'm-more-open',
      openEvt: 'more-open', closeEvt: 'more-close',
    };
    const DRAWERS = [MORE];
    const placeholders = {};

    function moveAllToDrawers() {
      for (const d of DRAWERS) {
        for (const id of d.moveIds) {
          const el = document.getElementById(id);
          if (!el || el.parentNode === d.bodyEl) continue;
          const ph = document.createComment('m-drawer-slot-' + id);
          placeholders[id] = ph;
          el.parentNode.insertBefore(ph, el);
          if (d.anchorBefore) d.bodyEl.insertBefore(el, d.anchorBefore);
          else d.bodyEl.appendChild(el);
        }
      }
    }
    function restoreAll() {
      for (const d of DRAWERS) {
        for (const id of d.moveIds) {
          const el = document.getElementById(id);
          const ph = placeholders[id];
          if (el && ph && ph.parentNode) {
            ph.parentNode.insertBefore(el, ph);
            ph.parentNode.removeChild(ph);
            delete placeholders[id];
          }
        }
      }
    }

    function openDrawer(d) {
      // exclusive: tapping one closes the other
      DRAWERS.filter(x => x !== d).forEach(closeDrawer);
      document.body.classList.add(d.openClass);
      d.drawerEl.setAttribute('aria-hidden', 'false');
      d.btnEl.setAttribute('aria-expanded', 'true');
      if (typeof gcEvent === 'function') gcEvent(d.openEvt);
    }
    function closeDrawer(d) {
      if (!document.body.classList.contains(d.openClass)) return;
      document.body.classList.remove(d.openClass);
      d.drawerEl.setAttribute('aria-hidden', 'true');
      d.btnEl.setAttribute('aria-expanded', 'false');
      if (typeof gcEvent === 'function') gcEvent(d.closeEvt);
    }
    function closeAllDrawers() { DRAWERS.forEach(closeDrawer); }

    function applyMode() {
      const mobile = mq.matches;
      document.body.dataset.mode = mobile ? 'mobile' : 'desktop';
      if (mobile) moveAllToDrawers();
      else { restoreAll(); closeAllDrawers(); }
    }

    MORE.btnEl.addEventListener('click', () => { closeHelpSheet(); openDrawer(MORE); });
    document.querySelectorAll('.m-drawer-close').forEach(btn => {
      btn.addEventListener('click', () => closeDrawer(MORE));
    });
    document.querySelectorAll('.m-page-help-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        closeAllDrawers();
        // toggle: tapping again closes the sheet
        if (document.body.classList.contains('m-help-open')) closeHelpSheet();
        else openHelpSheet();
      });
    });
    document.getElementById('m-help-close').addEventListener('click', closeHelpSheet);
    document.getElementById('m-help-cta').addEventListener('click', closeHelpSheet);
    document.getElementById('m-drawer-scrim').addEventListener('click', () => {
      closeAllDrawers(); closeHelpSheet();
    });
    document.addEventListener('keydown', e => {
      if (e.key === 'Escape') { closeAllDrawers(); closeHelpSheet(); }
    });

    // --- bottom-nav tap ---
    document.querySelectorAll('#m-bottomnav .m-tab[data-tab]').forEach(b => {
      b.addEventListener('click', () => switchTool(b.dataset.tab));
    });

    // --- swipe between tabs ---
    const ORDER = ['today', 'gochara', 'tarabalam'];
    function currentTab() {
      const active = document.querySelector('#m-bottomnav .m-tab.active');
      return active ? active.dataset.tab : 'today';
    }
    let touchX = null, touchY = null, touchT = 0;
    document.addEventListener('touchstart', e => {
      if (!mq.matches) return;
      // suppress while a drawer or help sheet is open
      if (document.body.classList.contains('m-more-open') ||
          document.body.classList.contains('m-help-open')) return;
      const t = e.touches[0]; touchX = t.clientX; touchY = t.clientY; touchT = Date.now();
    }, { passive: true });
    document.addEventListener('touchend', e => {
      if (!mq.matches || touchX === null) return;
      const t = e.changedTouches[0];
      const dx = t.clientX - touchX, dy = t.clientY - touchY;
      const ax = Math.abs(dx), ay = Math.abs(dy);
      touchX = null; touchY = null;
      if (Date.now() - touchT > 600) return;
      if (ax < 60 || ax < ay * 1.5) return;
      const startTarget = e.target.closest && e.target.closest('input, select, textarea, .tb-table-wrap, .url-box');
      if (startTarget) return;
      const i = ORDER.indexOf(currentTab());
      const next = dx < 0 ? Math.min(ORDER.length - 1, i + 1) : Math.max(0, i - 1);
      if (next !== i) switchTool(ORDER[next]);
    }, { passive: true });

    // --- resize: debounced re-apply, don't thrash on edge widths ---
    let rt;
    (mq.addEventListener ? mq.addEventListener('change', schedule) : mq.addListener(schedule));
    function schedule() { clearTimeout(rt); rt = setTimeout(applyMode, 120); }
    window.addEventListener('resize', schedule);

    applyMode();

    // Expose functions referenced by inline HTML onclick/onchange handlers.
    // Modules are scoped; inline event attributes look up names on window.
    Object.assign(window, {
      switchTool, showAppTab, setTimeFmt, toggleReadMore,
      calcTarabalam, tbAddRow, tbRemoveRow, tbResetProfiles,
      tbSaveProfiles, tbSetMode, tbToggleShowAll, tbExtendTo,
      findMuhurta, muToggleMobile,
      renderGochara, copyUrl,
      shareTodayOnWhatsApp, shareGocharaOnWhatsApp,
      shareTarabalamOnWhatsApp, shareMuhurtaOnWhatsApp,
    });
  })();
  // lightweight event tracking; no-ops if the counter is blocked or offline
  function gcEvent(name) {
    if (window.goatcounter && window.goatcounter.count) {
      window.goatcounter.count({ path: name, title: name, event: true });
    }
  }
  document.addEventListener('click', function (e) {
    const a = e.target.closest && e.target.closest('a');
    if (!a) return;
    if (a.href.includes('astrochaganti.com') && !a.href.includes('panchangam.')) gcEvent('consult-click');
    if (a.href.includes('pypi.org')) gcEvent('pypi-click');
  });
