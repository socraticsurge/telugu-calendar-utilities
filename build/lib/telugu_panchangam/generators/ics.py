# src/generators/ics.py
from datetime import timedelta
import pytz
from icalendar import Calendar, Event, vText

from telugu_panchangam.models.panchangam_day import PanchangamDay, Window
from telugu_panchangam.engines.base import ekadashi_name, GANDA_MOOLA_NAKSHATRAS


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

    def generate(self, days: list[PanchangamDay], system: str) -> bytes:
        cal = Calendar()
        cal.add('prodid', '-//Telugu Panchangam//EN')
        cal.add('version', '2.0')
        cal.add('x-wr-calname',
                f"AstroChaganti's Panchangam — {days[0].location.name} ({SYSTEM_LABELS[system]})")
        cal.add('x-wr-timezone', days[0].location.timezone)
        cal.add('x-wr-caldesc',
                'Telugu Panchangam: Tithi, Nakshatra, Yoga, Muhurtas, and special days')
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

    def _description(self, day: PanchangamDay, tz, next_day: PanchangamDay | None = None) -> str:
        fmt = self._fmt_time
        fmtr = lambda dt: self._fmt_time_rel(dt, tz, day.date)
        fmtw = lambda w: self._fmt_window(w, tz, day.date)
        lines = [
            f'{day.samvatsara}  ·  {day.maasam} Maasam  ·  {day.paksham} Paksham  ·  {day.vaaram}',
            f'Ayanam: {day.ayanam}  ·  Rituvu: {day.rituvu}',
            f'Sunrise {fmt(day.sunrise, tz)}  ·  Sunset {fmt(day.sunset, tz)}  ·  '
            f'Moonrise {fmt(day.moonrise, tz)}  ·  Moonset {fmt(day.moonset, tz)}',
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
        lines += [
            '',
            '─ Auspicious ─',
            f'  Brahma Muhurta   {fmtw(day.brahma_muhurta)}',
        ]
        if day.abhijit_muhurta:
            lines.append(f'  Abhijit Muhurta  {fmtw(day.abhijit_muhurta)}')
        for w in day.amrita_kalam:
            lines.append(f'  Amrita Kalam     {fmtw(w)}')
        lines += [
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
        if day.choghadiya:
            lines.append('')
            lines.append('─ Choghadiya ─')
            for w in day.choghadiya:
                lines.append(f'  {fmt(w.start, tz)} – {fmt(w.end, tz)}  {w.name}')
        if next_day is not None:
            weekday = (day.date.weekday() + 1) % 7  # 0=Sunday, engine convention
            names = _NIGHT_CHOGHADIYA[weekday]
            block = (next_day.sunrise - day.sunset) / 8
            lines.append('')
            lines.append('─ Night Choghadiya ─')
            for i in range(8):
                start = day.sunset + i * block
                end = day.sunset + (i + 1) * block
                lines.append(f'  {fmtr(start)} – {fmtr(end)}  {names[i]}')
        if day.eclipse:
            e = day.eclipse
            emoji = '🌒' if e.kind == 'Solar' else '🌕'
            visibility = 'visible from this location' if e.visible else 'not visible from this location'
            lines += [
                '',
                f'─ Eclipse ─',
                f'  {emoji} {e.kind} Eclipse ({e.subtype}) — {visibility}',
                f'  Window:   {self._fmt_eclipse_time(e.start, tz, day.date)} – {self._fmt_eclipse_time(e.end, tz, day.date)}',
            ]
            if e.visible:
                lines.append(
                    f'  Sutak:    {self._fmt_eclipse_time(e.sutak_start, tz, day.date)} – {self._fmt_eclipse_time(e.sutak_end, tz, day.date)}'
                )

        if day.special_yogas:
            lines += ['', '─ Special Yogas ─']
            for yoga in day.special_yogas:
                lines.append(f'  {yoga}')

        specials = list(day.festivals)
        if day.nakshatra.name in GANDA_MOOLA_NAKSHATRAS:
            specials.append(f'Ganda Moola ({day.nakshatra.name})')
        if day.is_ekadashi:        specials.append(f'{self._tithi_display(day)} — fasting day')
        if day.is_amavasya:        specials.append('Amavasya')
        if day.is_pournami:        specials.append('Pournami')
        if day.is_shani_pradosham: specials.append('Shani Pradosham')
        elif day.is_soma_pradosham: specials.append('Soma Pradosham')
        elif day.is_pradosham:     specials.append('Pradosham')
        if day.sankramanam and not (day.sankramanam == 'Makara'
                                    and 'Makara Sankranti' in day.festivals):
            specials.append(f'{day.sankramanam} Sankramanam')
        if day.eclipse:
            specials.append(f'{day.eclipse.kind} Eclipse ({day.eclipse.subtype})')
        if specials:
            lines += ['', '⚡ ' + '  ·  '.join(specials)]
        return '\n'.join(lines)
