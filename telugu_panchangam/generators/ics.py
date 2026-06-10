# src/generators/ics.py
from datetime import timedelta
import pytz
from icalendar import Calendar, Event, vText

from telugu_panchangam.models.panchangam_day import PanchangamDay, Window


SYSTEM_LABELS = {
    'drik': 'Drik Ganita',
    'surya_siddhanta': 'Surya Siddhanta',
    'vakya': 'Vakya',
}


class ICSGenerator:

    def generate(self, days: list[PanchangamDay], system: str) -> bytes:
        cal = Calendar()
        cal.add('prodid', '-//Telugu Panchangam//EN')
        cal.add('version', '2.0')
        cal.add('x-wr-calname',
                f'Telugu Panchangam — {days[0].location.name} ({SYSTEM_LABELS[system]})')
        cal.add('x-wr-timezone', days[0].location.timezone)
        cal.add('x-wr-caldesc',
                'Telugu Panchangam: Tithi, Nakshatra, Yoga, Muhurtas, and special days')

        for day in days:
            cal.add_component(self._make_event(day))

        return cal.to_ical()

    def _make_event(self, day: PanchangamDay) -> Event:
        tz = pytz.timezone(day.location.timezone)
        event = Event()

        title = self._title(day)
        event.add('summary', vText(title))
        event.add('dtstart', day.date)
        event.add('dtend', day.date + timedelta(days=1))
        event.add('description', vText(self._description(day, tz)))
        city = day.location.name.lower().replace(' ', '-').replace(',', '')
        event.add('uid', f'{day.date.isoformat()}-{city}-{day.system}@telugu-panchangam')

        return event

    def _title(self, day: PanchangamDay) -> str:
        prefix = '⚡ ' if self._is_special(day) else ''
        return f'{prefix}{day.tithi.name} · {day.nakshatra.name} · {day.yoga.name}'

    def _is_special(self, day: PanchangamDay) -> bool:
        return any([day.is_ekadashi, day.is_amavasya, day.is_pournami,
                    day.is_pradosham, day.is_sankranti, day.eclipse is not None])

    def _fmt_time(self, dt, tz) -> str:
        local = dt.astimezone(tz)
        return local.strftime('%H:%M')

    def _fmt_window(self, w: Window, tz) -> str:
        return f'{self._fmt_time(w.start, tz)} – {self._fmt_time(w.end, tz)}'

    def _fmt_eclipse_time(self, dt, tz, day_date) -> str:
        local = dt.astimezone(tz)
        prefix = 'Previous day ' if local.date() < day_date else ''
        return f'{prefix}{local.strftime("%H:%M")}'

    def _description(self, day: PanchangamDay, tz) -> str:
        fmt = self._fmt_time
        fmtw = self._fmt_window
        lines = [
            f'{day.samvatsara}  ·  {day.maasam} Maasam  ·  {day.paksham} Paksham  ·  {day.vaaram}',
            f'Ayanam: {day.ayanam}  ·  Rituvu: {day.rituvu}',
            f'Sunrise {fmt(day.sunrise, tz)}  ·  Sunset {fmt(day.sunset, tz)}  ·  '
            f'Moonrise {fmt(day.moonrise, tz)}  ·  Moonset {fmt(day.moonset, tz)}',
            f'Solar sign: {day.solar_sign}  ·  Lunar sign: {day.lunar_sign}',
            '',
            f'Tithi:     {day.tithi.name:<18} {fmt(day.tithi.start, tz)} – {fmt(day.tithi.end, tz)}',
            f'Nakshatra: {day.nakshatra.name:<18} {fmt(day.nakshatra.start, tz)} – {fmt(day.nakshatra.end, tz)}',
            f'Yoga:      {day.yoga.name:<18} {fmt(day.yoga.start, tz)} – {fmt(day.yoga.end, tz)}',
        ]
        if day.karana:
            karana_str = '  /  '.join(f'{k.name} {fmt(k.start, tz)}–{fmt(k.end, tz)}'
                                      for k in day.karana)
            lines.append(f'Karana:    {karana_str}')
        lines += [
            '',
            '─ Auspicious ─',
            f'  Brahma Muhurta   {fmtw(day.brahma_muhurta, tz)}',
        ]
        if day.abhijit_muhurta:
            lines.append(f'  Abhijit Muhurta  {fmtw(day.abhijit_muhurta, tz)}')
        for w in day.amrita_kalam:
            lines.append(f'  Amrita Kalam     {fmtw(w, tz)}')
        lines += [
            '',
            '─ Inauspicious ─',
            f'  Rahu Kalam       {fmtw(day.rahu_kalam, tz)}',
            f'  Gulika Kalam     {fmtw(day.gulika_kalam, tz)}',
            f'  Yamagandam       {fmtw(day.yamagandam, tz)}',
        ]
        for w in day.varjyam:
            lines.append(f'  Varjyam          {fmtw(w, tz)}')
        for w in day.durmuhurtham:
            lines.append(f'  Durmuhurtham     {fmtw(w, tz)}')
        if day.choghadiya:
            lines.append('')
            lines.append('─ Choghadiya ─')
            for w in day.choghadiya:
                lines.append(f'  {fmt(w.start, tz)} – {fmt(w.end, tz)}  {w.name}')
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

        specials = []
        if day.is_ekadashi:        specials.append('Ekadashi — fasting day')
        if day.is_amavasya:        specials.append('Amavasya')
        if day.is_pournami:        specials.append('Pournami')
        if day.is_shani_pradosham: specials.append('Shani Pradosham')
        elif day.is_soma_pradosham: specials.append('Soma Pradosham')
        elif day.is_pradosham:     specials.append('Pradosham')
        if day.is_sankranti:       specials.append('Sankranti')
        if day.eclipse:
            specials.append(f'{day.eclipse.kind} Eclipse ({day.eclipse.subtype})')
        if specials:
            lines += ['', '⚡ ' + '  ·  '.join(specials)]
        return '\n'.join(lines)
