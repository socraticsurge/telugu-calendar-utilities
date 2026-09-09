# src/generators/ics.py
from datetime import timedelta
from functools import partial

import pytz
from icalendar import Calendar, Event, vText

from telugu_panchangam.engines.base import ekadashi_name
from telugu_panchangam.models.panchangam_day import PanchangamDay, Window
from telugu_panchangam.panchangam_names import GANDA_MOOLA_NAKSHATRAS

SYSTEM_LABELS = {
    'drik': 'Drik Ganita',
    'surya_siddhanta': 'Surya Siddhanta',
    'vakya': 'Vakya',
}

# Night Choghadiya sequence (8 blocks from sunset to next sunrise), weekday
# 0=Sunday — same convention as the engines' day tables.
_NIGHT_CHOGHADIYA = {
    0: ['Shubh', 'Amrit', 'Char', 'Rog', 'Kaal', 'Labh', 'Udveg', 'Shubh'],
    1: ['Char', 'Rog', 'Kaal', 'Labh', 'Udveg', 'Shubh', 'Amrit', 'Char'],
    2: ['Kaal', 'Labh', 'Udveg', 'Shubh', 'Amrit', 'Char', 'Rog', 'Kaal'],
    3: ['Udveg', 'Shubh', 'Amrit', 'Char', 'Rog', 'Kaal', 'Labh', 'Udveg'],
    4: ['Amrit', 'Char', 'Rog', 'Kaal', 'Labh', 'Udveg', 'Shubh', 'Amrit'],
    5: ['Rog', 'Kaal', 'Labh', 'Udveg', 'Shubh', 'Amrit', 'Char', 'Rog'],
    6: ['Labh', 'Udveg', 'Shubh', 'Amrit', 'Char', 'Rog', 'Kaal', 'Labh'],
}


class ICSGenerator:

    def generate(self, days: list[PanchangamDay], system: str,
                 variant_label: str = '') -> bytes:
        """Generate an ICS calendar from a list of PanchangamDay.

        variant_label, if non-empty, is appended to the calendar name
        and rewrites the description — used by the per-anga variant
        feeds (Ekadashi-only, Festivals-only, Moon-Cycles) to give
        subscribers a distinguishable calendar in their client. Empty
        string preserves the existing dense-feed output byte-for-byte
        (sanity-checked by the golden-snapshot regression test).
        """
        cal = Calendar()
        cal.add('prodid', '-//Telugu Panchangam//EN')
        cal.add('version', '2.0')
        if variant_label:
            cal.add('x-wr-calname',
                    f"AstroChaganti's Panchangam — {days[0].location.name} "
                    f"({SYSTEM_LABELS[system]}, {variant_label})")
            cal.add('x-wr-caldesc',
                    f'Telugu Panchangam — {variant_label} only. '
                    f'Slim feed; subscribe to the dense feed for full daily detail.')
        else:
            cal.add('x-wr-calname',
                    f"AstroChaganti's Panchangam — {days[0].location.name} ({SYSTEM_LABELS[system]})")
            cal.add('x-wr-caldesc',
                    'Telugu Panchangam: Tithi, Nakshatra, Yoga, Muhurtas, and special days')
        cal.add('x-wr-timezone', days[0].location.timezone)
        # Hint clients to refetch twice a day so corrections propagate quickly
        cal.add('refresh-interval;value=duration', 'PT12H')
        cal.add('x-published-ttl', 'PT12H')

        for i, day in enumerate(days):
            next_day = days[i + 1] if i + 1 < len(days) else None
            cal.add_component(self._make_event(day, next_day))

        return cal.to_ical()

    def _make_event(self, day: PanchangamDay, next_day: PanchangamDay | None = None) -> Event:
        tz = pytz.timezone(day.location.timezone)
        event = Event()

        title = self._title(day)
        event.add('summary', vText(title))
        event.add('dtstart', day.date)
        event.add('dtend', day.date + timedelta(days=1))
        event.add('description', vText(self._description(day, tz, next_day)))
        city = day.location.name.lower().replace(' ', '-').replace(',', '')
        event.add('uid', f'{day.date.isoformat()}-{city}-{day.system}@telugu-panchangam')

        return event

    def _tithi_display(self, day: PanchangamDay) -> str:
        if day.is_ekadashi:
            name = ekadashi_name(day.maasam, day.paksham, day.solar_sign)
            if name:
                return f'{name} Ekadashi'
        return day.tithi.name

    def _title(self, day: PanchangamDay) -> str:
        base = f'{self._tithi_display(day)} · {day.nakshatra.name} · {day.yoga.name}'
        if day.festivals:
            return f'🪔 {" · ".join(day.festivals[:2])} — {base}'
        prefix = '⚡ ' if self._is_special(day) else ''
        return f'{prefix}{base}'

    def _is_special(self, day: PanchangamDay) -> bool:
        # Monthly sign transitions are informational, not special days —
        # Makara Sankranti is already a named festival.
        return any([day.is_ekadashi, day.is_amavasya, day.is_pournami,
                    day.is_pradosham, day.eclipse is not None])

    def _fmt_time(self, dt, tz) -> str:
        local = dt.astimezone(tz)
        return local.strftime('%H:%M')

    def _fmt_time_rel(self, dt, tz, day_date) -> str:
        """HH:MM, marked (+1)/(-1) when the instant falls outside `day_date`."""
        local = dt.astimezone(tz)
        suffix = ''
        if local.date() > day_date:
            suffix = ' (+1)'
        elif local.date() < day_date:
            suffix = ' (-1)'
        return f'{local.strftime("%H:%M")}{suffix}'

    def _fmt_window(self, w: Window, tz, day_date=None) -> str:
        if day_date is None:
            return f'{self._fmt_time(w.start, tz)} – {self._fmt_time(w.end, tz)}'
        return (f'{self._fmt_time_rel(w.start, tz, day_date)} – '
                f'{self._fmt_time_rel(w.end, tz, day_date)}')

    def _fmt_eclipse_time(self, dt, tz, day_date) -> str:
        local = dt.astimezone(tz)
        prefix = 'Previous day ' if local.date() < day_date else ''
        return f'{prefix}{local.strftime("%H:%M")}'

    def _description_header(self, day: PanchangamDay, tz) -> list[str]:
        fmt = self._fmt_time
        fmtr = partial(self._fmt_time_rel, tz=tz, day_date=day.date)
        lines = [
            (
                f'{day.samvatsara} Nama Samvatsara  ·  {day.maasam} Maasam  ·  '
                f'{day.paksham} Paksham  ·  {day.vaaram}'
            ),
            f'Ayanam: {day.ayanam}  ·  Rituvu: {day.rituvu}',
            (
                f'Sunrise {fmt(day.sunrise, tz)}  ·  '
                f'Sunset {fmt(day.sunset, tz)}  ·  '
                f'Moonrise {fmt(day.moonrise, tz)}  ·  '
                f'Moonset {fmt(day.moonset, tz)}'
            ),
            f'Solar sign: {day.solar_sign}  ·  Lunar sign: {day.lunar_sign}',
            '',
            f'Tithi:     {self._tithi_display(day):<18} {fmtr(day.tithi.start)} – {fmtr(day.tithi.end)}',
            f'Nakshatra: {day.nakshatra.name:<18} {fmtr(day.nakshatra.start)} – {fmtr(day.nakshatra.end)}',
            f'Yoga:      {day.yoga.name:<18} {fmtr(day.yoga.start)} – {fmtr(day.yoga.end)}',
        ]
        if day.karana:
            karana_str = '  /  '.join(f'{k.name} {fmtr(k.start)}–{fmtr(k.end)}'
                                      for k in day.karana)
            lines.append(f'Karana:    {karana_str}')
        return lines

    def _auspicious_lines(self, day: PanchangamDay, fmtw) -> list[str]:
        lines = [
            '',
            '─ Auspicious ─',
            f'  Brahma Muhurta   {fmtw(day.brahma_muhurta)}',
        ]
        if day.abhijit_muhurta:
            lines.append(f'  Abhijit Muhurta  {fmtw(day.abhijit_muhurta)}')
        for w in day.amrita_kalam:
            lines.append(f'  Amrita Kalam     {fmtw(w)}')
        return lines

    def _inauspicious_lines(self, day: PanchangamDay, fmtw) -> list[str]:
        lines = [
            '',
            '─ Inauspicious ─',
            f'  Rahu Kalam       {fmtw(day.rahu_kalam)}',
            f'  Gulika Kalam     {fmtw(day.gulika_kalam)}',
            f'  Yamagandam       {fmtw(day.yamagandam)}',
        ]
        for w in day.varjyam:
            lines.append(f'  Varjyam          {fmtw(w)}')
        for w in day.durmuhurtham:
            lines.append(f'  Durmuhurtham     {fmtw(w)}')
        return lines

    def _day_choghadiya_lines(self, day: PanchangamDay, tz) -> list[str]:
        if not day.choghadiya:
            return []
        lines = ['', '─ Choghadiya ─']
        for w in day.choghadiya:
            lines.append(
                f'  {self._fmt_time(w.start, tz)} – '
                f'{self._fmt_time(w.end, tz)}  {w.name}'
            )
        return lines

    def _night_choghadiya_lines(
        self, day: PanchangamDay, next_day: PanchangamDay | None, fmtr
    ) -> list[str]:
        if next_day is None:
            return []
        weekday = (day.date.weekday() + 1) % 7  # 0=Sunday, engine convention
        names = _NIGHT_CHOGHADIYA[weekday]
        block = (next_day.sunrise - day.sunset) / 8
        lines = ['', '─ Night Choghadiya ─']
        for i in range(8):
            start = day.sunset + i * block
            end = day.sunset + (i + 1) * block
            lines.append(f'  {fmtr(start)} – {fmtr(end)}  {names[i]}')
        return lines

    def _eclipse_lines(self, day: PanchangamDay, tz) -> list[str]:
        if not day.eclipse:
            return []
        eclipse = day.eclipse
        emoji = '🌒' if eclipse.kind == 'Solar' else '🌕'
        visibility = (
            'visible from this location'
            if eclipse.visible
            else 'not visible from this location'
        )
        lines = [
            '',
            '─ Eclipse ─',
            f'  {emoji} {eclipse.kind} Eclipse ({eclipse.subtype}) — {visibility}',
            (
                f'  Window:   '
                f'{self._fmt_eclipse_time(eclipse.start, tz, day.date)} – '
                f'{self._fmt_eclipse_time(eclipse.end, tz, day.date)}'
            ),
        ]
        if eclipse.visible:
            lines.append(
                f'  Sutak:    '
                f'{self._fmt_eclipse_time(eclipse.sutak_start, tz, day.date)} – '
                f'{self._fmt_eclipse_time(eclipse.sutak_end, tz, day.date)}'
            )
        return lines

    def _special_yoga_lines(self, day: PanchangamDay) -> list[str]:
        if not day.special_yogas:
            return []
        return ['', '─ Special Yogas ─', *(f'  {yoga}' for yoga in day.special_yogas)]

    def _pradosham_special(self, day: PanchangamDay) -> str | None:
        if day.is_shani_pradosham:
            return 'Shani Pradosham'
        if day.is_soma_pradosham:
            return 'Soma Pradosham'
        if day.is_pradosham:
            return 'Pradosham'
        return None

    def _sankramanam_special(self, day: PanchangamDay) -> str | None:
        if not day.sankramanam:
            return None
        if day.sankramanam == 'Makara' and 'Makara Sankranti' in day.festivals:
            return None
        return f'{day.sankramanam} Sankramanam'

    def _description_specials(self, day: PanchangamDay) -> list[str]:
        specials = list(day.festivals)
        conditional_specials = (
            (
                day.nakshatra.name in GANDA_MOOLA_NAKSHATRAS,
                f'Ganda Moola ({day.nakshatra.name})',
            ),
            (day.is_ekadashi, f'{self._tithi_display(day)} — fasting day'),
            (day.is_amavasya, 'Amavasya'),
            (day.is_pournami, 'Pournami'),
        )
        specials.extend(
            label for enabled, label in conditional_specials if enabled
        )
        pradosham = self._pradosham_special(day)
        if pradosham:
            specials.append(pradosham)
        sankramanam = self._sankramanam_special(day)
        if sankramanam:
            specials.append(sankramanam)
        if day.eclipse:
            specials.append(f'{day.eclipse.kind} Eclipse ({day.eclipse.subtype})')
        return specials

    def _special_lines(self, day: PanchangamDay) -> list[str]:
        specials = self._description_specials(day)
        if not specials:
            return []
        return ['', '⚡ ' + '  ·  '.join(specials)]

    def _description(
        self, day: PanchangamDay, tz, next_day: PanchangamDay | None = None
    ) -> str:
        fmtr = partial(self._fmt_time_rel, tz=tz, day_date=day.date)
        fmtw = partial(self._fmt_window, tz=tz, day_date=day.date)
        lines = self._description_header(day, tz)
        lines.extend(self._auspicious_lines(day, fmtw))
        lines.extend(self._inauspicious_lines(day, fmtw))
        lines.extend(self._day_choghadiya_lines(day, tz))
        lines.extend(self._night_choghadiya_lines(day, next_day, fmtr))
        lines.extend(self._eclipse_lines(day, tz))
        lines.extend(self._special_yoga_lines(day))
        lines.extend(self._special_lines(day))
        return '\n'.join(lines)
