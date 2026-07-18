// @ts-nocheck
import { getSelection, setSelection, initSelection, subscribeSelection } from './selection-store';
import { parseDescription, TIME_PART } from './lib/parse-description';
import { FEED_BASE_URL, feedFilename, loadFeed, slug } from './lib/feed-loader';
import { CITY_GROUPS } from './data/cities';
import { SYSTEMS } from './data/systems';
import { fmtT, dayMark, fmtRange, fmtPlain } from './lib/format';
import { htmlEsc } from './lib/html';
import { gcEvent } from './lib/analytics';
import { RASI_NAMES } from './data/rasis';
import { loadGochara, renderGochara, goBuildViewSelect, shareGocharaOnWhatsApp, goHasData } from './panels/gochara';
import { loadPreview, renderAll, toggleFestivalMonth, shareTodayOnWhatsApp, initTodayPanel } from './panels/today';
import {
  calcTarabalam, renderTarabalam, tbAddRow, tbRemoveRow, tbResetProfiles,
  tbSaveProfiles, tbSetMode, tbToggleShowAll, tbExtendTo,
  findMuhurta, renderMuhurta, shareTarabalamOnWhatsApp, shareMuhurtaOnWhatsApp,
  tbHasDays, muHasLast, initTarabalamPanel,
} from './panels/tarabalam';
import { loadLagna, lagnaDayFor } from './lib/lagna-loader';
import { stampOf } from './lib/format';

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
    const variant = (document.querySelector('input[name="sub-variant"]:checked') as HTMLInputElement)?.value ?? '';
    const url = `webcal://${FEED_BASE_URL.replace('https://', '')}${feedFilename(city, system, variant)}`;
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


  // --- Time formatting (12h/24h toggle) ---

  // Seed the store from persistence; fmtT (src/lib/format.ts) reads the
  // store on every call.
  initSelection({ timeFmt: localStorage.getItem('tc-time-fmt') === '24' ? '24' : '12' });

  function setTimeFmt(f) {
    setSelection({ timeFmt: f });
    applyTimeFmtUI();  // no-op patches don't notify; keep buttons right at boot
  }
  function applyTimeFmtUI() {
    const f = getSelection().timeFmt;
    document.getElementById('fmt-12').classList.toggle('active', f === '12');
    document.getElementById('fmt-24').classList.toggle('active', f === '24');
  }

  // --- Shell: section switching + contextual help sheet ---
  // (mobile help bottom-sheet pulls in the guide for the active tab —
  // Today has its own hidden source; Gochara and Tarabalam reuse the
  // existing #go-help and #tb-help guides verbatim.)

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
    // Help content exists for the three tool panels; other sections get Today's.
    const cur = document.body.dataset.tool;
    const tab = (cur === 'gochara' || cur === 'tarabalam') ? cur : 'today';
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
    const titles = PAGE_TITLES[which];
    document.getElementById('m-page-title-main').textContent = titles ? titles[0] : '';
    document.getElementById('m-page-title-sub').textContent = titles ? titles[1] : '';
    if (history.replaceState) history.replaceState(null, '', which === 'today' ? '#' : '#' + which);
    if (typeof gcEvent === 'function') gcEvent('tab-' + which);
    if (which === 'gochara') loadGochara();
  }


  // --- Init ---

  populateCitySelect(document.getElementById('tp-city'));
  populateSystemSelect(document.getElementById('tp-system'));
  populateCitySelect(document.getElementById('sub-city'));
  populateSystemSelect(document.getElementById('sub-system'));

  // SelectionStore wiring: user input flows select → store; everything
  // downstream (renders, share text, muhurta search) reads the store.
  // Programmatic changes (e.g. future deep-links) flow store → select
  // through the subscription below.
  initSelection({
    city: (document.getElementById('tp-city') as HTMLSelectElement).value,
    system: (document.getElementById('tp-system') as HTMLSelectElement).value,
  });
  document.getElementById('tp-city').addEventListener('change', e =>
    setSelection({ city: (e.target as HTMLSelectElement).value }));
  document.getElementById('tp-system').addEventListener('change', e =>
    setSelection({ system: (e.target as HTMLSelectElement).value }));
  subscribeSelection((sel, changed) => {
    if (changed.includes('timeFmt')) {
      localStorage.setItem('tc-time-fmt', sel.timeFmt);
      applyTimeFmtUI();
      renderAll();
      if (tbHasDays()) renderTarabalam();
      if (goHasData()) renderGochara();
      if (muHasLast()) renderMuhurta();
    }
    if (changed.includes('city') || changed.includes('system')) {
      const citySel = document.getElementById('tp-city') as HTMLSelectElement;
      const sysSel = document.getElementById('tp-system') as HTMLSelectElement;
      if (citySel.value !== sel.city) citySel.value = sel.city;
      if (sysSel.value !== sel.system) sysSel.value = sel.system;
      loadPreview();
    }
  });
  const _d = new Date();
  const todayISO = `${_d.getFullYear()}-${String(_d.getMonth()+1).padStart(2,'0')}-${String(_d.getDate()).padStart(2,'0')}`;
  initTodayPanel(todayISO);
  document.getElementById('sub-city').addEventListener('change', updateSubscribeUrl);
  document.getElementById('sub-system').addEventListener('change', updateSubscribeUrl);

  applyTimeFmtUI();

  initTarabalamPanel(todayISO);
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

  // ---------- Mobile shell — one nav: width flag + sidebar drawer + help sheet ----------
  (function mobileShell() {
    const mq = window.matchMedia('(max-width: 620px)');

    function applyMode() {
      const mobile = mq.matches;
      document.body.dataset.mode = mobile ? 'mobile' : 'desktop';
      if (!mobile) closeNav();
    }

    // --- sidebar drawer: the SAME #sidebar element as desktop, slid in ---
    const navBtn = document.getElementById('m-nav-btn');
    function openNav() {
      closeHelpSheet();
      document.body.classList.add('m-nav-open');
      navBtn.setAttribute('aria-expanded', 'true');
      if (typeof gcEvent === 'function') gcEvent('nav-open');
    }
    function closeNav() {
      if (!document.body.classList.contains('m-nav-open')) return;
      document.body.classList.remove('m-nav-open');
      navBtn.setAttribute('aria-expanded', 'false');
    }
    navBtn.addEventListener('click', () => {
      if (document.body.classList.contains('m-nav-open')) closeNav(); else openNav();
    });
    // choosing a section closes the drawer
    document.querySelectorAll('#sidebar .sidebar-item').forEach(b => {
      b.addEventListener('click', closeNav);
    });

    document.querySelectorAll('.m-page-help-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        closeNav();
        // toggle: tapping again closes the sheet
        if (document.body.classList.contains('m-help-open')) closeHelpSheet();
        else openHelpSheet();
      });
    });
    document.getElementById('m-help-close').addEventListener('click', closeHelpSheet);
    document.getElementById('m-help-cta').addEventListener('click', closeHelpSheet);
    document.getElementById('m-drawer-scrim').addEventListener('click', () => {
      closeNav(); closeHelpSheet();
    });
    document.addEventListener('keydown', e => {
      if (e.key === 'Escape') { closeNav(); closeHelpSheet(); }
    });

    // --- resize: debounced re-apply, don't thrash on edge widths ---
    let rt;
    (mq.addEventListener ? mq.addEventListener('change', schedule) : mq.addListener(schedule));
    function schedule() { clearTimeout(rt); rt = setTimeout(applyMode, 120); }
    window.addEventListener('resize', schedule);

    applyMode();

    // Expose functions referenced by inline HTML onclick/onchange handlers.
    // Modules are scoped; inline event attributes look up names on window.
    Object.assign(window, {
      switchTool, showAppTab, setTimeFmt, toggleReadMore, toggleFestivalMonth,
      calcTarabalam, tbAddRow, tbRemoveRow, tbResetProfiles,
      tbSaveProfiles, tbSetMode, tbToggleShowAll, tbExtendTo,
      findMuhurta,
      renderGochara, copyUrl, updateSubscribeUrl,
      shareTodayOnWhatsApp, shareGocharaOnWhatsApp,
      shareTarabalamOnWhatsApp, shareMuhurtaOnWhatsApp,
    });
  })();
  document.addEventListener('click', function (e) {
    const a = e.target.closest && e.target.closest('a');
    if (!a) return;
    if (a.href.includes('astrochaganti.com') && !a.href.includes('panchangam.')) gcEvent('consult-click');
    if (a.href.includes('pypi.org')) gcEvent('pypi-click');
  });
