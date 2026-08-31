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
import {
  initGocharaProfiles,
  loadGochara,
  renderGochara,
  goBuildViewSelect,
  shareGocharaOnWhatsApp,
  goHasData,
} from './panels/gochara';
import {
  loadPreview, renderAll, toggleFestivalMonth, openFestivalDate,
  shareTodayOnWhatsApp, initTodayPanel,
} from './panels/today';
import {
  calcTarabalam, renderTarabalam, tbAddRow, tbRemoveRow, tbResetProfiles,
  tbSaveProfiles, tbSetMode, tbToggleShowAll, tbExtendTo,
  findMuhurta, renderMuhurta, shareTarabalamOnWhatsApp, shareMuhurtaOnWhatsApp,
  tbHasDays, muHasLast, initTarabalamPanel, initTarabalamProfiles,
} from './panels/tarabalam';
import { loadLagna, lagnaDayFor } from './lib/lagna-loader';
import { stampOf } from './lib/format';
import {
  browserProfileStorage,
  createGuestProfileStore,
} from './lib/guest-profile-store';
import {
  initProfilesPanel,
  listenForGuestProfileStorageChanges,
} from './panels/profiles';

  // Access to the localStorage property itself can throw on restricted origins.
  // The lazy ProfileStorage adapter lets profile state degrade to memory, while
  // these preference helpers keep the rest of the shell bootable.
  const browserStorage = browserProfileStorage();
  function readBrowserPreference(key) {
    try { return browserStorage.getItem(key); } catch { return null; }
  }
  function writeBrowserPreference(key, value) {
    try { browserStorage.setItem(key, value); } catch { /* session only */ }
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
    const city = selEl('sub-city').value;
    const system = selEl('sub-system').value;
    const variant = (document.querySelector('input[name="sub-variant"]:checked') as HTMLInputElement)?.value ?? '';
    const url = `webcal://${FEED_BASE_URL.replace('https://', '')}${feedFilename(city, system, variant)}`;
    document.getElementById('sub-url').textContent = url;
  }

  function copyUrl() {
    if (typeof gcEvent === 'function') gcEvent('subscribe-copy');
    const url = document.getElementById('sub-url').textContent;
    const el = document.getElementById('copy-confirm');
    const write = navigator.clipboard?.writeText
      ? navigator.clipboard.writeText(url)
      : Promise.reject(new Error('Clipboard unavailable'));
    write.then(() => {
      el.textContent = 'Copied!';
      el.dataset.state = 'success';
      el.style.display = 'inline';
      setTimeout(() => { el.style.display = 'none'; el.textContent = ''; }, 2000);
    }).catch(() => {
      el.textContent = 'Could not copy. Select the URL and copy it manually.';
      el.dataset.state = 'error';
      el.style.display = 'inline';
    });
  }

  function showAppTab(name) {
    document.querySelectorAll<HTMLElement>('.app-tab').forEach(t => {
      const active = t.dataset.app === name;
      t.classList.toggle('active', active);
      t.setAttribute('aria-selected', active ? 'true' : 'false');
      t.setAttribute('tabindex', active ? '0' : '-1');
    });
    document.querySelectorAll<HTMLElement>('.app-panel').forEach(p => {
      const active = p.dataset.app === name;
      p.classList.toggle('active', active);
      p.hidden = !active;
    });
  }

  // --- Choosing a system card ---

  function toggleReadMore(id, btn) {
    const el = document.getElementById(id);
    const open = el.classList.toggle('open');
    el.hidden = !open;
    btn.setAttribute('aria-expanded', open ? 'true' : 'false');
    btn.textContent = open ? btn.dataset.less : btn.dataset.more;
  }

  // --- Today's Panchangam preview ---


  // --- Time formatting (12h/24h toggle) ---

  // Seed the store from persistence; fmtT (src/lib/format.ts) reads the
  // store on every call.
  initSelection({ timeFmt: readBrowserPreference('tc-time-fmt') === '24' ? '24' : '12' });

  function setTimeFmt(f) {
    setSelection({ timeFmt: f });
    applyTimeFmtUI();  // no-op patches don't notify; keep buttons right at boot
  }
  function applyTimeFmtUI() {
    const f = getSelection().timeFmt;
    const fmt12 = document.getElementById('fmt-12');
    const fmt24 = document.getElementById('fmt-24');
    fmt12.classList.toggle('active', f === '12');
    fmt24.classList.toggle('active', f === '24');
    fmt12.setAttribute('aria-pressed', f === '12' ? 'true' : 'false');
    fmt24.setAttribute('aria-pressed', f === '24' ? 'true' : 'false');
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
    const activeTrigger = document.activeElement;
    const focusHeading = activeTrigger instanceof Element
      && activeTrigger.matches('#sidebar .sidebar-item, .tool-tab');
    // Tool panels: show/hide the three original panels
    for (const t of TOOL_PANELS) {
      const active = t === which;
      const panel = document.getElementById('panel-' + t);
      const tab = document.getElementById('tab-' + t);
      panel.style.display = active ? '' : 'none';
      panel.setAttribute('aria-hidden', active ? 'false' : 'true');
      tab.classList.toggle('active', active);
      tab.setAttribute('aria-selected', active ? 'true' : 'false');
      tab.setAttribute('tabindex', active ? '0' : '-1');
    }
    document.body.dataset.tool = which;
    // sidebar stays in sync on desktop
    document.querySelectorAll('#sidebar .sidebar-item[id]').forEach(b => {
      const active = b.id === 'sidebar-' + which;
      b.classList.toggle('active', active);
      if (active) b.setAttribute('aria-current', 'page');
      else b.removeAttribute('aria-current');
    });
    const titles = PAGE_TITLES[which];
    document.getElementById('m-page-title-main').textContent = titles ? titles[0] : '';
    document.getElementById('m-page-title-sub').textContent = titles ? titles[1] : '';
    if (focusHeading && TOOL_PANELS.includes(which)) {
      queueMicrotask(() => document.getElementById('m-page-title')?.focus());
    }
    if (history.replaceState) history.replaceState(null, '', which === 'today' ? '#' : '#' + which);
    if (typeof gcEvent === 'function') gcEvent('tab-' + which);
    if (which === 'gochara') loadGochara();
  }

  const profileStore = createGuestProfileStore(browserStorage);
  let gocharaProfiles: ReturnType<typeof initGocharaProfiles> | null = null;
  let tarabalamProfiles: ReturnType<typeof initTarabalamProfiles> | null = null;
  const profilesPanel = initProfilesPanel(profileStore, {
    navigate: switchTool,
    onViewDailyHoroscope(profileId) {
      switchTool('gochara');
      queueMicrotask(() => gocharaProfiles?.selectProfile(profileId));
    },
    onFindMuhurtam(profileId) {
      switchTool('tarabalam');
      queueMicrotask(() => tarabalamProfiles?.selectProfile(profileId));
    },
  });
  listenForGuestProfileStorageChanges(profileStore);
  gocharaProfiles = initGocharaProfiles(profileStore, {
    createProfile(trigger) {
      switchTool('profiles');
      profilesPanel.openCreate({
        returnTo: 'gochara',
        requiredFor: 'horoscope',
        focusTarget: trigger,
        onSaved(profile) {
          gocharaProfiles?.selectProfile(profile.id);
        },
      });
    },
    editProfile(id, trigger) {
      switchTool('profiles');
      profilesPanel.openEdit(id, {
        returnTo: 'gochara',
        requiredFor: 'horoscope',
        focusTarget: trigger,
        onSaved(profile) {
          gocharaProfiles?.selectProfile(profile.id);
        },
      });
    },
    manageProfiles() {
      switchTool('profiles');
    },
  });
  tarabalamProfiles = initTarabalamProfiles(profileStore, {
    createProfile(trigger) {
      switchTool('profiles');
      profilesPanel.openCreate({
        returnTo: 'tarabalam',
        requiredFor: 'muhurta',
        focusTarget: trigger,
        onSaved(profile) {
          tarabalamProfiles?.selectProfile(profile.id);
        },
      });
    },
    editProfile(id, trigger) {
      switchTool('profiles');
      profilesPanel.openEdit(id, {
        returnTo: 'tarabalam',
        requiredFor: 'muhurta',
        focusTarget: trigger,
        onSaved(profile) {
          tarabalamProfiles?.selectProfile(profile.id);
        },
      });
    },
    manageProfiles() {
      switchTool('profiles');
    },
  });


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
    const savedCity = readBrowserPreference('tc-city');
    const savedSystem = readBrowserPreference('tc-system');
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
      writeBrowserPreference('tc-time-fmt', sel.timeFmt);
      applyTimeFmtUI();
      updateSettingsSummary();
      renderAll();
      if (tbHasDays()) renderTarabalam();
      if (goHasData()) renderGochara();
      if (muHasLast()) renderMuhurta();
    }
    if (changed.includes('city') || changed.includes('system')) {
      writeBrowserPreference('tc-city', sel.city);
      writeBrowserPreference('tc-system', sel.system);
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
  document.querySelectorAll('.sidebar-icon').forEach(icon => {
    icon.setAttribute('aria-hidden', 'true');
  });
  document.querySelectorAll<HTMLElement>('.app-tab').forEach(tab => {
    tab.addEventListener('keydown', event => {
      if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return;
      const tabs = [...document.querySelectorAll<HTMLElement>('.app-tab')];
      const current = tabs.indexOf(tab);
      const next = event.key === 'Home'
        ? 0
        : event.key === 'End'
          ? tabs.length - 1
          : (current + (event.key === 'ArrowRight' ? 1 : -1) + tabs.length) % tabs.length;
      event.preventDefault();
      showAppTab(tabs[next].dataset.app);
      tabs[next].focus();
    });
  });
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
    // Keep the compact one-shell drawer through narrow laptop/tablet widths.
    // Below 960px the 232px sidebar leaves too little room for Panchangam's
    // four-column evidence grid, even though the outer viewport looks wide.
    const mq = window.matchMedia('(max-width: 959px)');

    // --- sidebar drawer: the SAME #sidebar element as desktop, slid in ---
    const navBtn = document.getElementById('m-nav-btn');
    const sidebar = document.getElementById('sidebar') as HTMLElement;

    function setClosedDrawerState() {
      if (mq.matches && !document.body.classList.contains('m-nav-open')) {
        sidebar.inert = true;
        sidebar.setAttribute('aria-hidden', 'true');
      } else {
        sidebar.inert = false;
        sidebar.removeAttribute('aria-hidden');
      }
    }

    function openNav() {
      sidebar.inert = false;
      sidebar.removeAttribute('aria-hidden');
      document.body.classList.add('m-nav-open');
      navBtn.setAttribute('aria-expanded', 'true');
      navBtn.setAttribute('aria-label', 'Close navigation');
      modalOpen(sidebar,
                document.querySelector('#sidebar .sidebar-item.active') || undefined);
      if (typeof gcEvent === 'function') gcEvent('nav-open');
    }
    function closeNav() {
      const wasOpen = document.body.classList.contains('m-nav-open');
      if (wasOpen) {
        document.body.classList.remove('m-nav-open');
        modalClose(sidebar);
      }
      navBtn.setAttribute('aria-expanded', 'false');
      navBtn.setAttribute('aria-label', 'Open navigation');
      setClosedDrawerState();
    }

    function applyMode() {
      const mobile = mq.matches;
      document.body.dataset.mode = mobile ? 'mobile' : 'desktop';
      if (!mobile) closeNav();
      else setClosedDrawerState();
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
      openFestivalDate,
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
