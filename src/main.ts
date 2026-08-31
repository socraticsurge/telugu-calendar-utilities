import { getSelection, setSelection, initSelection, subscribeSelection } from './selection-store';
import { selEl } from './lib/dom';
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
import { createGuestProfileStore } from './lib/guest-profile-store';
import { initProfilesPanel } from './panels/profiles';

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
    const city = selEl('sub-city').value;
    const system = selEl('sub-system').value;
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
    document.querySelectorAll<HTMLElement>('.app-tab').forEach(t => t.classList.toggle('active', t.dataset.app === name));
    document.querySelectorAll<HTMLElement>('.app-panel').forEach(p => p.classList.toggle('active', p.dataset.app === name));
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

  // --- Shell: section switching + accessible navigation drawer ---
  const PAGE_TITLES = {
    today:     ["Today's Panchangam", 'What is the day?'],
    gochara:   ['Gochara · Rasi Phalalu', 'What does it mean for me?'],
    tarabalam: ['Tarabalam · Muhurtam', 'When should we act?'],
    profiles:  ['Profiles', 'Saved only in this browser'],
    festivals: ['Festivals', 'Special days — next 30 days'],
    subscribe: ['Subscribe', 'Get panchangam in your calendar'],
    useinai:   ['Use in AI', 'MCP server for AI assistants'],
    about:     ['About', 'What this is and how it works'],
  };
  // --- Modal a11y: dialog semantics + focus containment (Phase 4) ---
  // Applied to the navigation drawer:
  // role="dialog"/aria-modal while open, focus moved in on open and
  // restored on close, Tab cycling contained within the surface.
  let _modalRestoreFocus = null;
  function _focusables(container) {
    return [...container.querySelectorAll(
      'button, [href], select, input, textarea, [tabindex]:not([tabindex="-1"])'
    )].filter(el => el.offsetParent !== null);
  }
  function modalOpen(container, focusTarget) {
    _modalRestoreFocus = document.activeElement;
    container.setAttribute('role', 'dialog');
    container.setAttribute('aria-modal', 'true');
    (focusTarget || _focusables(container)[0])?.focus();
    container.addEventListener('keydown', _modalTrapTab);
  }
  function modalClose(container) {
    container.removeAttribute('role');
    container.removeAttribute('aria-modal');
    container.removeEventListener('keydown', _modalTrapTab);
    if (_modalRestoreFocus && _modalRestoreFocus.focus) _modalRestoreFocus.focus();
    _modalRestoreFocus = null;
  }
  function _modalTrapTab(e) {
    if (e.key !== 'Tab') return;
    const f = _focusables(e.currentTarget);
    if (!f.length) return;
    const first = f[0], last = f[f.length - 1];
    if (e.shiftKey && document.activeElement === first) { last.focus(); e.preventDefault(); }
    else if (!e.shiftKey && document.activeElement === last) { first.focus(); e.preventDefault(); }
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

  const profileStore = createGuestProfileStore(localStorage);
  const profilesPanel = initProfilesPanel(profileStore, { navigate: switchTool });


  // Quiet settings summary — the controls live behind it. The city
  // callout doubles as the timezone affordance that saves a diaspora
  // user from reading Rahu Kalam in the wrong timezone.
  function updateSettingsSummary() {
    const el = document.getElementById('settings-summary');
    if (!el) return;
    const sel = getSelection();
    const sysLabel = (SYSTEMS.find(([v]) => v === sel.system) || [])[1] || sel.system;
    el.textContent = `${sel.city} · ${sysLabel} · ${sel.timeFmt}h · Local time`;
  }
  function toggleSettings(open?) {
    const bar = document.getElementById('global-controls-bar');
    const btn = document.getElementById('settings-toggle');
    const show = open !== undefined ? open : bar.hidden;
    bar.hidden = !show;
    btn.setAttribute('aria-expanded', show ? 'true' : 'false');
  }

  // --- Init ---

  populateCitySelect(selEl('tp-city'));
  populateSystemSelect(selEl('tp-system'));
  populateCitySelect(selEl('sub-city'));
  populateSystemSelect(selEl('sub-system'));

  // SelectionStore wiring: user input flows select → store; everything
  // downstream (renders, share text, muhurta search) reads the store.
  // Programmatic changes (e.g. future deep-links) flow store → select
  // through the subscription below.
  // Restore the remembered selection (set once, forget) — the reason
  // the settings can recede behind the summary line at all.
  {
    const citySel = selEl('tp-city') as HTMLSelectElement;
    const sysSel = selEl('tp-system') as HTMLSelectElement;
    const savedCity = localStorage.getItem('tc-city');
    const savedSystem = localStorage.getItem('tc-system');
    if (savedCity && [...citySel.options].some(o => o.value === savedCity)) citySel.value = savedCity;
    if (savedSystem && [...sysSel.options].some(o => o.value === savedSystem)) sysSel.value = savedSystem;
  }
  initSelection({
    city: (selEl('tp-city') as HTMLSelectElement).value,
    system: (selEl('tp-system') as HTMLSelectElement).value,
  });
  selEl('tp-city').addEventListener('change', e =>
    setSelection({ city: (e.target as HTMLSelectElement).value }));
  selEl('tp-system').addEventListener('change', e =>
    setSelection({ system: (e.target as HTMLSelectElement).value }));
  subscribeSelection((sel, changed) => {
    if (changed.includes('timeFmt')) {
      localStorage.setItem('tc-time-fmt', sel.timeFmt);
      applyTimeFmtUI();
      updateSettingsSummary();
      renderAll();
      if (tbHasDays()) renderTarabalam();
      if (goHasData()) renderGochara();
      if (muHasLast()) renderMuhurta();
    }
    if (changed.includes('city') || changed.includes('system')) {
      localStorage.setItem('tc-city', sel.city);
      localStorage.setItem('tc-system', sel.system);
      updateSettingsSummary();
      const citySel = selEl('tp-city') as HTMLSelectElement;
      const sysSel = selEl('tp-system') as HTMLSelectElement;
      if (citySel.value !== sel.city) citySel.value = sel.city;
      if (sysSel.value !== sel.system) sysSel.value = sel.system;
      loadPreview();
    }
  });
  const _d = new Date();
  const todayISO = `${_d.getFullYear()}-${String(_d.getMonth()+1).padStart(2,'0')}-${String(_d.getDate()).padStart(2,'0')}`;
  initTodayPanel(todayISO);
  document.getElementById('settings-toggle').addEventListener('click', () => toggleSettings());
  selEl('sub-city').addEventListener('change', updateSubscribeUrl);
  selEl('sub-system').addEventListener('change', updateSubscribeUrl);

  applyTimeFmtUI();
  updateSettingsSummary();

  initTarabalamPanel(todayISO);
  document.body.dataset.tool = 'today';
  if (location.hash === '#tarabalam') switchTool('tarabalam');
  if (location.hash === '#gochara') switchTool('gochara');
  if (location.hash === '#muhurta') switchTool('tarabalam');  // muhurtam lives there now
  if (location.hash === '#profiles') switchTool('profiles');
  if (location.hash === '#festivals') switchTool('festivals');
  if (location.hash === '#subscribe') switchTool('subscribe');
  if (location.hash === '#useinai') switchTool('useinai');
  if (location.hash === '#about') switchTool('about');
  updateSubscribeUrl();
  loadPreview();

  // ---------- Mobile shell — one nav: width flag + sidebar drawer ----------
  (function mobileShell() {
    // Keep the compact one-shell drawer through tablet widths. The earlier
    // 620px split left too little room for the data canvas beside the sidebar.
    const mq = window.matchMedia('(max-width: 839px)');

    function applyMode() {
      const mobile = mq.matches;
      document.body.dataset.mode = mobile ? 'mobile' : 'desktop';
      if (!mobile) closeNav();
    }

    // --- sidebar drawer: the SAME #sidebar element as desktop, slid in ---
    const navBtn = document.getElementById('m-nav-btn');
    function openNav() {
      document.body.classList.add('m-nav-open');
      navBtn.setAttribute('aria-expanded', 'true');
      modalOpen(document.getElementById('sidebar'),
                document.querySelector('#sidebar .sidebar-item.active') || undefined);
      if (typeof gcEvent === 'function') gcEvent('nav-open');
    }
    function closeNav() {
      if (!document.body.classList.contains('m-nav-open')) return;
      document.body.classList.remove('m-nav-open');
      navBtn.setAttribute('aria-expanded', 'false');
      modalClose(document.getElementById('sidebar'));
    }
    navBtn.addEventListener('click', () => {
      if (document.body.classList.contains('m-nav-open')) closeNav(); else openNav();
    });
    // choosing a section closes the drawer
    document.querySelectorAll('#sidebar .sidebar-item').forEach(b => {
      b.addEventListener('click', closeNav);
    });

    document.getElementById('m-drawer-scrim').addEventListener('click', () => {
      closeNav();
    });
    document.addEventListener('keydown', e => {
      if (e.key === 'Escape') closeNav();
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
    const t = e.target as Element;
    const a = t.closest && t.closest('a');
    if (!a) return;
    if (a.href.includes('astrochaganti.com') && !a.href.includes('panchangam.')) gcEvent('consult-click');
    if (a.href.includes('pypi.org')) gcEvent('pypi-click');
  });
